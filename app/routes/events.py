from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from models import Event

events_bp = Blueprint('events', __name__, url_prefix='/events')

EVENT_TYPES = [
    'Divine Service', 'Sabbath School', 'Prayer Meeting',
    'Evangelistic Campaign', 'Youth Program', 'Women\'s Ministry',
    'Men\'s Ministry', 'Community Outreach', 'Health Fair',
    'Marriage Seminar', 'Children\'s Program', 'Church Board',
    'Business Meeting', 'Special Event', 'Other'
]

@events_bp.route('/')
def list_events():
    events = Event.query.order_by(Event.date).all()
    return render_template('events/list.html', events=events, EVENT_TYPES=EVENT_TYPES)

@events_bp.route('/add', methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        e = Event(
            title=request.form['title'],
            date=request.form['date'],
            time=request.form.get('time', ''),
            location=request.form.get('location', ''),
            event_type=request.form.get('event_type', ''),
            description=request.form.get('description', ''),
            organizer=request.form.get('organizer', ''),
        )
        db.session.add(e)
        db.session.commit()
        return redirect(url_for('events.list_events'))
    return render_template('events/form.html', event=None, EVENT_TYPES=EVENT_TYPES)

@events_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_event(id):
    e = Event.query.get_or_404(id)
    if request.method == 'POST':
        e.title = request.form['title']
        e.date = request.form['date']
        e.time = request.form.get('time', '')
        e.location = request.form.get('location', '')
        e.event_type = request.form.get('event_type', '')
        e.description = request.form.get('description', '')
        e.organizer = request.form.get('organizer', '')
        db.session.commit()
        return redirect(url_for('events.list_events'))
    return render_template('events/form.html', event=e, EVENT_TYPES=EVENT_TYPES)

@events_bp.route('/delete/<int:id>', methods=['POST'])
def delete_event(id):
    e = Event.query.get_or_404(id)
    db.session.delete(e)
    db.session.commit()
    return redirect(url_for('events.list_events'))
