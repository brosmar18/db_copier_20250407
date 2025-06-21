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
            # Fallback: try to get from environment variable or default to PostgreSQL 15
            pg_restore_exe = os.environ.get("PG_RESTORE_PATH", r"C:\Program Files\PostgreSQL\15\bin\pg_restore.exe")
            if not os.path.exists(pg_restore_exe):
                # Try other common PostgreSQL versions
                common_paths = [
                    r"C:\Program Files\PostgreSQL\17\bin\pg_restore.exe",
                    r"C:\Program Files\PostgreSQL\16\bin\pg_restore.exe",
                    r"C:\Program Files\PostgreSQL\15\bin\pg_restore.exe",
                    r"C:\Program Files\PostgreSQL\14\bin\pg_restore.exe",
                    r"C:\Program Files\PostgreSQL\13\bin\pg_restore.exe",
                    r"C:\Program Files\PostgreSQL\12\bin\pg_restore.exe",
                ]
                
                pg_restore_exe = None
                for path in common_paths:
                    if os.path.exists(path):
                        pg_restore_exe = path
                        break
                
                if not pg_restore_exe:
                    raise Exception(
                        "pg_restore executable not found. Please:\n\n"
                        "1. Install PostgreSQL 15 or later\n"
                        "2. Add PostgreSQL's bin folder to your system PATH\n"
                        "3. Or specify the correct PostgreSQL Bin Path in the form\n\n"
                        "Common installation paths:\n"
                        "• C:\\Program Files\\PostgreSQL\\15\\bin\n"
                        "• C:\\Program Files\\PostgreSQL\\16\\bin\n"
                        "• C:\\Program Files\\PostgreSQL\\17\\bin"
                    )
    
    # Check pg_restore version compatibility
    try:
        version_result = subprocess.run(
            [pg_restore_exe, "--version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if version_result.returncode == 0:
            version_output = version_result.stdout.strip()
            print(f"Using pg_restore: {version_output}")
    except Exception as e:
        print(f"Warning: Could not check pg_restore version: {e}")
    
    # Construct the pg_restore command.
    cmd = [
        pg_restore_exe,
        "-U", credentials["user"],
        "-h", credentials["host"],
        "-p", str(credentials["port"]),
        "-d", db_name,
        "-v",  # Verbose output for better debugging
        backup_file
    ]
    
    # Pass the password via the environment.
    env = os.environ.copy()
    env["PGPASSWORD"] = credentials["password"]
    
    try:
        # Run with detailed error capture
        result = subprocess.run(
            cmd, 
            check=True, 
            env=env, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Log successful restore
        if result.stderr:
            print(f"pg_restore output: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        raise Exception("Restore operation timed out after 5 minutes. The backup file may be too large or corrupted.")
        
    except subprocess.CalledProcessError as e:
        error_message = e.stderr if e.stderr else str(e)
        
        # Provide specific guidance for common errors
        if "unsupported version" in error_message.lower():
            # Extract version information if possible
            version_info = ""
            if "version" in error_message:
                version_info = f"\n\nError details: {error_message}"
            
            raise Exception(
                "Version Compatibility Issue:\n\n"
                "The backup file was created with a newer version of PostgreSQL than your pg_restore tool. "
                "To fix this:\n\n"
                "1. Install PostgreSQL 15 or later from: https://www.postgresql.org/download/\n"
                "2. Update the 'PostgreSQL Bin Path' field to point to the newer installation\n"
                "   (e.g., C:\\Program Files\\PostgreSQL\\15\\bin)\n"
                "3. Restart the restore process\n\n"
                "Alternative: Export your data as a SQL file (.sql) instead of a custom format (.backup) "
                "for better compatibility between PostgreSQL versions."
                f"{version_info}"
            )
        elif "authentication failed" in error_message.lower():
            raise Exception(
                "Authentication Failed:\n\n"
                "Could not connect to the database with the provided credentials. "
                "Please check:\n"
                "• Username and password are correct\n"
                "• Database server is running\n"
                "• Host and port are correct\n"
                "• User has permission to create/restore databases"
            )
        elif "could not connect" in error_message.lower():
            raise Exception(
                "Connection Failed:\n\n"
                "Could not connect to the PostgreSQL server. Please check:\n"
                "• PostgreSQL server is running\n"
                "• Host and port are correct\n"
                "• Firewall is not blocking the connection\n"
                "• Network connectivity is available"
            )
        elif "database" in error_message.lower() and "does not exist" in error_message.lower():
            raise Exception(
                "Database Not Found:\n\n"
                "The target database was not created properly. This is usually an internal error. "
                "Please try the restore operation again."
            )
        else:
            # Generic error with full details
            raise Exception(
                f"Restore Failed:\n\n"
                f"pg_restore encountered an error:\n\n"
                f"{error_message}\n\n"
                f"Command used: {' '.join(cmd[:-1])} [backup_file]\n\n"
                f"Tips:\n"
                f"• Ensure the backup file is not corrupted\n"
                f"• Check that you have sufficient disk space\n"
                f"• Verify the backup file format is compatible\n"
                f"• Try using PostgreSQL 15+ for better compatibility"
            )