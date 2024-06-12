import os
import pandas as pd
from flask import Flask, request, render_template, send_from_directory
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(CONVERTED_FOLDER):
    os.makedirs(CONVERTED_FOLDER)

def process_files(files):
    all_data = []
    for file in files:
        try:
            data = pd.read_csv(file)
            data['Full_Address'] = data['Property Address'] + ', ' + data['Property City'] + ', ' + data['Property State'] + ' ' + data['Property Zip'].astype(str)
            
            # Reorder columns to place Full_Address as the 4th column
            cols = list(data.columns)
            if 'Full_Address' in cols:
                cols.insert(3, cols.pop(cols.index('Full_Address')))
                data = data[cols]
                
            all_data.append(data)
        except Exception as e:
            print(f"Error processing file {file.filename}: {e}")
    
    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        current_date = datetime.now().strftime('%Y-%m-%d')
        output_file_path = os.path.join(CONVERTED_FOLDER, f'converted_{current_date}.csv')
        if os.path.exists(output_file_path):
            existing_data = pd.read_csv(output_file_path)
            combined_data = pd.concat([existing_data, combined_data], ignore_index=True)
        combined_data.to_csv(output_file_path, index=False)
        return output_file_path
    return None

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'files[]' not in request.files:
            return render_template('index.html')
        files = request.files.getlist('files[]')
        if not files or any(file.filename == '' for file in files):
            return render_template('index.html')
        if all(file.filename.endswith('.csv') for file in files):
            saved_files = []
            for file in files:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                saved_files.append(file_path)
            processed_file_path = process_files(saved_files)
            if processed_file_path:
                return render_template('success.html', download_link=f'/download/{os.path.basename(processed_file_path)}')
    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(CONVERTED_FOLDER, filename)

# Add the following lines to use Gunicorn
if __name__ == '__main__':
    # Use Gunicorn to serve the Flask app
    # -b 0.0.0.0:$PORT tells Gunicorn to bind to the port provided by Netlify
    # app:app specifies the Flask app and its name
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run()
