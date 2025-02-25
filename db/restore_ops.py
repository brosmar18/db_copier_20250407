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

def restore_database(credentials, db_name, backup_file, pg_restore_dir=None):
    """
    Restore the specified database from a local .backup file using pg_restore.
    
    Parameters:
      - credentials: Database connection credentials.
      - db_name: Name of the database to restore.
      - backup_file: Path to the backup file.
      - pg_restore_dir: Optional; user-specified directory containing pg_restore.exe.
                        If provided, the directory will be appended with 'pg_restore.exe'.
                        Otherwise, the function will try system PATH, environment variable,
                        or fall back to the default full path.
    """
    if not os.path.exists(backup_file):
        raise Exception("Backup file does not exist.")
    
    if pg_restore_dir and pg_restore_dir.strip() != "":
        # Append 'pg_restore.exe' to the user-provided directory.
        pg_restore_exe = os.path.join(pg_restore_dir, "pg_restore.exe")
        if not os.path.exists(pg_restore_exe):
            raise Exception(f"Provided pg_restore directory does not contain pg_restore.exe: {pg_restore_exe}")
    else:
        # Try to locate pg_restore in the system PATH.
        pg_restore_exe = shutil.which("pg_restore")
        if pg_restore_exe is None:
            # Fallback: try to get from environment variable or default to our known full path.
            pg_restore_exe = os.environ.get("PG_RESTORE_PATH", r"C:\Program Files\PostgreSQL\12\bin\pg_restore.exe")
            if not os.path.exists(pg_restore_exe):
                raise Exception(
                    "pg_restore executable not found in system PATH. "
                    "Please ensure PostgreSQL's bin folder is in your PATH, "
                    "or set the PG_RESTORE_PATH environment variable to the full path of pg_restore."
                )
    
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
