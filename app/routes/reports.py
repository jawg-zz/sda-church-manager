from flask import Blueprint, render_template, request
from app import db
from models import Member, TitheRecord, Offering, Baptism, Event
from sqlalchemy import func
from datetime import datetime

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
def index():
    return render_template('reports/index.html')

@reports_bp.route('/membership')
def membership_report():
    statuses = ['active', 'inactive', 'transferred', 'deceased', 'suspended']
    counts = {}
    for s in statuses:
        counts[s] = Member.query.filter_by(membership_status=s).count()
    total = sum(counts.values())
    return render_template('reports/membership.html', counts=counts, total=total)

@reports_bp.route('/financial')
def financial_report():
    year = request.args.get('year', str(datetime.now().year))
    months = range(1, 13)
    monthly_tithes = []
    monthly_offerings = []
    total_tithe = 0
    total_offering = 0
    for m in months:
        t = db.session.query(func.sum(TitheRecord.amount)) \
            .filter(TitheRecord.period_year == int(year),
                    TitheRecord.period_month == m).scalar() or 0
        o = db.session.query(func.sum(Offering.amount)) \
            .filter(Offering.date >= f'{year}-{m:02d}-01',
                    Offering.date <= f'{year}-{m:02d}-31').scalar() or 0
        monthly_tithes.append(t)
        monthly_offerings.append(o)
        total_tithe += t
        total_offering += o
    return render_template('reports/financial.html',
        year=int(year), months=months,
        monthly_tithes=monthly_tithes, monthly_offerings=monthly_offerings,
        total_tithe=total_tithe, total_offering=total_offering)

@reports_bp.route('/baptism')
def baptism_report():
    year = request.args.get('year', str(datetime.now().year))
    baptisms = Baptism.query.filter(
        Baptism.baptism_date >= f'{year}-01-01',
        Baptism.baptism_date <= f'{year}-12-31'
    ).order_by(Baptism.baptism_date).all()
    total = len(baptisms)
    return render_template('reports/baptism.html', baptisms=baptisms, total=total, year=year)
