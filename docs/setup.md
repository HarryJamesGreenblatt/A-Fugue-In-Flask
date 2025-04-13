# A Fugue In Flask - Beginner's Setup Guide

This step-by-step guide walks you through setting up and running the Flask application, with detailed explanations of each step and common troubleshooting tips.

## Prerequisites

Before you begin, make sure you have the following installed on your system:

- **Python 3.9+**: The programming language used to build the application
- **pip**: Python package manager (usually comes with Python)
- **Git**: Version control system (optional, but recommended)
- **A code editor**: VS Code, PyCharm, Sublime Text, etc.

## Step 1: Clone or Download the Repository

### Option A: Using Git

```bash
git clone https://github.com/HarryJamesGreenblatt/A-Fugue-In-Flask.git
cd A-Fugue-In-Flask
```

### Option B: Download ZIP

1. Go to https://github.com/HarryJamesGreenblatt/A-Fugue-In-Flask
2. Click the green "Code" button and select "Download ZIP"
3. Extract the ZIP file to a folder of your choice
4. Open a terminal or command prompt and navigate to that folder

## Step 2: Set Up a Virtual Environment

A virtual environment isolates your project dependencies from other Python projects.

### Windows

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

### macOS/Linux

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

> **How to tell if it worked**: Your command prompt should show `(venv)` at the beginning, indicating the virtual environment is active.

## Step 3: Install Dependencies

With your virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

> **What's happening**: This command reads the `requirements.txt` file and installs all the packages listed there, including Flask and its extensions.

> **Troubleshooting**: If you see errors about specific packages not being found, try updating pip (`pip install --upgrade pip`) or install the problematic packages individually.

## Step 4: Set Up Environment Variables

Create a `.env` file in the project root to store configuration variables. You can copy the example file:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

> **Why this matters**: Environment variables configure how your application behaves (e.g., development mode, database location).

## Step 5: Initialize the Database

Run the database initialization script to create the SQLite database and set up the initial user:

### Windows

```bash
# Using the provided batch file
init_db.bat

# OR run the script directly
python -m scripts.init_db
```

### macOS/Linux

```bash
python -m scripts.init_db
```

> **What's happening behind the scenes**:
> 1. A SQLite database file is created in the `instance` folder
> 2. Database tables are defined based on your model classes
> 3. A default admin user is created for you to log in

> **Troubleshooting**: If you see errors about missing modules, ensure all dependencies are installed and your virtual environment is activated.

## Step 6: Run the Flask Application

With everything set up, you can now run the application:

```bash
flask run
```

> **What's happening**: This command starts the Flask development server, which:
> 1. Loads your application from `app.py`
> 2. Connects to the database
> 3. Listens for HTTP requests on `http://127.0.0.1:5000`

## Step 7: Access the Application

Open your web browser and navigate to:

```
http://127.0.0.1:5000
```

You should see the home page of your Flask application. You can log in with:

- **Username**: admin
- **Password**: password

## Understanding the Project Structure

Here's a quick overview of the most important files and directories:

```
app.py                  # Application entry point
├── app/                # Main application package
│   ├── __init__.py     # Application factory
│   ├── routes/         # URL route handlers
│   ├── models/         # Database models
│   ├── templates/      # HTML templates
│   └── static/         # CSS, JavaScript, images
├── instance/           # Instance-specific data (like SQLite database)
└── migrations/         # Database migration files
```

## Common Issues and Solutions

### "No module named 'flask'"

This means Flask isn't installed in your active environment. Make sure you:
1. Activated your virtual environment
2. Ran `pip install -r requirements.txt`

### "Error: Could not locate a Flask application"

The Flask command can't find your app. Make sure:
1. You're in the project root directory
2. Your `.env` file has `FLASK_APP=app.py`

### Database errors

If you see database-related errors:
1. Make sure you ran the initialization script
2. Check if the `instance` directory contains a `dev.db` file
3. If needed, delete the database and re-initialize it

### "ImportError: No module named 'flask_migrate'"

Some dependencies might be missing. Try:
```bash
pip install flask-migrate
```

## Next Steps

After getting the application running, you might want to:

1. **Explore the code**: Look through the different files to understand how they work together
2. **Make a small change**: Modify a template or add a new route to see how changes affect the app
3. **Read the architecture documentation**: See `docs/architecture.md` for a deeper understanding
4. **Deploy the application**: Follow the deployment guide at `docs/deployment.md`

## Flask Development Workflow

As you develop with Flask, you'll typically follow this workflow:

1. **Make code changes** in your editor
2. **Save the files** - the development server will usually auto-reload
3. **Refresh your browser** to see changes
4. **Check the console** for any errors
5. **Repeat** until you're satisfied with the results

> **Tip**: The Flask development server has hot-reloading enabled by default, so most changes will be reflected without restarting the server. However, some changes (like adding new files or changing the application structure) might require a manual restart.

## Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Flask-WTF Documentation](https://flask-wtf.readthedocs.io/)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)