from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import Member

members_bp = Blueprint('members', __name__, url_prefix='/members')

@members_bp.route('/')
def list_members():
    status = request.args.get('status', 'all')
    search = request.args.get('search', '')
    query = Member.query.order_by(Member.full_name)
    if status != 'all':
        query = query.filter_by(membership_status=status)
    if search:
        query = query.filter(Member.full_name.ilike(f'%{search}%'))
    members = query.all()
    return render_template('members/list.html', members=members, status=status, search=search)

@members_bp.route('/add', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        member = Member(
            full_name=request.form['full_name'],
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
    return render_template('members/form.html', member=None)

@members_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_member(id):
    member = Member.query.get_or_404(id)
    if request.method == 'POST':
        member.full_name = request.form['full_name']
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
    return render_template('members/form.html', member=member)

@members_bp.route('/view/<int:id>')
def view_member(id):
    member = Member.query.get_or_404(id)
    return render_template('members/view.html', member=member)

@members_bp.route('/delete/<int:id>', methods=['POST'])
def delete_member(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    flash('Member deleted', 'warning')
    return redirect(url_for('members.list_members'))
