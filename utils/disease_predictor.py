import pandas as pd
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
import joblib
import os

# Paths for model and data
MODEL_PATH = "model.pkl"
SYMPTOMS_PATH = "symptoms.pkl"
TRAINING_CSV = r"C:\Users\deepl\Downloads\Deepika NMIT\swastyaai_app\data\Training.csv"
TESTING_CSV = r"C:\Users\deepl\Downloads\Deepika NMIT\swastyaai_app\data\testing.csv"

def train_and_save_model():
    """Train the Naive Bayes model and save it along with symptoms list."""
    training_df = pd.read_csv(TRAINING_CSV).dropna()
    testing_df = pd.read_csv(TESTING_CSV).dropna()

    # Select top 90 symptoms
    top_symptoms = training_df.drop(columns=['prognosis']).sum().sort_values(ascending=False).index[:90]

    X_train = training_df[top_symptoms]
    y_train = training_df['prognosis']
    X_test = testing_df[top_symptoms]
    y_test = testing_df['prognosis']

    model = MultinomialNB()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"✅ Model Accuracy: {accuracy:.2f}")

    # Save model and top_symptoms list
    joblib.dump(model, MODEL_PATH)
    joblib.dump(list(top_symptoms), SYMPTOMS_PATH)
    print("📦 Model and symptoms list saved.")

def load_model():
    """Load the trained model and symptoms list."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SYMPTOMS_PATH):
        print("⚠ Model files not found. Training a new one...")
        train_and_save_model()
    model = joblib.load(MODEL_PATH)
    top_symptoms = joblib.load(SYMPTOMS_PATH)
    return model, top_symptoms

# Load once when imported
model, top_symptoms = load_model()
def predict_top_diseases(symptoms, top_n=3):
    input_data = [1 if symptom in symptoms else 0 for symptom in top_symptoms]
    df = pd.DataFrame([input_data], columns=top_symptoms)
    
    # Get probability distribution over all classes
    probas = model.predict_proba(df)[0]  # shape: (num_classes,)
    
    # Get indices of top_n highest probabilities
    top_indices = probas.argsort()[-top_n:][::-1]
    
    # Map to disease names only (no confidence)
    top_predictions = [str(model.classes_[i]) for i in top_indices]
    return top_predictions

def predict_disease(symptoms):
    """Predict the disease based on symptoms."""
    input_data = [1 if symptom in symptoms else 0 for symptom in top_symptoms]
    df = pd.DataFrame([input_data], columns=top_symptoms)
    prediction = model.predict(df)
    return prediction[0]

def list_symptoms_for_disease(disease_name):
    """List associated symptoms for a given disease."""
    training_df = pd.read_csv(TRAINING_CSV).dropna()
    disease_rows = training_df[training_df['prognosis'] == disease_name]
    symptom_counts = disease_rows[top_symptoms].sum()
    return symptom_counts[symptom_counts > 0].index.tolist()

if __name__ == "__main__":
    train_and_save_model()
