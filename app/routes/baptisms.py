from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import Baptism, Member

baptisms_bp = Blueprint('baptisms', __name__, url_prefix='/baptisms')

@baptisms_bp.route('/')
def list_baptisms():
    baptisms = Baptism.query.order_by(Baptism.baptism_date.desc()).all()
    return render_template('baptisms/list.html', baptisms=baptisms)

@baptisms_bp.route('/add', methods=['GET', 'POST'])
def add_baptism():
    if request.method == 'POST':
        b = Baptism(
            member_id=request.form['member_id'],
            baptism_date=request.form['baptism_date'],
            baptizer=request.form.get('baptizer', ''),
            location=request.form.get('location', ''),
            certificate_number=request.form.get('certificate_number', ''),
            notes=request.form.get('notes', ''),
        )
        db.session.add(b)
        # Update the member's baptism info if not set
        member = Member.query.get(b.member_id)
        if member and not member.baptism_date:
            member.baptism_date = b.baptism_date
            member.baptism_location = b.location
            member.baptism_by = b.baptizer
        db.session.commit()
        flash('Baptism recorded successfully', 'success')
        return redirect(url_for('baptisms.list_baptisms'))
    members = Member.query.order_by(Member.full_name).all()
    from datetime import datetime
    return render_template('baptisms/form.html', members=members, current_date=datetime.now().strftime('%Y-%m-%d'))

@baptisms_bp.route('/view/<int:id>')
def view_baptism(id):
    b = Baptism.query.get_or_404(id)
    return render_template('baptisms/view.html', baptism=b)

@baptisms_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_baptism(id):
    b = Baptism.query.get_or_404(id)
    if request.method == 'POST':
        b.member_id = request.form['member_id']
        b.baptism_date = request.form['baptism_date']
        b.baptizer = request.form.get('baptizer', '')
        b.location = request.form.get('location', '')
        b.certificate_number = request.form.get('certificate_number', '')
        b.notes = request.form.get('notes', '')
        db.session.commit()
        flash('Baptism record updated', 'success')
        return redirect(url_for('baptisms.list_baptisms'))
    members = Member.query.order_by(Member.full_name).all()
    from datetime import datetime
    return render_template('baptisms/form.html', baptism=b, members=members,
                          current_date=datetime.now().strftime('%Y-%m-%d'))

@baptisms_bp.route('/delete/<int:id>', methods=['POST'])
def delete_baptism(id):
    b = Baptism.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    flash('Baptism record deleted', 'warning')
    return redirect(url_for('baptisms.list_baptisms'))
