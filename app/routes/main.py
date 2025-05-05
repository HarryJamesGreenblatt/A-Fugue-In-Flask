"""
Main Blueprint Module for A Fugue In Flask

This module defines the main routes for the application using Flask's Blueprint system.
Blueprints are a way to organize a Flask application into distinct components, allowing
modular development, cleaner code organization, and better separation of concerns.

The main blueprint handles general pages like the homepage and about page.
"""
from flask import Blueprint, render_template, current_app
import os
import json

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

@main_bp.route('/architecture')
def architecture():
    """
    Architecture page route handler.
    
    This function handles requests to the /architecture URL and renders the architecture template.
    It provides detailed information about the architectural pattern used in this template.
    It also determines what type of diagram (PNG or HTML) is available to display.
    
    Returns:
        str: Rendered HTML from the architecture.html template
    """
    # Check what type of diagram is available (PNG or HTML)
    diagram_type = "png"  # Default to PNG
    
    # Path to static directory
    static_dir = os.path.join(current_app.root_path, 'static', 'img')
    
    # Check if meta file exists to determine diagram type
    meta_file = os.path.join(static_dir, 'architecture_diagram_meta.json')
    if os.path.exists(meta_file):
        try:
            with open(meta_file, 'r') as f:
                meta_data = json.load(f)
                if meta_data.get('type') == 'fallback_html':
                    diagram_type = "html"
        except (json.JSONDecodeError, IOError):
            pass
    # If no meta file but HTML exists
    elif not os.path.exists(os.path.join(static_dir, 'architecture_diagram.png')) and \
         os.path.exists(os.path.join(static_dir, 'architecture_diagram.html')):
        diagram_type = "html"
    
    return render_template('main/architecture.html', title='Architectural Pattern', diagram_type=diagram_type)