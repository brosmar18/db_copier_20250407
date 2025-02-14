# db/restore_ops.py
import subprocess
import os
import shutil
from .connection import connect_to_db

def create_database(credentials, db_name):
    """
    Create a new database using the provided credentials.
    """
    conn = connect_to_db(credentials)
    if not conn:
        raise Exception("Unable to connect to database.")
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE {db_name};")
        cur.close()
    except Exception as e:
        raise Exception(f"Error creating database: {e}")
    finally:
        conn.close()

def restore_database(credentials, db_name, backup_file):
    """
    Restore the specified database from a local .backup file using pg_restore.
    """
    if not os.path.exists(backup_file):
        raise Exception("Backup file does not exist.")
    
    # Try to locate pg_restore in the system PATH.
    pg_restore_exe = shutil.which("pg_restore")
    
    # If not found, check for the PG_RESTORE_PATH environment variable.
    if pg_restore_exe is None:
        # Fallback: try to get from environment variable or default to our known path.
        pg_restore_exe = os.environ.get("PG_RESTORE_PATH", r"C:\Program Files\PostgreSQL\12\bin\pg_restore.exe")
        if not os.path.exists(pg_restore_exe):
            raise Exception(
                "pg_restore executable not found in system PATH. "
                "Please ensure PostgreSQL's bin folder is in your PATH, "
                "or set the PG_RESTORE_PATH environment variable to the full path of pg_restore."
            )
    
    # Debug print (optional)
    # print("Using pg_restore executable at:", pg_restore_exe)
    
    # Construct the pg_restore command.
    cmd = [
        pg_restore_exe,
        "-U", credentials["user"],
        "-d", db_name,
        backup_file
    ]
    
    # Pass the password via the environment.
    env = os.environ.copy()
    env["PGPASSWORD"] = credentials["password"]
    
    try:
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Restore failed: {e}")
