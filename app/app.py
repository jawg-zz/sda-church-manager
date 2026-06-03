import os
from flask import Flask, redirect, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required

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

    # Lazy table creation on first request (avoids gunicorn worker race condition)
    @app.before_request
    def ensure_tables():
        global _db_initialized
        if not _db_initialized:
            from models import Member, TitheRecord, Offering, SabbathSchoolClass, \
                SabbathSchoolAttendance, Baptism, ChurchOfficer, Event, User
            with app.app_context():
                db.create_all()
                # Create default admin user if none exists
                if User.query.count() == 0:
                    admin = User(username='admin', role='admin')
                    admin.set_password('admin')
                    db.session.add(admin)
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
        now = datetime.now()
        year = now.year
        month = now.month

        total_members = Member.query.filter_by(membership_status='active').count()
        total_tithes = db.session.query(func.sum(TitheRecord.amount)) \
            .filter(TitheRecord.date >= f'{year}-01-01',
                    TitheRecord.date <= f'{year}-12-31').scalar() or 0
        total_baptisms = Baptism.query.filter(
            Baptism.baptism_date >= f'{year}-01-01').count()
        active_officers = ChurchOfficer.query.filter_by(
            active=True).count()
        classes = SabbathSchoolClass.query.count()
        new_members_this_month = Member.query.filter(
            Member.join_date >= f'{year}-{month:02d}-01').count()
        upcoming_events = Event.query.filter(
            Event.date >= now.strftime('%Y-%m-%d')
        ).order_by(Event.date).limit(5).all()

        # Monthly tithe data for chart
        monthly_tithes = []
        monthly_offerings = []
        for m in range(1, 13):
            t = db.session.query(func.sum(TitheRecord.amount)) \
                .filter(TitheRecord.period_year == year,
                        TitheRecord.period_month == m).scalar() or 0
            o = db.session.query(func.sum(Offering.amount)) \
                .filter(Offering.date >= f'{year}-{m:02d}-01',
                        Offering.date <= f'{year}-{m:02d}-31').scalar() or 0
            monthly_tithes.append(float(t))
            monthly_offerings.append(float(o))

        # Recent activity
        recent_members = Member.query.order_by(Member.created_at.desc()).limit(5).all()
        recent_baptisms = Baptism.query.order_by(Baptism.created_at.desc()).limit(5).all()
        recent_tithes = TitheRecord.query.order_by(TitheRecord.created_at.desc()).limit(5).all()

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
