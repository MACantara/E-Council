# Flask-based Python Project Setup

## Introduction

This project is a Flask-based web application that integrates with the Google Gemini AI model for generating responses based on user input and uploaded files. This document provides instructions on how to set up the project on a new device.

## Prerequisites

1. **Python**: Ensure Python 3.6 or higher is installed. You can download it from [python.org](https://www.python.org/downloads/).
2. **Pip**: Python's package installer. It comes bundled with Python 3.4 and higher.

## Setup Instructions

### 1. Clone the Repository

First, clone the repository from GitHub or download the project files.

```bash
git clone https://github.com/yourusername/your-repository.git
cd your-repository
```

### 2. Create and Activate a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

#### Create a Virtual Environment

```bash
python -m venv venv
```

#### Activate the Virtual Environment

- On Windows:
    - ```bash
      venv\Scripts\activate
      ```
- On macOS/Linux:
    - ```bash
      source venv/bin/activate
      ```

### 3. Install Project Dependencies

With the virtual environment activated, install the required packages listed in requirements.txt.

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

The project uses environment variables for configuration. Create a .env file in the root directory of the project and add the following line, replacing GOOGLE_GEMINI_AI_API_KEY with your actual Google Gemini AI API key:

```makefile
GOOGLE_GEMINI_AI_API_KEY=YOUR_API_KEY
```

### 5. Set up the Uploards Directory

Ensure the uploads directory exists in the root of the project. If it doesn’t, create it manually:

```bash
mkdir uploads
```

### 6. Run the Flask Application

Start the Flask development server with:

```bash
python app.py
```

Replace app.py with the name of your Flask application file if different.

### 7. Access the Application

Open your web browser and navigate to http://127.0.0.1:5000/ to view the application.

## Troubleshooting

- FileNotFoundError: Ensure the uploads directory exists and has the correct permissions.
- ModuleNotFoundError: Verify that all dependencies are installed in your virtual environment.