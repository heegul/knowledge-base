import sqlite3
import json

# Function to create a connection to the SQLite database
def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

# Function to create tables
def create_tables(conn):
    try:
        cursor = conn.cursor()
        
        # Create Sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Sources (
                source_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                url TEXT,
                author TEXT,
                publication_date DATE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Videos (
                video_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL,
                publication_date DATE,
                channel_id INTEGER,
                topic_id INTEGER,
                summary TEXT,
                FOREIGN KEY (channel_id) REFERENCES Channels (channel_id),
                FOREIGN KEY (topic_id) REFERENCES Topics (topic_id)
            )
        ''')

        # Create Topics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Topics (
                topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            )
        ''')

        # Create Articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Articles (
                article_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                abstract TEXT,
                content TEXT,
                publication_date DATE,
                source_id INTEGER,
                topic_id INTEGER,
                FOREIGN KEY (source_id) REFERENCES Sources (source_id),
                FOREIGN KEY (topic_id) REFERENCES Topics (topic_id)
            )
        ''')

        # Create Experts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Experts (
                expert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                affiliation TEXT,
                bio TEXT,
                fields TEXT,
                contact_info TEXT
            )
        ''')

        # Create Events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date DATE,
                location TEXT,
                description TEXT,
                url TEXT
            )
        ''')

        # Create Courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                provider TEXT,
                description TEXT,
                url TEXT,
                start_date DATE,
                end_date DATE
            )
        ''')
        
        conn.commit()
    except Exception as e:
        print(e)

# Function to insert sample data
def insert_sample_data(conn):
    cursor = conn.cursor()

    # Insert sample sources
    sources = [
        ("AI Research Journal", "Journal", "https://ai-journal.com", "John Doe", "2024-01-15"),
        ("AI News Daily", "News", "https://ainewsdaily.com", "Jane Smith", "2024-05-10"),
        ("YouTube AI Channel", "YouTube", "https://youtube.com/AIChannel", "Tech Guru", "2024-03-20")
    ]
    cursor.executemany('''
        INSERT INTO Sources (name, type, url, author, publication_date)
        VALUES (?, ?, ?, ?, ?)
    ''', sources)

    # Insert sample topics
    topics = [
        ("Machine Learning", "The study of algorithms that improve automatically through experience."),
        ("Neural Networks", "A subset of machine learning involving algorithms inspired by the structure of the human brain."),
        ("Natural Language Processing", "The field focused on the interaction between computers and humans through natural language."),
        ("Semantic Communications", "The field focused on communications all the way in which one mind may affect another in desired way")
    ]
    cursor.executemany('''
        INSERT INTO Topics (name, description)
        VALUES (?, ?)
    ''', topics)

    # Insert sample articles
    articles = [
        ("Introduction to Machine Learning", "An overview of machine learning techniques.", "Full content of the article goes here.", "2024-01-20", 1, 1),
        ("Advances in Neural Networks", "Latest research in neural networks.", "Full content of the article goes here.", "2024-03-15", 1, 2),
        ("NLP for Beginners", "Introduction to Natural Language Processing.", "Full content of the article goes here.", "2024-02-10", 2, 3),
        ("Semantic communication", "Introduction to Semantic Communications.", "Full content of the article goes here.", "2024-02-10", 1, 4)
    ]
    cursor.executemany('''
        INSERT INTO Articles (title, abstract, content, publication_date, source_id, topic_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', articles)

    # Insert sample experts
    experts = [
        ("Andrew Ng", "Stanford University", "Pioneer in machine learning and online education.", "Machine Learning, AI", "andrew.ng@stanford.edu"),
        ("Yoshua Bengio", "University of Montreal", "Renowned for his work on deep learning.", "Deep Learning, Neural Networks", "yoshua.bengio@umontreal.ca")
    ]
    cursor.executemany('''
        INSERT INTO Experts (name, affiliation, bio, fields, contact_info)
        VALUES (?, ?, ?, ?, ?)
    ''', experts)

    # Insert sample events
    events = [
        ("AI Conference 2024", "2024-08-15", "San Francisco, CA", "Annual conference on AI advancements.", "https://aiconference2024.com"),
        ("NLP Workshop", "2024-09-10", "New York, NY", "Workshop on Natural Language Processing.", "https://nlpworkshop2024.com")
    ]
    cursor.executemany('''
        INSERT INTO Events (name, date, location, description, url)
        VALUES (?, ?, ?, ?, ?)
    ''', events)

    # Insert sample courses
    courses = [
        ("Machine Learning by Andrew Ng", "Coursera", "Comprehensive course on machine learning.", "https://coursera.org/ml-course", "2024-06-01", "2024-12-01"),
        ("Deep Learning Specialization", "Coursera", "Series of courses on deep learning.", "https://coursera.org/deep-learning", "2024-07-01", "2024-12-31")
    ]
    cursor.executemany('''
        INSERT INTO Courses (name, provider, description, url, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', courses)

    conn.commit()

# Function to query data and save as JSON
def query_data_to_json(conn):
    cursor = conn.cursor()
    
    # Query articles
    cursor.execute('''
        SELECT a.title, a.abstract, a.publication_date, s.name as source_name, t.name as topic_name
        FROM Articles a
        JOIN Sources s ON a.source_id = s.source_id
        JOIN Topics t ON a.topic_id = t.topic_id
    ''')
    articles = cursor.fetchall()
    
    # Convert articles to dictionary
    articles_list = []
    for article in articles:
        articles_list.append({
            "title": article[0],
            "abstract": article[1],
            "publication_date": article[2],
            "source_name": article[3],
            "topic_name": article[4]
        })
    
    # Save articles to JSON file
    with open('articles.json', 'w') as json_file:
        json.dump({"articles": articles_list}, json_file, indent=4)
    
    print("Data saved to articles.json")

# Main execution
if __name__ == "__main__":
    conn = create_connection('knowledge_base.db')
    create_tables(conn)
    insert_sample_data(conn)
    query_data_to_json(conn)
    conn.close()
