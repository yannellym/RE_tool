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
        print(f"Processing file: {file_path}")  # Print the file path being processed
        
        try:
            if file_path.endswith('.csv'):
                data = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                data = pd.read_excel(file_path, engine='openpyxl')
            else:
                continue
            
            # Convert all column names to lowercase and strip spaces
            data.columns = data.columns.str.strip().str.lower()
            
            # Ensure lowercase column names are used for Full_Address creation
            if all(col in data.columns for col in ['property address', 'property city', 'property state', 'property zip']):
                # Convert 'property zip' to string and remove decimals if present
                data['property zip'] = data['property zip'].astype(str).str.split('.').str[0]
                
                data['Full_Address'] = (
                    data['property address'] + ', ' + 
                    data['property city'] + ', ' + 
                    data['property state'] + ' ' + 
                    data['property zip']
                )
                
                # Adjust column names with spaces and different casing
                column_mapping = {
                    'first name': 'First Name',
                    'last name': 'Last Name',
                    'phone 1': 'Phone 1'
                }
                
                # Select only the required columns using adjusted names
                required_columns = ['Full_Address', 'First Name', 'Last Name', 'Phone 1']
                data_selected = data.rename(columns=column_mapping)[required_columns]
                
                # Handle missing 'Phone 1' column by filling with 'N/A'
                if 'Phone 1' not in data_selected.columns:
                    data_selected['Phone 1'] = 'N/A'
                
                all_data.append(data_selected)
                
            else:
                print(f"Required columns missing in file: {file_path}")
        
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Save combined data to CSV
        current_date = datetime.now().strftime('%Y-%m-%d')
        output_file_path = os.path.join(CONVERTED_FOLDER, f'combined_data_{current_date}.csv')
        
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
