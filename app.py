from flask import Flask, render_template, request, send_from_directory, after_this_request
import fitz  # PyMuPDF
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploaded_pdfs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            pdf_file = request.files.get('pdf')
            numbers_input = request.form.get('numbers', '')

            if not pdf_file or not numbers_input.strip():
                return "❌ PDF file and numbers required", 400

            numbers = [n.strip() for n in numbers_input.split(',') if n.strip()]
            if not numbers:
                return "❌ Please enter at least one valid number", 400

            input_filename = str(uuid.uuid4()) + ".pdf"
            input_path = os.path.join(UPLOAD_FOLDER, input_filename)
            output_path = input_path.replace(".pdf", "_highlighted.pdf")
            pdf_file.save(input_path)

            try:
                doc = fitz.open(input_path)
            except Exception as e:
                return f"❌ Failed to open PDF: {e}", 500

            highlight_color = (1, 1, 0)  # Yellow
            matched_pages = set()

            for page_num, page in enumerate(doc, start=1):
                try:
                    blocks = page.get_text("dict")["blocks"]
                except Exception as e:
                    print(f"[⚠️ Page {page_num}] Text extraction failed: {e}")
                    continue

                for number in numbers:
                    for block in blocks:
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                if number in span.get("text", ""):
                                    rect = fitz.Rect(span["bbox"])
                                    highlight = page.add_highlight_annot(rect)
                                    highlight.set_colors(stroke=highlight_color)
                                    highlight.update()
                                    matched_pages.add((number, page_num))

            try:
                doc.save(output_path)
                doc.close()
            except Exception as e:
                return f"❌ Error saving PDF: {e}", 500

            # Auto-delete input file after processing
            if os.path.exists(input_path):
                os.remove(input_path)

            return render_template("view_pdf.html",
                                   filename=os.path.basename(output_path),
                                   matches=sorted(matched_pages))

        except Exception as e:
            return f"❌ Unexpected error: {e}", 500

    return render_template("index.html")

@app.route('/files/<filename>')
def view_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    @after_this_request
    def remove_file(response):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🧹 Auto-deleted file: {filename}")
        except Exception as e:
            print(f"⚠️ Failed to delete {filename}: {e}")
        return response

    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)