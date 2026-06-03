from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import SabbathSchoolClass, SabbathSchoolAttendance, Member

sabbath_school_bp = Blueprint('ss', __name__, url_prefix='/sabbath-school')

@sabbath_school_bp.route('/')
@login_required
def dashboard():
    classes = SabbathSchoolClass.query.all()
    return render_template('ss/dashboard.html', classes=classes)

@sabbath_school_bp.route('/class/add', methods=['GET', 'POST'])
@login_required
def add_class():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Class name is required', 'danger')
            return render_template('ss/class_form.html')
        try:
            c = SabbathSchoolClass(
                name=name,
                teacher=request.form.get('teacher', ''),
                description=request.form.get('description', ''),
            )
            db.session.add(c)
            db.session.commit()
            flash('Class created successfully', 'success')
            return redirect(url_for('ss.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating class: {str(e)}', 'danger')
    return render_template('ss/class_form.html')

@sabbath_school_bp.route('/class/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_class(id):
    c = SabbathSchoolClass.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Class name is required', 'danger')
            return render_template('ss/class_form.html', cls=c)
        try:
            c.name = name
            c.teacher = request.form.get('teacher', '')
            c.description = request.form.get('description', '')
            db.session.commit()
            flash('Class updated successfully', 'success')
            return redirect(url_for('ss.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating class: {str(e)}', 'danger')
    return render_template('ss/class_form.html', cls=c)

@sabbath_school_bp.route('/class/delete/<int:id>', methods=['POST'])
@login_required
def delete_class(id):
    if not current_user.can_delete:
        flash('Only admins can delete records', 'danger')
        return redirect(url_for('ss.dashboard'))
    c = SabbathSchoolClass.query.get_or_404(id)
    try:
        db.session.delete(c)
        db.session.commit()
        flash('Class deleted', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting class: {str(e)}', 'danger')
    return redirect(url_for('ss.dashboard'))

@sabbath_school_bp.route('/attendance/<int:class_id>', methods=['GET', 'POST'])
@login_required
def attendance(class_id):
    cls = SabbathSchoolClass.query.get_or_404(class_id)
    date = request.args.get('date', '')
    if request.method == 'POST':
        date = request.form['date']
        try:
            members = Member.query.filter_by(membership_status='active').all()
            for m in members:
                key = f'present_{m.id}'
                present = key in request.form
                existing = SabbathSchoolAttendance.query.filter_by(
                    class_id=class_id, member_id=m.id, date=date).first()
                if existing:
                    existing.present = present
                else:
                    db.session.add(SabbathSchoolAttendance(
                        class_id=class_id, member_id=m.id, date=date, present=present))
            db.session.commit()
            flash('Attendance saved', 'success')
            return redirect(url_for('ss.view_attendance', class_id=class_id, date=date))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving attendance: {str(e)}', 'danger')

    members = Member.query.filter_by(membership_status='active').order_by(Member.full_name).all()
    existing = []
    if date:
        existing = SabbathSchoolAttendance.query.filter_by(class_id=class_id, date=date).all()
        existing_ids = {a.member_id for a in existing}
    else:
        existing_ids = set()
    return render_template('ss/attendance.html', cls=cls, members=members,
                          existing=existing, existing_ids=existing_ids, date=date)

@sabbath_school_bp.route('/attendance/<int:class_id>/view')
@login_required
def view_attendance(class_id):
    cls = SabbathSchoolClass.query.get_or_404(class_id)
    date = request.args.get('date', '')
    records = []
    if date:
        records = SabbathSchoolAttendance.query.filter_by(class_id=class_id, date=date).all()
    return render_template('ss/view_attendance.html', cls=cls, records=records, date=date)
