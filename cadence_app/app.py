from flask import Flask, request, send_from_directory, redirect, url_for, jsonify
import os
from os import getenv
from werkzeug.utils import secure_filename
from ccw_client import CCWConfigurationError, execute_ccw_graphql
from excel_automation import refresh_power_query_workbook
from pipeline_conversion import convert_to_cisco_funnel

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'replace-this-with-secure-key'
FRONTEND_URL = getenv('FRONTEND_URL', 'http://127.0.0.1:5173')

ALLOWED_EXT = {'.xlsx', '.xlsm', '.xlsb', '.xls'}


def wants_json_response():
    requested_with = request.headers.get('X-Requested-With', '').lower()
    if requested_with == 'fetch':
        return True
    return request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']


def build_upload_payload(result, workbook_url, report_url, cisco_url, conversion_error):
    return {
        'workbook_name': os.path.basename(result['output_path']),
        'report_name': os.path.basename(result['report_path']) if result['report_path'] else None,
        'workbook_url': workbook_url,
        'report_url': report_url,
        'cisco_url': cisco_url,
        'report_summary': result.get('report_summary'),
        'report_error': result.get('report_error'),
        'conversion_error': conversion_error,
    }

def allowed_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXT

@app.route('/')
def index():
    return redirect(FRONTEND_URL)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        src_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(src_path)
        try:
            out_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + filename)
            report_filename = os.path.splitext(filename)[0] + '_report.html'
            report_path = os.path.join(app.config['UPLOAD_FOLDER'], report_filename)
            result = refresh_power_query_workbook(src_path, out_path, report_path=report_path)

            # Run the Cisco Funnel conversion on the refreshed workbook (use output_path)
            cisco_file = None
            try:
                refreshed_path = result.get('output_path') or out_path
                cisco_name = convert_to_cisco_funnel(refreshed_path, app.config['UPLOAD_FOLDER'])
                cisco_file = url_for('download_file', filename=cisco_name)
                conversion_error = None
            except Exception as conv_exc:
                # conversion failure should not block the main result; show flash later
                conversion_error = f'Conversion to Cisco Funnel failed: {conv_exc}'

            payload = build_upload_payload(
                result,
                url_for('download_file', filename=os.path.basename(result['output_path'])),
                url_for('view_report', filename=os.path.basename(result['report_path'])) if result['report_path'] else None,
                cisco_file,
                conversion_error,
            )
            return jsonify(payload)
        except Exception as e:
            return jsonify({'error': f'Processing failed: {e}'}), 500
    else:
        return jsonify({'error': 'Unsupported file type'}), 400


@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/report/<path:filename>')
def view_report(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, mimetype='text/html')


@app.route('/api/ccw/graphql', methods=['POST'])
def ccw_graphql():
    payload = request.get_json(silent=True) or {}
    query = payload.get('query')
    variables = payload.get('variables')
    operation_name = payload.get('operationName')

    if not query:
        return jsonify({'error': 'Missing GraphQL query'}), 400

    try:
        result = execute_ccw_graphql(query, variables=variables, operation_name=operation_name)
        return jsonify(result)
    except CCWConfigurationError as exc:
        return jsonify({'error': str(exc)}), 500
    except Exception as exc:
        return jsonify({'error': f'CCW request failed: {exc}'}), 502

if __name__ == '__main__':
    app.run(debug=True)
