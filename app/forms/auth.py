"""
Authentication Forms Module for A Fugue In Flask

This module defines WTForms classes for handling authentication-related forms,
including login and registration. Using WTForms provides:

- Consistent form generation
- Form validation with customizable validators
- CSRF protection
- Error handling and messages

These forms work with the templates to render HTML form elements and
with the auth routes to validate user input.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    """
    User login form.
    
    This form is used for authenticating existing users. It includes:
    - Email field with validation
    - Password field with validation
    - Remember me checkbox for persistent sessions
    - Submit button
    
    The form uses multiple validators to ensure data quality and security:
    - DataRequired: Ensures fields are not empty
    - Email: Validates proper email format
    - Length: Ensures password meets minimum length requirement
    """
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Valid email address required")
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters")
    ])
    
    remember_me = BooleanField('Remember Me')
    
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    """
    User registration form.
    
    This form is used for creating new user accounts. It includes:
    - Username field with validation
    - Email field with validation
    - Password field with validation
    - Password confirmation field with validation
    - Submit button
    
    The form uses multiple validators to ensure data quality and security:
    - DataRequired: Ensures fields are not empty
    - Length: Ensures username and password meet length requirements
    - Email: Validates proper email format
    - EqualTo: Ensures password confirmation matches password
    
    It also includes custom validators to check if a username or email
    is already in use by querying the database.
    """
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=64, message="Username must be between 3 and 64 characters")
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Valid email address required"),
        Length(max=120, message="Email must be less than 120 characters")
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters")
    ])
    
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(message="Password confirmation is required"),
        EqualTo('password', message="Passwords must match")
    ])
    
    submit = SubmitField('Register')
    
    # Custom validators to check for username and email uniqueness
    def validate_username(self, username):
        """
        Custom validator for username uniqueness.
        
        This validator checks if a username is already taken by querying the database.
        It's automatically called during form validation for the username field.
        
        Args:
            username: The username field object from the form
            
        Raises:
            ValidationError: If the username is already taken
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """
        Custom validator for email uniqueness.
        
        This validator checks if an email is already registered by querying the database.
        It's automatically called during form validation for the email field.
        
        Args:
            email: The email field object from the form
            
        Raises:
            ValidationError: If the email is already registered
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered. Please use a different one or log in.')