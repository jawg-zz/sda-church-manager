from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from app import db
from models import User, ROLES

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.can_manage_users:
            flash('Admin access required', 'danger')
            return redirect('/dashboard')
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or '/dashboard')
        flash('Invalid username or password', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'warning')
    return redirect(url_for('auth.login'))


@auth_bp.route('/users')
@admin_required
def list_users():
    users = User.query.order_by(User.username).all()
    return render_template('auth/users.html', users=users, ROLES=ROLES)


@auth_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'clerk')
        department = request.form.get('department', '').strip()
        if not username or not password:
            flash('Username and password are required', 'danger')
        elif len(password) < 4:
            flash('Password must be at least 4 characters', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        elif role not in ROLES:
            flash('Invalid role', 'danger')
        else:
            try:
                user = User(username=username, role=role, department=department or None)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash(f'User {username} created', 'success')
                return redirect(url_for('auth.list_users'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating user: {str(e)}', 'danger')
    return render_template('auth/user_form.html', user=None, ROLES=ROLES)


@auth_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        role = request.form.get('role', user.role)
        department = request.form.get('department', '').strip()
        new_password = request.form.get('password', '').strip()
        if role not in ROLES:
            flash('Invalid role', 'danger')
        else:
            try:
                user.role = role
                user.department = department or None
                if new_password:
                    if len(new_password) < 4:
                        flash('Password must be at least 4 characters', 'danger')
                        return render_template('auth/user_form.html', user=user, ROLES=ROLES)
                    user.set_password(new_password)
                db.session.commit()
                flash(f'User {user.username} updated', 'success')
                return redirect(url_for('auth.list_users'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating user: {str(e)}', 'danger')
    return render_template('auth/user_form.html', user=user, ROLES=ROLES)


@auth_bp.route('/users/delete/<int:id>', methods=['POST'])
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Cannot delete your own account', 'danger')
        return redirect(url_for('auth.list_users'))
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} deleted', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    return redirect(url_for('auth.list_users'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current = request.form.get('current_password', '')
        new = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        if not current_user.check_password(current):
            flash('Current password is incorrect', 'danger')
        elif len(new) < 4:
            flash('New password must be at least 4 characters', 'danger')
        elif new != confirm:
            flash('New passwords do not match', 'danger')
        else:
            try:
                current_user.set_password(new)
                db.session.commit()
                flash('Password changed successfully', 'success')
                return redirect('/dashboard')
            except Exception as e:
                db.session.rollback()
                flash(f'Error changing password: {str(e)}', 'danger')
    return render_template('auth/change_password.html')
