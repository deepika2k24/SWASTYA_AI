  # SWASTYA AI PRE-DIAGNOSTIC-HEALTHCARE-ASSISTANT 🩺 


SWASTYA_AI is an AI-powered pre-diagnostic healthcare assistant built with Flask.
It helps users identify possible health conditions based on their symptoms, suggests basic over-the-counter remedies, and guides them toward professional medical advice when necessary.

The aim of SWASTYA_AI is not to replace doctors, but to bridge the gap between feeling unwell and seeking medical attention — empowering individuals with quick, preliminary health insights.

✨ Features

🩺 Symptom Analysis & Disease Prediction using ML models.

💊 Medicine Suggestions for mild, non-critical conditions.

📊 Health Monitoring Tools – BMI, BP, and Sugar level tracking.

🔒 Secure & Privacy-Focused – Credentials handled directly in the code (for local use).

🛠 Tech Stack

Backend: Python, Flask

Frontend: HTML, CSS, JavaScript

Data: Symptom–disease mappings

Database: MySQL

🚀 Installation

Clone the repository

git clone https://github.com/YOUR-USERNAME/SWASTYA_AI.git
cd SWASTYA_AI


Create and activate a virtual environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install dependencies

pip install -r requirements.txt


Update database credentials
Inside your Flask app’s config section (e.g., app.py), update your MySQL connection details:

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'yourpassword'
app.config['MYSQL_DB'] = 'hospital_data'


Run the application

python app.py


Access the app
Open your browser and go to http://127.0.0.1:5000
