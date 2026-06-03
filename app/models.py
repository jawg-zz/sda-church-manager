from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


ROLES = {
    'admin': 'Admin',
    'pastor': 'Pastor',
    'clerk': 'Clerk',
    'dept_head': 'Department Head',
}


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='clerk')
    department = db.Column(db.String(100))  # for dept_head role
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SabbathSchoolClass(db.Model):
    __tablename__ = 'ss_classes'
    id = db.Column(db.Integer, primary_key=True)
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
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20))
    location = db.Column(db.String(200))
    event_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    organizer = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
