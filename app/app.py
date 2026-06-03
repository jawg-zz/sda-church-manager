import os
from flask import Flask, redirect, render_template, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user

db = SQLAlchemy()
login_manager = LoginManager()
_db_initialized = False

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///app/data/church.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_church():
        from models import Church
        cid = session.get('church_id')
        church = Church.query.get(cid) if cid else None
        return dict(current_church=church)

    # Lazy table creation on first request (avoids gunicorn worker race condition)
    @app.before_request
    def ensure_tables():
        global _db_initialized
        if not _db_initialized:
            from models import (Member, TitheRecord, Offering, SabbathSchoolClass,
                SabbathSchoolAttendance, Baptism, ChurchOfficer, Event, User, Church)
            with app.app_context():
                db.create_all()
                # Create default church and users if none exist
                if Church.query.count() == 0:
                    church = Church(name='SDA Central Church', location='Nairobi',
                                    district='Nairobi Central', region='Central Kenya')
                    db.session.add(church)
                    db.session.flush()
                    defaults = [
                        ('admin', 'admin', 'admin', None, church.id),
                        ('pastor', 'pastor', 'pastor', None, church.id),
                        ('clerk', 'clerk', 'clerk', None, church.id),
                        ('ss_head', 'ss123', 'dept_head', 'Sabbath School', church.id),
                    ]
                    for username, password, role, dept, cid in defaults:
                        u = User(username=username, role=role, department=dept, church_id=cid)
                        u.set_password(password)
                        db.session.add(u)
                    db.session.commit()
            _db_initialized = True

    # Register blueprints
    from routes.auth import auth_bp
    from routes.members import members_bp
    from routes.finances import finances_bp
    from routes.sabbath_school import sabbath_school_bp
    from routes.baptisms import baptisms_bp
    from routes.officers import officers_bp
    from routes.events import events_bp
    from routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(finances_bp)
    app.register_blueprint(sabbath_school_bp)
    app.register_blueprint(baptisms_bp)
    app.register_blueprint(officers_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(reports_bp)

    # Main routes
    @app.route('/')
    def index():
        return redirect('/dashboard')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        from sqlalchemy import func
        from models import Member, TitheRecord, Offering, Baptism, ChurchOfficer, SabbathSchoolClass, Event
        from datetime import datetime
        cid = session.get('church_id')
        if not cid:
            return redirect('/auth/select-church')
        now = datetime.now()
        year = now.year
        month = now.month

        total_members = Member.query.filter_by(church_id=cid, membership_status='active').count()
        total_tithes = db.session.query(func.sum(TitheRecord.amount)) \
            .filter(TitheRecord.church_id == cid,
                    TitheRecord.date >= f'{year}-01-01',
                    TitheRecord.date <= f'{year}-12-31').scalar() or 0
        total_baptisms = Baptism.query.filter(
            Baptism.church_id == cid,
            Baptism.baptism_date >= f'{year}-01-01').count()
        active_officers = ChurchOfficer.query.filter_by(church_id=cid, active=True).count()
        classes = SabbathSchoolClass.query.filter_by(church_id=cid).count()
        new_members_this_month = Member.query.filter(
            Member.church_id == cid,
            Member.join_date >= f'{year}-{month:02d}-01').count()
        upcoming_events = Event.query.filter(
            Event.church_id == cid,
            Event.date >= now.strftime('%Y-%m-%d')
        ).order_by(Event.date).limit(5).all()

        monthly_tithes = []
        monthly_offerings = []
        for m in range(1, 13):
            t = db.session.query(func.sum(TitheRecord.amount)) \
                .filter(TitheRecord.church_id == cid,
                        TitheRecord.period_year == year,
                        TitheRecord.period_month == m).scalar() or 0
            o = db.session.query(func.sum(Offering.amount)) \
                .filter(Offering.church_id == cid,
                        Offering.date >= f'{year}-{m:02d}-01',
                        Offering.date <= f'{year}-{m:02d}-31').scalar() or 0
            monthly_tithes.append(float(t))
            monthly_offerings.append(float(o))

        recent_members = Member.query.filter_by(church_id=cid).order_by(Member.created_at.desc()).limit(5).all()
        recent_baptisms = Baptism.query.filter_by(church_id=cid).order_by(Baptism.created_at.desc()).limit(5).all()
        recent_tithes = TitheRecord.query.filter_by(church_id=cid).order_by(TitheRecord.created_at.desc()).limit(5).all()

        return render_template('dashboard.html',
            total_members=total_members,
            total_tithes=total_tithes,
            total_baptisms=total_baptisms,
            active_officers=active_officers,
            classes=classes,
            new_members_this_month=new_members_this_month,
            upcoming_events=upcoming_events,
            monthly_tithes=monthly_tithes,
            monthly_offerings=monthly_offerings,
            recent_members=recent_members,
            recent_baptisms=recent_baptisms,
            recent_tithes=recent_tithes,
            year=year)

    @app.route('/health')
    def health():
        return jsonify({"status": "ok", "app": "sda-church-manager"})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
