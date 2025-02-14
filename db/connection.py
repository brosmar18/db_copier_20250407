import psycopg2

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
