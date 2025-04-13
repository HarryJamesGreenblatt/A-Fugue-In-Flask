"""
Authentication Blueprint Module for A Fugue In Flask

This module defines authentication-related routes using Flask's Blueprint system.
It handles user authentication functionality including login, registration, and logout.

The authentication system is built using:
- Flask-Login: For session management and "remember me" functionality
- Werkzeug: For password hashing and verification
- SQLAlchemy: For database operations with the User model

This blueprint demonstrates Flask best practices:
- Modular code organization with blueprints
- Form handling and validation
- Flash messages for user feedback
- Secure password management
- Login session management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm

# Create a Blueprint named 'auth' with the current module as its location
# The url_prefix='/auth' will be prepended to all routes defined in this blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route handler.
    
    This function:
    1. Handles both GET and POST requests to the /auth/login URL
    2. Redirects already authenticated users to the home page
    3. Validates submitted login credentials
    4. Creates a user session with Flask-Login on successful authentication
    5. Supports "remember me" functionality for persistent sessions
    6. Handles "next" URL parameter for redirecting after successful login
    7. Provides feedback through flash messages
    
    Flow:
    - GET request: Renders the login form
    - POST request: Processes form submission, authenticates user, and redirects
    
    Returns:
        On GET: Rendered login form template
        On POST (success): Redirect to next page or home page
        On POST (failure): Re-rendered login form with error messages
    """
    # Redirect already logged-in users to the home page
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Initialize the login form (WTForms)
    form = LoginForm()
    
    # Handle form submission (POST request with valid form data)
    if form.validate_on_submit():
        # Query the database for the user with the provided email
        user = User.query.filter_by(email=form.email.data).first()
        
        # Verify both user existence and password correctness
        if user and check_password_hash(user.password_hash, form.password.data):
            # Log the user in and create a session
            login_user(user, remember=form.remember_me.data)
            
            # Handle "next" parameter for redirect after login
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
            
        # Show error message for invalid credentials
        flash('Invalid email or password', 'danger')
    
    # Render the login template with the form
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route handler.
    
    This function:
    1. Handles both GET and POST requests to the /auth/register URL
    2. Redirects already authenticated users to the home page
    3. Validates submitted registration data
    4. Creates new user accounts with securely hashed passwords
    5. Provides feedback through flash messages
    
    Flow:
    - GET request: Renders the registration form
    - POST request: Validates data, creates new user, redirects to login
    
    Security features:
    - Passwords are never stored in plain text
    - Werkzeug's generate_password_hash creates secure password hashes
    
    Returns:
        On GET: Rendered registration form template
        On POST (success): Redirect to login page with success message
        On POST (failure): Re-rendered registration form with error messages
    """
    # Redirect already logged-in users to the home page
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Initialize the registration form (WTForms)
    form = RegistrationForm()
    
    # Handle form submission (POST request with valid form data)
    if form.validate_on_submit():
        # Create a new user instance with securely hashed password
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        
        # Add and commit the new user to the database
        db.session.add(user)
        db.session.commit()
        
        # Show success message and redirect to login page
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    # Render the registration template with the form
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """
    User logout route handler.
    
    This function:
    1. Requires authentication (via @login_required decorator)
    2. Ends the user's session using Flask-Login
    3. Provides feedback through flash messages
    4. Redirects to the home page
    
    The @login_required decorator protects this route from unauthorized access.
    If an unauthenticated user tries to access this route, they will be
    redirected to the login page (specified by login_manager.login_view).
    
    Returns:
        Redirect to the home page
    """
    # End the user's session
    logout_user()
    
    # Show success message
    flash('You have been logged out.', 'info')
    
    # Redirect to the home page
    return redirect(url_for('main.index'))