from flask import Flask, render_template, request, send_file, redirect, url_for
import fitz  # PyMuPDF
import os
import pandas as pd
import json
import zipfile
import shutil
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER
app.secret_key = 'your-secret-key-here'

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'pdfFile' not in request.files:
        return redirect(request.url)
    
    file = request.files['pdfFile']
    conversion_type = request.form['conversionType']
    
    if file.filename == '':
        return redirect(request.url)
    
    if not file or not allowed_file(file.filename):
        return "Invalid file type. Only PDF files are allowed.", 400
    
    try:
        # Secure filename and create input path
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        # Process conversion based on type
        if conversion_type == 'text':
            output = pdf_to_text(input_path)
            return send_file(
                output,
                as_attachment=True,
                download_name=f"{os.path.splitext(filename)[0]}.txt",
                mimetype='text/plain'
            )
        elif conversion_type == 'images':
            zip_buffer = pdf_to_images(input_path)
            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name=f"{os.path.splitext(filename)[0]}_images.zip",
                mimetype='application/zip'
            )
        elif conversion_type == 'json':
            output = pdf_to_json(input_path)
            return send_file(
                output,
                as_attachment=True,
                download_name=f"{os.path.splitext(filename)[0]}.json",
                mimetype='application/json'
            )
        elif conversion_type == 'csv':
            output = pdf_to_csv(input_path)
            return send_file(
                output,
                as_attachment=True,
                download_name=f"{os.path.splitext(filename)[0]}.csv",
                mimetype='text/csv'
            )
        else:
            return "Invalid conversion type selected.", 400
            
    except Exception as e:
        return f"Conversion failed: {str(e)}", 500
    finally:
        # Clean up uploaded file
        if os.path.exists(input_path):
            os.remove(input_path)

def pdf_to_text(input_path):
    doc = fitz.open(input_path)
    text = "\n".join([page.get_text() for page in doc])
    
    # Create in-memory file
    output = BytesIO()
    output.write(text.encode('utf-8'))
    output.seek(0)
    return output

def pdf_to_images(input_path):
    doc = fitz.open(input_path)
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, page in enumerate(doc):
            pix = page.get_pixmap()
            img_data = pix.tobytes()
            zip_file.writestr(f"page_{i+1}.png", img_data)
    
    zip_buffer.seek(0)
    return zip_buffer

def pdf_to_json(input_path):
    doc = fitz.open(input_path)
    data = {
        "metadata": {
            "pages": len(doc),
            "author": doc.metadata.get('author', ''),
            "title": doc.metadata.get('title', '')
        },
        "pages": [
            {
                "page_number": i+1,
                "text": page.get_text()
            } for i, page in enumerate(doc)
        ]
    }
    
    output = BytesIO()
    output.write(json.dumps(data, indent=2).encode('utf-8'))
    output.seek(0)
    return output

def pdf_to_csv(input_path):
    doc = fitz.open(input_path)
    data = [{
        "Page Number": i+1,
        "Text": page.get_text()
    } for i, page in enumerate(doc)]
    
    output = BytesIO()
    df = pd.DataFrame(data)
    df.to_csv(output, index=False)
    output.seek(0)
    return output

if __name__ == '__main__':
    app.run(debug=True)
    #abhishek