import sqlite3
import json

def create_connection(db_file='knowledge_base.db'):
    conn = sqlite3.connect(db_file)
    return conn

def create_tables():
    conn = create_connection()
    try:
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
                date DATE,
                topic TEXT,
                keywords TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()

def update_json_files():
    conn = create_connection()
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
            'content': video[2],
            'url': video[3],
            'date': video[4],
            'topic': video[5],
            'keywords': video[6]
        } for video in videos], f, indent=4)

    # Update pdfs.json
    cursor.execute('SELECT title, content, url, date, topic, keywords FROM PDFs')
    pdfs = cursor.fetchall()
    with open('static/pdfs.json', 'w') as f:
        json.dump([{
            'title': pdf[0],
            'content': pdf[1],
            'url': pdf[2],
            'date': pdf[3] if pdf[3] else 'N/A',  # Default to 'N/A' if date is empty
            'topic': pdf[4] if pdf[4] else 'Unspecified',  # Default to 'Unspecified' if topic is empty
            'keywords': pdf[5] if pdf[5] else 'None'  # Default to 'None' if keywords are empty
        } for pdf in pdfs], f, indent=4)

    conn.close()
