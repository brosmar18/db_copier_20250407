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
    Perform the database copy operation with enhanced progress tracking.
    update_status_callback: a callback that accepts (message, progress_percent)
    """
    conn = connect_to_db(credentials)
    if not conn:
        raise Exception("Unable to connect to database.")
    
    try:
        # Step 1: Initial setup and validation (0-10%)
        update_status_callback("Initializing copy operation...", 5)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Get source database size for progress estimation
        update_status_callback("Analyzing source database...", 10)
        db_size_mb = get_database_size_mb(credentials, src_db)
        
        # Step 2: Validate source database exists (10-15%)
        update_status_callback("Validating source database...", 12)
        check_query = "SELECT 1 FROM pg_database WHERE datname = %s"
        cur.execute(check_query, (src_db,))
        if not cur.fetchone():
            raise Exception(f"Source database '{src_db}' does not exist")
        
        # Step 3: Check if target database already exists (15-20%)
        update_status_callback("Checking target database name...", 15)
        cur.execute(check_query, (new_db,))
        if cur.fetchone():
            raise Exception(f"Database '{new_db}' already exists")
        
        # Step 4: Terminate active connections (20-30%)
        update_status_callback("Terminating active connections...", 25)
        terminate_query = """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid();
        """
        cur.execute(terminate_query, (src_db,))
        
        # Step 5: Create new database - this is the longest step (30-90%)
        update_status_callback("Creating database copy...", 30)
        
        # Provide progress updates during the copy based on estimated time
        import threading
        import time
        
        # Estimate copy time based on database size (rough heuristic)
        estimated_seconds = max(5, db_size_mb / 50)  # ~50MB per second estimate
        progress_thread = None
        stop_progress = threading.Event()
        
        def progress_updater():
            """Update progress during the long copy operation"""
            start_progress = 30
            end_progress = 90
            start_time = time.time()
            
            while not stop_progress.is_set():
                elapsed = time.time() - start_time
                progress = min(elapsed / estimated_seconds, 1.0)
                current_progress = start_progress + (progress * (end_progress - start_progress))
                
                if db_size_mb > 0:
                    size_info = f" ({db_size_mb}MB)"
                else:
                    size_info = ""
                
                update_status_callback(f"Copying database data{size_info}...", int(current_progress))
                
                if stop_progress.wait(2):  # Update every 2 seconds
                    break
        
        # Start progress updates for large databases
        if estimated_seconds > 5:
            progress_thread = threading.Thread(target=progress_updater, daemon=True)
            progress_thread.start()
        
        try:
            # Execute the actual copy command
            create_query = sql.SQL("CREATE DATABASE {} WITH TEMPLATE {} OWNER {}").format(
                sql.Identifier(new_db),
                sql.Identifier(src_db),
                sql.Identifier(credentials["user"]),
            )
            cur.execute(create_query)
            
        finally:
            # Stop progress updates
            if progress_thread:
                stop_progress.set()
                progress_thread.join(timeout=1)
        
        # Step 6: Finalization (90-100%)
        update_status_callback("Finalizing database copy...", 95)
        
        # Verify the new database was created
        cur.execute(check_query, (new_db,))
        if not cur.fetchone():
            raise Exception("Database copy completed but verification failed")
        
        cur.close()
        update_status_callback("Database copy completed successfully.", 100)
        
    except Exception as e:
        # Stop any running progress updates
        if 'stop_progress' in locals():
            stop_progress.set()
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
    Includes safety protection for critical system databases.
    """
    # Safety check - prevent deletion of critical system databases
    protected_databases = ["postgres", "template0", "template1"]
    if db_name.lower() in [db.lower() for db in protected_databases]:
        raise Exception(
            f"Cannot delete system database '{db_name}'. This database is protected for system stability."
        )

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
    Includes safety protection for critical system databases.

    Parameters:
      - credentials: Database connection credentials
      - old_name: Current database name
      - new_name: New database name
      - update_status_callback: Callback function to update UI status
    """
    # Safety check - prevent renaming of critical system databases
    protected_databases = ["postgres", "template0", "template1"]
    if old_name.lower() in [db.lower() for db in protected_databases]:
        raise Exception(
            f"Cannot rename system database '{old_name}'. This database is protected for system stability."
        )

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

    # Check if new name would conflict with protected databases
    if new_name.lower() in [db.lower() for db in protected_databases]:
        raise Exception(
            f"Cannot use '{new_name}' as it conflicts with a protected system database name."
        )

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


def execute_sql_query(credentials, db_name, sql_query):
    """
    Execute a SQL query on the specified database and return results.

    Parameters:
      - credentials: Database connection credentials
      - db_name: Target database name
      - sql_query: SQL query to execute

    Returns:
      - Dictionary with query results, column names, row count, and execution time
    """
    import time

    if not sql_query or not sql_query.strip():
        raise Exception("SQL query cannot be empty")

    # Connect to the target database
    conn = connect_to_db(credentials, database=db_name)
    if not conn:
        raise Exception(f"Unable to connect to database '{db_name}'")

    start_time = time.time()

    try:
        cur = conn.cursor()

        # Execute the query
        cur.execute(sql_query.strip())

        execution_time = round(
            (time.time() - start_time) * 1000, 2
        )  # Convert to milliseconds

        # Determine query type and handle results accordingly
        query_type = sql_query.strip().upper().split()[0] if sql_query.strip() else ""

        if query_type in ["SELECT", "WITH", "SHOW", "EXPLAIN", "ANALYZE"]:
            # Fetch results for SELECT-type queries
            try:
                rows = cur.fetchall()
                columns = (
                    [desc[0] for desc in cur.description] if cur.description else []
                )
                row_count = len(rows)

                result = {
                    "success": True,
                    "query_type": "SELECT",
                    "columns": columns,
                    "rows": rows,
                    "row_count": row_count,
                    "execution_time_ms": execution_time,
                    "message": f"Query executed successfully. {row_count} rows returned.",
                }
            except Exception:
                # Handle cases where query doesn't return results
                result = {
                    "success": True,
                    "query_type": "SELECT",
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "execution_time_ms": execution_time,
                    "message": "Query executed successfully. No results returned.",
                }
        else:
            # Handle modification queries (INSERT, UPDATE, DELETE, etc.)
            try:
                affected_rows = cur.rowcount
                conn.commit()

                result = {
                    "success": True,
                    "query_type": "MODIFICATION",
                    "columns": [],
                    "rows": [],
                    "row_count": affected_rows if affected_rows >= 0 else 0,
                    "execution_time_ms": execution_time,
                    "message": f"Query executed successfully. {affected_rows if affected_rows >= 0 else 0} rows affected.",
                }
            except Exception:
                conn.rollback()
                raise

        cur.close()
        return result

    except Exception as e:
        execution_time = round((time.time() - start_time) * 1000, 2)

        result = {
            "success": False,
            "query_type": "ERROR",
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time_ms": execution_time,
            "message": f"Query failed: {str(e)}",
        }
        return result

    finally:
        conn.close()

def get_database_size_mb(credentials, db_name):
    """
    Get the size of a database in MB for progress estimation.
    Returns the size in MB, or 0 if unable to determine.
    """
    conn = connect_to_db(credentials)
    if not conn:
        return 0
    try:
        cur = conn.cursor()
        query = """
            SELECT pg_size_pretty(pg_database_size(%s)) as size_pretty,
                   pg_database_size(%s) / (1024*1024) as size_mb
        """
        cur.execute(query, (db_name, db_name))
        row = cur.fetchone()
        cur.close()
        return int(row[1]) if row else 0
    except Exception as e:
        print(f"Error getting database size: {e}")
        return 0
    finally:
        conn.close()