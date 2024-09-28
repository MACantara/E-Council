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

### 4. Run the Flask Application

Start the Flask development server with:

```bash
python app.py
```

Replace app.py with the name of your Flask application file if different.

### 5. Access the Application

Open your web browser and navigate to http://127.0.0.1:5000/ to view the application.
