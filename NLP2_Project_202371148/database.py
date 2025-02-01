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
                description TEXT,
                url TEXT,
                video_id TEXT,
                date DATE,
                topic TEXT,
                keywords TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS PDFs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                summary TEXT,
                path TEXT,
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
    cursor.execute('SELECT title, content, url, date, topic, keywords FROM Articles')
    articles = cursor.fetchall()
    with open('static/articles.json', 'w') as f:
        json.dump([{
            'title': article[0],
            'content': article[1],
            'url': article[2],
            'date': article[3],
            'topic': article[4],
            'keywords': article[5]
        } for article in articles], f, indent=4)

    # Update videos.json
    cursor.execute('SELECT title, description, url, date, topic, keywords FROM Videos')
    videos = cursor.fetchall()
    with open('static/videos.json', 'w') as f:
        json.dump([{
            'title': video[0],
            'description': video[1],
            'url': video[2],
            'date': video[3],
            'topic': video[4],
            'keywords': video[5]
        } for video in videos], f, indent=4)

    # Update pdfs.json
    cursor.execute('SELECT filename, summary, path, date, topic, keywords FROM PDFs')
    pdfs = cursor.fetchall()
    with open('static/pdfs.json', 'w') as f:
        json.dump([{
            'title': pdf[0],
            'content': pdf[1],
            'url': pdf[2],
            'date': pdf[3],  # PDFs do not have a date
            'topic': pdf[4],
            'keywords': pdf[5]
        } for pdf in pdfs], f, indent=4)

    conn.close()

