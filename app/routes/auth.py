from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from app import db
from models import User, Church, ROLES
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
                flash('Password changed successfully', 'success')
                return redirect('/dashboard')
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {str(e)}', 'danger')
    return render_template('auth/change_password.html')
