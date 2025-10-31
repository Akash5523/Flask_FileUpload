from flask import Flask, redirect, url_for, render_template, request, session, flash, abort, send_from_directory
from werkzeug.utils import secure_filename
from config import Config
from dotenv import load_dotenv
import os
# import secrets

load_dotenv()

app = Flask(__name__)
# app.secret_key = secrets.token_hex(16)

app.config.from_object(Config)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'pptx', 'xlsx', 'csv', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    username = session.get('username')
    if username:
        return render_template('fileUpload_dashboard.html', username=username)
    return render_template('fileUpload_login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()

        if not username:
            flash("Username field cannot be empty !!!", "warning")
            return redirect(url_for('index'))
        
        session['username'] = username
        flash(f"Welcome {username}", "success")
        return redirect(url_for("dashboard"))
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    if not username:
        flash("Please login to access the dashboard.", "warning")
        return redirect(url_for('index'))
    
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('fileUpload_dashboard.html', username=username, files=files)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    username = session.get('username')
    if not username:
        flash("Please login before uploading a file.", "warning")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            flash('No files selected', 'warning')
            return redirect(request.url)
        
        uploaded_files =[]
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                uploaded_files.append(filename)
            else:
                flash(f'File type not allowed: {file.filename}', 'danger')

        if uploaded_files:
            flash(f"Successfully uploaded: {', '.join(uploaded_files)}", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('No valid files uploaded!', 'warning')
            return redirect(request.url)
    return render_template('fileUpload_upload.html', username=username)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/download/<filename>')
def download_file(filename):
    if 'username' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('index'))

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/delete/<filename>')
def delete_file(filename):
    if 'username' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('index'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"File '{filename}' deleted successfully.", "info")
    else:
        flash("File not found.", "danger")

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out successfully", "info")
    return redirect(url_for('index'))

