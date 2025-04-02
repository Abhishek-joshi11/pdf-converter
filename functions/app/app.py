from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
import os
import pandas as pd
import json
from PIL import Image

app = Flask(__name__)

# Define folders for uploads and conversions
UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["CONVERTED_FOLDER"] = CONVERTED_FOLDER

@app.route('/')
def index():
    print("index route accessed")
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)

def pdf_converter(input_pdf):
    if not os.path.exists(input_pdf):
        print("Error: File not found! Please check the file path.")
        return
    
    try:
        doc = fitz.open(input_pdf)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return
    
    print("Choose conversion type:")
    print("1. PDF to Text")
    print("2. PDF to Images")
    print("3. PDF to JSON")
    print("4. PDF to CSV")
    choice = input("Enter your choice (1/2/3/4): ")
    
    try:
        if choice == "1":  # PDF to Text
            text = "".join([page.get_text("text") for page in doc])
            if not text.strip():
                print("Warning: No extractable text found in the PDF!")
            output_txt = input_pdf.replace(".pdf", ".txt")
            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"PDF converted to Text: {output_txt}")

        elif choice == "2":  # PDF to Images
            output_folder = input_pdf.replace(".pdf", "_images")
            os.makedirs(output_folder, exist_ok=True)
            for i, page in enumerate(doc):
                image = page.get_pixmap()
                img_path = os.path.join(output_folder, f"page_{i+1}.png")
                image.save(img_path)
            print(f"PDF pages saved as images in: {output_folder}")

        elif choice == "3":  # PDF to JSON
            data = {"pages": [{"page_number": i+1, "text": page.get_text("text")} for i, page in enumerate(doc)]}
            output_json = input_pdf.replace(".pdf", ".json")
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print(f"PDF converted to JSON: {output_json}")

        elif choice == "4":  # PDF to CSV
            tables = [[i+1, page.get_text("text")] for i, page in enumerate(doc)]
            df = pd.DataFrame(tables, columns=["Page Number", "Text Content"])
            output_csv = input_pdf.replace(".pdf", ".csv")
            df.to_csv(output_csv, index=False)
            print(f"PDF converted to CSV: {output_csv}")

        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")
    except PermissionError:
        print("Error: Permission denied! Check file write permissions.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example Usage
if __name__ == "__main__":
    input_pdf = input("Enter the PDF file path: ")
    pdf_converter(input_pdf)
