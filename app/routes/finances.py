from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from models import Member, TitheRecord, Offering

finances_bp = Blueprint('finances', __name__, url_prefix='/finances')

@finances_bp.route('/')
def dashboard():
    tithes = TitheRecord.query.order_by(TitheRecord.date.desc()).limit(50).all()
    offerings = Offering.query.order_by(Offering.date.desc()).limit(50).all()
    members = Member.query.filter_by(membership_status='active').order_by(Member.full_name).all()
    return render_template('finances/dashboard.html', tithes=tithes, offerings=offerings, members=members)

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
        return redirect(url_for('finances.dashboard'))
    members = Member.query.filter_by(membership_status='active').order_by(Member.full_name).all()
    return render_template('finances/tithe_form.html', members=members)

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
        if o.member_id == '':
            o.member_id = None
        db.session.add(o)
        db.session.commit()
        return redirect(url_for('finances.dashboard'))
    members = Member.query.filter_by(membership_status='active').order_by(Member.full_name).all()
    return render_template('finances/offering_form.html', members=members)

@finances_bp.route('/tithe/delete/<int:id>', methods=['POST'])
def delete_tithe(id):
    t = TitheRecord.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for('finances.dashboard'))

@finances_bp.route('/offering/delete/<int:id>', methods=['POST'])
def delete_offering(id):
    o = Offering.query.get_or_404(id)
    db.session.delete(o)
    db.session.commit()
    return redirect(url_for('finances.dashboard'))
