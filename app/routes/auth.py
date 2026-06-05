from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from app import db
from models import User, Church, ROLES, log_audit
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.can_manage_users:
            flash('Admin access required', 'danger')
            return redirect('/dashboard')
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            log_audit(user.church_id, user.id, 'login', 'user', user.id, f'User {user.username} logged in')
            # Auto-select church if user belongs to only one
            churches = Church.query.filter_by(id=user.church_id).all() if user.church_id else []
            if len(churches) == 1:
                session['church_id'] = churches[0].id
            elif user.role == 'admin' and not user.church_id:
                # Super admin - no church assigned yet
                pass
            flash('Logged in successfully', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or '/dashboard')
        flash('Invalid username or password', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    if request.method == 'POST':
        church_name = request.form.get('church_name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not church_name or not username or not password:
            flash('All fields are required', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return render_template('auth/register.html')
        church = Church(name=church_name)
        db.session.add(church)
        db.session.flush()
        user = User(username=username, role='admin', church_id=church.id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        log_audit(church.id, user.id, 'register', 'church', church.id, f'Church {church_name} registered by {username}')
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')


@auth_bp.route('/select-church', methods=['GET', 'POST'])
@login_required
def select_church():
    if current_user.church_id:
        session['church_id'] = current_user.church_id
        return redirect('/dashboard')
    # Admin without church - show all churches
    churches = Church.query.order_by(Church.name).all()
    if request.method == 'POST':
        church_id = request.form.get('church_id', type=int)
        if church_id:
            session['church_id'] = church_id
            return redirect('/dashboard')
        flash('Select a church', 'warning')
    return render_template('auth/select_church.html', churches=churches)


@auth_bp.route('/logout')
@login_required
def logout():
    session.pop('church_id', None)
    logout_user()
    flash('Logged out', 'warning')
    return redirect(url_for('auth.login'))


@auth_bp.route('/switch-church/<int:church_id>')
@login_required
def switch_church(church_id):
    # Verify user has access to this church
    if current_user.role != 'admin' and current_user.church_id and current_user.church_id != church_id:
        flash('You do not have access to this church', 'danger')
        return redirect('/dashboard')
    from models import Church
    church = Church.query.get(church_id)
    if not church:
        flash('Church not found', 'danger')
        return redirect('/dashboard')
    session['church_id'] = church_id
    session.modified = True
    flash(f'Switched to {church.name}', 'success')
    resp = redirect('/dashboard')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@auth_bp.route('/users')
@admin_required
def list_users():
    users = User.query.filter_by(church_id=session.get('church_id')).order_by(User.username).all()
    return render_template('auth/users.html', users=users, ROLES=ROLES)


@auth_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'clerk')
        department = request.form.get('department', '').strip()
        cid = session.get('church_id')
        if not username or not password:
            flash('Username and password are required', 'danger')
        elif len(password) < 4:
            flash('Password must be at least 4 characters', 'danger')
        elif User.query.filter_by(username=username, church_id=cid).first():
            flash('Username already exists in this church', 'danger')
        elif role not in ROLES:
            flash('Invalid role', 'danger')
        else:
            try:
                user = User(username=username, role=role, department=department or None, church_id=cid)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                log_audit(cid, current_user.id, 'create', 'user', user.id, f'Created user: {username}')
                flash(f'User {username} created', 'success')
                return redirect(url_for('auth.list_users'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating user: {str(e)}', 'danger')
    return render_template('auth/user_form.html', user=None, ROLES=ROLES)


@auth_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    if user.church_id != session.get('church_id'):
        flash('Access denied', 'danger')
        return redirect(url_for('auth.list_users'))
    if request.method == 'POST':
        role = request.form.get('role', user.role)
        department = request.form.get('department', '').strip()
        new_password = request.form.get('password', '').strip()
        if role not in ROLES:
            flash('Invalid role', 'danger')
        else:
            try:
                user.role = role
                user.department = department or None
                if new_password:
                    if len(new_password) < 4:
                        flash('Password must be at least 4 characters', 'danger')
                        return render_template('auth/user_form.html', user=user, ROLES=ROLES)
                    user.set_password(new_password)
                db.session.commit()
                log_audit(session.get('church_id'), current_user.id, 'update', 'user', user.id, f'Updated user: {user.username}')
                flash(f'User {user.username} updated', 'success')
                return redirect(url_for('auth.list_users'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating user: {str(e)}', 'danger')
    return render_template('auth/user_form.html', user=user, ROLES=ROLES)


@auth_bp.route('/users/delete/<int:id>', methods=['POST'])
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Cannot delete your own account', 'danger')
        return redirect(url_for('auth.list_users'))
    try:
        db.session.delete(user)
        db.session.commit()
        log_audit(session.get('church_id'), current_user.id, 'delete', 'user', id, f'Deleted user: {user.username}')
        flash(f'User {user.username} deleted', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    return redirect(url_for('auth.list_users'))


@auth_bp.route('/churches')
@admin_required
def list_churches():
    from sqlalchemy import func
    from models import Member, TitheRecord, Baptism
    churches = Church.query.order_by(Church.name).all()
    stats = {}
    for c in churches:
        member_count = Member.query.filter_by(church_id=c.id, membership_status='active').count()
        tithe_total = db.session.query(func.sum(TitheRecord.amount)).filter(
            TitheRecord.church_id == c.id).scalar() or 0
        baptism_count = Baptism.query.filter_by(church_id=c.id).count()
        stats[c.id] = {'members': member_count, 'tithes': float(tithe_total), 'baptisms': baptism_count}
    return render_template('auth/churches.html', churches=churches, stats=stats)


@auth_bp.route('/churches/add', methods=['GET', 'POST'])
@admin_required
def add_church():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Church name is required', 'danger')
        else:
            try:
                church = Church(
                    name=name,
                    location=request.form.get('location', ''),
                    district=request.form.get('district', ''),
                    region=request.form.get('region', ''),
                    phone=request.form.get('phone', ''),
                    email=request.form.get('email', ''),
                )
                db.session.add(church)
                db.session.commit()
                log_audit(session.get('church_id'), current_user.id, 'create', 'church', church.id, f'Created church: {name}')
                flash(f'Church "{name}" created', 'success')
                return redirect(url_for('auth.list_churches'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {str(e)}', 'danger')
    return render_template('auth/church_form.html', church=None)


@auth_bp.route('/churches/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_church(id):
    church = Church.query.get_or_404(id)
    if request.method == 'POST':
        church.name = request.form.get('name', church.name)
        church.location = request.form.get('location', '')
        church.district = request.form.get('district', '')
        church.region = request.form.get('region', '')
        church.phone = request.form.get('phone', '')
        church.email = request.form.get('email', '')
        try:
            db.session.commit()
            log_audit(session.get('church_id'), current_user.id, 'update', 'church', church.id, f'Updated church: {church.name}')
            flash('Church updated', 'success')
            return redirect(url_for('auth.list_churches'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('auth/church_form.html', church=church)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current = request.form.get('current_password', '')
        new = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        if not current_user.check_password(current):
            flash('Current password is incorrect', 'danger')
        elif len(new) < 4:
            flash('New password must be at least 4 characters', 'danger')
        elif new != confirm:
            flash('New passwords do not match', 'danger')
        else:
            try:
                current_user.set_password(new)
                db.session.commit()
                log_audit(session.get('church_id'), current_user.id, 'update', 'user', current_user.id, f'Password changed for user: {current_user.username}')
                flash('Password changed successfully', 'success')
                return redirect('/dashboard')
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {str(e)}', 'danger')
    return render_template('auth/change_password.html')


@auth_bp.route('/clear-demo', methods=['POST'])
@admin_required
def clear_demo():
    from seed import clear_demo_data
    from models import (Church, User, Member, TitheRecord, Offering,
        SabbathSchoolClass, SabbathSchoolAttendance, Baptism, ChurchOfficer, Event)
    models = {'Church': Church, 'User': User, 'Member': Member,
        'TitheRecord': TitheRecord, 'Offering': Offering,
        'SabbathSchoolClass': SabbathSchoolClass,
        'SabbathSchoolAttendance': SabbathSchoolAttendance,
        'Baptism': Baptism, 'ChurchOfficer': ChurchOfficer, 'Event': Event}
    clear_demo_data(db, models)
    session.pop('church_id', None)
    flash('All data cleared. Restart app to seed fresh data.', 'warning')
    return redirect('/dashboard')


@auth_bp.route('/audit-log')
@login_required
def audit_log():
    if not (current_user.can_manage_users or current_user.role == 'pastor'):
        flash('Access denied', 'danger')
        return redirect('/dashboard')
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    entity_filter = request.args.get('entity', '')
    from models import AuditLog, User
    query = AuditLog.query.filter_by(church_id=cid)
    if action_filter:
        query = query.filter_by(action=action_filter)
    if entity_filter:
        query = query.filter_by(entity=entity_filter)
    pagination = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False)
    # Get user names for display
    user_ids = {log.user_id for log in pagination.items if log.user_id}
    users = {u.id: u.username for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return render_template('auth/audit_log.html', logs=pagination.items,
        pagination=pagination, users=users, action_filter=action_filter,
        entity_filter=entity_filter)


@auth_bp.route('/api/sync', methods=['POST'])
@login_required
def sync_offline():
    """Accept batch of offline records and process them."""
    cid = session.get('church_id')
    if not cid:
        return jsonify({'error': 'No church selected'}), 400
    from models import Member, TitheRecord, Offering, Baptism, Event, log_audit
    from flask import jsonify
    data = request.get_json(silent=True) or request.form
    items = data.get('items', []) if isinstance(data, dict) else []
    if not items:
        return jsonify({'error': 'No items'}), 400
    created = 0
    errors = []
    for item in items:
        try:
            url = item.get('url', '')
            payload = item.get('payload', {})
            if '/members/add' in url:
                m = Member(church_id=cid, full_name=payload.get('full_name', ''),
                    phone=payload.get('phone', ''), email=payload.get('email', ''),
                    gender=payload.get('gender', ''), membership_status=payload.get('membership_status', 'active'))
                db.session.add(m)
                db.session.flush()
                log_audit(cid, current_user.id, 'create', 'member', m.id, f'Offline sync: {m.full_name}')
            elif '/tithe/add' in url:
                t = TitheRecord(church_id=cid, member_id=int(payload.get('member_id', 0)),
                    amount=float(payload.get('amount', 0)), date=payload.get('date', ''),
                    period_month=int(payload.get('period_month', 1)), period_year=int(payload.get('period_year', 2026)))
                db.session.add(t)
                db.session.flush()
                log_audit(cid, current_user.id, 'create', 'tithe', t.id, 'Offline sync tithe')
            elif '/offering/add' in url:
                o = Offering(church_id=cid, member_id=int(payload.get('member_id', 0)) or None,
                    amount=float(payload.get('amount', 0)), date=payload.get('date', ''),
                    category=payload.get('category', 'General'))
                db.session.add(o)
                db.session.flush()
                log_audit(cid, current_user.id, 'create', 'offering', o.id, 'Offline sync offering')
            elif '/baptisms/add' in url:
                b = Baptism(church_id=cid, member_id=int(payload.get('member_id', 0)),
                    baptism_date=payload.get('baptism_date', ''), baptizer=payload.get('baptizer', ''),
                    location=payload.get('location', ''))
                db.session.add(b)
                db.session.flush()
                log_audit(cid, current_user.id, 'create', 'baptism', b.id, 'Offline sync baptism')
            elif '/events/add' in url:
                e = Event(church_id=cid, title=payload.get('title', ''),
                    date=payload.get('date', ''), time=payload.get('time', ''),
                    location=payload.get('location', ''), event_type=payload.get('event_type', ''))
                db.session.add(e)
                db.session.flush()
                log_audit(cid, current_user.id, 'create', 'event', e.id, 'Offline sync event')
            created += 1
        except Exception as ex:
            errors.append(str(ex))
    db.session.commit()
    return jsonify({'created': created, 'errors': errors})
