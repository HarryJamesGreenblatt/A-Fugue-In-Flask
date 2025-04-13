"""
Main Blueprint Module for A Fugue In Flask

This module defines the main routes for the application using Flask's Blueprint system.
Blueprints are a way to organize a Flask application into distinct components, allowing
modular development, cleaner code organization, and better separation of concerns.

The main blueprint handles general pages like the homepage and about page.
"""
from flask import Blueprint, render_template, current_app

# Create a Blueprint named 'main' with the current module as its location
# The Blueprint name 'main' is used for URL generation with url_for()
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Main landing page route handler.
    
    This function handles requests to the root URL (/) and renders the index template.
    It demonstrates a simple route that renders a template with a context variable.
    
    Returns:
        str: Rendered HTML from the index.html template
    """
    return render_template('main/index.html', title='Home')

@main_bp.route('/about')
def about():
    """
    About page route handler.
    
    This function handles requests to the /about URL and renders the about template.
    It follows the same pattern as the index route for consistency.
    
    Returns:
        str: Rendered HTML from the about.html template
    """
    return render_template('main/about.html', title='About')