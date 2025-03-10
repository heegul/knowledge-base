import sqlite3

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

def check_articles(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Articles')
    articles = cursor.fetchall()
    print("All articles:")
    for article in articles:
        print(article)

def check_videos(conn, topic):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Videos WHERE topic = ?', (topic,))
    videos = cursor.fetchall()
    print(f"Videos with topic '{topic}':")
    for video in videos:
        print(video)

def check_pdfs(conn, keyword):
    cursor = conn.cursor()
    #cursor.execute('SELECT * FROM PDFs WHERE keywords LIKE ?', ('%' + keyword + '%',))
    cursor.execute('SELECT * FROM PDFs')
    pdfs = cursor.fetchall()
    print(f"PDFs with keyword '{keyword}':")
    for pdf in pdfs:
        print(pdf)

import sqlite3

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

def insert_sample_data(conn):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Articles (title, content, url, date, topic, keywords)
        VALUES ('Sample Article', 'This is a sample article.', 'http://example.com', '2024-06-16', 'Technology', 'sample, article')
    ''')
    cursor.execute('''
        INSERT INTO Videos (title, content, url, date, topic, keywords)
        VALUES ('Sample Video', 'This is a sample video description.', 'http://youtube.com', '12345', '2024-06-16', 'AI', 'sample, video')
    ''')
    cursor.execute('''
        INSERT INTO PDFs (title, content, url, date, topic, keywords)
        VALUES ('Sample PDF', 'This is a sample PDF summary.', 'uploads/sample.pdf', '2024-06-16', 'Education', 'sample, pdf')
    ''')
    cursor.execute('''
        INSERT INTO PDFs (title, content, url, date, topic, keywords)
        VALUES ('Study PDF', 'This is a sample study PDF summary.', 'uploads/study.pdf', '2024-06-16', 'Study', 'sample, study')
    ''')
    conn.commit()



def main():
    database = 'knowledge_base.db'
    conn = create_connection(database)
    # if conn:
    #     insert_sample_data(conn)
    #     print("Sample data inserted.")
    #     conn.close()
    # else:
    #     print("Error! Cannot create the database connection.")
    
    # conn = create_connection(database)
    if conn:
    #    check_articles(conn)
    #    check_videos(conn, 'AI')
        check_pdfs(conn, 'paper')
        conn.close()
    else:
        print("Error! Cannot create the database connection.")

if __name__ == '__main__':
    main()
