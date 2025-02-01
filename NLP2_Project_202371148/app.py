from flask import Flask, request, jsonify, render_template
import json
import os
from werkzeug.utils import secure_filename
import sqlite3
import time
from pdf_read import extract_text_from_pdf, get_pdf_summary
from database import create_connection, create_tables, update_json_files
from youtube_api import get_youtube_video_info
from article_fetch import get_article_info
import datetime


import time

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

def extract_summary_from_pdf(filepath):
    text = extract_text_from_pdf(filepath)
    summary = get_pdf_summary(text)
    return summary


@app.route('/add-entry', methods=['POST'])
def add_entry():
    data = request.json
    table_name = data['table_name']
    link = data['link']
    topic = data['topic']
    keywords = ', '.join(data['keywords'])
    content_type = data.get('content_type','default')

    conn = create_connection()
    cursor = conn.cursor()

    success = False
    retries = 5
    while not success and retries > 0:
        try:
            if table_name == 'videos':
                video_id = link.split('v=')[-1]
                video_info = get_youtube_video_info(video_id, content_type)
                if video_info:
                    title, description, url, video_id, date = video_info
                    cursor.execute('''
                        INSERT INTO Videos (title, description, url, video_id, date, topic, keywords)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (title, description, url, video_id, date, topic, keywords))
                else:
                    return jsonify({"success": False, "error": "Failed to get video info"})

            elif table_name == 'articles':
                article_info = get_article_info(link, content_type)
                if article_info and article_info[0] is not None:
                    title, content, url, date = article_info
                    cursor.execute('''
                        INSERT INTO Articles (title, content, url, date, topic, keywords)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (title, content, url, date, topic, keywords))
                else:
                    return jsonify({"success": False, "error": "Failed to get article info or title is None"})

            conn.commit()
            success = True
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                retries -= 1
                time.sleep(1)
            else:
                conn.rollback()
                return jsonify({"success": False, "error": str(e)})
        finally:
            conn.close()

    if not success:
        return jsonify({"success": False, "error": "Database is locked. Please try again later."})

    update_json_files()
    return jsonify({"success": True})


@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    topic = request.form['topic']
    keywords = request.form['keywords']

    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No selected file"})
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
        else:
            return jsonify({"success": False, "error": "Invalid file type"})
    elif 'url' in request.form:
        pdf_url = request.form['url']
        filename = pdf_url.split('/')[-1]
        if not allowed_file(filename):
            return jsonify({"success": False, "error": "Invalid file type"})
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        response = requests.get(pdf_url)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
        else:
            return jsonify({"success": False, "error": "Failed to download file"})
    else:
        return jsonify({"success": False, "error": "No file or URL provided"})

    # Process the PDF file and extract summary
    summary = extract_summary_from_pdf(filepath)
    date = datetime.datetime.now().date() # Set today's date
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO PDFs (filename, summary, path, topic, keywords, date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, summary, filepath, topic, keywords, date))
    conn.commit()
    conn.close()

    update_json_files()
    return jsonify({"success": True})

@app.route('/get-entries', methods=['GET'])
def get_entries():
    table = request.args.get('table')
    topic = request.args.get('topic', '')
    keyword = request.args.get('keyword', '')

    conn = create_connection()
    cursor = conn.cursor()
    if table == 'articles':
        cursor.execute('''
            SELECT title, content, url, date, topic, keywords FROM Articles 
            WHERE topic LIKE ? AND keywords LIKE ?
        ''', ('%' + topic + '%', '%' + keyword + '%'))
    elif table == 'videos':
        cursor.execute('''
            SELECT title, description AS content, url, date, topic, keywords FROM Videos 
            WHERE topic LIKE ? AND keywords LIKE ?
        ''', ('%' + topic + '%', '%' + keyword + '%'))
    elif table == 'pdfs':
        cursor.execute('''
            SELECT filename AS title, summary AS content, path AS url, topic, keywords, date FROM PDFs 
            WHERE topic LIKE ? AND keywords LIKE ?
        ''', ('%' + topic + '%', '%' + keyword + '%'))
    entries = cursor.fetchall()
    conn.close()

    return jsonify([{
        'title': entry[0],
        'content': entry[1],
        'url': entry[2],
        'date': entry[3] if table != 'pdfs' else '',  # PDFs do not have a date
        'topic': entry[4],
        'keywords': entry[5]
    } for entry in entries])



@app.route('/get-topics', methods=['GET'])
def get_topics():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT topic FROM (
            SELECT topic FROM Articles
            UNION
            SELECT topic FROM Videos
            UNION
            SELECT topic FROM PDFs
        )
    ''')
    topics = cursor.fetchall()
    conn.close()

    return jsonify([topic[0] for topic in topics])
@app.route('/delete-entry', methods=['POST'])
def delete_entry():
    data = request.json
    table_name = data['table_name']
    entry_id = data['id']

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {table_name.capitalize()} WHERE id = ?', (entry_id,))
    conn.commit()
    conn.close()
    update_json_files()
    return jsonify({"success": True})


if __name__ == '__main__':
    create_tables()
    app.run(port=5001, debug=True)
