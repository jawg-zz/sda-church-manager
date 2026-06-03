from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import db
from models import Event, log_audit
from datetime import datetime

events_bp = Blueprint('events', __name__, url_prefix='/events')

EVENT_TYPES = [
    'Divine Service', 'Sabbath School', 'Prayer Meeting',
    'Evangelistic Campaign', 'Youth Program', 'Women\'s Ministry',
    'Men\'s Ministry', 'Community Outreach', 'Health Fair',
    'Marriage Seminar', 'Children\'s Program', 'Church Board',
    'Business Meeting', 'Special Event', 'Other'
]

@events_bp.route('/')
@login_required
def list_events():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    page = request.args.get('page', 1, type=int)
    pagination = Event.query.filter_by(church_id=cid).order_by(Event.date.desc()).paginate(
        page=page, per_page=12, error_out=False)
    return render_template('events/list.html', events=pagination.items,
                           pagination=pagination, EVENT_TYPES=EVENT_TYPES)

@events_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_event():
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Event title is required', 'danger')
            return render_template('events/form.html', event=None, EVENT_TYPES=EVENT_TYPES,
                                  current_date=datetime.now().strftime('%Y-%m-%d'))
        try:
            e = Event(
                church_id=cid,
                title=title,
                date=request.form['date'],
                time=request.form.get('time', ''),
                location=request.form.get('location', ''),
                event_type=request.form.get('event_type', ''),
                description=request.form.get('description', ''),
                organizer=request.form.get('organizer', ''),
            )
            db.session.add(e)
            db.session.commit()
            log_audit(cid, current_user.id, 'create', 'event', e.id, f'Added event: {e.title}')
            flash('Event created successfully', 'success')
            return redirect(url_for('events.list_events'))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating event: {str(e)}', 'danger')
    return render_template('events/form.html', event=None, EVENT_TYPES=EVENT_TYPES,
                          current_date=datetime.now().strftime('%Y-%m-%d'))

@events_bp.route('/view/<int:id>')
@login_required
def view_event(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    e = Event.query.filter_by(id=id, church_id=cid).first()
    if not e:
        flash('Event not found', 'danger')
        return redirect(url_for('events.list_events'))
    return render_template('events/view.html', event=e)

@events_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_event(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    e = Event.query.filter_by(id=id, church_id=cid).first()
    if not e:
        flash('Event not found', 'danger')
        return redirect(url_for('events.list_events'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Event title is required', 'danger')
            return render_template('events/form.html', event=e, EVENT_TYPES=EVENT_TYPES,
                                  current_date=datetime.now().strftime('%Y-%m-%d'))
        try:
            e.title = title
            e.date = request.form['date']
            e.time = request.form.get('time', '')
            e.location = request.form.get('location', '')
            e.event_type = request.form.get('event_type', '')
            e.description = request.form.get('description', '')
            e.organizer = request.form.get('organizer', '')
            db.session.commit()
            log_audit(cid, current_user.id, 'update', 'event', e.id, f'Updated event: {e.title}')
            flash('Event updated successfully', 'success')
            return redirect(url_for('events.list_events'))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating event: {str(e)}', 'danger')
    return render_template('events/form.html', event=e, EVENT_TYPES=EVENT_TYPES,
                          current_date=datetime.now().strftime('%Y-%m-%d'))

@events_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_event(id):
    cid = session.get('church_id')
    if not cid:
        return redirect('/auth/select-church')
    if not current_user.can_delete:
        flash('Only admins can delete records', 'danger')
        return redirect(url_for('events.list_events'))
    e = Event.query.filter_by(id=id, church_id=cid).first()
    if not e:
        flash('Event not found', 'danger')
        return redirect(url_for('events.list_events'))
    try:
        db.session.delete(e)
        db.session.commit()
        log_audit(cid, current_user.id, 'delete', 'event', id, f'Deleted event')
        flash('Event deleted', 'warning')
    except Exception as ex:
        db.session.rollback()
        flash(f'Error deleting event: {str(ex)}', 'danger')
    return redirect(url_for('events.list_events'))
