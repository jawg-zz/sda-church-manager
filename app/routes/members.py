from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from flask_login import login_required, current_user
from app import db
from models import Member, Church
import csv
import io

members_bp = Blueprint('members', __name__, url_prefix='/members')

@members_bp.route('/')
@login_required
def list_members():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', 'all')
    search = request.args.get('search', '')
    query = Member.query.filter_by(church_id=cid).order_by(Member.full_name)
    if status != 'all':
        query = query.filter_by(membership_status=status)
    if search:
        query = query.filter(Member.full_name.ilike(f'%{search}%'))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('members/list.html', members=pagination.items,
                           pagination=pagination, status=status, search=search)

@members_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_member():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        if not full_name:
            flash('Full name is required', 'danger')
            return render_template('members/form.html', member=None)
        try:
            member = Member(
                church_id=cid,
                full_name=full_name,
                date_of_birth=request.form.get('date_of_birth', ''),
                gender=request.form.get('gender', ''),
                phone=request.form.get('phone', ''),
                email=request.form.get('email', ''),
                address=request.form.get('address', ''),
                membership_status=request.form.get('membership_status', 'active'),
                baptism_date=request.form.get('baptism_date', ''),
                baptism_location=request.form.get('baptism_location', ''),
                baptism_by=request.form.get('baptism_by', ''),
                join_date=request.form.get('join_date', ''),
                transfer_from=request.form.get('transfer_from', ''),
                tribe=request.form.get('tribe', ''),
                language=request.form.get('language', ''),
                occupation=request.form.get('occupation', ''),
                education_level=request.form.get('education_level', ''),
                emergency_contact=request.form.get('emergency_contact', ''),
                emergency_phone=request.form.get('emergency_phone', ''),
                notes=request.form.get('notes', ''),
            )
            db.session.add(member)
            db.session.commit()
            flash('Member added successfully', 'success')
            return redirect(url_for('members.list_members'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding member: {str(e)}', 'danger')
    return render_template('members/form.html', member=None)

@members_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_member(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    member = Member.query.filter_by(id=id, church_id=cid).first()
    if not member:
        flash('Member not found', 'danger')
        return redirect(url_for('members.list_members'))
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        if not full_name:
            flash('Full name is required', 'danger')
            return render_template('members/form.html', member=member)
        try:
            member.full_name = full_name
            member.date_of_birth = request.form.get('date_of_birth', '')
            member.gender = request.form.get('gender', '')
            member.phone = request.form.get('phone', '')
            member.email = request.form.get('email', '')
            member.address = request.form.get('address', '')
            member.membership_status = request.form.get('membership_status', 'active')
            member.baptism_date = request.form.get('baptism_date', '')
            member.baptism_location = request.form.get('baptism_location', '')
            member.baptism_by = request.form.get('baptism_by', '')
            member.join_date = request.form.get('join_date', '')
            member.transfer_from = request.form.get('transfer_from', '')
            member.tribe = request.form.get('tribe', '')
            member.language = request.form.get('language', '')
            member.occupation = request.form.get('occupation', '')
            member.education_level = request.form.get('education_level', '')
            member.emergency_contact = request.form.get('emergency_contact', '')
            member.emergency_phone = request.form.get('emergency_phone', '')
            member.notes = request.form.get('notes', '')
            db.session.commit()
            flash('Member updated successfully', 'success')
            return redirect(url_for('members.list_members'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating member: {str(e)}', 'danger')
    return render_template('members/form.html', member=member)

@members_bp.route('/view/<int:id>')
@login_required
def view_member(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    member = Member.query.filter_by(id=id, church_id=cid).first()
    if not member:
        flash('Member not found', 'danger')
        return redirect(url_for('members.list_members'))
    return render_template('members/view.html', member=member)

@members_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_member(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if not current_user.can_delete:
        flash('Only admins can delete records', 'danger')
        return redirect(url_for('members.list_members'))
    member = Member.query.filter_by(id=id, church_id=cid).first()
    if not member:
        flash('Member not found', 'danger')
        return redirect(url_for('members.list_members'))
    try:
        db.session.delete(member)
        db.session.commit()
        flash('Member deleted', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting member: {str(e)}', 'danger')
    return redirect(url_for('members.list_members'))

@members_bp.route('/transfer/<int:id>', methods=['GET', 'POST'])
@login_required
def transfer_member(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if not current_user.can_manage_users:
        flash('Only admins can transfer members', 'danger')
        return redirect(url_for('members.list_members'))
    member = Member.query.filter_by(id=id, church_id=cid).first()
    if not member:
        flash('Member not found', 'danger')
        return redirect(url_for('members.list_members'))
    churches = Church.query.filter(Church.id != cid).order_by(Church.name).all()
    if request.method == 'POST':
        target_church_id = request.form.get('target_church_id', type=int)
        transfer_date = request.form.get('transfer_date', '').strip()
        reason = request.form.get('reason', '').strip()
        if not target_church_id:
            flash('Please select a target church', 'danger')
            return render_template('members/transfer.html', member=member, churches=churches)
        target_church = Church.query.get(target_church_id)
        if not target_church:
            flash('Target church not found', 'danger')
            return render_template('members/transfer.html', member=member, churches=churches)
        try:
            old_church = Church.query.get(cid)
            member.transfer_from = old_church.name if old_church else ''
            member.membership_status = 'transferred'
            member.church_id = target_church_id
            if reason:
                member.notes = (member.notes or '') + f'\n[Transfer {transfer_date or "N/A"} to {target_church.name}]: {reason}'
            db.session.commit()
            flash(f'{member.full_name} has been transferred to {target_church.name}', 'success')
            return redirect(url_for('members.list_members'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error transferring member: {str(e)}', 'danger')
    return render_template('members/transfer.html', member=member, churches=churches)


@members_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_members():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')

    EXPECTED_FIELDS = [
        'full_name', 'phone', 'email', 'gender', 'date_of_birth',
        'membership_status', 'join_date', 'tribe', 'language',
        'occupation', 'address', 'emergency_contact', 'emergency_phone', 'notes'
    ]

    # Confirm import from session-stored data
    if request.form.get('confirm') == 'yes':
        pending = session.get('import_pending')
        if not pending:
            flash('No pending import found. Please upload again.', 'danger')
            return redirect(url_for('members.import_members'))
        rows = pending['rows']
        field_map = pending['field_map']
        imported = 0
        skipped = 0
        errors = []
        for i, row in enumerate(rows, 1):
            try:
                name_key = list(field_map.keys())[0] if field_map else None
                name = row.get(name_key, '').strip() if name_key else ''
                if not name:
                    skipped += 1
                    continue
                member_data = {'church_id': cid, 'full_name': name}
                for csv_header, model_field in field_map.items():
                    val = row.get(csv_header, '').strip()
                    if val and model_field != 'full_name':
                        member_data[model_field] = val
                member = Member(**member_data)
                db.session.add(member)
                imported += 1
            except Exception as e:
                errors.append(f'Row {i}: {str(e)}')
                skipped += 1
        db.session.commit()
        session.pop('import_pending', None)
        flash(f'Imported {imported} members ({skipped} skipped)', 'success')
        for err in errors[:5]:
            flash(err, 'warning')
        return redirect(url_for('members.list_members'))

    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file or not file.filename.endswith('.csv'):
            flash('Please upload a valid CSV file', 'danger')
            return render_template('members/import.html', preview=None)
        try:
            content = file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
            if not rows:
                flash('CSV file is empty', 'danger')
                return render_template('members/import.html', preview=None)
            headers = list(rows[0].keys())
            field_map = {}
            for header in headers:
                clean = header.strip().lower().replace(' ', '_').replace('-', '_')
                for field in EXPECTED_FIELDS:
                    if clean == field or clean in field:
                        field_map[header] = field
                        break
            # Store in session for confirm step
            session['import_pending'] = {'rows': rows, 'field_map': field_map}
            session.modified = True
            preview_rows = rows[:10]
            return render_template('members/import.html',
                preview=preview_rows, headers=headers, field_map=field_map,
                total=len(rows), EXPECTED_FIELDS=EXPECTED_FIELDS)
        except Exception as e:
            flash(f'Error reading CSV: {str(e)}', 'danger')
            return render_template('members/import.html', preview=None)

    return render_template('members/import.html', preview=None)


@members_bp.route('/export')
@login_required
def export_members():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    members = Member.query.filter_by(church_id=cid).order_by(Member.full_name).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['full_name', 'phone', 'email', 'gender', 'date_of_birth',
                     'membership_status', 'join_date', 'tribe', 'language',
                     'occupation', 'address', 'emergency_contact', 'emergency_phone', 'notes'])
    for m in members:
        writer.writerow([
            m.full_name, m.phone or '', m.email or '', m.gender or '',
            m.date_of_birth or '', m.membership_status or '', m.join_date or '',
            m.tribe or '', m.language or '', m.occupation or '',
            m.address or '', m.emergency_contact or '', m.emergency_phone or '',
            m.notes or ''
        ])
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=members_export.csv'}
    )
