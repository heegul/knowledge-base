import sqlite3
import json
import os
import shutil

# Define the database path
DB_PATH = 'knowledge_base.db'
BACKUP_DB_PATH = 'backup_knowledge_base.db'


def create_connection(db_path):
    return sqlite3.connect(db_path)


def create_tables(conn):
    cursor = conn.cursor()
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
            content TEXT,
            url TEXT,
            date DATE,
            topic TEXT,
            keywords TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PDFs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT,
            topic TEXT,
            keywords TEXT,
            date DATE
        )
    ''')
    conn.commit()

def backup_data():
    conn = create_connection(DB_PATH)
    backup_conn = create_connection(BACKUP_DB_PATH)
    cursor = conn.cursor()
    backup_cursor = backup_conn.cursor()

    # Create backup tables if not exist
    create_tables(backup_conn)

    # Backup Articles
    cursor.execute('SELECT title, content, url, date, topic, keywords FROM Articles')
    articles = cursor.fetchall()
    backup_cursor.executemany('INSERT INTO Articles (title, content, url, date, topic, keywords) VALUES (?, ?, ?, ?, ?, ?)', articles)

    # Backup Videos
    cursor.execute('SELECT title, description, url, date, topic, keywords FROM Videos')
    videos = cursor.fetchall()
    backup_cursor.executemany('INSERT INTO Videos (title, description, url, date, topic, keywords) VALUES (?, ?, ?, ?, ?, ?, ?)', videos)

    # Backup PDFs
    cursor.execute('SELECT filename, summary, path, topic, keywords, date FROM PDFs')
    pdfs = cursor.fetchall()
    backup_cursor.executemany('INSERT INTO PDFs (filename, summary, path, topic, keywords, date) VALUES (?, ?, ?, ?, ?, ?)', pdfs)

    backup_conn.commit()
    conn.close()
    backup_conn.close()
    print('Data backed up successfully.')


def refresh_database():
    conn = create_connection(DB_PATH)
    cursor = conn.cursor()

    # Drop existing tables
    cursor.execute('DROP TABLE IF EXISTS Articles')
    cursor.execute('DROP TABLE IF EXISTS Videos')
    cursor.execute('DROP TABLE IF EXISTS PDFs')

    # Recreate tables with new schema
    create_tables(conn)
    conn.close()
    print('Database schema updated.')

def restore_data():
    conn = create_connection(DB_PATH)
    backup_conn = create_connection(BACKUP_DB_PATH)
    cursor = conn.cursor()
    backup_cursor = backup_conn.cursor()

    # Restore Articles
    backup_cursor.execute('SELECT title, content, url, date, topic, keywords FROM Articles')
    articles = backup_cursor.fetchall()
    cursor.executemany('INSERT INTO Articles (title, content, url, date, topic, keywords) VALUES (?, ?, ?, ?, ?, ?)', articles)

    # Restore Videos
    backup_cursor.execute('SELECT title, content, url, video_id, date, topic, keywords FROM Videos')
    videos = backup_cursor.fetchall()
    cursor.executemany('INSERT INTO Videos (title, content, url, video_id, date, topic, keywords) VALUES (?, ?, ?, ?, ?, ?, ?)', videos)

    # Restore PDFs
    backup_cursor.execute('SELECT title, content, url, topic, keywords, date FROM PDFs')
    pdfs = backup_cursor.fetchall()
    cursor.executemany('INSERT INTO PDFs (title, content, url, topic, keywords, date) VALUES (?, ?, ?, ?, ?, ?)', pdfs)

    conn.commit()
    conn.close()
    backup_conn.close()
    print('Data restored successfully.')


def update_json_files():
    conn = create_connection(DB_PATH)
    cursor = conn.cursor()

    # Update articles.json
    cursor.execute('SELECT id, title, content, url, date, topic, keywords FROM Articles')
    articles = cursor.fetchall()
    with open('static/articles.json', 'w') as f:
        json.dump([{
            'id': article[0],
            'title': article[1],
            'content': article[2],
            'url': article[3],
            'date': article[4],
            'topic': article[5],
            'keywords': article[6]
        } for article in articles], f, indent=4)

    # Update videos.json
    cursor.execute('SELECT id, title, content, url, date, topic, keywords FROM Videos')
    videos = cursor.fetchall()
    with open('static/videos.json', 'w') as f:
        json.dump([{
            'id': video[0],
            'title': video[1],
            'description': video[2],
            'url': video[3],
            'date': video[4],
            'topic': video[5],
            'keywords': video[6]
        } for video in videos], f, indent=4)

    # Update pdfs.json
    cursor.execute('SELECT id, title, content, url, topic, keywords, date FROM PDFs')
    pdfs = cursor.fetchall()
    with open('static/pdfs.json', 'w') as f:
        json.dump([{
            'id': pdf[0],
            'title': pdf[1],
            'content': pdf[2],
            'url': pdf[3],
            'date': pdf[6],
            'topic': pdf[4],
            'keywords': pdf[5]
        } for pdf in pdfs], f, indent=4)

    conn.close()
    print('JSON files updated.')


def main():
    # Create a backup of the current data
    backup_data()

    # Refresh the database schema
    refresh_database()

    # Restore the data to the new schema
    restore_data()

    # Update JSON files
    update_json_files()
    print('Database and JSON files are successfully updated.')


if __name__ == '__main__':
    main()
