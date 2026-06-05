from flask import Flask, request, render_template, send_file, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
from excel_automation import refresh_power_query_workbook

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'replace-this-with-secure-key'

ALLOWED_EXT = {'.xlsx', '.xlsm', '.xlsb', '.xls'}

def allowed_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXT

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        src_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(src_path)
        try:
            out_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + filename)
            refresh_power_query_workbook(src_path, out_path)
            return send_file(out_path, as_attachment=True)
        except Exception as e:
            flash(f'Processing failed: {e}')
            return redirect(url_for('index'))
    else:
        flash('Unsupported file type')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
