from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import Member, TitheRecord, Offering

finances_bp = Blueprint('finances', __name__, url_prefix='/finances')

@finances_bp.route('/')
def dashboard():
    tithes = TitheRecord.query.order_by(TitheRecord.date.desc()).limit(50).all()
    offerings = Offering.query.order_by(Offering.date.desc()).limit(50).all()
    members = Member.query.filter_by(membership_status='active').order_by(Member.full_name).all()
    return render_template('finances/dashboard.html', tithes=tithes, offerings=offerings, members=members)

@finances_bp.route('/member/<int:member_id>')
def member_statement(member_id):
    member = Member.query.get_or_404(member_id)
    tithes = TitheRecord.query.filter_by(member_id=member_id).order_by(TitheRecord.date.desc()).all()
    offerings = Offering.query.filter_by(member_id=member_id).order_by(Offering.date.desc()).all()
    total_tithes = sum(t.amount for t in tithes)
    total_offerings = sum(o.amount for o in offerings)
    return render_template('finances/member_statement.html',
        member=member, tithes=tithes, offerings=offerings,
        total_tithes=total_tithes, total_offerings=total_offerings)

@finances_bp.route('/tithe/add', methods=['GET', 'POST'])
def add_tithe():
    if request.method == 'POST':
        t = TitheRecord(
            member_id=request.form['member_id'],
            amount=float(request.form['amount']),
            date=request.form['date'],
            period_month=int(request.form['period_month']),
            period_year=int(request.form['period_year']),
            notes=request.form.get('notes', ''),
        )
        db.session.add(t)
        db.session.commit()
        flash('Tithe recorded successfully', 'success')
        return redirect(url_for('finances.dashboard'))
    members = Member.query.filter_by(membership_status='active').order_by(Member.full_name).all()
    from datetime import datetime
    return render_template('finances/tithe_form.html', members=members, current_year=datetime.now().year, current_month=datetime.now().month)

@finances_bp.route('/offering/add', methods=['GET', 'POST'])
def add_offering():
    if request.method == 'POST':
        o = Offering(
            member_id=request.form.get('member_id') or None,
            amount=float(request.form['amount']),
            date=request.form['date'],
            category=request.form['category'],
            notes=request.form.get('notes', ''),
        )
        db.session.add(o)
        db.session.commit()
        flash('Offering recorded successfully', 'success')
        return redirect(url_for('finances.dashboard'))
    members = Member.query.filter_by(membership_status='active').order_by(Member.full_name).all()
    from datetime import datetime
    return render_template('finances/offering_form.html', members=members, current_date=datetime.now().strftime('%Y-%m-%d'))

@finances_bp.route('/tithe/edit/<int:id>', methods=['GET', 'POST'])
def edit_tithe(id):
    t = TitheRecord.query.get_or_404(id)
    if request.method == 'POST':
        t.member_id = request.form['member_id']
        t.amount = float(request.form['amount'])
        t.date = request.form['date']
        t.period_month = int(request.form['period_month'])
        t.period_year = int(request.form['period_year'])
        t.notes = request.form.get('notes', '')
        db.session.commit()
        flash('Tithe updated', 'success')
        return redirect(url_for('finances.dashboard'))
    members = Member.query.filter_by(membership_status='active').order_by(Member.full_name).all()
    from datetime import datetime
    return render_template('finances/tithe_form.html', tithe=t, members=members,
                          current_year=datetime.now().year, current_month=datetime.now().month)

@finances_bp.route('/tithe/delete/<int:id>', methods=['POST'])
def delete_tithe(id):
    t = TitheRecord.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    flash('Tithe record deleted', 'warning')
    return redirect(url_for('finances.dashboard'))

@finances_bp.route('/offering/edit/<int:id>', methods=['GET', 'POST'])
def edit_offering(id):
    o = Offering.query.get_or_404(id)
    if request.method == 'POST':
        o.member_id = request.form.get('member_id') or None
        o.amount = float(request.form['amount'])
        o.date = request.form['date']
        o.category = request.form['category']
        o.notes = request.form.get('notes', '')
        db.session.commit()
        flash('Offering updated', 'success')
        return redirect(url_for('finances.dashboard'))
    members = Member.query.filter_by(membership_status='active').order_by(Member.full_name).all()
    from datetime import datetime
    return render_template('finances/offering_form.html', offering=o, members=members,
                          current_date=datetime.now().strftime('%Y-%m-%d'))

@finances_bp.route('/offering/delete/<int:id>', methods=['POST'])
def delete_offering(id):
    o = Offering.query.get_or_404(id)
    db.session.delete(o)
    db.session.commit()
    flash('Offering record deleted', 'warning')
    return redirect(url_for('finances.dashboard'))
