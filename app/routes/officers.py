from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import ChurchOfficer, Member

officers_bp = Blueprint('officers', __name__, url_prefix='/officers')

ROLES = [
    'Senior Pastor', 'Associate Pastor', 'Head Elder', 'Elder',
    'Head Deacon', 'Deacon', 'Head Deaconess', 'Deaconess',
    'Church Clerk', 'Assistant Church Clerk', 'Treasurer',
    'Assistant Treasurer', 'Sabbath School Superintendent',
    'Youth Leader', 'Children\'s Ministries Leader',
    'Communications Secretary', 'Music Director',
    'Personal Ministries Leader', 'Health Ministries Leader',
    'Women\'s Ministries Leader', 'Adventist Men\'s Leader',
    'Stewardship Leader', 'Education Secretary'
]

DEPARTMENTS = [
    'General', 'Sabbath School', 'Youth', 'Children\'s Ministries',
    'Music', 'Communications', 'Personal Ministries',
    'Health Ministries', 'Women\'s Ministries', 'Men\'s Ministries',
    'Stewardship', 'Education', 'Publishing'
]

@officers_bp.route('/')
def list_officers():
    active = request.args.get('active', 'true')
    query = ChurchOfficer.query
    if active == 'true':
        query = query.filter_by(active=True)
    officers = query.order_by(ChurchOfficer.role).all()
    return render_template('officers/list.html', officers=officers, ROLES=ROLES)

@officers_bp.route('/add', methods=['GET', 'POST'])
def add_officer():
    if request.method == 'POST':
        o = ChurchOfficer(
            member_id=request.form['member_id'],
            role=request.form['role'],
            department=request.form.get('department', ''),
            start_date=request.form['start_date'],
            end_date=request.form.get('end_date', ''),
            active=request.form.get('active', 'true') == 'true',
        )
        db.session.add(o)
        db.session.commit()
        flash('Officer assigned successfully', 'success')
        return redirect(url_for('officers.list_officers'))
    members = Member.query.filter_by(membership_status='active').order_by(Member.full_name).all()
    from datetime import datetime
    return render_template('officers/form.html', members=members, ROLES=ROLES, DEPARTMENTS=DEPARTMENTS, current_date=datetime.now().strftime('%Y-%m-%d'))

@officers_bp.route('/view/<int:id>')
def view_officer(id):
    o = ChurchOfficer.query.get_or_404(id)
    return render_template('officers/view.html', officer=o)

@officers_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_officer(id):
    o = ChurchOfficer.query.get_or_404(id)
    if request.method == 'POST':
        o.member_id = request.form['member_id']
        o.role = request.form['role']
        o.department = request.form.get('department', '')
        o.start_date = request.form['start_date']
        o.end_date = request.form.get('end_date', '')
        o.active = request.form.get('active', 'true') == 'true'
        db.session.commit()
        flash('Officer updated successfully', 'success')
        return redirect(url_for('officers.list_officers'))
    members = Member.query.filter_by(membership_status='active').order_by(Member.full_name).all()
    from datetime import datetime
    return render_template('officers/form.html', officer=o, members=members, ROLES=ROLES, DEPARTMENTS=DEPARTMENTS, current_date=datetime.now().strftime('%Y-%m-%d'))

@officers_bp.route('/delete/<int:id>', methods=['POST'])
def delete_officer(id):
    o = ChurchOfficer.query.get_or_404(id)
    db.session.delete(o)
    db.session.commit()
    flash('Officer removed', 'warning')
    return redirect(url_for('officers.list_officers'))
