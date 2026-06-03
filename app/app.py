import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
_db_initialized = False

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///app/data/church.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

    db.init_app(app)

    # Lazy table creation on first request (avoids gunicorn worker race condition)
    @app.before_request
    def ensure_tables():
        global _db_initialized
        if not _db_initialized:
            from models import Member, TitheRecord, Offering, SabbathSchoolClass, \
                SabbathSchoolAttendance, Baptism, ChurchOfficer, Event
            with app.app_context():
                db.create_all()
            _db_initialized = True

    # Register blueprints
    from routes.members import members_bp
    from routes.finances import finances_bp
    from routes.sabbath_school import sabbath_school_bp
    from routes.baptisms import baptisms_bp
    from routes.officers import officers_bp
    from routes.events import events_bp
    from routes.reports import reports_bp

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
        from flask import redirect
        return redirect('/dashboard')

    @app.route('/dashboard')
    def dashboard():
        from flask import render_template
        from sqlalchemy import func
        now = __import__('datetime').datetime.now()
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

        return render_template('dashboard.html',
            total_members=total_members,
            total_tithes=total_tithes,
            total_baptisms=total_baptisms,
            active_officers=active_officers,
            classes=classes,
            new_members_this_month=new_members_this_month,
            upcoming_events=upcoming_events,
            year=year)

    @app.route('/health')
    def health():
        from flask import jsonify
        return jsonify({"status": "ok", "app": "sda-church-manager"})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
