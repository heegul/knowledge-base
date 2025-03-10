from flask import Flask, request, jsonify, render_template, send_from_directory
import json
import os
import requests
from werkzeug.utils import secure_filename
import sqlite3
import time
from pdf_read import extract_text_from_pdf, get_pdf_summary, get_pdf_summary_lama3, get_pdf_summary_claude, get_pdf_summary_deepseek, get_summary_grok
from database import create_connection, create_tables, update_json_files
from youtube_api import get_youtube_video_info
from article_fetch import get_article_info
import datetime

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

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def extract_summary_from_pdf(filepath):
    text = extract_text_from_pdf(filepath)
    print("Grok PDF summarization starting...\n")
    summary = get_summary_grok(text)
    print("Done!\n")
    return summary


@app.route('/add-entry', methods=['POST'])
def add_entry():
    data = request.json
    table_name = data['table_name']
    link = data['link']
    topic = data['topic']
    keywords = ', '.join(data['keywords'])
    content_type = data.get('content_type', 'default')

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
                        INSERT INTO Videos (title, content, url, date, topic, keywords)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (title, description, url, date, topic, keywords))
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
            if conn:
                conn.close()

    if not success:
        return jsonify({"success": False, "error": "Database is locked. Please try again later."})

    update_json_files()
    return jsonify({"success": True})


def download_pdf_from_url(url, upload_folder):
    response = requests.get(url)
    if response.status_code == 200:
        filename = secure_filename(url.split('/')[-1])
        filepath = os.path.join(upload_folder, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filename, filepath
    else:
        raise Exception(f"Failed to download file from {url}. Status code: {response.status_code}")


@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    print("Entering upload_pdf()")
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process the PDF file and extract summary
        topic = request.form['topic'] or 'Unspecified'  # Default to 'Unspecified' if empty
        keywords = request.form.get('keywords', '').strip() or 'None'  # Default to 'None' if empty
        summary = extract_summary_from_pdf(filepath)  # Implement this function

        title = filename  # Use filename as title if extraction fails
        date = datetime.datetime.now().date().isoformat()  # Use current date as date

        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO PDFs (title, content, url, date, topic, keywords) VALUES (?, ?, ?, ?, ?, ?)''', (title, summary, filepath, date, topic, keywords))
            conn.commit()
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
        finally:
            conn.close()

        update_json_files()
        return jsonify({"success": True})

    return jsonify({"success": False, "error": "Invalid file type"})

@app.route('/get-entries', methods=['GET'])
def get_entries():
    table = request.args.get('table')
    topic = request.args.get('topic', '')
    keyword = request.args.get('keyword', '')

    conn = create_connection()
    cursor = conn.cursor()
    if table == 'articles':
        cursor.execute('''
            SELECT id, title, content, url, date, topic, keywords FROM Articles 
            WHERE topic LIKE ? AND keywords LIKE ?
        ''', ('%' + topic + '%', '%' + keyword + '%'))
    elif table == 'videos':
        cursor.execute('''
            SELECT id, title, content, url, date, topic, keywords FROM Videos 
            WHERE topic LIKE ? AND keywords LIKE ?
        ''', ('%' + topic + '%', '%' + keyword + '%'))
    elif table == 'pdfs':
        cursor.execute('''
            SELECT id, title, content, url, date, topic, keywords FROM PDFs 
            WHERE topic LIKE ? AND keywords LIKE ?
        ''', ('%' + topic + '%', '%' + keyword + '%'))
    entries = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id': entry[0],
        'title': entry[1],
        'content': entry[2],
        'url': entry[3],
        'date': entry[4],
        'topic': entry[5],
        'keywords': entry[6]
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
    table_name = data.get('table_name')
    entry_id = data.get('id')
    
    if not table_name or not entry_id:
        return jsonify({"success": False, "error": "Missing table_name or id"})
    
    # Validate table_name to prevent SQL injection
    valid_tables = ['articles', 'videos', 'pdfs']
    if table_name.lower() not in valid_tables:
        return jsonify({"success": False, "error": "Invalid table name"})
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Capitalize the first letter of table_name for the SQL query
        table = table_name.capitalize()
        if table.endswith('s'):
            table = table[:-1] + 's'  # Ensure proper pluralization
            
        cursor.execute(f"DELETE FROM {table} WHERE id = ?", (entry_id,))
        conn.commit()
        
        # Update the JSON files after deletion
        update_json_files()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        conn.close()


@app.route('/update-title', methods=['POST'])
def update_title():
    data = request.json
    table_name = data['table_name']
    entry_id = data['id']
    new_title = data['title']

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f'''
            UPDATE {table_name.capitalize()}
            SET title = ?
            WHERE id = ?
        ''', (new_title, entry_id))
        conn.commit()
        update_json_files()  # Ensure JSON files are updated after title change
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        conn.close()

@app.route('/update-content', methods=['POST'])
def update_content():
    data = request.json
    print("Received data:", data)  # Log received data for debugging

    if 'table_name' not in data or 'id' not in data or 'value' not in data or 'field_name' not in data:
        return jsonify({"success": False, "error": "Missing required keys in the request data"})

    table_name = data['table_name']
    entry_id = data['id']
    new_content = data['value']
    field_name = data['field_name']

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f'''
            UPDATE {table_name.capitalize()}
            SET {field_name} = ?
            WHERE id = ?
        ''', (new_content, entry_id))
        conn.commit()
        update_json_files()  # Ensure JSON files are updated after title change
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        conn.close()


if __name__ == '__main__':
    create_tables()
    app.run(port=5001, debug=True)
