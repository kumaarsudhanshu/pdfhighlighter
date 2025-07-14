from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
import os
import tempfile
import uuid

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_file = request.files['pdf']
        numbers = request.form['numbers'].split(',')

        if not pdf_file or not numbers:
            return "PDF file and numbers required", 400

        # Clean numbers
        numbers = [n.strip() for n in numbers if n.strip()]
        if not numbers:
            return "Please enter at least one valid number", 400

        # Save uploaded PDF temporarily
        temp_dir = tempfile.gettempdir()
        input_path = os.path.join(temp_dir, str(uuid.uuid4()) + ".pdf")
        output_path = input_path.replace(".pdf", "_highlighted.pdf")
        pdf_file.save(input_path)

        # Define color palette (cycled)
        colors = [
            (1, 1, 0),      # Yellow
            
        ]

        # Open and process PDF
        doc = fitz.open(input_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            for i, number in enumerate(numbers):
                matches = page.search_for(number)
                color = colors[i % len(colors)]
                for inst in matches:
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=color)
                    highlight.update()

        doc.save(output_path)
        doc.close()

        return send_file(output_path, as_attachment=True)

    return render_template("index.html")
if __name__ == '__main__':
    app.run()
