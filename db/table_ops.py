from .connection import connect_to_db

def get_tables_for_database(credentials, db_name):
    """
    Fetch the list of tables in the public schema of the specified database.
    Returns a list of table names.
    """
    conn = connect_to_db(credentials, database=db_name)
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        return tables
    except Exception as e:
        print("Error fetching tables:", e)
        return []
    finally:
        conn.close()

def get_columns_for_table(credentials, db_name, table_name):
    """
    Fetch the list of columns for a given table in the public schema.
    Returns a list of column names sorted alphabetically.
    """
    conn = connect_to_db(credentials, database=db_name)
    if not conn:
        return []
    try:
        cur = conn.cursor()
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY column_name;
        """
        cur.execute(query, (table_name,))
        columns = [row[0] for row in cur.fetchall()]
        cur.close()
        return columns
    except Exception as e:
        print("Error fetching columns:", e)
        return []
    finally:
        conn.close()

def get_table_details(credentials, db_name, table_name):
    """
    Fetch details about a specific table from the public schema.
    Returns a dictionary with:
      - Table Name
      - Record Count (an estimated number of records)
    """
    conn = connect_to_db(credentials, database=db_name)
    if not conn:
        return {}
    try:
        cur = conn.cursor()
        query = """
            SELECT c.relname AS table_name,
                   c.reltuples::bigint AS estimated_rows
            FROM pg_class c
            WHERE c.relname = %s AND c.relkind = 'r';
        """
        cur.execute(query, (table_name,))
        row = cur.fetchone()
        if row:
            details = {
                "Table Name": row[0],
                "Record Count": row[1]
            }
            return details
        else:
            return {}
    except Exception as e:
        print("Error fetching table details:", e)
        return {}
    finally:
        conn.close()
