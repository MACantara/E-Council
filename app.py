import os
from flask import Flask, request, render_template, Response, send_from_directory
import google.generativeai as genai
from dotenv import load_dotenv
from docx import Document
import PyPDF2
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Configure the API key for the generative model
genai.configure(api_key=os.environ['GOOGLE_GEMINI_AI_API_KEY'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Create the uploads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from .docx files
def extract_text_from_docx(filepath):
    doc = docx.Document(filepath)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return '\n'.join(full_text)

# Function to extract text from .pdf files
def extract_text_from_pdf(filepath):
    pdf_text = []
    with open(filepath, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in range(len(reader.pages)):
            pdf_text.append(reader.pages[page].extract_text())
    return '\n'.join(pdf_text)

# Function to handle streaming response from Gemini AI
def stream_response(user_input, file_content=None):
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Combine user input and file content for context
    if file_content:
        user_input += f"\n\nContext from file:\n{file_content}"

    response = model.generate_content(user_input, stream=True)

    final_response = ""
    for chunk in response:
        final_response += chunk.text

    return final_response

@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route to handle the form and file upload
def handle_file_upload(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        if filename.endswith('.docx'):
            return extract_text_from_docx(filepath)
        elif filename.endswith('.pdf'):
            return extract_text_from_pdf(filepath)
    return None

def create_docx_from_template(ai_response, template_path, output_path):
    doc = Document(template_path)
    doc.add_paragraph(ai_response)
    doc.save(output_path)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input = request.form['user_input']
        file = request.files.get('file')

        file_content = handle_file_upload(file)
        ai_response = stream_response(user_input, file_content)

        template_path = os.path.join('ms-word-templates', 'concept-paper-with-header-and-footer-template.docx')
        response_filename = 'response.docx'
        response_filepath = os.path.join(app.config['UPLOAD_FOLDER'], response_filename)
        create_docx_from_template(ai_response, template_path, response_filepath)

        return render_template('index.html', download_link=response_filename)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)