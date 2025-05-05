#!/usr/bin/env python
"""
Architecture Diagram Generator for A Fugue In Flask

This script generates a visualization of the application's architecture pattern using the diagrams library.
If Graphviz is not available, it will create a fallback HTML representation.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json

# Output paths
OUTPUT_DIR = "app/static/img"
DIAGRAM_NAME = "architecture_diagram"
OUTPUT_PATH = f"{OUTPUT_DIR}/{DIAGRAM_NAME}"

def check_graphviz_installation():
    """Check if the Graphviz 'dot' executable is in the PATH."""
    dot_path = shutil.which('dot')
    if dot_path:
        print(f"✅ Found Graphviz 'dot' executable at: {dot_path}")
        return True
    else:
        print("❌ Graphviz 'dot' executable not found in PATH.")
        print("\nTo fix this issue:")
        print("1. Download Graphviz from: https://graphviz.org/download/")
        print("2. Run the Windows installer (.exe or .msi)")
        print("3. During installation, select the option to add Graphviz to your PATH")
        return False

def create_fallback_html():
    """Create a fallback HTML diagram that doesn't require Graphviz."""
    # Create the output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # HTML representation of the architecture
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Application Factory Pattern with Blueprint Modularity</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .diagram-container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 5px;
        }
        .node {
            border: 1px solid #666;
            border-radius: 5px;
            padding: 10px 15px;
            margin: 10px 0;
            background-color: #f8f9fa;
            text-align: center;
        }
        .factory {
            background-color: #007bff;
            color: white;
            font-weight: bold;
        }
        .extensions {
            background-color: #6c757d;
            color: white;
        }
        .blueprints {
            background-color: #dc3545;
            color: white;
        }
        .models {
            background-color: #28a745;
            color: white;
        }
        .templates {
            background-color: #ffc107;
            color: black;
        }
        .azure {
            background-color: #17a2b8;
            color: white;
        }
        .cluster {
            border: 1px dashed #aaa;
            border-radius: 5px;
            padding: 10px;
            margin: 15px 0;
        }
        .cluster-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #555;
        }
        .arrow {
            text-align: center;
            font-size: 24px;
            color: #666;
            margin: 5px 0;
        }
        .entry-point {
            background-color: #f8f9fa;
            border: 2px solid #343a40;
        }
    </style>
</head>
<body>
    <div class="diagram-container">
        <h2 style="text-align: center;">Application Factory Pattern with Blueprint Modularity</h2>
        
        <!-- Entry Point -->
        <div class="node entry-point">app.py - Entry Point</div>
        
        <div class="arrow">↓</div>
        
        <!-- Application Factory -->
        <div class="node factory">create_app - Application Factory</div>
        
        <div class="arrow">↓</div>
        
        <!-- Main Components -->
        <div style="display: flex; justify-content: space-between;">
            <!-- Left Column -->
            <div style="flex: 1; margin-right: 10px;">
                <div class="cluster">
                    <div class="cluster-title">Configuration</div>
                    <div class="node">config.py - Environment Settings</div>
                </div>
            </div>
            
            <!-- Middle Column -->
            <div style="flex: 1; margin-right: 10px;">
                <div class="cluster">
                    <div class="cluster-title">Extensions</div>
                    <div class="node">SQLAlchemy - Database ORM</div>
                    <div class="node">Flask-Login - Authentication</div>
                    <div class="node">Flask-Migrate - Migrations</div>
                </div>
                
                <div class="arrow">↓</div>
                
                <div class="cluster">
                    <div class="cluster-title">Models</div>
                    <div class="node">User Model</div>
                </div>
            </div>
            
            <!-- Right Column -->
            <div style="flex: 1;">
                <div class="cluster">
                    <div class="cluster-title">Blueprints</div>
                    <div class="node">Main Blueprint</div>
                    <div class="node">Auth Blueprint</div>
                </div>
                
                <div class="arrow">↓</div>
                
                <div class="cluster">
                    <div class="cluster-title">Templates</div>
                    <div class="node">main/*.html</div>
                    <div class="node">auth/*.html</div>
                </div>
            </div>
        </div>
        
        <div class="arrow">↓</div>
        
        <!-- Azure Deployment -->
        <div class="cluster">
            <div class="cluster-title">Azure Deployment</div>
            <div style="display: flex; justify-content: space-between;">
                <div class="node azure" style="flex: 1; margin-right: 5px;">Azure App Service</div>
                <div class="node azure" style="flex: 1; margin-right: 5px;">Azure SQL Database</div>
                <div class="node azure" style="flex: 1;">Azure Key Vault</div>
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    # Save the HTML file
    with open(f"{OUTPUT_PATH}.html", "w") as f:
        f.write(html_content)
    
    print(f"✅ Created fallback HTML diagram at {OUTPUT_PATH}.html")
    
    # Also save a metadata file to indicate that we used the fallback
    metadata = {
        "type": "fallback_html",
        "reason": "Graphviz not available",
        "created_at": str(datetime.datetime.now()),
        "path": f"{OUTPUT_PATH}.html"
    }
    
    with open(f"{OUTPUT_PATH}_meta.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    return True

try:
    import datetime
    from diagrams import Diagram, Cluster, Edge
    from diagrams.programming.framework import Flask
    from diagrams.programming.language import Python
    from diagrams.onprem.database import PostgreSQL as Database
    from diagrams.azure.database import SQLDatabases
    from diagrams.azure.security import KeyVaults
    from diagrams.azure.web import AppServices
    from diagrams.azure.devops import Repos
    
    DIAGRAMS_IMPORTED = True
    print("✅ Successfully imported diagrams library")
except ImportError as e:
    DIAGRAMS_IMPORTED = False
    print(f"❌ Error importing diagrams library: {e}")
    print("   You can install it with: pip install diagrams")

def generate_diagram(output_path=OUTPUT_PATH, show_diagram=False):
    """Generate the architecture diagram using the diagrams library."""
    if not DIAGRAMS_IMPORTED:
        print("❌ Cannot generate diagram: diagrams library is not available")
        return False
        
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"🔄 Generating architecture diagram to: {output_path}.png")
    
    try:
        graph_attrs = {
            "layout": "fdp",      # Use the default hierarchical engine
            "splines": "spline",  # Use orthogonal splines for edges
        }
        with Diagram("Application Factory Pattern with Blueprint Modularity", 
                    show=show_diagram, filename=output_path, outformat="png", graph_attr=graph_attrs):
            # Entry point
            app_py = Python("app.py\nEntry Point")
            
            # Application Factory
            app_factory = Flask("create_app\nApplication Factory")
            
            # Connect app.py to factory
            app_py >> app_factory
            
            # Create a cluster for configuration
            with Cluster("Configuration"):
                config = Python("config.py\nEnvironment Settings")
            
            # Create a cluster for extensions
            with Cluster("Extensions"):
                database = Database("SQLAlchemy\nORM")
                auth = Flask("Flask-Login\nAuthentication")
                migrations = Flask("Flask-Migrate\nMigrations")
            
            # Create a cluster for blueprints
            with Cluster("Blueprints"):
                main_bp = Flask("Main Blueprint\nHome, About, Architecture")
                auth_bp = Flask("Auth Blueprint\nLogin, Register, Logout")
            
            # Connect factory to other components
            app_factory >> Edge(color="darkgreen") >> config
            app_factory >> Edge(color="darkblue") >> database
            app_factory >> Edge(color="darkblue") >> auth
            app_factory >> Edge(color="darkblue") >> migrations
            app_factory >> Edge(color="darkred") >> main_bp
            app_factory >> Edge(color="darkred") >> auth_bp
            
            # Create a cluster for models
            with Cluster("Models"):
                user_model = Python("User Model")
            
            # Create a cluster for templates
            with Cluster("Templates"):
                main_templates = Python("main/\nTemplates")
                auth_templates = Python("auth/\nTemplates")
            
            # Connect models and templates
            database >> user_model
            main_bp >> main_templates
            auth_bp >> auth_templates
            
            # Create a cluster for static files
            with Cluster("Static Files"):
                static = Python("CSS, JS, Images")
            
            main_bp >> static
            
            # Azure deployment components
            with Cluster("Azure Deployment"):
                app_service = AppServices("Azure App Service")
                sql_db = SQLDatabases("Azure SQL Database")
                key_vault = KeyVaults("Azure Key Vault")
                github = Repos("GitHub Actions CI/CD")
                
                # Connect Azure components
                github >> app_service
                app_service >> sql_db
                app_service >> key_vault

            # Connect application to Azure
            app_factory >> Edge(style="dotted") >> app_service
            
        print(f"✅ Architecture diagram generated successfully at {output_path}.png")
        
        # Save metadata
        metadata = {
            "type": "graphviz_png",
            "created_at": str(datetime.datetime.now()),
            "path": f"{output_path}.png"
        }
        
        with open(f"{output_path}_meta.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        return True
    except Exception as e:
        print(f"❌ Error generating diagram: {e}")
        return False

def create_direct_dot_file(output_path=OUTPUT_PATH):
    """Create a DOT file directly that can be converted to an image."""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create the DOT file content
    dot_content = """
digraph "Application Factory Pattern" {
    graph [fontname="Arial", rankdir=TB, splines=true, nodesep=0.8, ranksep=1.0];
    node [fontname="Arial", shape=box, style="rounded,filled", fillcolor=lightgrey, fontsize=12];
    edge [fontname="Arial"];

    // Entry point and Factory
    app_py [label="app.py\\nEntry Point", fillcolor=lightyellow];
    app_factory [label="create_app\\nApplication Factory", fillcolor=lightblue];
    
    // Main components
    config [label="Configuration\\nSettings", fillcolor=lightgreen];
    database [label="SQLAlchemy\\nORM", fillcolor=lightpink];
    auth [label="Flask-Login\\nAuthentication", fillcolor=lightpink];
    migrations [label="Flask-Migrate", fillcolor=lightpink];
    main_bp [label="Main Blueprint", fillcolor=lightsalmon];
    auth_bp [label="Auth Blueprint", fillcolor=lightsalmon];
    user_model [label="User Model", fillcolor=lightcyan];
    main_templates [label="main/\\nTemplates", fillcolor=lightgoldenrod];
    auth_templates [label="auth/\\nTemplates", fillcolor=lightgoldenrod];
    static [label="Static Files\\nCSS, JS, Images", fillcolor=lightskyblue];
    
    // Azure components
    app_service [label="Azure App Service", fillcolor=azure];
    sql_db [label="Azure SQL Database", fillcolor=azure];
    key_vault [label="Azure Key Vault", fillcolor=azure];
    github [label="GitHub Actions\\nCI/CD", fillcolor=azure];
    
    // Connections
    app_py -> app_factory;
    app_factory -> config;
    app_factory -> database;
    app_factory -> auth;
    app_factory -> migrations;
    app_factory -> main_bp;
    app_factory -> auth_bp;
    database -> user_model;
    main_bp -> main_templates;
    auth_bp -> auth_templates;
    main_bp -> static;
    github -> app_service;
    app_service -> sql_db;
    app_service -> key_vault;
    app_factory -> app_service [style=dotted];
    
    // Subgraphs
    subgraph cluster_extensions {
        label = "Extensions";
        style = "dashed";
        database; auth; migrations;
    }
    
    subgraph cluster_blueprints {
        label = "Blueprints";
        style = "dashed";
        main_bp; auth_bp;
    }
    
    subgraph cluster_templates {
        label = "Templates";
        style = "dashed";
        main_templates; auth_templates;
    }
    
    subgraph cluster_azure {
        label = "Azure Deployment";
        style = "dashed";
        app_service; sql_db; key_vault; github;
    }
}
"""
    
    # Write the DOT file
    dot_file = f"{output_path}.dot"
    with open(dot_file, "w") as f:
        f.write(dot_content)
        
    print(f"✅ DOT file created at: {dot_file}")
    return dot_file

def convert_dot_to_image(dot_file, output_format="png"):
    """Convert a DOT file to an image using the dot executable."""
    output_path = dot_file.replace(".dot", f".{output_format}")
    
    try:
        result = subprocess.run(
            ["dot", f"-T{output_format}", dot_file, "-o", output_path], 
            capture_output=True, text=True, check=True
        )
        print(f"✅ Image generated at: {output_path}")
        return True
    except subprocess.SubprocessError as e:
        print(f"❌ Error running dot command: {e}")
        print(f"Command output: {e.stdout if hasattr(e, 'stdout') else 'No output'}")
        print(f"Command error: {e.stderr if hasattr(e, 'stderr') else 'No error details'}")
        return False
    except FileNotFoundError:
        print("❌ dot command not found. Make sure Graphviz is installed and in your PATH.")
        return False

if __name__ == "__main__":
    print("📊 Architecture Diagram Generator\n")
    
    # First check if we have the diagrams library
    if not DIAGRAMS_IMPORTED:
        print("ℹ️ diagrams library not available. Will use alternative approaches.")
    
    # Check if Graphviz is installed
    graphviz_available = check_graphviz_installation()
    
    success = False
    
    # Create the output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if DIAGRAMS_IMPORTED and graphviz_available:
        # Method 1: Use the diagrams library (preferred)
        print("\n🔄 Attempting to generate diagram using diagrams library...")
        success = generate_diagram(OUTPUT_PATH)
    
    if not success and graphviz_available:
        # Method 2: Use direct DOT file and Graphviz
        print("\n🔄 Falling back to direct DOT file generation...")
        dot_file = create_direct_dot_file(OUTPUT_PATH)
        success = convert_dot_to_image(dot_file)
    
    if not success:
        # Method 3: Create an HTML fallback
        print("\n🔄 Creating HTML fallback diagram...")
        success = create_fallback_html()
    
    # Final message
    if success:
        print("\n✅ Diagram generation complete!")
        print(f"   You can now use this diagram in your architecture page.")
        
        # Check what kind of file we generated
        if os.path.exists(f"{OUTPUT_PATH}.png"):
            print(f"   Image file: {os.path.abspath(f'{OUTPUT_PATH}.png')}")
        elif os.path.exists(f"{OUTPUT_PATH}.html"):
            print(f"   HTML file: {os.path.abspath(f'{OUTPUT_PATH}.html')}")
    else:
        print("\n❌ Failed to generate diagram through any method.")
        print("   Please install Graphviz and make sure it's in your PATH.")
        print("   Visit https://graphviz.org/download/ for installation instructions.")