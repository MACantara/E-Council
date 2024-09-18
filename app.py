import os
from flask import Flask, request, render_template, send_from_directory
from docx import Document
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create the uploads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        response_filename = 'concept_paper.docx'
        response_filepath = os.path.join(app.config['UPLOAD_FOLDER'], response_filename)
        create_docx(form_data, response_filepath)
        return render_template('index.html', download_link=response_filename)
    return render_template('index.html')

def create_docx(data, output_path):
    template_path = os.path.join('ms-word-templates', 'concept-paper-with-header-and-footer-template.docx')
    doc = Document(template_path)

    # Replace placeholders in paragraphs
    replace_placeholder(doc, '{{ signatory_name_1 }}', data['signatory_name_1'])
    replace_placeholder(doc, '{{ signatory_position_1 }}', data['signatory_position_1'])
    replace_placeholder(doc, '{{ signatory_name_2 }}', data['signatory_name_2'])
    replace_placeholder(doc, '{{ signatory_position_2 }}', data['signatory_position_2'])
    replace_placeholder(doc, '{{ signatory_department_2 }}', data['signatory_department_2'])
    replace_placeholder(doc, '{{ signatory_name_3 }}', data['signatory_name_3'])
    replace_placeholder(doc, '{{ signatory_position_3 }}', data['signatory_position_3'])
    replace_placeholder(doc, '{{ signatory_department_3 }}', data['signatory_department_3'])
    replace_placeholder(doc, '{{ subject_title }}', data['subject_title'])
    replace_placeholder(doc, '{{ date }}', data['date'])
    replace_placeholder(doc, '{{ introductory_paragraph }}', data['introductory_paragraph'])
    replace_placeholder(doc, '{{ time }}', data['time'])
    replace_placeholder(doc, '{{ location }}', data['location'])
    replace_placeholder(doc, '{{ participants }}', data['participants'])
    replace_placeholder(doc, '{{ budget }}', data['budget'])
    replace_placeholder(doc, '{{ descriptions }}', data['descriptions'])
    replace_placeholder(doc, '{{ objective_of_the_activity_1 }}', data['objective_of_the_activity_1'])
    replace_placeholder(doc, '{{ objective_of_the_activity_2 }}', data['objective_of_the_activity_2'])
    replace_placeholder(doc, '{{ objective_of_the_activity_3 }}', data['objective_of_the_activity_3'])
    replace_placeholder(doc, '{{ objective_of_the_activity_4 }}', data['objective_of_the_activity_4'])
    replace_placeholder(doc, '{{ learning_outcome_1 }}', data['learning_outcome_1'])
    replace_placeholder(doc, '{{ learning_outcome_2 }}', data['learning_outcome_2'])
    replace_placeholder(doc, '{{ learning_outcome_3 }}', data['learning_outcome_3'])
    replace_placeholder(doc, '{{ learning_outcome_4 }}', data['learning_outcome_4'])
    replace_placeholder(doc, '{{ number_of_expected_students }}', data['number_of_expected_students'])
    replace_placeholder(doc, '{{ number_of_expected_faculty }}', data['number_of_expected_faculty'])
    replace_placeholder(doc, '{{ prepared_by_name }}', data['prepared_by_name'])
    replace_placeholder(doc, '{{ prepared_by_position }}', data['prepared_by_position'])
    replace_placeholder(doc, '{{ prepared_by_student_council }}', data['prepared_by_student_council'])
    replace_placeholder(doc, '{{ signed_and_reviewed_by_name }}', data['signed_and_reviewed_by_name'])
    replace_placeholder(doc, '{{ signed_and_reviewed_by_position }}', data['signed_and_reviewed_by_position'])
    replace_placeholder(doc, '{{ signed_and_reviewed_by_student_council }}', data['signed_and_reviewed_by_student_council'])

    doc.save(output_path)

def replace_placeholder(doc, placeholder, replacement):
    # Replace placeholders in paragraphs
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            replace_in_paragraph(paragraph, placeholder, replacement)

    # Replace placeholders in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                replace_placeholder(cell, placeholder, replacement)

def replace_in_paragraph(paragraph, placeholder, replacement):
    # Concatenate all runs' text
    full_text = ''.join(run.text for run in paragraph.runs)
    
    # Replace the placeholder
    if placeholder in full_text:
        full_text = full_text.replace(placeholder, replacement)
        
        # Clear the paragraph's runs
        for run in paragraph.runs:
            run.text = ''
        
        # Add the new text back into the paragraph
        paragraph.runs[0].text = full_text

@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)