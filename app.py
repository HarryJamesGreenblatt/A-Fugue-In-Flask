"""
A Fugue In Flask - Flask Application Template for Azure Deployment
Main application entry point
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG', False))