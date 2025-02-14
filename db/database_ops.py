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
