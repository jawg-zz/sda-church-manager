from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from models import Event
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
    page = request.args.get('page', 1, type=int)
    pagination = Event.query.order_by(Event.date.desc()).paginate(
        page=page, per_page=12, error_out=False)
    return render_template('events/list.html', events=pagination.items,
                           pagination=pagination, EVENT_TYPES=EVENT_TYPES)

@events_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Event title is required', 'danger')
            return render_template('events/form.html', event=None, EVENT_TYPES=EVENT_TYPES,
                                  current_date=datetime.now().strftime('%Y-%m-%d'))
        try:
            e = Event(
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
    e = Event.query.get_or_404(id)
    return render_template('events/view.html', event=e)

@events_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_event(id):
    e = Event.query.get_or_404(id)
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
    e = Event.query.get_or_404(id)
    try:
        db.session.delete(e)
        db.session.commit()
        flash('Event deleted', 'warning')
    except Exception as ex:
        db.session.rollback()
        flash(f'Error deleting event: {str(ex)}', 'danger')
    return redirect(url_for('events.list_events'))
