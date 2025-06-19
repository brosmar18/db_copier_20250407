from psycopg2 import sql
from .connection import connect_to_db


def fetch_databases(credentials):
    """Fetch the list of non-template databases from PostgreSQL."""
    conn = connect_to_db(credentials)
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = [row[0] for row in cur.fetchall()]
        cur.close()
        return databases
    except Exception as e:
        print(f"Error fetching databases: {e}")
        return []
    finally:
        conn.close()


def copy_database_logic(credentials, src_db, new_db, update_status_callback):
    """
    Perform the database copy operation.
    update_status_callback: a callback to update status messages in the UI.
    """
    conn = connect_to_db(credentials)
    if not conn:
        raise Exception("Unable to connect to database.")
    try:
        conn.autocommit = True
        cur = conn.cursor()

        update_status_callback("Terminating active connections...")
        terminate_query = """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid();
        """
        cur.execute(terminate_query, (src_db,))

        update_status_callback("Creating new database...")
        create_query = sql.SQL("CREATE DATABASE {} WITH TEMPLATE {} OWNER {}").format(
            sql.Identifier(new_db),
            sql.Identifier(src_db),
            sql.Identifier(credentials["user"]),
        )
        cur.execute(create_query)

        cur.close()
        update_status_callback("Database copy completed successfully.")
    except Exception as e:
        raise e
    finally:
        conn.close()


def get_database_details(credentials, db_name):
    """
    Fetch detailed information for a specific database.
    Returns a dictionary with:
      - Database Name
      - Active Connections (number of connections currently active)
      - Last Updated (formatted as MM/DD/YYYY)
    """
    conn = connect_to_db(credentials)
    if not conn:
        return {}
    try:
        cur = conn.cursor()
        query = """
            SELECT d.datname,
                   (SELECT count(*) FROM pg_stat_activity WHERE datname = d.datname) AS active_connections,
                   to_char(s.stats_reset, 'MM/DD/YYYY') as last_updated
            FROM pg_database d
            JOIN pg_stat_database s ON d.datname = s.datname
            WHERE d.datname = %s;
        """
        cur.execute(query, (db_name,))
        row = cur.fetchone()
        if row:
            details = {
                "Database Name": row[0],
                "Active Connections": row[1],
                "Last Updated": row[2],
            }
            return details
        else:
            return {}
    except Exception as e:
        print("Error fetching details:", e)
        return {}
    finally:
        conn.close()


def terminate_and_delete_database(credentials, db_name):
    """
    Terminates all sessions for the specified database and then deletes it.
    """
    conn = connect_to_db(credentials, database="postgres")
    if not conn:
        raise Exception("Unable to connect to database")
    try:
        conn.autocommit = True
        cur = conn.cursor()
        # Terminate active sessions for the target database
        terminate_query = """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid();
        """
        cur.execute(terminate_query, (db_name,))

        # Drop the database safely using the sql module
        drop_query = sql.SQL("DROP DATABASE {}").format(sql.Identifier(db_name))
        cur.execute(drop_query)
        cur.close()
    except Exception as e:
        raise Exception(f"Failed to delete database '{db_name}': {e}")
    finally:
        conn.close()


def rename_database(credentials, old_name, new_name, update_status_callback):
    """
    Rename a database by terminating connections and using ALTER DATABASE.

    Parameters:
      - credentials: Database connection credentials
      - old_name: Current database name
      - new_name: New database name
      - update_status_callback: Callback function to update UI status
    """
    # Validate new name
    if not new_name or not new_name.strip():
        raise Exception("New database name cannot be empty")

    new_name = new_name.strip()

    # Check if new name is different from old name
    if old_name.lower() == new_name.lower():
        raise Exception("New database name must be different from current name")

    # Check if new database name already exists
    existing_databases = fetch_databases(credentials)
    if new_name.lower() in [db.lower() for db in existing_databases]:
        raise Exception(f"Database '{new_name}' already exists")

    # Validate database name (PostgreSQL naming rules)
    import re

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", new_name):
        raise Exception(
            "Database name can only contain letters, numbers, and underscores, and must start with a letter or underscore"
        )

    if len(new_name) > 63:
        raise Exception("Database name cannot exceed 63 characters")

    # Connect to postgres database (not the target database)
    conn = connect_to_db(credentials, database="postgres")
    if not conn:
        raise Exception("Unable to connect to PostgreSQL server")

    try:
        conn.autocommit = True
        cur = conn.cursor()

        update_status_callback("Checking database exists...")

        # Verify the source database exists
        check_query = "SELECT 1 FROM pg_database WHERE datname = %s"
        cur.execute(check_query, (old_name,))
        if not cur.fetchone():
            raise Exception(f"Source database '{old_name}' does not exist")

        update_status_callback("Terminating active connections...")

        # Terminate all active connections to the target database
        terminate_query = """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid();
        """
        cur.execute(terminate_query, (old_name,))

        update_status_callback(f"Renaming database to '{new_name}'...")

        # Rename the database using ALTER DATABASE
        rename_query = sql.SQL("ALTER DATABASE {} RENAME TO {}").format(
            sql.Identifier(old_name), sql.Identifier(new_name)
        )
        cur.execute(rename_query)

        cur.close()
        update_status_callback("Database renamed successfully.")

    except Exception as e:
        raise Exception(f"Failed to rename database '{old_name}' to '{new_name}': {e}")
    finally:
        conn.close()
