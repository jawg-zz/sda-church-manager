"""Demo seed data for SDA Church Manager.
Realistic Kenyan SDA church data for demonstrations.
"""
import random
from datetime import date, timedelta

# Kenyan names
FIRST_NAMES_M = ['James', 'John', 'Peter', 'Paul', 'David', 'Daniel', 'Samuel',
    'Joseph', 'Mark', 'Stephen', 'Brian', 'Kevin', 'Martin', 'Patrick',
    'Francis', 'Michael', 'Charles', 'Robert', 'William', 'Thomas',
    'Emmanuel', 'Isaac', 'Jacob', 'Moses', 'Aaron', 'Caleb', 'Joshua',
    'Timothy', 'Victor', 'Edward', 'Walter', 'Dennis', 'Andrew', 'Simon',
    'Philip', 'Nathan', 'Benjamin', 'Richard', 'Anthony', 'George']
FIRST_NAMES_F = ['Grace', 'Mary', 'Sarah', 'Agnes', 'Jane', 'Esther', 'Ruth',
    'Faith', 'Joy', 'Peace', 'Charity', 'Rose', 'Anne', 'Priscilla',
    'Tabitha', 'Martha', 'Hannah', 'Rebecca', 'Rachel', 'Naomi',
    'Evelyn', 'Janet', 'Patricia', 'Dorothy', 'Catherine', 'Julia',
    'Florence', 'Beatrice', 'Lucy', 'Winnie', 'Lilian', 'Mercy',
    'Sylvia', 'Margaret', 'Gladys', 'Hellen', 'Alice', 'Elizabeth',
    'Caroline', 'Susan']
LAST_NAMES = ['Mwangi', 'Kamau', 'Wanjiku', 'Ochieng', 'Odhiambo', 'Kipchoge',
    'Mutua', 'Kioko', 'Njoroge', 'Wambua', 'Ouma', 'Otieno', 'Muthoni',
    'Njeri', 'Kibaki', 'Wafula', 'Simiyu', 'Wekesa', 'Barasa', ' Masinde',
    'Onyango', 'Owino', 'Okeyo', 'Auma', 'Akinyi', 'Atieno', 'Awino',
    'Nyambura', 'Wairimu', 'Njenga', 'Kariuki', 'Maina', 'Githinji',
    'Ngugi', 'Kamotho', 'Thuo', 'Gitonga', 'Mugo', 'Kinyua', 'Nderitu']

TRIBES = ['Kikuyu', 'Luo', 'Kalenjin', 'Kamba', 'Kisii', 'Meru', 'Luhya',
    'Turkana', 'Maasai', 'Embu', 'Mijikenda', 'Taita']
LANGUAGES = ['English', 'Swahili', 'Kikuyu', 'Luo', 'Kalenjin', 'Kamba', 'Kisii']
DISTRICTS = ['Nairobi Central', 'Nairobi East', 'Nairobi West', 'Kiambu',
    'Nakuru', 'Kisumu', 'Mombasa', 'Eldoret', 'Thika', 'Nyeri']
LOCATIONS = ['Nairobi', 'Kiambu', 'Nakuru', 'Kisumu', 'Mombasa', 'Eldoret',
    'Thika', 'Nyeri', 'Machakos', 'Kakamega', 'Kitale', 'Meru']
OCCUPATIONS = ['Teacher', 'Nurse', 'Doctor', 'Engineer', 'Accountant',
    'Business Owner', 'Farmer', 'Driver', 'Mechanic', 'Reverend',
    'Police Officer', 'Lawyer', 'Student', 'Housewife', 'Pastor',
    'Clerk', 'Technician', 'Pharmacist', 'Journalist', 'Social Worker']
EDUCATION = ['Primary', 'Secondary', 'Diploma', 'Bachelor', 'Master', 'PhD', 'None']

CHURCH_NAMES = [
    'SDA Central Church', 'SDA Nairobi West', 'SDA Kisumu Central',
    'SDA Nakuru Town', 'SDA Mombasa Central', 'SDA Eldoret Town',
    'SDA Thika Central', 'SDA Nyeri Town', 'SDA Machakos Town',
    'SDA Kakamega Town'
]

SS_CLASSES = ['Adult Bible Study', 'Youth Class', 'Young Adults',
    'Children\'s Corner', 'Beginners', 'Kindergarten', 'Cradle Roll']

ROLES = ['Senior Pastor', 'Head Elder', 'Elder', 'Head Deacon', 'Deacon',
    'Deaconess', 'Church Clerk', 'Treasurer', 'Sabbath School Superintendent',
    'Youth Leader', 'Music Director', 'Communications Secretary']

EVENT_TYPES = ['Divine Service', 'Sabbath School', 'Prayer Meeting',
    'Evangelistic Campaign', 'Youth Program', 'Community Outreach',
    'Health Fair', 'Church Board', 'Business Meeting', 'Special Event']

OFFERING_CATEGORIES = ['Sabbath School', 'Church Budget', 'Building Fund',
    'Mission', 'Youth', 'Welfare', 'Education', 'Community Outreach']


def _rand_date(year, month=None):
    if month:
        d = random.randint(1, 28)
        return date(year, month, d)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return date(year, m, d)


def seed_demo_data(db, models):
    """Seed the database with realistic demo data."""
    Church = models['Church']
    User = models['User']
    Member = models['Member']
    TitheRecord = models['TitheRecord']
    Offering = models['Offering']
    Baptism = models['Baptism']
    ChurchOfficer = models['ChurchOfficer']
    SabbathSchoolClass = models['SabbathSchoolClass']
    SabbathSchoolAttendance = models['SabbathSchoolAttendance']
    Event = models['Event']

    # Create 3 demo churches
    churches = []
    for name in CHURCH_NAMES[:3]:
        c = Church(
            name=name,
            location=random.choice(LOCATIONS),
            district=random.choice(DISTRICTS),
            region='Central Kenya',
            phone=f'+254{random.randint(700000000, 799999999)}',
            email=f'{name.lower().replace(" ", "").replace("sda", "sda")}@example.com'
        )
        db.session.add(c)
        churches.append(c)
    db.session.flush()

    # Create users for each church
    for church in churches:
        for username, password, role in [('admin', 'admin', 'admin'), ('clerk', 'clerk', 'clerk')]:
            u = User(username=username, role=role, church_id=church.id)
            u.set_password(password)
            db.session.add(u)

    # Create members for each church
    all_members = []
    for church in churches:
        church_members = []
        num_members = random.randint(45, 80)
        for _ in range(num_members):
            gender = random.choice(['M', 'F'])
            first = random.choice(FIRST_NAMES_M if gender == 'M' else FIRST_NAMES_F)
            last = random.choice(LAST_NAMES)
            year = random.randint(1950, 2005)
            month = random.randint(1, 12)
            member = Member(
                church_id=church.id,
                full_name=f'{first} {last}',
                date_of_birth=f'{year}-{month:02d}-{random.randint(1,28):02d}',
                gender=gender,
                phone=f'+254{random.randint(700000000, 799999999)}',
                email=f'{first.lower()}.{last.lower()}@example.com',
                address=f'P.O. Box {random.randint(100, 9999)} {random.choice(LOCATIONS)}',
                membership_status=random.choice(['active']*8 + ['inactive', 'transferred']),
                baptism_date=f'{random.randint(2010, 2025)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                baptism_location=f'{church.location} SDA Church',
                baptism_by='Pastor John Mwangi',
                join_date=f'{random.randint(2015, 2025)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                transfer_from=random.choice(['', '', '', f'SDA {random.choice(LOCATIONS)}']),
                tribe=random.choice(TRIBES),
                language=random.choice(LANGUAGES),
                occupation=random.choice(OCCUPATIONS),
                education_level=random.choice(EDUCATION),
                emergency_contact=f'{random.choice(FIRST_NAMES_M)} {random.choice(LAST_NAMES)}',
                emergency_phone=f'+254{random.randint(700000000, 799999999)}',
            )
            db.session.add(member)
            church_members.append(member)
        all_members.extend(church_members)
        db.session.flush()

        # Create tithes for each member
        for member in church_members:
            if member.membership_status != 'active':
                continue
            num_tithes = random.randint(3, 12)
            for _ in range(num_tithes):
                m = random.randint(1, 12)
                y = random.choice([2024, 2025, 2026])
                t = TitheRecord(
                    church_id=church.id,
                    member_id=member.id,
                    amount=round(random.uniform(500, 15000), 2),
                    date=f'{y}-{m:02d}-{random.randint(1,28):02d}',
                    period_month=m,
                    period_year=y,
                    notes=random.choice(['', '', 'Monthly tithe', 'Weekly tithe'])
                )
                db.session.add(t)

        # Create offerings
        for _ in range(random.randint(20, 40)):
            m = random.randint(1, 12)
            y = random.choice([2024, 2025, 2026])
            member = random.choice(church_members) if random.random() > 0.3 else None
            o = Offering(
                church_id=church.id,
                member_id=member.id if member else None,
                amount=round(random.uniform(200, 5000), 2),
                date=f'{y}-{m:02d}-{random.randint(1,28):02d}',
                category=random.choice(OFFERING_CATEGORIES),
                notes=random.choice(['', '', 'Sabbath offering'])
            )
            db.session.add(o)

        # Create baptisms
        for _ in range(random.randint(3, 8)):
            member = random.choice(church_members)
            b = Baptism(
                church_id=church.id,
                member_id=member.id,
                baptism_date=f'{random.randint(2020, 2025)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                baptizer=random.choice(['Pastor John Mwangi', 'Pastor David Ochieng', 'Elder Peter Kamau']),
                location=f'{church.location} SDA Church',
                certificate_number=f'SDA-{random.randint(1000, 9999)}'
            )
            db.session.add(b)

        # Create officers
        officer_members = random.sample(church_members, min(6, len(church_members)))
        for i, member in enumerate(officer_members):
            o = ChurchOfficer(
                church_id=church.id,
                member_id=member.id,
                role=ROLES[i % len(ROLES)],
                department=random.choice(['General', 'Sabbath School', 'Youth', 'Music', 'Personal Ministries']),
                start_date=f'{random.randint(2020, 2025)}-01-01',
                active=random.random() > 0.2
            )
            db.session.add(o)

        # Create SS classes
        for cls_name in random.sample(SS_CLASSES, random.randint(3, 5)):
            ss = SabbathSchoolClass(
                church_id=church.id,
                name=cls_name,
                teacher=f'{random.choice(FIRST_NAMES_M)} {random.choice(LAST_NAMES)}',
                description=f'{cls_name} class for the church'
            )
            db.session.add(ss)
        db.session.flush()

        # Create events
        for _ in range(random.randint(5, 10)):
            e = Event(
                church_id=church.id,
                title=random.choice(['Divine Service', 'Youth Rally', 'Health Sabbath',
                    'Prayer Night', 'Community Outreach', 'Baptismal Service',
                    'Church Board Meeting', 'Choir Practice', 'Bible Study']),
                date=f'{random.randint(2025, 2026)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                time=random.choice(['08:00', '09:00', '10:00', '14:00', '18:00']),
                location=f'{church.location} SDA Church',
                event_type=random.choice(EVENT_TYPES),
                description=f'Annual {random.choice(["spiritual", "youth", "health", "outreach"])} program',
                organizer=f'{random.choice(FIRST_NAMES_M)} {random.choice(LAST_NAMES)}'
            )
            db.session.add(e)

    db.session.commit()
    total_members = Member.query.count()
    total_tithes = TitheRecord.query.count()
    total_offerings = Offering.query.count()
    return {
        'churches': len(churches),
        'members': total_members,
        'tithes': total_tithes,
        'offerings': total_offerings,
    }


def clear_demo_data(db, models):
    """Remove all demo data (all churches and their data)."""
    for model_name in ['Event', 'SabbathSchoolAttendance', 'SabbathSchoolClass',
                        'ChurchOfficer', 'Baptism', 'Offering', 'TitheRecord',
                        'Member', 'User', 'Church']:
        model = models[model_name]
        model.query.delete()
    db.session.commit()
