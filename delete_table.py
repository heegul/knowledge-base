import sqlite3

def delete_table(table_name):
    conn = sqlite3.connect('knowledge_base.db')
    cursor = conn.cursor()
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        print(f"Table '{table_name}' deleted successfully.")
    except sqlite3.Error as e:
        print(f"Error deleting table '{table_name}': {e}")
    finally:
        conn.close()

# Example usage:
delete_table('PDFs')  # Replace 'PDFs' with the name of the table you want to delete
