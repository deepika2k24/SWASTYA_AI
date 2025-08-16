import pandas as pd

# Load the dataset
df = pd.read_csv('medicines.csv')

# Function to suggest drug for a given disease (matching as a substring)
def suggest_drug_for_disease(df, disease_name):
    """
    Suggests a drug for a given disease, considering the disease name as a substring.

    :param df: DataFrame containing the dataset with diseases and drugs.
    :param disease_name: The name of the disease to query.
    :return: A list of drugs associated with the disease.
    """
    disease_name_lower = disease_name.lower().strip()
    drugs = df[df['disease'].str.lower().str.contains(disease_name_lower)]['drug'].tolist()
    if drugs:
        return list(set(drugs))  # Return unique drugs
    else:
        return ["No drug found for the given disease"]

# Function to find disease associated with a given drug
def find_disease_for_drug(df, drug_name):
    """
    Finds the disease associated with a given drug.

    :param df: DataFrame containing the dataset with diseases and drugs.
    :param drug_name: The name of the drug to query.
    :return: A list of diseases associated with the drug.
    """
    diseases = df[df['drug'].str.lower() == drug_name.lower()]['disease'].tolist()
    if diseases:
        return list(set(diseases))  # Return unique diseases
    else:
        return ["No disease found for the given drug"]

# Example usage:
input_disease = input("Enter Disease: ");  # Replace with the disease name you want to query
input_drug = input("Enter Drug: ");  # Replace with the drug name you want to query

# Print the input for debugging
print(f"Querying for disease: {input_disease}")
print(f"Querying for drug: {input_drug}")

drugs_for_disease = suggest_drug_for_disease(df, input_disease)
diseases_for_drug = find_disease_for_drug(df, input_drug)

print(f"Drugs for '{input_disease}': {drugs_for_disease}")
print(f"Diseases for '{input_drug}': {diseases_for_drug}")
