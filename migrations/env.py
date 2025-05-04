import logging
from logging.config import fileConfig
import os
from flask import current_app

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        # Following Azure best practices for secure credential handling
        # Don't include passwords in logs or rendered URLs
        url = get_engine().url
        # For newer SQLAlchemy versions that have render_as_string
        if hasattr(url, 'render_as_string'):
            # Secure: hide passwords in connection strings
            return url.render_as_string(hide_password=False).replace('%', '%%')
        # For older SQLAlchemy versions
        else:
            return str(url).replace('%', '%%')
    except AttributeError as e:
        logger.warning(f"Error getting engine URL: {e}")
        # Centralized database handling - fallback if engine URL retrieval fails
        if os.environ.get('USE_CENTRALIZED_DB') == 'True':
            db_server = os.environ.get('DB_SERVER', 'sequitur-sql-server.database.windows.net')
            db_name = os.environ.get('DB_NAME', 'fugue-flask-db')
            # Use managed identity or centralized connection string if available
            if 'TEMPLATE_DATABASE_URI' in os.environ:
                logger.info("Using TEMPLATE_DATABASE_URI for migrations")
                return os.environ.get('TEMPLATE_DATABASE_URI').replace('%', '%%')
            else:
                logger.info("Using centralized DB configuration for migrations")
                # We can't construct a full connection string here without credentials,
                # Alembic will get them from the Flask app's config
                return f"mssql+pyodbc://@{db_server}/{db_name}".replace('%', '%%')
        # Default fallback
        return str(get_engine().url).replace('%', '%%')


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
