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

def process_files(file_paths):
    all_data = []
    for file_path in file_paths:
        try:
            if file_path.endswith('.csv'):
                data = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                data = pd.read_excel(file_path, engine='openpyxl')
            else:
                continue
            
            # Convert all column names to lowercase
            data.columns = data.columns.str.lower()
            
            # Ensure lowercase column names are used for Full_Address creation
            if 'property address' in data.columns and 'property city' in data.columns and 'property state' in data.columns and 'property zip' in data.columns:
                data['Full_Address'] = data['property address'] + ', ' + data['property city'] + ', ' + data['property state'] + ' ' + data['property zip'].astype(str)
                
                # Reorder columns to place Full_Address as the 4th column
                cols = list(data.columns)
                if 'full_address' in cols:
                    cols.insert(3, cols.pop(cols.index('full_address')))
                    data = data[cols]
                    
                all_data.append(data)
            else:
                print(f"Required columns missing in file: {file_path}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
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
            return render_template('index.html', message="No files selected")
        files = request.files.getlist('files[]')
        if not files or any(file.filename == '' for file in files):
            return render_template('index.html', message="No files selected")
        if all(file.filename.endswith(('.csv', '.xlsx')) for file in files):
            saved_files = []
            for file in files:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                saved_files.append(file_path)
            processed_file_path = process_files(saved_files)
            if processed_file_path:
                return send_from_directory(CONVERTED_FOLDER, os.path.basename(processed_file_path))
        else:
            return render_template('index.html', message="Please upload CSV or XLSX files only")
    return render_template('index.html', message="Upload a CSV or XLSX file")

if __name__ == '__main__':
    app.run(debug=True)
