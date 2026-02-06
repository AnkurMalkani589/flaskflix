from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from models import User
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('movies.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('movies.index'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('movies.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_exists = User.query.filter((User.username==username) | (User.email==email)).first()
        if user_exists:
            flash('Username or email already exists.', 'danger')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Account created! You can now login.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('movies.index'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('movies.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # In a real app, you would send an email here
            token = user.get_reset_token()
            flash(f'Password reset link has been sent to {email}. (Demo: copy the link below)', 'info')
            flash(f'Reset Link: {url_for("auth.reset_token", token=token, _external=True)}', 'warning')
        else:
            flash('No account found with that email address.', 'danger')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_request.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('movies.index'))
    
    user = User.verify_reset_token(token)
    
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.reset_request'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            user.set_password(password)
            db.session.commit()
            flash('Your password has been reset! You can now login.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_token.html', token=token)

