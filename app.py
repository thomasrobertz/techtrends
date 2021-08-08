import sys
import logging
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash

HTTP_STATUS_OK: int = 200
HTTP_STATUS_NOT_FOUND: int = 404
HTTP_STATUS_INTERNAL_ERROR: int = 500
DATABASE_FILE: str = "database.db"
db_connection_count: int = 0

PRODUCTION_MODE: bool = True

logging.basicConfig(level = logging.DEBUG,
                    format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt = '%m-%d %H:%M')

appLog = logging.getLogger('app')

# Function to get a database connection.
def get_raw_db_connection():
    raw_connection = sqlite3.connect(DATABASE_FILE)
    global db_connection_count
    db_connection_count += 1
    return raw_connection

# Function to get a Row connection.
# This function connects to database with the name `database.db`.
def get_db_connection():
    connection = get_raw_db_connection()
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID.
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to get the total amount of posts.
def get_post_count():
    connection = get_raw_db_connection()
    cursor = connection.cursor()
    postCount = cursor.execute('SELECT COUNT(*) FROM posts').fetchone()
    return postCount[0]

# Function to check whether the database file exists.
def database_file_exists(pathToDatabaseFile):
    return Path(pathToDatabaseFile).exists()

# Function to check whether the database has the given table.
def database_has_table(tableName):
    connection = get_db_connection()
    postsTable = connection.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tableName}'").fetchone()
    connection.close()
    return postsTable is not None

# Define the Flask application.
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application.
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered.
# If the post ID is not found a 404 page is shown.
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      appLog.info(f"Post {post_id} not found - returning 404.")
      return render_template('404.html'), HTTP_STATUS_NOT_FOUND
    else:
      appLog.info(f"Get post {post_id}.")
      return render_template('post.html', post=post)

# Define the About Us page.
@app.route('/about')
def about():
    appLog.info("'About Us' page accessed.")
    return render_template('about.html')

# Define the post creation functionality.
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            appLog.info(f"New post with title '{title}' created.")
            return redirect(url_for('index'))

    return render_template('create.html')

# Endpoint to get the health status of the app.
@app.route("/healthz")
def healthz():
    appLog.info("healthz")
    statusText = "ERROR - Database file not exists or posts table not found"
    status = HTTP_STATUS_INTERNAL_ERROR
    if (database_file_exists(DATABASE_FILE)):
        statusText = "ERROR - Posts table not found"
        if (database_has_table("posts")):
            statusText = "OK - healthy"
            status = HTTP_STATUS_OK
    return {
        "result": statusText
    }, status

# Endpoint to get some metrics for the app.
@app.route("/metrics")
def metrics():
    global db_connection_count
    return {
        "post_count": get_post_count(),
        "db_connection_count": db_connection_count
    }, HTTP_STATUS_OK

# start the application on port 3111.
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111', debug= not PRODUCTION_MODE)
   # Route STDOUT and STDERR to app logger
   sys.stdout.write = appLog.info
   sys.stderr.write = appLog.info
