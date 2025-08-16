import spacy

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Define the symptoms
keywords = [
    'itching', 'skin_rash', 'nodal_skin_eruptions', 'continuous_sneezing', 'shivering',
    'chills', 'joint_pain', 'stomach_pain', 'acidity', 'ulcers_on_tongue',
    'muscle_wasting', 'vomiting', 'burning_micturition', 'spotting_ urination', 'fatigue',
    'weight_gain', 'anxiety', 'cold_hands_and_feets', 'mood_swings', 'weight_loss',
    'restlessness', 'lethargy', 'patches_in_throat', 'irregular_sugar_level', 'cough',
    'high_fever', 'sunken_eyes', 'breathlessness', 'sweating', 'dehydration',
    'indigestion', 'headache', 'yellowish_skin', 'dark_urine', 'nausea', 'loss_of_appetite',
    'pain_behind_the_eyes', 'back_pain', 'constipation', 'abdominal_pain', 'diarrhoea',
    'mild_fever', 'yellow_urine', 'yellowing_of_eyes', 'acute_liver_failure', 'fluid_overload',
    'swelling_of_stomach', 'swelled_lymph_nodes', 'malaise', 'blurred_and_distorted_vision',
    'phlegm', 'throat_irritation', 'redness_of_eyes', 'sinus_pressure', 'runny_nose',
    'congestion', 'chest_pain', 'weakness_in_limbs', 'fast_heart_rate', 'pain_during_bowel_movements',
    'pain_in_anal_region', 'bloody_stool', 'irritation_in_anus', 'neck_pain', 'dizziness',
    'cramps', 'bruising', 'obesity', 'swollen_legs', 'swollen_blood_vessels', 'puffy_face_and_eyes',
    'enlarged_thyroid', 'brittle_nails', 'swollen_extremeties', 'excessive_hunger',
    'extra_marital_contacts', 'drying_and_tingling_lips', 'slurred_speech', 'knee_pain',
    'hip_joint_pain', 'muscle_weakness', 'stiff_neck', 'swelling_joints', 'movement_stiffness',
    'spinning_movements', 'loss_of_balance', 'unsteadiness', 'weakness_of_one_body_side',
    'loss_of_smell', 'bladder_discomfort', 'foul_smell_of urine', 'continuous_feel_of_urine',
    'passage_of_gases', 'internal_itching', 'toxic_look_(typhos)', 'depression', 'irritability',
    'muscle_pain', 'altered_sensorium', 'red_spots_over_body', 'belly_pain', 'abnormal_menstruation',
    'dischromic _patches', 'watering_from_eyes', 'increased_appetite', 'polyuria', 'family_history',
    'mucoid_sputum', 'rusty_sputum', 'lack_of_concentration', 'visual_disturbances',
    'receiving_blood_transfusion', 'receiving_unsterile_injections', 'coma', 'stomach_bleeding',
    'distention_of_abdomen', 'history_of_alcohol_consumption', 'fluid_overload', 'blood_in_sputum',
    'prominent_veins_on_calf', 'palpitations', 'painful_walking', 'pus_filled_pimples', 'blackheads',
    'scurring', 'skin_peeling', 'silver_like_dusting', 'small_dents_in_nails', 'inflammatory_nails',
    'blister', 'red_sore_around_nose', 'yellow_crust_ooze'
]

# User-friendly symptom mapping
user_symptom_map = {
    'fever': 'high_fever',
    'cold': 'runny_nose',
    'flu': 'high_fever',
    'chills': 'chills',
    'cough': 'cough',
    'nausea': 'nausea',
    'vomit': 'vomiting',
    'headache': 'headache',
    'sore throat': 'throat_irritation',
    'throat pain': 'throat_irritation',
    'body pain': 'muscle_pain',
    'muscle pain': 'muscle_pain',
    'fatigue': 'fatigue',
    'tired': 'fatigue',
    'runny nose': 'runny_nose',
    'sneezing': 'continuous_sneezing',
    'diarrhea': 'diarrhoea',
    'loose motion': 'diarrhoea',
    'stomach pain': 'stomach_pain',
    'abdominal pain': 'abdominal_pain',
    'joint pain': 'joint_pain',
    'chest pain': 'chest_pain',
    'rash': 'skin_rash',
    'itch': 'itching',
    'itching': 'itching',
    'dizzy': 'dizziness',
    'dizziness': 'dizziness',
    'sweating': 'sweating',
    'mild fever': 'mild_fever',
    'high fever': 'high_fever',
    'loss of appetite': 'loss_of_appetite',
    'weight loss': 'weight_loss',
    'weight gain': 'weight_gain',
    'anxiety': 'anxiety',
    'depression': 'depression',
    'irritability': 'irritability',
    # Add more mappings as needed
}

SYMPTOM_SYNONYMS = {
    # Fever-related
    "fever": "high_fever",
    "high temperature": "high_fever",
    "mild fever": "mild_fever",
    "low fever": "mild_fever",
    "chills": "chills",
    "shivering": "shivering",
    "hot flashes": "high_fever",
    # Respiratory
    "cough": "cough",
    "dry cough": "cough",
    "wet cough": "cough",
    "runny nose": "runny_nose",
    "blocked nose": "congestion",
    "nasal congestion": "congestion",
    "sneezing": "continuous_sneezing",
    "difficulty breathing": "breathlessness",
    "shortness of breath": "breathlessness",
    # Gastrointestinal
    "stomach ache": "abdominal_pain",
    "tummy pain": "abdominal_pain",
    "belly pain": "belly_pain",
    "nausea": "nausea",
    "feeling sick": "nausea",
    "vomiting": "vomiting",
    "throwing up": "vomiting",
    "diarrhea": "diarrhoea",
    "loose motions": "diarrhoea",
    "constipation": "constipation",
    "acid reflux": "acidity",
    "heartburn": "acidity",
    # Skin
    "rash": "skin_rash",
    "skin rash": "skin_rash",
    "itchy skin": "itching",
    "itchiness": "itching",
    "red spots": "red_spots_over_body",
    "pimples": "pus_filled_pimples",
    "boils": "boils",
    # General malaise
    "fatigue": "fatigue",
    "tiredness": "fatigue",
    "weakness": "weakness_in_limbs",
    "body ache": "joint_pain",
    "muscle pain": "muscle_pain",
    "joint pain": "joint_pain",
    "headache": "headache",
    "dizziness": "dizziness",
    # Urinary
    "pain while urinating": "burning_micturition",
    "burning sensation while urinating": "burning_micturition",
    "frequent urination": "polyuria",
    "smelly urine": "foul_smell_of_urine",
    # Eyes
    "yellow eyes": "yellowing_of_eyes",
    "yellow skin": "yellowing_of_eyes",
    "blurry vision": "blurred_and_distorted_vision",
    "loss of eyesight": "blurred_and_distorted_vision",
    # Mental health / Neurological
    "anxiety": "anxiety",
    "depression": "depression",
    "irritability": "irritability",
    "mood swings": "mood_swings",
    "loss of balance": "loss_of_balance",
    "unsteadiness": "unsteadiness",
    # Others
    "swelling of stomach": "swelling_of_stomach",
    "puffy face": "puffy_face_and_eyes",
    "dry lips": "drying_and_tingling_lips",
    "slurred speech": "slurred_speech",
    "neck pain": "neck_pain",
    "knee pain": "knee_pain",
    "hip joint pain": "hip_joint_pain",
}

# Function to extract symptoms from a sentence
def extract_symptoms(sentence):
    doc = nlp(sentence.lower())  # Convert the sentence to lowercase for case insensitivity
    symptoms = set()  # Use a set to automatically handle duplicates

    # Map user-friendly terms and synonyms to model symptoms
    for phrase, model_symptom in SYMPTOM_SYNONYMS.items():
        if phrase in sentence.lower():
            symptoms.add(model_symptom)

    # Iterate through the tokens in the document
    for token in doc:
        # Check if the token's lemma or text matches any of the keywords
        if token.lemma_.lower() in keywords:
            symptoms.add(token.lemma_)
        elif token.text.lower() in keywords:
            symptoms.add(token.text)
    
    # Check for substring matches of keywords in the sentence
    for keyword in keywords:
        if keyword in doc.text:
            symptoms.add(keyword)
    
    return list(symptoms)  # Return the symptoms as a list
