import sqlite3


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = sqlite3.connect(db_file)
    return conn


def print_table_content(conn, table_name):
    """
    Print all rows in the specified table
    :param conn: the Connection object
    :param table_name: the table name
    """
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")

        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]

        print(f"Contents of table {table_name}:")

        # Print column names
        print(" | ".join(column_names))

        # Print rows
        for row in rows:
            print(" | ".join(str(value) for value in row))

    except sqlite3.OperationalError as e:
        print(f"An error occurred: {e}")


def main():
    database = "knowledge_base.db"

    # Create a database connection
    conn = create_connection(database)

    if conn is not None:
        table_name = input("Enter the table name to print its contents: ")
        print_table_content(conn, table_name)
        conn.close()
    else:
        print("Error! Cannot create the database connection.")


if __name__ == "__main__":
    main()
