import psycopg2
from psycopg2 import sql

def connect_to_db(credentials, database="postgres"):
    """Establish a PostgreSQL connection using provided credentials."""
    try:
        conn = psycopg2.connect(
            host=credentials["host"],
            port=credentials["port"],
            user=credentials["user"],
            password=credentials["password"],
            database=database
        )
        return conn
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

def test_connection(credentials):
    """
    Test the connection with the provided credentials.
    Returns (True, None) if successful, else (False, error_message)
    """
    try:
        conn = psycopg2.connect(
            host=credentials["host"],
            port=credentials["port"],
            user=credentials["user"],
            password=credentials["password"],
            database="postgres"
        )
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

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
            sql.Identifier(credentials["user"])
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
    Returns a dictionary of details.
    """
    conn = connect_to_db(credentials)
    if not conn:
        return {}
    try:
        cur = conn.cursor()
        # Query for basic details from pg_database and lookup owner name from pg_roles.
        query = """
            SELECT d.datname,
                   (SELECT rolname FROM pg_roles WHERE oid = d.datdba) AS owner,
                   d.encoding,
                   d.datcollate,
                   d.datctype,
                   d.datistemplate,
                   d.datallowconn
            FROM pg_database d
            WHERE d.datname = %s;
        """
        cur.execute(query, (db_name,))
        row = cur.fetchone()
        if row:
            details = {
                "Database Name": row[0],
                "Owner": row[1],
                "Encoding": row[2],
                "Collate": row[3],
                "Ctype": row[4],
                "Template": row[5],
                "Allow Connections": row[6]
            }
            return details
        else:
            return {}
    except Exception as e:
        print("Error fetching details:", e)
        return {}
    finally:
        conn.close()
