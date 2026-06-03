from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import db
from models import ChurchOfficer, Member
from datetime import datetime

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
    'Music', 'Communications', 'Personal Ministries', 'Health Ministries',
    'Women\'s Ministries', 'Men\'s Ministries', 'Stewardship', 'Education', 'Publishing'
]

@officers_bp.route('/')
@login_required
def list_officers():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    page = request.args.get('page', 1, type=int)
    active = request.args.get('active', 'true')
    query = ChurchOfficer.query.filter_by(church_id=cid)
    if active == 'true':
        query = query.filter_by(active=True)
    pagination = query.order_by(ChurchOfficer.role).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('officers/list.html', officers=pagination.items,
                           pagination=pagination, ROLES=ROLES)

@officers_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_officer():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if request.method == 'POST':
        try:
            o = ChurchOfficer(
                church_id=cid,
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
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error assigning officer: {str(e)}', 'danger')
    members = Member.query.filter_by(church_id=cid, membership_status='active').order_by(Member.full_name).all()
    return render_template('officers/form.html', members=members, ROLES=ROLES,
                           DEPARTMENTS=DEPARTMENTS, current_date=datetime.now().strftime('%Y-%m-%d'))

@officers_bp.route('/view/<int:id>')
@login_required
def view_officer(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    o = ChurchOfficer.query.filter_by(id=id, church_id=cid).first()
    if not o:
        flash('Officer not found', 'danger')
        return redirect(url_for('officers.list_officers'))
    return render_template('officers/view.html', officer=o)

@officers_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_officer(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    o = ChurchOfficer.query.filter_by(id=id, church_id=cid).first()
    if not o:
        flash('Officer not found', 'danger')
        return redirect(url_for('officers.list_officers'))
    if request.method == 'POST':
        try:
            o.member_id = request.form['member_id']
            o.role = request.form['role']
            o.department = request.form.get('department', '')
            o.start_date = request.form['start_date']
            o.end_date = request.form.get('end_date', '')
            o.active = request.form.get('active', 'true') == 'true'
            db.session.commit()
            flash('Officer updated successfully', 'success')
            return redirect(url_for('officers.list_officers'))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating officer: {str(e)}', 'danger')
    members = Member.query.filter_by(church_id=cid, membership_status='active').order_by(Member.full_name).all()
    return render_template('officers/form.html', officer=o, members=members, ROLES=ROLES,
                           DEPARTMENTS=DEPARTMENTS, current_date=datetime.now().strftime('%Y-%m-%d'))

@officers_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_officer(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if not current_user.can_delete:
        flash('Only admins can delete records', 'danger')
        return redirect(url_for('officers.list_officers'))
    o = ChurchOfficer.query.filter_by(id=id, church_id=cid).first()
    if not o:
        flash('Officer not found', 'danger')
        return redirect(url_for('officers.list_officers'))
    try:
        db.session.delete(o)
        db.session.commit()
        flash('Officer removed', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing officer: {str(e)}', 'danger')
    return redirect(url_for('officers.list_officers'))
