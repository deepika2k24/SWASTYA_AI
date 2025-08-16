import fitz  # PyMuPDF
import PyPDF2
import re
import os

def find_hospitals(pdf_path, pincode=None, city=None):
    hospitals = []
    # Try PyPDF2 for line-by-line extraction
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                lines = text.split('\n')
                for line in lines:
                    print(f"[DEBUG] PDF Line: {line}")  # Debug: print every line
                    # Flexible pincode matching: ignore spaces, allow variations
                    clean_line = re.sub(r'\s+', '', line)
                    clean_pincode = re.sub(r'\s+', '', pincode) if pincode else None
                    if (clean_pincode and clean_pincode in clean_line) or (city and city.lower() in line.lower()):
                        match = re.search(fr'(.+?)\s*{clean_pincode}', line) if clean_pincode else None
                        if match:
                            hospital_info = match.group(1).strip()+"<br>"
                            hospitals.append(hospital_info)
        if hospitals:
            return hospitals
    except Exception as e:
        print(f"[ERROR] PyPDF2 failed: {e}")
    # Fallback: Try PyMuPDF (fitz) for page-level extraction
    try:
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text = page.get_text()
                if (pincode and pincode in text) or (city and city.lower() in text.lower()):
                    hospitals.append(text.strip())
        return hospitals
    except Exception as e:
        print(f"[ERROR] PyMuPDF failed: {e}")
    return hospitals

def extract_hospitals_by_pincode(pdf_path, target_pincode):
    hospitals = []
    found = False
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line in lines:
                # Remove all non-digit characters from pincode and line for matching
                line_digits = re.sub(r'\D', '', line)
                pincode_digits = re.sub(r'\D', '', target_pincode)
                if pincode_digits and pincode_digits in line_digits:
                    hospitals.append(line.strip())
                    found = True
    if not found:
        print("[DEBUG] No match found. Sample lines from PDF:")
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if not text:
                    continue
                lines = text.split('\n')
                for line in lines[:10]:
                    print(line)
    return hospitals

# Example usage:
# hospitals = find_hospitals('data/hospitals.pdf', pincode='560010', city='Bengaluru')
