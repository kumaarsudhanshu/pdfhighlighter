from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import fitz  # PyMuPDF
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploaded_pdfs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_file = request.files['pdf']
        numbers = request.form['numbers'].split(',')

        if not pdf_file or not numbers:
            return "PDF file and numbers required", 400

        # Clean input numbers
        numbers = [n.strip() for n in numbers if n.strip()]
        if not numbers:
            return "Please enter at least one valid number", 400

        # Save uploaded PDF
        input_filename = str(uuid.uuid4()) + ".pdf"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        output_path = input_path.replace(".pdf", "_highlighted.pdf")
        pdf_file.save(input_path)

        doc = fitz.open(input_path)
        highlight_color = (1, 1, 0)  # Yellow

        matched_pages = set()

        for page_num, page in enumerate(doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            for number in numbers:
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                if number in span["text"]:
                                    rect = fitz.Rect(span["bbox"])
                                    highlight = page.add_highlight_annot(rect)
                                    highlight.set_colors(stroke=highlight_color)
                                    highlight.update()
                                    matched_pages.add((number, page_num))

        doc.save(output_path)
        doc.close()

        output_filename = os.path.basename(output_path)
        return render_template("view_pdf.html", filename=output_filename, matches=sorted(matched_pages))

    return render_template("index.html")

@app.route('/view/<filename>')
def view_pdf(filename):
    return render_template('view_pdf.html', filename=filename, matches=[])

@app.route('/files/<filename>')
def view_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)