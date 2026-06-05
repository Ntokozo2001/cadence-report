from flask import Flask, request, render_template, send_file, send_from_directory, redirect, url_for, flash, jsonify
import os
from werkzeug.utils import secure_filename
from ccw_client import CCWConfigurationError, execute_ccw_graphql
from excel_automation import refresh_power_query_workbook
from pipeline_conversion import convert_to_cisco_funnel

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
            report_filename = os.path.splitext(filename)[0] + '_report.html'
            report_path = os.path.join(app.config['UPLOAD_FOLDER'], report_filename)
            result = refresh_power_query_workbook(src_path, out_path, report_path=report_path)

            # Run the Cisco Funnel conversion on the refreshed workbook (use output_path)
            cisco_file = None
            try:
                refreshed_path = result.get('output_path') or out_path
                cisco_name = convert_to_cisco_funnel(refreshed_path, app.config['UPLOAD_FOLDER'])
                cisco_file = url_for('download_file', filename=cisco_name)
            except Exception as conv_exc:
                # conversion failure should not block the main result; show flash later
                flash(f'Conversion to Cisco Funnel failed: {conv_exc}')

            return render_template(
                'result.html',
                workbook_name=os.path.basename(result['output_path']),
                report_name=os.path.basename(result['report_path']) if result['report_path'] else None,
                workbook_url=url_for('download_file', filename=os.path.basename(result['output_path'])),
                report_url=url_for('view_report', filename=os.path.basename(result['report_path'])) if result['report_path'] else None,
                cisco_url=cisco_file,
                report_summary=result.get('report_summary'),
                report_error=result.get('report_error'),
            )
        except Exception as e:
            flash(f'Processing failed: {e}')
            return redirect(url_for('index'))
    else:
        flash('Unsupported file type')
        return redirect(url_for('index'))


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
