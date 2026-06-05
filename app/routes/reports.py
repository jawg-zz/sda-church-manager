from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import db
from models import Member, TitheRecord, Offering, Baptism, ChurchOfficer, SabbathSchoolClass, SabbathSchoolAttendance, Event, Church
from sqlalchemy import func
from datetime import datetime

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    return render_template('reports/index.html')

@reports_bp.route('/membership')
@login_required
def membership_report():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    statuses = ['active', 'inactive', 'transferred', 'deceased', 'suspended']
    counts = {}
    for s in statuses:
        counts[s] = Member.query.filter_by(church_id=cid, membership_status=s).count()
    total = sum(counts.values())
    return render_template('reports/membership.html', counts=counts, total=total)

@reports_bp.route('/financial')
@login_required
def financial_report():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    year = request.args.get('year', str(datetime.now().year))
    months = range(1, 13)
    monthly_tithes = []
    monthly_offerings = []
    total_tithe = 0
    total_offering = 0
    for m in months:
        t = db.session.query(func.sum(TitheRecord.amount)) \
            .filter(TitheRecord.church_id == cid,
                    TitheRecord.period_year == int(year),
                    TitheRecord.period_month == m).scalar() or 0
        o = db.session.query(func.sum(Offering.amount)) \
            .filter(Offering.church_id == cid,
                    Offering.date >= f'{year}-{m:02d}-01',
                    Offering.date <= f'{year}-{m:02d}-31').scalar() or 0
        monthly_tithes.append(float(t))
        monthly_offerings.append(float(o))
        total_tithe += float(t)
        total_offering += float(o)
    return render_template('reports/financial.html',
        year=int(year), months=months,
        monthly_tithes=monthly_tithes, monthly_offerings=monthly_offerings,
        total_tithe=total_tithe, total_offering=total_offering)

@reports_bp.route('/baptism')
@login_required
def baptism_report():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    year = request.args.get('year', str(datetime.now().year))
    baptisms = Baptism.query.filter(
        Baptism.church_id == cid,
        Baptism.baptism_date >= f'{year}-01-01',
        Baptism.baptism_date <= f'{year}-12-31'
    ).order_by(Baptism.baptism_date).all()
    total = len(baptisms)
    return render_template('reports/baptism.html', baptisms=baptisms, total=total, year=year)

@reports_bp.route('/quarterly')
@login_required
def quarterly_report():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    year = request.args.get('year', str(datetime.now().year))
    quarter = request.args.get('quarter', '1', type=int)
    q_months = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
    months = q_months.get(quarter, [1,2,3])

    # Membership at quarter start and end
    start_date = f'{year}-{months[0]:02d}-01'
    if months[-1] == 12:
        end_date = f'{year}-12-31'
    else:
        end_date = f'{year}-{months[-1]+1:02d}-01'

    total_members = Member.query.filter(
        Member.church_id == cid,
        Member.join_date <= end_date,
        (Member.membership_status == 'active') |
        (Member.membership_status == 'inactive')
    ).count()

    new_members = Member.query.filter(
        Member.church_id == cid,
        Member.join_date >= start_date,
        Member.join_date <= end_date
    ).count()

    baptisms_q = Baptism.query.filter(
        Baptism.church_id == cid,
        Baptism.baptism_date >= start_date,
        Baptism.baptism_date <= end_date
    ).count()

    # Financial totals for quarter
    total_tithe = 0
    total_offering = 0
    for m in months:
        t = db.session.query(func.sum(TitheRecord.amount)) \
            .filter(TitheRecord.church_id == cid,
                    TitheRecord.period_year == int(year),
                    TitheRecord.period_month == m).scalar() or 0
        o = db.session.query(func.sum(Offering.amount)) \
            .filter(Offering.church_id == cid,
                    Offering.date >= f'{year}-{m:02d}-01',
                    Offering.date <= f'{year}-{m:02d}-31').scalar() or 0
        total_tithe += float(t)
        total_offering += float(o)

    # SS attendance average
    ss_classes = SabbathSchoolClass.query.filter_by(church_id=cid).count()
    total_ss_members = Member.query.filter_by(church_id=cid, membership_status='active').count()

    # Active officers
    active_officers = ChurchOfficer.query.filter_by(church_id=cid, active=True).count()

    # Events in quarter
    events_q = Event.query.filter(
        Event.church_id == cid,
        Event.date >= start_date,
        Event.date <= end_date
    ).count()

    return render_template('reports/quarterly.html',
        year=int(year), quarter=quarter,
        total_members=total_members, new_members=new_members,
        baptisms_q=baptisms_q,
        total_tithe=total_tithe, total_offering=total_offering,
        ss_classes=ss_classes, ss_members=total_ss_members,
        active_officers=active_officers, events_q=events_q,
        months=months)

@reports_bp.route('/growth')
@login_required
def growth_report():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    year = request.args.get('year', str(datetime.now().year))
    months = range(1, 13)
    monthly_members = []
    monthly_baptisms = []
    for m in range(1, 13):
        count = Member.query.filter(
            Member.church_id == cid,
            Member.join_date <= f'{year}-{m:02d}-31',
            (Member.membership_status == 'active') |
            (Member.membership_status == 'inactive')
        ).count()
        bapt = Baptism.query.filter(
            Baptism.church_id == cid,
            Baptism.baptism_date >= f'{year}-{m:02d}-01',
            Baptism.baptism_date <= f'{year}-{m:02d}-31'
        ).count()
        monthly_members.append(count)
        monthly_baptisms.append(bapt)

    # Year-over-year comparison
    current_year_total = Member.query.filter(
        Member.church_id == cid,
        Member.join_date <= f'{year}-12-31',
        (Member.membership_status == 'active') |
        (Member.membership_status == 'inactive')
    ).count()
    prev_year_total = Member.query.filter(
        Member.church_id == cid,
        Member.join_date <= f'{int(year)-1}-12-31',
        (Member.membership_status == 'active') |
        (Member.membership_status == 'inactive')
    ).count()
    growth = current_year_total - prev_year_total
    growth_pct = (growth / prev_year_total * 100) if prev_year_total > 0 else 0

    return render_template('reports/growth.html',
        year=int(year), months=months,
        monthly_members=monthly_members, monthly_baptisms=monthly_baptisms,
        current_year_total=current_year_total,
        prev_year_total=prev_year_total,
        growth=growth, growth_pct=growth_pct)

@reports_bp.route('/conference')
@login_required
def conference_report():
    if not current_user.can_manage_users:
        flash('Admin access required', 'danger')
        return redirect(url_for('reports.index'))
    cid = session.get('church_id')
    # Users with a fixed church_id only see their own church
    if current_user.church_id:
        churches = Church.query.filter_by(id=cid).all()
    else:
        churches = Church.query.order_by(Church.name).all()
    church_stats = []
    totals = {'active_members': 0, 'total_tithes': 0.0, 'total_offerings': 0.0, 'total_baptisms': 0}
    for c in churches:
        active = Member.query.filter_by(church_id=c.id, membership_status='active').count()
        tithes = db.session.query(func.sum(TitheRecord.amount)).filter(TitheRecord.church_id == c.id).scalar() or 0
        offerings = db.session.query(func.sum(Offering.amount)).filter(Offering.church_id == c.id).scalar() or 0
        baptisms = Baptism.query.filter_by(church_id=c.id).count()
        church_stats.append({
            'name': c.name,
            'location': c.location,
            'active_members': active,
            'total_tithes': float(tithes),
            'total_offerings': float(offerings),
            'total_baptisms': baptisms,
        })
        totals['active_members'] += active
        totals['total_tithes'] += float(tithes)
        totals['total_offerings'] += float(offerings)
        totals['total_baptisms'] += baptisms
    return render_template('reports/conference.html', church_stats=church_stats, totals=totals)
