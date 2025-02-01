import sqlite3


def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn


def recreate_tables(conn):
    try:
        cursor = conn.cursor()

        # Drop the existing tables if they exist
        cursor.execute('DROP TABLE IF EXISTS Articles')
        cursor.execute('DROP TABLE IF EXISTS Videos')

        # Create the tables again with the correct schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                url TEXT,
                date DATE,
                topic TEXT,
                keywords TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT,
                video_id TEXT,
                date DATE,
                topic TEXT,
                keywords TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        print(e)


def main():
    database = "knowledge_base.db"
    conn = create_connection(database)
    recreate_tables(conn)
    conn.close()


if __name__ == "__main__":
    main()
