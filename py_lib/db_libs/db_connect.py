## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import sqlalchemy
import import_helper as ih
import logging
import time
import random
from sqlalchemy.exc import SQLAlchemyError

# Retrieve database connection info from environment variables
db_info = ih.get_env_val("DB_INFO")
conn_str = "{}://{}:{}@{}:{}/{}".format(
  db_info["dbms_name"],
  db_info["username"], db_info["password"],
  db_info["host"], db_info["port"], db_info["name"]
)
max_time_conn = db_info["max_time_connection"]

# Initialize SQLAlchemy engine
engine = sqlalchemy.create_engine(conn_str)

class DBConnection:
    """
    A class to manage individual database connections, execute SQL statements, 
    and handle connection timeouts.
    """
  
    def __init__(self):  
        """
        Initializes a database connection and starts a timer for connection age.
        """
        self.start_time = time.time()
        self.connection = engine.connect()
        self.isOn = False

    def execute(self, stmt, listOfDict=None):
        """
        Executes a given SQL statement on the current connection.

        Args:
            stmt: The SQL statement to execute.
            listOfDict: Optional list of dictionary parameters for the SQL statement.

        Returns:
            The result of the executed statement.

        Raises:
            SQLAlchemyError: If an error occurs during SQL execution.
        """
        self.isOn = True

        try:
            if listOfDict is None:
                rp = self.connection.execute(stmt)
            else:
                rp = self.connection.execute(stmt, listOfDict)

            self.connection.commit()  # Commit transaction after execution
        except SQLAlchemyError as e:
            print(f"Error executing statement: {e}")
            self.connection.rollback()  # Rollback transaction on error
            raise
        finally:
            self.isOn = False

        return rp

    def isBusy(self):
        """
        Check if the connection is currently executing a statement.

        Returns:
            bool: True if the connection is busy, False otherwise.
        """
        return self.isOn

    def age(self):
        """
        Calculate the age of the connection since its creation.

        Returns:
            float: The age of the connection in seconds.
        """
        return time.time() - self.start_time

    def terminate(self):
        """
        Terminates the connection by closing it.
        """
        self.connection.close()

conn_info = {"connections": []}
# Setup basic logging
logging.basicConfig(level=logging.INFO)

def del_old_connections():
    """
    Removes any connections from the pool that have exceeded the maximum allowed age.
    """
    young_connections = []
    for conn in conn_info["connections"]:
        if conn.age() > max_time_conn:
            logging.info(f"Terminating old connection, age: {conn.age()}s")
            conn.terminate()
        else:
            young_connections.append(conn)
    conn_info["connections"] = young_connections


connection_index = 0  # Used for round-robin connection selection
def run_stmt(stmt):
    """
    Executes an SQL statement using one of the available database connections.

    If no available connections exist, a new one is created.

    Args:
        stmt: The SQL statement to execute.

    Returns:
        The result of the SQL execution.
    """
    del_old_connections()

    rp = None

    # If no connections are available, create a new one
    if len(conn_info["connections"]) == 0:
        conn = DBConnection()
        try:
            logging.info("No existing connections, creating a new connection.")
            rp = conn.execute(stmt)
        except SQLAlchemyError as e:
            logging.error(f"SQL execution failed: {e}")
            conn.terminate()
        else:
            conn_info["connections"].append(conn)
    else:
        global connection_index
        # Use round-robin to pick a connection
        conn = conn_info["connections"][connection_index % len(conn_info["connections"])]
        connection_index += 1

        try:
            logging.info(f"Using existing connection (index {connection_index % len(conn_info['connections'])}).")
            rp = conn.execute(stmt)
        except SQLAlchemyError as e:
            logging.error(f"SQL execution failed: {e}")
            conn.terminate()
            # Remove terminated connection from pool
            conn_info["connections"].remove(conn)
        else:
            # If successful, keep connection in the pool
            conn_info["connections"].append(conn)

    return rp

## EOF
