from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import fitz  # PyMuPDF
import os
import uuid
import re

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 MB limit

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploaded_pdfs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_file = request.files['pdf']
        terms = request.form['numbers'].split(',')

        if not pdf_file or not terms:
            return "PDF file and search terms required", 400

        # Clean inputs
        terms = [t.strip() for t in terms if t.strip()]
        if not terms:
            return "Please enter at least one valid term", 400

        input_filename = str(uuid.uuid4()) + ".pdf"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        output_path = input_path.replace(".pdf", "_highlighted.pdf")
        pdf_file.save(input_path)

        try:
            doc = fitz.open(input_path)
        except Exception as e:
            return f"❌ Failed to open PDF: {e}", 500

        highlight_color = (1, 1, 0)  # Yellow highlight
        matched_pages = set()

        for page_num, page in enumerate(doc, start=1):
            try:
                blocks = page.get_text("dict")["blocks"]
            except Exception as e:
                print(f"⚠️ Error reading page {page_num}: {e}")
                continue

            for term in terms:
                normalized_term = re.sub(r'[\s\-–—]', '', term.lower())

                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                span_text = span["text"]
                                normalized_span = re.sub(r'[\s\-–—]', '', span_text.lower())

                                if normalized_term in normalized_span:
                                    rect = fitz.Rect(span["bbox"])
                                    highlight = page.add_highlight_annot(rect)
                                    highlight.set_colors(stroke=highlight_color)
                                    highlight.update()
                                    matched_pages.add((term, page_num))

        try:
            doc.save(output_path)
            doc.close()
        except Exception as e:
            return f"❌ Error saving PDF: {e}", 500

        # Generate full URL to view the file
        view_url = url_for('view_file', filename=os.path.basename(output_path), _external=True)

        return render_template("view_pdf.html",
                               filename=os.path.basename(output_path),
                               matches=sorted(matched_pages, key=lambda x: x[1]),
                               view_url=view_url)

    return render_template("index.html")


@app.route('/view/<filename>')
def view_pdf(filename):
    # Fallback if user tries to access view directly
    view_url = url_for('view_file', filename=filename, _external=True)
    return render_template("view_pdf.html", filename=filename, matches=[], view_url=view_url)


@app.route('/files/<filename>')
def view_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5050))
    app.run(host='0.0.0.0', port=port, debug=True)