from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import db
from models import Baptism, Member, log_audit
from datetime import datetime

baptisms_bp = Blueprint('baptisms', __name__, url_prefix='/baptisms')

@baptisms_bp.route('/')
@login_required
def list_baptisms():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = Baptism.query.filter_by(church_id=cid).order_by(Baptism.baptism_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return render_template('baptisms/list.html', baptisms=pagination.items, pagination=pagination)

@baptisms_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_baptism():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if request.method == 'POST':
        try:
            b = Baptism(
                church_id=cid,
                member_id=request.form['member_id'],
                baptism_date=request.form['baptism_date'],
                baptizer=request.form.get('baptizer', ''),
                location=request.form.get('location', ''),
                certificate_number=request.form.get('certificate_number', ''),
                notes=request.form.get('notes', ''),
            )
            db.session.add(b)
            member = Member.query.filter_by(id=b.member_id, church_id=cid).first()
            if member and not member.baptism_date:
                member.baptism_date = b.baptism_date
                member.baptism_location = b.location
                member.baptism_by = b.baptizer
            db.session.commit()
            log_audit(cid, current_user.id, 'create', 'baptism', b.id, f'Added baptism record')
            flash('Baptism recorded successfully', 'success')
            return redirect(url_for('baptisms.list_baptisms'))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording baptism: {str(e)}', 'danger')
    members = Member.query.filter_by(church_id=cid).order_by(Member.full_name).all()
    return render_template('baptisms/form.html', members=members,
                          current_date=datetime.now().strftime('%Y-%m-%d'))

@baptisms_bp.route('/view/<int:id>')
@login_required
def view_baptism(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    b = Baptism.query.filter_by(id=id, church_id=cid).first()
    if not b:
        flash('Baptism record not found', 'danger')
        return redirect(url_for('baptisms.list_baptisms'))
    return render_template('baptisms/view.html', baptism=b)

@baptisms_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_baptism(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    b = Baptism.query.filter_by(id=id, church_id=cid).first()
    if not b:
        flash('Baptism record not found', 'danger')
        return redirect(url_for('baptisms.list_baptisms'))
    if request.method == 'POST':
        try:
            b.member_id = request.form['member_id']
            b.baptism_date = request.form['baptism_date']
            b.baptizer = request.form.get('baptizer', '')
            b.location = request.form.get('location', '')
            b.certificate_number = request.form.get('certificate_number', '')
            b.notes = request.form.get('notes', '')
            db.session.commit()
            log_audit(cid, current_user.id, 'update', 'baptism', b.id, f'Updated baptism record')
            flash('Baptism record updated', 'success')
            return redirect(url_for('baptisms.list_baptisms'))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating baptism: {str(e)}', 'danger')
    members = Member.query.filter_by(church_id=cid).order_by(Member.full_name).all()
    return render_template('baptisms/form.html', baptism=b, members=members,
                          current_date=datetime.now().strftime('%Y-%m-%d'))

@baptisms_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_baptism(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if not current_user.can_delete:
        flash('Only admins can delete records', 'danger')
        return redirect(url_for('baptisms.list_baptisms'))
    b = Baptism.query.filter_by(id=id, church_id=cid).first()
    if not b:
        flash('Baptism record not found', 'danger')
        return redirect(url_for('baptisms.list_baptisms'))
    try:
        db.session.delete(b)
        db.session.commit()
        log_audit(cid, current_user.id, 'delete', 'baptism', id, f'Deleted baptism record')
        flash('Baptism record deleted', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting baptism: {str(e)}', 'danger')
    return redirect(url_for('baptisms.list_baptisms'))
