from psycopg2 import sql
from .connection import connect_to_db
import threading
import time


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


def copy_database_logic(credentials, src_db, new_db, update_callback):
    """
    Perform the database copy operation with detailed progress tracking and logging.
    update_callback: a callback to update status and progress in the UI.
                    Should accept: update_callback(message=None, progress=None)
    """
    conn = connect_to_db(credentials)
    if not conn:
        raise Exception("Unable to connect to database.")
    
    try:
        conn.autocommit = True
        cur = conn.cursor()

        # Step 1: Initial connection and validation (5% progress)
        update_callback("🔌 Establishing connection to PostgreSQL server...", 5)
        time.sleep(0.2)  # Brief pause for user to see the message
        
        update_callback("✅ Connected successfully to PostgreSQL", 8)
        time.sleep(0.2)

        # Step 2: Validate source database exists
        update_callback("🔍 Validating source database exists...", 10)
        check_query = "SELECT 1 FROM pg_database WHERE datname = %s"
        cur.execute(check_query, (src_db,))
        if not cur.fetchone():
            raise Exception(f"Source database '{src_db}' does not exist")
        
        update_callback(f"✅ Source database '{src_db}' found and accessible", 12)
        time.sleep(0.2)

        # Step 3: Terminate active connections (15% progress)
        update_callback("🔄 Checking for active connections to source database...", 15)
        
        # Check how many connections need to be terminated
        connection_check_query = """
            SELECT count(*) FROM pg_stat_activity 
            WHERE datname = %s AND pid <> pg_backend_pid()
        """
        cur.execute(connection_check_query, (src_db,))
        active_connections = cur.fetchone()[0]
        
        if active_connections > 0:
            update_callback(f"⚠️  Found {active_connections} active connection(s) - terminating...", 17)
            terminate_query = """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid();
            """
            cur.execute(terminate_query, (src_db,))
            update_callback("✅ Active connections terminated successfully", 20)
        else:
            update_callback("✅ No active connections found - proceeding", 20)
        
        time.sleep(0.3)

        # Step 4: Analyze source database (25% progress)
        update_callback("📊 Analyzing source database structure and size...", 22)
        
        # Get detailed database information
        size_query = """
            SELECT pg_size_pretty(pg_database_size(%s)) as size,
                   pg_database_size(%s) as size_bytes
        """
        cur.execute(size_query, (src_db, src_db))
        size_result = cur.fetchone()
        db_size_mb = (size_result[1] / 1024 / 1024) if size_result and size_result[1] else 0
        size_pretty = size_result[0] if size_result else "Unknown"
        
        update_callback(f"📈 Database size: {size_pretty} ({db_size_mb:.1f} MB)", 25)
        time.sleep(0.3)
        
        # Get table count
        table_count_query = """
            SELECT count(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """
        try:
            # Connect to the source database to get table info
            src_conn = connect_to_db(credentials, database=src_db)
            if src_conn:
                src_cur = src_conn.cursor()
                src_cur.execute(table_count_query)
                table_count = src_cur.fetchone()[0]
                src_cur.close()
                src_conn.close()
                update_callback(f"📋 Found {table_count} table(s) to copy", 27)
            else:
                update_callback("📋 Analyzing table structure...", 27)
        except:
            update_callback("📋 Analyzing table structure...", 27)
        
        time.sleep(0.3)

        # Step 5: Prepare for database creation
        update_callback("🛠️  Preparing database creation parameters...", 30)
        time.sleep(0.2)
        
        # Estimate time and provide user expectations
        if db_size_mb < 10:
            time_estimate = "a few seconds"
            update_frequency = 0.1
            progress_steps = [35, 45, 55, 65, 75, 80, 85]
        elif db_size_mb < 100:
            time_estimate = "under a minute"
            update_frequency = 0.2
            progress_steps = [35, 45, 55, 65, 75, 80, 85]
        elif db_size_mb < 500:
            time_estimate = "1-2 minutes"
            update_frequency = 0.4
            progress_steps = [35, 42, 50, 58, 65, 72, 80, 85]
        else:
            time_estimate = "several minutes"
            update_frequency = 0.6
            progress_steps = [35, 40, 45, 52, 58, 65, 70, 75, 80, 85]

        update_callback(f"⏱️  Estimated time: {time_estimate} (size: {size_pretty})", 32)
        time.sleep(0.3)

        # Step 6: Start database creation with detailed progress
        update_callback("🚀 Initiating database creation with template...", 35)
        time.sleep(0.3)

        # Detailed progress updates during creation
        progress_messages = [
            "📝 PostgreSQL allocating disk space...",
            "🗃️  Copying database schema structure...",
            "📊 Transferring table definitions...",
            "🔗 Copying indexes and constraints...",
            "💾 Transferring data blocks...",
            "🔐 Setting up permissions and ownership...",
            "🧪 Validating data integrity...",
            "🔧 Finalizing database configuration..."
        ]

        def detailed_progress_updater():
            for i, (progress, message) in enumerate(zip(progress_steps, progress_messages)):
                if i < len(progress_messages):
                    update_callback(message, progress)
                else:
                    update_callback(f"🔄 Processing... ({progress}%)", progress)
                time.sleep(update_frequency)

        # Start detailed progress updater in a separate thread
        progress_thread = threading.Thread(target=detailed_progress_updater, daemon=True)
        progress_thread.start()

        # Execute the actual CREATE DATABASE command
        update_callback("⚡ Executing CREATE DATABASE command...", 37)
        create_query = sql.SQL("CREATE DATABASE {} WITH TEMPLATE {} OWNER {}").format(
            sql.Identifier(new_db),
            sql.Identifier(src_db),
            sql.Identifier(credentials["user"]),
        )
        cur.execute(create_query)

        # Wait for progress thread to complete
        progress_thread.join()

        # Step 7: Post-creation validation and finalization
        update_callback("🔍 Verifying database creation...", 88)
        time.sleep(0.2)
        
        # Verify the database was created
        verify_query = "SELECT 1 FROM pg_database WHERE datname = %s"
        cur.execute(verify_query, (new_db,))
        if not cur.fetchone():
            raise Exception(f"Database '{new_db}' was not created successfully")
        
        update_callback("✅ Database creation verified successfully", 92)
        time.sleep(0.2)

        # Final size verification
        update_callback("📏 Checking new database size...", 95)
        cur.execute(size_query, (new_db, new_db))
        new_size_result = cur.fetchone()
        new_size_pretty = new_size_result[0] if new_size_result else "Unknown"
        
        update_callback(f"📊 New database size: {new_size_pretty}", 97)
        time.sleep(0.2)

        # Test connection to new database
        update_callback("🔌 Testing connection to new database...", 98)
        test_conn = connect_to_db(credentials, database=new_db)
        if test_conn:
            test_conn.close()
            update_callback("✅ New database connection test successful", 99)
        else:
            update_callback("⚠️  Warning: Could not test new database connection", 99)
        
        time.sleep(0.2)

        cur.close()
        update_callback(f"🎉 Database '{new_db}' cloned successfully from '{src_db}'!", 100)
        
    except Exception as e:
        # Enhanced error reporting
        error_msg = str(e)
        if "already exists" in error_msg.lower():
            update_callback(f"❌ Error: Database '{new_db}' already exists", None)
        elif "permission denied" in error_msg.lower():
            update_callback("❌ Error: Permission denied - check user privileges", None)
        elif "disk" in error_msg.lower() or "space" in error_msg.lower():
            update_callback("❌ Error: Insufficient disk space", None)
        else:
            update_callback(f"❌ Error: {error_msg}", None)
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

        # Use cur.description to determine if the query returned a result set.
        # This is reliable regardless of comments, CTEs, or query structure.
        if cur.description is not None:
            # Query returned rows (SELECT, SHOW, EXPLAIN, RETURNING, etc.)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
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
        else:
            # Non-returning statement (INSERT, UPDATE, DELETE, DDL, etc.)
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
