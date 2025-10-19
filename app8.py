import spacy
import pandas as pd
import re
import PyPDF2
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
from utils.symptom_extractor import extract_symptoms
from utils.disease_predictor import predict_disease, predict_top_diseases
import MySQLdb
import wikipediaapi
import requests
from bs4 import BeautifulSoup
import tabula
import pandas as pd
import pickle
from rapidfuzz import process, fuzz
from utils.hospital_finder import find_hospitals
from datetime import datetime
import pandas as pd


# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Load the dataset
df = pd.read_csv(r"C:\Users\deepl\Downloads\Deepika NMIT\swastyaai_app\data\medicines.csv")


# Initialize Wikipedia API with a user agent
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='YourAppName/1.0 (contact@example.com)'
)

# Function to fetch summary from Wikipedia
def fetch_wikipedia_summary(disease_name):
    page = wiki_wiki.page(disease_name)
    print(f"Fetching Wikipedia page for: {disease_name}")
    if page.exists():
        summary = page.summary
        print(f"Page found. Summary length: {len(summary)}")
        sentences = summary.split('. ')
        if len(sentences) > 3:
            return '. '.join(sentences[:3]) + '.'
        else:
            return '. '.join(sentences) + '.'
    else:
        return 0


# Function to fetch disease summary from multiple sources
def fetch_disease_summary(disease_name):
    simplified_name = re.sub(r'\(.*?\)', '', disease_name).strip()
    print(f"Searching for: {simplified_name}")

    summary = fetch_wikipedia_summary(simplified_name)
    if summary:
        return f"Information from Wikipedia:\n{summary}"



    return 0

# Function to suggest drug for a given disease (matching as a substring)
def suggest_drug_for_disease(df, disease_name):
    disease_name_lower = disease_name.lower().strip()
    print(f"Looking for drugs for disease: {disease_name_lower}")  # Debug
    drugs = df[df['disease'].str.lower().str.contains(disease_name_lower)]['drug'].tolist()
    print(f"Drugs found: {drugs}")  # Debug
    if drugs:
        return list(set(drugs))  # unique drugs
    else:
        return ["No drug found for the given disease"]
   
# Function to find disease associated with a given drug
def find_disease_for_drug(df, drug_name):
    drug_name_lower = drug_name.lower().strip()
    diseases = df[df['drug'].str.lower().apply(lambda drugs: any(drug_name_lower in drug for drug in drugs.split(' / ')))]['disease'].tolist()
    if diseases:
        return list(set(diseases))  # Return unique diseases
    else:
        return ["No disease found for the given drug"]

def extract_hospitals_by_pincode_excel(file_path, pincode, city=None):
    import pandas as pd
    print(f"[DEBUG] Reading hospitals from: {file_path}")
    df = pd.read_excel(file_path, dtype=str, skiprows=1)
    df.columns = df.columns.str.strip().str.lower()
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    # Normalize pin code column to strings without spaces
    df['pin code'] = df['pin code'].astype(str).str.replace(' ', '')
    clean_pincode = str(pincode).strip().replace(' ', '')
    
    # Filter only by pincode
    results = df[df['pin code'] == clean_pincode]
    
    print(f"[DEBUG] Found {len(results)} hospitals for pincode={pincode} (city input ignored in filtering)")
    return results[['hospital name', 'address', 'city', 'state', 'pin code']].to_dict(orient='records')



app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'your_secret_key_here'

app.config['MYSQL_HOST'] = '********'
app.config['MYSQL_USER'] = '*****'
app.config['MYSQL_PASSWORD'] = '*****'
app.config['MYSQL_DB'] = '******'

mysql = MySQL(app)

detected_symptoms = []
asked_about_wellbeing = False
predicted_disease = None
asked_for_more_symptoms = False
asked_about_info = False
expecting_symptoms = False

def respond_to_greeting(sentence):
    import re
    global asked_about_wellbeing
    greetings = [
        "hey", "hello", "hi", "hii", "hiii", "namaskara", "greetings", "good morning", "good afternoon", "good evening", "what's up", "yo", "sup"
    ]
    farewells = [
        "bye", "goodbye", "ok", "see you", "take care", "farewell", "later", "ciao", "adios", "see ya"
    ]
    s = sentence.lower()
    if any(re.search(rf"\b{re.escape(word)}\b", s) for word in greetings):
        asked_about_wellbeing = True
        return "Hello! How are you doing today?"
    elif any(re.search(rf"\b{re.escape(word)}\b", s) for word in farewells):
        return "Goodbye! Take care."
    else:
        return None


def respond_to_wellbeing(sentence):
    import re
    global detected_symptoms, expecting_symptoms
    positive_responses = [
        "good", "fine", "great", "okay", "not bad", "well", "alright", "excellent", "awesome", "fantastic", "doing good", "doing well", "pretty good", "all good", "better"
    ]
    negative_responses = [
        "not good", "unwell", "sick", "bad", "poorly", "worst", "not fine", "ill", "terrible", "awful", "not okay", "not well", "feeling down", "feeling low", "horrible", "miserable"
    ]
    s = sentence.lower()
    if any(re.search(rf"\b{re.escape(word)}\b", s) for word in negative_responses):
        expecting_symptoms = True
        return "I'm sorry to hear that. Can you describe your symptoms?"
    elif any(re.search(rf"\b{re.escape(word)}\b", s) for word in positive_responses):
        return "I'm glad to hear that! Take care!"
    else:
        return None
# List of common symptoms
common_symptoms = [
    'itching', 'skin_rash', 'continuous_sneezing', 'shivering', 'chills', 'joint_pain', 'stomach_pain', 'acidity',
    'ulcers_on_tongue', 'vomiting', 'fatigue', 'weight_gain', 'anxiety', 'cold_hands_and_feet', 'mood_swings',
    'weight_loss', 'restlessness', 'lethargy', 'patches_in_throat', 'cough', 'sweating', 'indigestion', 'headache',
    'nausea', 'loss_of_appetite', 'back_pain', 'constipation', 'abdominal_pain', 'mild_fever', 'yellow_urine',
    'runny_nose', 'congestion', 'chest_pain', 'dizziness', 'cramps', 'bruising', 'obesity', 'puffy_face_and_eyes',
    'brittle_nails', 'excessive_hunger', 'drying_and_tingling_lips', 'knee_pain', 'hip_joint_pain', 'muscle_weakness',
    'stiff_neck', 'swelling_joints', 'movement_stiffness', 'loss_of_balance', 'unsteadiness', 'weakness_of_one_body_side',
    'loss_of_smell', 'bladder_discomfort', 'passage_of_gases', 'internal_itching', 'depression', 'irritability',
    'muscle_pain', 'altered_sensorium', 'increased_appetite', 'visual_disturbances', 'lack_of_concentration',
    'receiving_blood_transfusion', 'receiving_unsterile_injections', 'history_of_alcohol_consumption', 'palpitations',
    'painful_walking', 'blackheads', 'scarring', 'skin_peeling', 'silver_like_dusting', 'small_dents_in_nails',
    'inflammatory_nails', 'blister', 'red_sore_around_nose', 'yellow_crust_ooze', 'mucoid_sputum', 'family_history',    # Added synonyms and missing symptoms
    'toxic_look', 'belly_pain', 'diarrhoea', 'diarrhea', 'polyuria', 'irregular_sugar_level', 'blurred_vision', 'distorted_vision','sunken_eyes','dehydration','fluid_overload','high_fever','foul_smell_of_urine','lack_of_concentration','loss_of_balance','spinning_movements',
    
]

def fuzzy_match_disease(user_input, disease_list, threshold=80):
    # Returns the best match if similarity is above threshold, else None
    match, score, _ = process.extractOne(user_input, disease_list, scorer=fuzz.token_sort_ratio)
    if score >= threshold:
        return match
    return None

import difflib

def extract_symptoms(user_input, common_symptoms, threshold=70):  # lower threshold
    input_symptoms = [s.strip().lower().replace(' ', '_') for s in re.split(r',|and', user_input)]
    detected = []
    for user_symptom in input_symptoms:
        for ks in common_symptoms:
            ks_norm = ks.lower().replace('_', ' ').strip()
            us_norm = user_symptom.lower().replace('_', ' ').strip()
            score = fuzz.ratio(us_norm, ks_norm)
            print(f"[DEBUG] comparing '{us_norm}' with '{ks_norm}' → {score}")  # show scores
            if score >= threshold:
                detected.append(ks)
    return list(set(detected))




def chatbot_response(input_sentence):
    text = input_sentence.lower().strip()
    
    global asked_about_wellbeing, detected_symptoms, predicted_disease
    global asked_for_more_symptoms, asked_about_info, expecting_symptoms

    # Disease alias mapping for user-friendly queries
    disease_aliases = {
        'jaundice': 'Hyperbilirubinemia',
    }
    # If no symptoms, check for alias match first
    for alias, real_disease in disease_aliases.items():
        if alias in text:
            drugs = suggest_drug_for_disease(df, real_disease)
            summary = fetch_wikipedia_summary(real_disease)
            response = f"Recommended medicines for {real_disease}: {', '.join(drugs)}"
            if summary:
                response += f"\nInfo: {summary}"
            return response

    response = ""

    # Medicine request intent (combined: if both 'medicine' or 'medicines' and a disease name/alias are present, answer immediately)
    # Also handle common misspellings like 'medcine', 'medcines', etc.
    medicine_keywords = ["medicine", "medicines", "medcine", "medcines", "medicin", "drug", "drugs"]
    if any(word in text for word in medicine_keywords):
        # Fuzzy match: if user input contains a disease alias, map to closest disease name
        disease_aliases = {
            'cold': 'Cold Symptoms',
            'common cold': 'Cold Symptoms',
            'cough': 'Cough',
            'fever': 'Fever',
            'headache': 'Headache',
            # Add more as needed
        }
        # Import symptom synonyms from extractor
        try:
            from utils.symptom_extractor import SYMPTOM_SYNONYMS, user_symptom_map
        except ImportError:
            SYMPTOM_SYNONYMS = {}
            user_symptom_map = {}
        # Check for symptom synonyms in user input
        for alias, model_symptom in {**SYMPTOM_SYNONYMS, **user_symptom_map}.items():
            if alias in text:
                # Try to find a disease with the same name as the mapped symptom
                for disease in df['disease'].unique():
                    if model_symptom.lower() == disease.lower():
                        drugs = suggest_drug_for_disease(df, disease)
                        # If no drug found, fallback to Wikipedia
                        if not drugs or (len(drugs) == 1 and 'no drug found' in drugs[0].lower()):
                            summary = fetch_wikipedia_summary(disease)
                            if summary:
                                return f"No medicines found in our database for {disease}.\nWikipedia info: {summary}"
                            else:
                                return f"No medicines found in our database for {disease}, and no Wikipedia info available."
                        summary = fetch_wikipedia_summary(disease)
                        response = f"Recommended medicines for {disease}: {', '.join(drugs)}"
                        if summary:
                            response += f"\nInfo: {summary}"
                        return response
        for alias, real_disease in disease_aliases.items():
            if alias in text:
                drugs = suggest_drug_for_disease(df, real_disease)
                if not drugs or (len(drugs) == 1 and 'no drug found' in drugs[0].lower()):
                    summary = fetch_wikipedia_summary(real_disease)
                    if summary:
                        return f"No medicines found in our database for {real_disease}.\nWikipedia info: {summary}"
                    else:
                        return f"No medicines found in our database for {real_disease}, and no Wikipedia info available."
                summary = fetch_wikipedia_summary(real_disease)
                response = f"Recommended medicines for {real_disease}: {', '.join(drugs)}"
                if summary:
                    response += f"\nInfo: {summary}"
                return response
        # Fuzzy match for symptoms (e.g., 'medicines for headache')
        symptom_aliases = {
            'headache': 'Headache',
            'stomach pain': 'Abdominal Pain',
            'joint pain': 'Joint Pain',
            "mucoid sputum": "mucoid_sputum",
            "high fever": "high_fever",
            "shortness of breath": "breathlessness"
            # Add more as needed
        }
        for alias, real_disease in symptom_aliases.items():
            if alias in text:
                drugs = suggest_drug_for_disease(df, real_disease)
                if not drugs or (len(drugs) == 1 and 'no drug found' in drugs[0].lower()):
                    summary = fetch_wikipedia_summary(real_disease)
                    if summary:
                        return f"No medicines found in our database for {real_disease}.\nWikipedia info: {summary}"
                    else:
                        return f"No medicines found in our database for {real_disease}, and no Wikipedia info available."
                summary = fetch_wikipedia_summary(real_disease)
                response = f"Recommended medicines for {real_disease}: {', '.join(drugs)}"
                if summary:
                    response += f"\nInfo: {summary}"
                return response
        # Substring match for disease names in user input
        for disease in df['disease'].unique():
            disease_lower = disease.lower()
            if disease_lower in text:
                drugs = suggest_drug_for_disease(df, disease)
                if not drugs or (len(drugs) == 1 and 'no drug found' in drugs[0].lower()):
                    summary = fetch_wikipedia_summary(disease)
                    if summary:
                        return f"No medicines found in our database for {disease}.\nWikipedia info: {summary}"
                    else:
                        return f"No medicines found in our database for {disease}, and no Wikipedia info available."
                summary = fetch_wikipedia_summary(disease)
                response = f"Recommended medicines for {disease}: {', '.join(drugs)}"
                if summary:
                    response += f"\nInfo: {summary}"
                return response
        # Generalized: For any query containing 'medicine' (or variants) and a disease name, always try to extract the disease name(s) and fetch from Wikipedia if not found in the CSV
        import re
        # Try to extract disease name(s) after 'medicine for', 'medicines for', 'drug for', etc. (support comma- and 'and'-separated)
        med_for_match = re.search(r"(?:medicines?|medcines?|medcine|medicin|drugs?) for ([a-zA-Z0-9 ,\-and]+)", text)
        if med_for_match:
            disease_query = med_for_match.group(1).strip()
            # Split on commas, 'and' (with or without spaces), and also handle cases like 'malariaandtyphoid'
            disease_list = re.split(r",|\band\b| and |and", disease_query)
            # Remove empty and normalize
            disease_list = [d.strip() for d in disease_list if d.strip()]
            print(f"[DEBUG] Extracted disease list: {disease_list}")
            responses = []
            for disease_item in disease_list:
                disease_item_lower = disease_item.lower()
                disease_item_norm = disease_item_lower.strip().replace(' ', '')
                # Try normalization and full/substring match
                matched_diseases = [d for d in df['disease'].unique() if disease_item_norm == d.lower().replace(' ', '') or disease_item_norm in d.lower().replace(' ', '')]
                # If not found, try substring match (user input is substring of CSV disease name)
                if not matched_diseases:
                    matched_diseases = [d for d in df['disease'].unique() if disease_item_lower in d.lower()]
                print(f"[DEBUG] Matching '{disease_item}' (normalized: '{disease_item_norm}') to: {matched_diseases}")
                if not matched_diseases:
                    best_match = fuzzy_match_disease(disease_item_norm, [d.lower().replace(' ', '') for d in df['disease'].unique()])
                    print(f"[DEBUG] Fuzzy match for '{disease_item_norm}': {best_match}")
                    if best_match:
                        matched_diseases = [d for d in df['disease'].unique() if d.lower().replace(' ', '') == best_match]
                if matched_diseases:
                    found_csv = False
                    for matched_disease in matched_diseases:
                        drugs = suggest_drug_for_disease(df, matched_disease)
                        unique_drugs = list(dict.fromkeys(drugs))
                        print(f"[DEBUG] Drugs for '{matched_disease}': {unique_drugs}")
                        if unique_drugs and not (len(unique_drugs) == 1 and 'no drug found' in unique_drugs[0].lower()):
                            found_csv = True
                            summary = fetch_wikipedia_summary(matched_disease)
                            resp = f"Recommended medicines for {matched_disease}: {', '.join(unique_drugs)}"
                            if summary:
                                resp += f"\nInfo: {summary}"
                            responses.append(resp)
                    if not found_csv:
                        summary = fetch_wikipedia_summary(disease_item)
                        if summary:
                            responses.append(f"No medicines found in our database for {disease_item}.\nWikipedia info: {summary}")
                        else:
                            responses.append(f"No medicines found in our database for {disease_item}, and no Wikipedia info available.")
                else:
                    summary = fetch_wikipedia_summary(disease_item)
                    if summary:
                        responses.append(f"No medicines found in our database for {disease_item}.\nWikipedia info: {summary}")
                    else:
                        responses.append(f"No medicines found in our database for {disease_item}, and no Wikipedia info available.")
            if responses:
                return "\n\n".join(responses)
            else:
                return "No medicines found in our database for the diseases you mentioned, and no Wikipedia info available."
        # Special handling for 'cold' and common variants
        if "cold" in text:
            drugs = suggest_drug_for_disease(df, "Cold Symptoms")
            if not drugs or (len(drugs) == 1 and 'no drug found' in drugs[0].lower()):
                summary = fetch_wikipedia_summary("Cold Symptoms")
                if summary:
                    return f"No medicines found in our database for Cold Symptoms.\nWikipedia info: {summary}"
                else:
                    return f"No medicines found in our database for Cold Symptoms, and no Wikipedia info available."
            summary = fetch_wikipedia_summary("Cold Symptoms")
            response = f"Recommended medicines for Cold Symptoms: {', '.join(drugs)}"
            if summary:
                response += f"\nInfo: {summary}"
            return response
        # Otherwise, try fuzzy match to disease names
        best_match = fuzzy_match_disease(text, [d.lower() for d in df['disease'].unique()])
        if best_match:
            orig_disease = next(d for d in df['disease'].unique() if d.lower() == best_match)
            drugs = suggest_drug_for_disease(df, orig_disease)
            if not drugs or (len(drugs) == 1 and 'no drug found' in drugs[0].lower()):
                summary = fetch_wikipedia_summary(orig_disease)
                if summary:
                    return f"No medicines found in our database for {orig_disease}.\nWikipedia info: {summary}"
                else:
                    return f"No medicines found in our database for {orig_disease}, and no Wikipedia info available."
            summary = fetch_wikipedia_summary(orig_disease)
            response = f"Recommended medicines for {orig_disease}: {', '.join(drugs)}"
            if summary:
                response += f"\nInfo: {summary}"
            return response
        return "Please tell me the disease name so I can suggest medicines."

    # Direct disease name input for medicine recommendation (only if input is a single disease name, not a list of symptoms)
    for disease in df['disease'].unique():
        disease_lower = disease.lower()
        # Only match if the entire input is the disease name (not a substring or comma-separated list)
        if text.strip() == disease_lower:
            drugs = suggest_drug_for_disease(df, disease)
            summary = fetch_wikipedia_summary(disease)
            response = f"Recommended medicines for {disease}: {', '.join(drugs)}"
            if summary:
                response += f"\nInfo: {summary}"
            return response
    # Fuzzy match: if user input is a common alias, map to closest disease name
    disease_aliases = {
        'cold': 'Cold Symptoms',
        'common cold': 'Cold Symptoms',
        'cough': 'Cough',
        'fever': 'Fever',
        # Add more as needed
    }
    if text.strip() in disease_aliases:
        real_disease = disease_aliases[text.strip()]
        drugs = suggest_drug_for_disease(df, real_disease)
        summary = fetch_wikipedia_summary(real_disease)
        response = f"Recommended medicines for {real_disease}: {', '.join(drugs)}"
        if summary:
            response += f"\nInfo: {summary}"
        return response

    # Reset handling if conversation is over
    response = ""
    # 1. Handle thanks
    if "thanks" in input_sentence.lower() or "thank you" in input_sentence.lower():
        return "You're welcome!"

    # 2. List symptoms intent
    # If user asks for symptoms of a specific disease, first check model, then Wikipedia
    import re
    symptom_match = re.search(r"symptoms? (?:of|for) ([a-zA-Z0-9 \-]+)", input_sentence.lower())
    if symptom_match:
        disease_query = symptom_match.group(1).strip()
        # Try to find symptoms from the model (Training.csv or similar)
        try:
            training_df = pd.read_csv(r"C:\Users\deepl\Downloads\Deepika NMIT\swastyaai_app\data\Training.csv")
            disease_row = training_df[training_df['prognosis'].str.lower() == disease_query.lower()]
            if not disease_row.empty:
                # List symptoms (columns with value 1)
                symptoms = [col.replace('_', ' ') for col in training_df.columns if col not in ['prognosis'] and disease_row.iloc[0][col] == 1]
                if symptoms:
                    return f"Symptoms of {disease_query.title()}:\n- " + "\n- ".join(symptoms)
        except Exception as e:
            pass
        # If not found in model, fetch from Wikipedia
        summary = fetch_wikipedia_summary(disease_query + " symptoms")
        if not summary:
            summary = fetch_wikipedia_summary(disease_query)
        if summary:
            return f"Symptoms of {disease_query.title()}:\n{summary}"
        else:
            return f"Sorry, I couldn't find symptom information for {disease_query}."
    if "symptom" in input_sentence.lower():
        symptoms_list = ", ".join(common_symptoms)
        return f"The possible symptoms are: {symptoms_list}"
# Removed duplicate respond_to_greeting and respond_to_wellbeing definitions to fix indentation error.

    # 3. Greeting detection and wellbeing follow-up
    global asked_about_wellbeing

    # Always check for greeting, and reset wellbeing state if user greets again
    greeting_response = respond_to_greeting(input_sentence)
    if greeting_response:
        asked_about_wellbeing = True
        expecting_symptoms = False
        return greeting_response

    # If we have just asked about wellbeing, expect a wellbeing response
    if asked_about_wellbeing:
        wellbeing_response = respond_to_wellbeing(input_sentence)
        if wellbeing_response:
            if "glad" in wellbeing_response or "Take care" in wellbeing_response:
                asked_about_wellbeing = False
                expecting_symptoms = False
                return wellbeing_response
            return wellbeing_response
        # Robust symptom extraction: match ignoring spaces, case, and partial matches
        input_symptoms = [s.strip().lower().replace(' ', '_') for s in re.split(r',|and', input_sentence)]
        detected_symptoms.clear()
        for user_symptom in input_symptoms:
            for known_symptom in common_symptoms:
                if user_symptom in known_symptom or known_symptom in user_symptom:
                    detected_symptoms.append(known_symptom)
        detected_symptoms = list(set(detected_symptoms))
        print(f"[DEBUG] Detected symptoms: {detected_symptoms}")
        if detected_symptoms:
            asked_about_wellbeing = False
            expecting_symptoms = False
            if len(detected_symptoms) < 3:
                return "Please tell me about at least three symptoms to make a prediction."
            top_preds = predict_top_diseases(detected_symptoms, top_n=3)
            response = "Based on your symptoms, the top possible diseases are:<br><ul>"
            for disease in top_preds:
                summary = fetch_wikipedia_summary(disease)
                response += f"<li><b>{disease}</b><br>"
                if summary:
                    response += f"{summary}<br>"
                response += "</li>"
            response += "</ul>If you want medicine recommendations, please mention the disease name."
            return response
        return "Can you tell me how you're feeling or describe your symptoms?"

    # If user was prompted for symptoms after negative wellbeing, treat next input as symptoms
    if expecting_symptoms:
        # Robust symptom extraction: match ignoring spaces, case, and partial matches
        input_symptoms = [s.strip().lower().replace(' ', '_') for s in re.split(r',|and', input_sentence)]
        detected_symptoms.clear()
        for user_symptom in input_symptoms:
            for known_symptom in common_symptoms:
                if user_symptom in known_symptom or known_symptom in user_symptom:
                    detected_symptoms.append(known_symptom)
        detected_symptoms = list(set(detected_symptoms))
        print(f"[DEBUG] Detected symptoms: {detected_symptoms}")
        if detected_symptoms:
            expecting_symptoms = False
            asked_about_wellbeing = False
            if len(detected_symptoms) < 3:
                return f"Please tell me about at least three symptoms to make a prediction. (Detected: {', '.join(detected_symptoms)})"
            top_preds = predict_top_diseases(detected_symptoms, top_n=3)
            response = "Based on your symptoms, the top possible diseases are:<br><ul>"
            for disease in top_preds:
                summary = fetch_wikipedia_summary(disease)
                response += f"<li><b>{disease}</b><br>"
                if summary:
                    response += f"{summary}<br>"
                response += "</li>"
            response += "</ul>If you want medicine recommendations, please mention the disease name."
            return response
        return "Please describe your symptoms in more detail."
    # Standalone symptom input (not in a wellbeing flow)
    # If user input looks like a comma-separated symptom list, reset detected_symptoms and extract new ones
    if ',' in input_sentence or ' and ' in input_sentence:
        # Robust symptom extraction: match ignoring spaces, case, and partial matches
        input_symptoms = [s.strip().lower().replace(' ', '_') for s in re.split(r',|and', input_sentence)]
        detected_symptoms.clear()
        for user_symptom in input_symptoms:
            for known_symptom in common_symptoms:
                if user_symptom in known_symptom or known_symptom in user_symptom:
                    detected_symptoms.append(known_symptom)
        detected_symptoms = list(set(detected_symptoms))
        print(f"[DEBUG] Detected symptoms: {detected_symptoms}")
        if len(detected_symptoms) >= 3:
            top_preds = predict_top_diseases(detected_symptoms, top_n=3)
            response = "Based on your symptoms, the top possible diseases are:<br><ul>"
            for disease in top_preds:
                summary = fetch_wikipedia_summary(disease)
                response += f"<li><b>{disease}</b><br>"
                if summary:
                    response += f"{summary}<br>"
                response += "</li>"
            response += "</ul>If you want medicine recommendations, please mention the disease name."
            return response
        elif len(detected_symptoms) > 0:
            return "Please tell me about at least three symptoms to make a prediction."
        else:
            return "I couldn't recognize any symptoms. Please try again with different words."

    # If no conditions match, ask for symptoms again
    return "Please describe your symptoms, or let me know how I can assist you further."
app.secret_key = 'yoursecretkey'  # needed for flash()

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email=%s AND password=%s', (email, password))
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['userid'] = account['userid']
            session['username'] = account['name']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            message = 'Incorrect email or password!'
    return render_template('login.html', message=message)


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email=%s', (email,))
        account = cursor.fetchone()

        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not name or not password or not email:
            message = 'Please fill out the form!'
        else:
            cursor.execute(
                'INSERT INTO user (name, email, password) VALUES (%s, %s, %s)',
                (name, email, password)
            )
            mysql.connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', message=message)


@app.route('/dashboard') 
def dashboard():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    username = session.get('username')  # <-- change here
    return render_template('dashboard.html', username=username)

@app.route('/save_bmi', methods=['POST'])
def save_bmi():
    if 'loggedin' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    data = request.get_json()
    height = data.get('height')
    weight = data.get('weight')
    bmi = data.get('bmi')
    userid = session['userid']

    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO bmi_records (userid, height, weight, bmi) VALUES (%s, %s, %s, %s)', (userid, height, weight, bmi))
    mysql.connection.commit()
    return jsonify({"status": "success"})





@app.route('/chat', methods=['POST'])
def chat():
    if not session.get('loggedin'):
        return jsonify({"response": "Please login first."}), 401

    data = request.get_json()
    if not data:
        return jsonify({"response": "Invalid request."}), 400

    symptom = data.get('symptom', '').strip()
    if not symptom:
        return jsonify({"response": "Please provide symptoms."}), 400

    # Optional: limit symptom length to prevent abuse
    if len(symptom) > 500:
        return jsonify({"response": "Input too long."}), 400

    try:
        reply = chatbot_response(symptom)
        
    except Exception as e:
        # Log the error
        app.logger.error(f"Chatbot error: {e}")
        return jsonify({"response": "Sorry, something went wrong."}), 500

    return jsonify({"response": reply}), 200


@app.route('/save_bp_sugar', methods=['POST'])
def save_bp_sugar():
    if 'loggedin' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    data = request.get_json()
    sys = data.get('sys')
    dia = data.get('dia')
    sugar = data.get('sugar')
    userid = session['userid']

    if sys is None or dia is None or sugar is None:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute(
        'INSERT INTO bp_sugar_records (userid, systolic, diastolic, blood_sugar) VALUES (%s, %s, %s, %s)',
        (userid, sys, dia, sugar)
    )
    mysql.connection.commit()

    return jsonify({"status": "success", "message": "BP and sugar readings saved successfully"})


# API for hospital list by pincode
@app.route('/teleconsult', methods=['POST'])
def teleconsult():
    user_id = session.get('userid', 1)
    pincode = request.form.get('pincode', '').strip()
    city = request.form.get('city', '').strip()
    print(f"[DEBUG] /teleconsult called with user_id={user_id}, pincode={pincode}, city={city}")
    file_path = os.path.join('data', 'hospitals.xlsx')
    hospitals_list = extract_hospitals_by_pincode_excel(file_path, pincode, city)
    print(f"[DEBUG] hospitals_list: {hospitals_list}")
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO teleconsultations (user_id, pincode, city)
            VALUES (%s, %s, %s)
        """, (user_id, pincode, city))
        mysql.connection.commit()
        consult_id = cursor.lastrowid
        print(f"[DEBUG] Inserted teleconsultation with consult_id={consult_id}")
        for hospital in hospitals_list:
            cursor.execute("""
                INSERT INTO suggested_hospitals (consult_id, hospital_name, address)
                VALUES (%s, %s, %s)
            """, (
                consult_id,
                hospital.get('hospital name', ''),
                hospital.get('address', '')
            ))
        mysql.connection.commit()
        print(f"[DEBUG] Inserted {len(hospitals_list)} hospitals for consult_id={consult_id}")
        return jsonify({
            "status": "success",
            "hospitals": hospitals_list
        })
    except Exception as e:
        print(f"[ERROR] teleconsult DB error: {e}")
        return jsonify({"status": "error", "message": str(e)})


@app.route('/hospitals', methods=['GET'])
def get_hospitals():
    pincode = request.args.get('pincode')
    if not pincode:
        return jsonify({"hospitals": [], "error": "Pincode parameter missing"}), 400

    file_path = os.path.join('data', 'hospitals.xlsx')
    try:
        hospitals = extract_hospitals_by_pincode_excel(file_path, pincode)
        if not hospitals:
            return jsonify({"hospitals": [], "message": "No hospitals found for this pincode"})
        return jsonify({"hospitals": hospitals})
    except Exception as e:
        return jsonify({"hospitals": [], "error": str(e)}), 500


@app.route('/')
def home():
    return render_template('base.html')

if __name__ == '__main__':
    app.run(debug=True)
