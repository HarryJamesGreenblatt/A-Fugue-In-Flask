"""
User Model Module for A Fugue In Flask

This module defines the User model for the application, which is used for authentication,
user management, and associating data with specific users.

The User model implements:
- SQLAlchemy ORM mapping for database operations
- Flask-Login UserMixin integration for authentication
- Secure password handling (hashing/verification is in the auth routes)
- User representation methods
"""
from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    """
    User model for authentication and user management.
    
    This model inherits from:
    - UserMixin: Provides default implementations for Flask-Login interface methods
      (is_authenticated, is_active, is_anonymous, get_id)
    - db.Model: SQLAlchemy's base model class for ORM functionality
    
    The User model stores essential user information and implements the required
    methods for Flask-Login integration.
    """
    # Table name explicitly set for clarity
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Authentication fields
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # User status and metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Add relationships to other models here if needed, for example:
    # posts = db.relationship('Post', backref='author', lazy='dynamic')
    
    def __repr__(self):
        """
        String representation of the User instance.
        
        This is useful for debugging and logging, providing a readable
        representation of the User object.
        
        Returns:
            str: A string showing the User's ID and username
        """
        return f'<User {self.id}: {self.username}>'

# Flask-Login user loader callback
@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login user loader callback.
    
    This function is required by Flask-Login to load a user from the database
    based on the user ID stored in the session cookie. It's called automatically
    when a user is logged in to retrieve the User object for the current session.
    
    Args:
        user_id (str): The user ID as a string (Flask-Login requirement)
        
    Returns:
        User: The User object corresponding to the user_id, or None if not found
    """
    return User.query.get(int(user_id))