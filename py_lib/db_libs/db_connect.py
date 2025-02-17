## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import sqlalchemy
import import_helper as ih
import time

# Retrieve database connection info from environment variables
db_info = ih.get_env_val("DB_INFO")
conn_str = "{}://{}:{}@{}:{}/{}".format(
    db_info["dbms_name"],
    db_info["username"], db_info["password"],
    db_info["host"], db_info["port"], db_info["name"]
)
max_time_conn = db_info["max_time_connection"]

# Initialize SQLAlchemy engine with connection pooling
engine = sqlalchemy.create_engine(
    conn_str,
    pool_size=10,          # Number of connections to maintain in the pool
    max_overflow=5,        # Allow up to 5 additional connections beyond pool_size
    pool_timeout=30,       # Seconds to wait for a connection to become available
    pool_recycle=1800      # Recycle connections every 1800 seconds (30 minutes)
)

class DBConnection:
    """
    A class to manage database interactions using pooled connections.
    """

    def __init__(self):
        """
        Initializes a database connection and starts a timer for connection age.
        """
        self.start_time = time.time()
        self.connection = engine.connect()  # Uses a pooled connection

    def execute(self, stmt, listOfDict=None):
        """
        Executes a given SQL statement on the current connection.

        Args:
            stmt: The SQL statement to execute.
            listOfDict: Optional list of dictionary parameters for the SQL statement.

        Returns:
            The result of the executed statement.
        """
        try:
            if listOfDict is None:
                rp = self.connection.execute(stmt)
            else:
                rp = self.connection.execute(stmt, listOfDict)

            self.connection.commit()  # Commit transaction after execution
            return rp
        except Exception as e:
            self.connection.rollback()  # Rollback transaction on error
            raise e
        finally:
            self.connection.close()  # Close the connection to return it to the pool

    def age(self):
        """
        Calculate the age of the connection since its creation.

        Returns:
            float: The age of the connection in seconds.
        """
        return time.time() - self.start_time

def run_stmt(stmt):
    """
    Executes an SQL statement using a pooled database connection.

    Args:
        stmt: The SQL statement to execute.

    Returns:
        The result of the SQL execution.
    """
    conn = DBConnection()
    return conn.execute(stmt)

## EOF
