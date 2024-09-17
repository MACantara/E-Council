import os
from flask import Flask, request, render_template, Response
import google.generativeai as genai
from dotenv import load_dotenv
import docx
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

    for chunk in response:
        yield chunk.text

# Route to handle the form and file upload
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input = request.form['user_input']
        file = request.files.get('file')

        file_content = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Extract text based on file type
            if filename.endswith('.docx'):
                file_content = extract_text_from_docx(filepath)
            elif filename.endswith('.pdf'):
                file_content = extract_text_from_pdf(filepath)

        # Stream the AI-generated response with file content as context
        return Response(stream_response(user_input, file_content), content_type='text/html')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)