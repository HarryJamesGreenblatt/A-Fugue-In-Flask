"""
A Fugue In Flask - Flask Application Template for Azure Deployment
Main application entry point

This file serves as the main entry point for the Flask application. Its primary purposes are:
1. To import the application factory function (create_app) from the app package
2. To create an instance of the Flask application
3. To run the application when executed directly (not when imported)

The application factory pattern used here provides several advantages:
- It allows for creating multiple app instances with different configurations (useful for testing)
- It keeps the application creation process in a single, centralized function
- It allows for lazy-loading of resources and configurations
- It makes the application easier to extend and maintain

When the application is run directly (python app.py), the debug mode is automatically
set based on the application's configuration.
"""
from app import create_app

# Create the application instance using the factory function
app = create_app()

# This conditional ensures the app only runs when this script is executed directly
# (not when imported as a module in another script)
if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG', False))