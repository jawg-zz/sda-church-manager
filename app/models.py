from app import db
from datetime import datetime
from flask_login import UserMixin
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash


ROLES = {
    'admin': 'Admin',
    'pastor': 'Pastor',
    'clerk': 'Clerk',
    'dept_head': 'Department Head',
}


def current_church_id():
    return session.get('church_id')


class Church(db.Model):
    __tablename__ = 'churches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    district = db.Column(db.String(100))
    region = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='church', lazy=True)
    members = db.relationship('Member', backref='church', lazy=True)

    def __repr__(self):
        return f'<Church {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='clerk')
    department = db.Column(db.String(100))
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('username', 'church_id', name='uq_user_church'),)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_name(self):
        return ROLES.get(self.role, self.role)

    @property
    def can_delete(self):
        return self.role in ('admin',)

    @property
    def can_manage_users(self):
        return self.role == 'admin'

    @property
    def can_view_finances(self):
        return self.role in ('admin', 'pastor', 'clerk')

    @property
    def can_manage_members(self):
        return self.role in ('admin', 'pastor', 'clerk')

    @property
    def can_manage_departments(self):
        return self.role in ('admin', 'pastor', 'dept_head')

    def __repr__(self):
        return f'<User {self.username}>'


class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'), nullable=False, index=True)
    full_name = db.Column(db.String(200), nullable=False)
    date_of_birth = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    membership_status = db.Column(db.String(20), default='active')
    baptism_date = db.Column(db.String(20))
    baptism_location = db.Column(db.String(200))
    baptism_by = db.Column(db.String(100))
    join_date = db.Column(db.String(20))
    transfer_from = db.Column(db.String(200))
    tribe = db.Column(db.String(50))
    language = db.Column(db.String(50))
    occupation = db.Column(db.String(100))
    education_level = db.Column(db.String(50))
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tithes = db.relationship('TitheRecord', backref='member', lazy=True)
    offerings = db.relationship('Offering', backref='member', lazy=True)

    def age(self):
        if not self.date_of_birth:
            return None
        from datetime import date
        parts = self.date_of_birth.split('-')
        if len(parts) != 3:
            return None
        try:
            born = date(int(parts[0]), int(parts[1]), int(parts[2]))
            today = date.today()
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        except:
            return None

    def __repr__(self):
        return f'<Member {self.full_name}>'


class TitheRecord(db.Model):
    __tablename__ = 'tithes'
    id = db.Column(db.Integer, primary_key=True)
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    period_month = db.Column(db.Integer)
    period_year = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Offering(db.Model):
    __tablename__ = 'offerings'
    id = db.Column(db.Integer, primary_key=True)
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SabbathSchoolClass(db.Model):
    __tablename__ = 'ss_classes'
    id = db.Column(db.Integer, primary_key=True)
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    teacher = db.Column(db.String(200))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendances = db.relationship('SabbathSchoolAttendance', backref='class_', lazy=True)


class SabbathSchoolAttendance(db.Model):
    __tablename__ = 'ss_attendance'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('ss_classes.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    present = db.Column(db.Boolean, default=True)

    member = db.relationship('Member', backref='ss_attendances')


class Baptism(db.Model):
    __tablename__ = 'baptisms'
    id = db.Column(db.Integer, primary_key=True)
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    baptism_date = db.Column(db.String(20), nullable=False)
    baptizer = db.Column(db.String(200))
    location = db.Column(db.String(200))
    certificate_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref='baptisms')


class ChurchOfficer(db.Model):
    __tablename__ = 'officers'
    id = db.Column(db.Integer, primary_key=True)
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref='officer_roles')


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20))
    location = db.Column(db.String(200))
    event_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    organizer = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(20), nullable=False)
    entity = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity} by {self.user_id}>'


def log_audit(church_id, user_id, action, entity, entity_id=None, details=None, ip=None):
    """Helper to write an audit log entry."""
    from flask import session, request
    entry = AuditLog(
        church_id=church_id,
        user_id=user_id or (session.get('_user_id')),
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
        ip_address=ip or (request.remote_addr if request else None),
    )
    # Use the db from the same module context
    from app import db as _db
    _db.session.add(entry)
    _db.session.flush()
