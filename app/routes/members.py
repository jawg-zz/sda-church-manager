from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import db
from models import Member, Church

members_bp = Blueprint('members', __name__, url_prefix='/members')

@members_bp.route('/')
@login_required
def list_members():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', 'all')
    search = request.args.get('search', '')
    query = Member.query.filter_by(church_id=cid).order_by(Member.full_name)
    if status != 'all':
        query = query.filter_by(membership_status=status)
    if search:
        query = query.filter(Member.full_name.ilike(f'%{search}%'))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('members/list.html', members=pagination.items,
                           pagination=pagination, status=status, search=search)

@members_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_member():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        if not full_name:
            flash('Full name is required', 'danger')
            return render_template('members/form.html', member=None)
        try:
            member = Member(
                church_id=cid,
                full_name=full_name,
                date_of_birth=request.form.get('date_of_birth', ''),
                gender=request.form.get('gender', ''),
                phone=request.form.get('phone', ''),
                email=request.form.get('email', ''),
                address=request.form.get('address', ''),
                membership_status=request.form.get('membership_status', 'active'),
                baptism_date=request.form.get('baptism_date', ''),
                baptism_location=request.form.get('baptism_location', ''),
                baptism_by=request.form.get('baptism_by', ''),
                join_date=request.form.get('join_date', ''),
                transfer_from=request.form.get('transfer_from', ''),
                tribe=request.form.get('tribe', ''),
                language=request.form.get('language', ''),
                occupation=request.form.get('occupation', ''),
                education_level=request.form.get('education_level', ''),
                emergency_contact=request.form.get('emergency_contact', ''),
                emergency_phone=request.form.get('emergency_phone', ''),
                notes=request.form.get('notes', ''),
            )
            db.session.add(member)
            db.session.commit()
            flash('Member added successfully', 'success')
            return redirect(url_for('members.list_members'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding member: {str(e)}', 'danger')
    return render_template('members/form.html', member=None)

@members_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_member(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    member = Member.query.filter_by(id=id, church_id=cid).first()
    if not member:
        flash('Member not found', 'danger')
        return redirect(url_for('members.list_members'))
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        if not full_name:
            flash('Full name is required', 'danger')
            return render_template('members/form.html', member=member)
        try:
            member.full_name = full_name
            member.date_of_birth = request.form.get('date_of_birth', '')
            member.gender = request.form.get('gender', '')
            member.phone = request.form.get('phone', '')
            member.email = request.form.get('email', '')
            member.address = request.form.get('address', '')
            member.membership_status = request.form.get('membership_status', 'active')
            member.baptism_date = request.form.get('baptism_date', '')
            member.baptism_location = request.form.get('baptism_location', '')
            member.baptism_by = request.form.get('baptism_by', '')
            member.join_date = request.form.get('join_date', '')
            member.transfer_from = request.form.get('transfer_from', '')
            member.tribe = request.form.get('tribe', '')
            member.language = request.form.get('language', '')
            member.occupation = request.form.get('occupation', '')
            member.education_level = request.form.get('education_level', '')
            member.emergency_contact = request.form.get('emergency_contact', '')
            member.emergency_phone = request.form.get('emergency_phone', '')
            member.notes = request.form.get('notes', '')
            db.session.commit()
            flash('Member updated successfully', 'success')
            return redirect(url_for('members.list_members'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating member: {str(e)}', 'danger')
    return render_template('members/form.html', member=member)

@members_bp.route('/view/<int:id>')
@login_required
def view_member(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    member = Member.query.filter_by(id=id, church_id=cid).first()
    if not member:
        flash('Member not found', 'danger')
        return redirect(url_for('members.list_members'))
    return render_template('members/view.html', member=member)

@members_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_member(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if not current_user.can_delete:
        flash('Only admins can delete records', 'danger')
        return redirect(url_for('members.list_members'))
    member = Member.query.filter_by(id=id, church_id=cid).first()
    if not member:
        flash('Member not found', 'danger')
        return redirect(url_for('members.list_members'))
    try:
        db.session.delete(member)
        db.session.commit()
        flash('Member deleted', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting member: {str(e)}', 'danger')
    return redirect(url_for('members.list_members'))

@members_bp.route('/transfer/<int:id>', methods=['GET', 'POST'])
@login_required
def transfer_member(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if not current_user.can_manage_users:
        flash('Only admins can transfer members', 'danger')
        return redirect(url_for('members.list_members'))
    member = Member.query.filter_by(id=id, church_id=cid).first()
    if not member:
        flash('Member not found', 'danger')
        return redirect(url_for('members.list_members'))
    churches = Church.query.filter(Church.id != cid).order_by(Church.name).all()
    if request.method == 'POST':
        target_church_id = request.form.get('target_church_id', type=int)
        transfer_date = request.form.get('transfer_date', '').strip()
        reason = request.form.get('reason', '').strip()
        if not target_church_id:
            flash('Please select a target church', 'danger')
            return render_template('members/transfer.html', member=member, churches=churches)
        target_church = Church.query.get(target_church_id)
        if not target_church:
            flash('Target church not found', 'danger')
            return render_template('members/transfer.html', member=member, churches=churches)
        try:
            old_church = Church.query.get(cid)
            member.transfer_from = old_church.name if old_church else ''
            member.membership_status = 'transferred'
            member.church_id = target_church_id
            if reason:
                member.notes = (member.notes or '') + f'\n[Transfer {transfer_date or "N/A"} to {target_church.name}]: {reason}'
            db.session.commit()
            flash(f'{member.full_name} has been transferred to {target_church.name}', 'success')
            return redirect(url_for('members.list_members'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error transferring member: {str(e)}', 'danger')
    return render_template('members/transfer.html', member=member, churches=churches)
