from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import db
from models import Member, TitheRecord, Offering, log_audit
from datetime import datetime

finances_bp = Blueprint('finances', __name__, url_prefix='/finances')

@finances_bp.route('/')
@login_required
def dashboard():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    page_t = request.args.get('page_t', 1, type=int)
    page_o = request.args.get('page_o', 1, type=int)
    per_page = 25
    tithes = TitheRecord.query.filter_by(church_id=cid).order_by(TitheRecord.date.desc()).paginate(
        page=page_t, per_page=per_page, error_out=False)
    offerings = Offering.query.filter_by(church_id=cid).order_by(Offering.date.desc()).paginate(
        page=page_o, per_page=per_page, error_out=False)
    members = Member.query.filter_by(church_id=cid, membership_status='active').order_by(Member.full_name).all()
    return render_template('finances/dashboard.html', tithes=tithes, offerings=offerings, members=members)

@finances_bp.route('/member/<int:member_id>')
@login_required
def member_statement(member_id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    member = Member.query.filter_by(id=member_id, church_id=cid).first()
    if not member:
        flash('Member not found', 'danger')
        return redirect(url_for('finances.dashboard'))
    tithes = TitheRecord.query.filter_by(church_id=cid, member_id=member_id).order_by(TitheRecord.date.desc()).all()
    offerings = Offering.query.filter_by(church_id=cid, member_id=member_id).order_by(Offering.date.desc()).all()
    total_tithes = sum(t.amount for t in tithes)
    total_offerings = sum(o.amount for o in offerings)
    return render_template('finances/member_statement.html',
        member=member, tithes=tithes, offerings=offerings,
        total_tithes=total_tithes, total_offerings=total_offerings)

@finances_bp.route('/tithe/add', methods=['GET', 'POST'])
@login_required
def add_tithe():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if request.method == 'POST':
        try:
            t = TitheRecord(
                church_id=cid,
                member_id=request.form['member_id'],
                amount=float(request.form['amount']),
                date=request.form['date'],
                period_month=int(request.form['period_month']),
                period_year=int(request.form['period_year']),
                notes=request.form.get('notes', ''),
            )
            db.session.add(t)
            db.session.commit()
            log_audit(cid, current_user.id, 'create', 'tithe', t.id, f'Added tithe: {t.amount}')
            flash('Tithe recorded successfully', 'success')
            return redirect(url_for('finances.dashboard'))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording tithe: {str(e)}', 'danger')
    members = Member.query.filter_by(church_id=cid, membership_status='active').order_by(Member.full_name).all()
    return render_template('finances/tithe_form.html', members=members,
                          current_year=datetime.now().year, current_month=datetime.now().month)

@finances_bp.route('/tithe/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tithe(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    t = TitheRecord.query.filter_by(id=id, church_id=cid).first()
    if not t:
        flash('Tithe record not found', 'danger')
        return redirect(url_for('finances.dashboard'))
    if request.method == 'POST':
        try:
            t.member_id = request.form['member_id']
            t.amount = float(request.form['amount'])
            t.date = request.form['date']
            t.period_month = int(request.form['period_month'])
            t.period_year = int(request.form['period_year'])
            t.notes = request.form.get('notes', '')
            db.session.commit()
            log_audit(cid, current_user.id, 'update', 'tithe', t.id, f'Updated tithe: {t.amount}')
            flash('Tithe updated', 'success')
            return redirect(url_for('finances.dashboard'))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating tithe: {str(e)}', 'danger')
    members = Member.query.filter_by(church_id=cid, membership_status='active').order_by(Member.full_name).all()
    return render_template('finances/tithe_form.html', tithe=t, members=members,
                          current_year=datetime.now().year, current_month=datetime.now().month)

@finances_bp.route('/tithe/delete/<int:id>', methods=['POST'])
@login_required
def delete_tithe(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if not current_user.can_delete:
        flash('Only admins can delete records', 'danger')
        return redirect(url_for('finances.dashboard'))
    t = TitheRecord.query.filter_by(id=id, church_id=cid).first()
    if not t:
        flash('Tithe record not found', 'danger')
        return redirect(url_for('finances.dashboard'))
    try:
        db.session.delete(t)
        db.session.commit()
        log_audit(cid, current_user.id, 'delete', 'tithe', id, f'Deleted tithe record')
        flash('Tithe record deleted', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting tithe: {str(e)}', 'danger')
    return redirect(url_for('finances.dashboard'))

@finances_bp.route('/offering/add', methods=['GET', 'POST'])
@login_required
def add_offering():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if request.method == 'POST':
        try:
            o = Offering(
                church_id=cid,
                member_id=request.form.get('member_id') or None,
                amount=float(request.form['amount']),
                date=request.form['date'],
                category=request.form['category'],
                notes=request.form.get('notes', ''),
            )
            db.session.add(o)
            db.session.commit()
            log_audit(cid, current_user.id, 'create', 'offering', o.id, f'Added offering: {o.amount}')
            flash('Offering recorded successfully', 'success')
            return redirect(url_for('finances.dashboard'))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording offering: {str(e)}', 'danger')
    members = Member.query.filter_by(church_id=cid, membership_status='active').order_by(Member.full_name).all()
    return render_template('finances/offering_form.html', members=members,
                          current_date=datetime.now().strftime('%Y-%m-%d'))

@finances_bp.route('/offering/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_offering(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    o = Offering.query.filter_by(id=id, church_id=cid).first()
    if not o:
        flash('Offering record not found', 'danger')
        return redirect(url_for('finances.dashboard'))
    if request.method == 'POST':
        try:
            o.member_id = request.form.get('member_id') or None
            o.amount = float(request.form['amount'])
            o.date = request.form['date']
            o.category = request.form['category']
            o.notes = request.form.get('notes', '')
            db.session.commit()
            log_audit(cid, current_user.id, 'update', 'offering', o.id, f'Updated offering: {o.amount}')
            flash('Offering updated', 'success')
            return redirect(url_for('finances.dashboard'))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating offering: {str(e)}', 'danger')
    members = Member.query.filter_by(church_id=cid, membership_status='active').order_by(Member.full_name).all()
    return render_template('finances/offering_form.html', offering=o, members=members,
                          current_date=datetime.now().strftime('%Y-%m-%d'))

@finances_bp.route('/offering/delete/<int:id>', methods=['POST'])
@login_required
def delete_offering(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if not current_user.can_delete:
        flash('Only admins can delete records', 'danger')
        return redirect(url_for('finances.dashboard'))
    o = Offering.query.filter_by(id=id, church_id=cid).first()
    if not o:
        flash('Offering record not found', 'danger')
        return redirect(url_for('finances.dashboard'))
    try:
        db.session.delete(o)
        db.session.commit()
        log_audit(cid, current_user.id, 'delete', 'offering', id, f'Deleted offering record')
        flash('Offering record deleted', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting offering: {str(e)}', 'danger')
    return redirect(url_for('finances.dashboard'))
