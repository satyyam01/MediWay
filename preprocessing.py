import re
import os
import json
import uuid
import requests
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class MedicalReportProcessor:
    def __init__(self, username, mongo_uri="mongodb://localhost:27017", db_name="mediway"):
        self.username = username  # From Streamlit session
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.patients = self.db["patients"]
        self.tests = self.db["tests"]

    def extract_first_page_as_image(self, pdf_file, output_file):
        try:
            images = convert_from_path(pdf_file, dpi=300, first_page=1, last_page=1)
            images[0].save(output_file, "PNG")
            print(f"First page successfully saved as an image: {output_file}")
            return True
        except Exception as e:
            print(f"Error extracting PDF page: {e}")
            return False

    def extract_text_from_image(self, image_file):
        try:
            image = Image.open(image_file)
            text = pytesseract.image_to_string(image)
            print("Text extraction complete.")
            return text
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return None

    def parse_report_text_llm(self, text):
        if not GROQ_API_KEY:
            print("GROQ_API_KEY not found.")
            return None

        prompt = f"""
You are a medical report parser.

Given the following raw OCR text, extract and return a **strictly valid JSON** object in the below format.

Respond ONLY with the JSON object — no explanation, no extra markdown, and no formatting.

Required Format:
{{
  "Patient Details": {{
    "Collected": "",
    "Reported": ""
  }},
  "Tests": [
    {{
      "Name": "",
      "Result": "",
      "Unit": "",
      "Reference Interval": {{
        "Lower": "",
        "Upper": ""
      }}
    }}
  ]
}}

Ensure:
- All keys are present even if values are empty.
- The response is valid JSON (not markdown).
- If any field is missing, leave its value as an empty string.

Raw OCR Text:
\\n\"\"\"{text}\"\"\"
"""
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "compound-beta",
                    "messages": [
                        {"role": "system", "content": "You extract structured data from medical reports."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2048
                }
            )

            print("==RAW LLM RESPONSE==")
            print(f"Status Code: {response.status_code}")
            print(response.text)

            result = response.json()
            if "choices" not in result:
                raise ValueError("Missing 'choices' in response")

            content = result["choices"][0]["message"]["content"]

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    return json.loads(json_str)
                raise ValueError("No valid JSON block found in LLM response.")

        except Exception as e:
            print("LLM parsing failed:", e)
            return None

    def insert_data(self, data, report_id, name, age, gender):
        try:
            patient = data["Patient Details"]
            patient_doc = {
                "report_id": report_id,
                "username": self.username,
                "name": name,
                "age": age,
                "gender": gender,
                "collected_date": patient.get("Collected"),
                "reported_date": patient.get("Reported")
            }
            self.patients.insert_one(patient_doc)

            for test in data["Tests"]:
                self.tests.insert_one({
                    "report_id": report_id,
                    "username": self.username,
                    "test_name": test.get("Name"),
                    "result": test.get("Result"),
                    "unit": test.get("Unit"),
                    "reference_interval": f"{test['Reference Interval'].get('Lower', '')} - {test['Reference Interval'].get('Upper', '')}"
                })

            print(f"Data committed to MongoDB with report_id: {report_id}")

        except Exception as e:
            print(f"MongoDB error: {e}")

    def process_report(self, pdf_path, name, age, gender, temp_image_path=None):
        print(f"Processing report: {pdf_path}")
        report_id = str(uuid.uuid4())  # Generate unique report_id

        if not temp_image_path:
            temp_image_path = f"temp_page_{report_id[:8]}.png"

        print(f"[DEBUG] Using temp image file: {temp_image_path}")

        if not self.extract_first_page_as_image(pdf_path, temp_image_path):
            return None

        text = self.extract_text_from_image(temp_image_path)
        if not text:
            return None

        parsed_data = self.parse_report_text_llm(text)
        if not parsed_data:
            print("LLM parsing failed, skipping report.")
            return None

        self.insert_data(parsed_data, report_id, name, age, gender)

        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            print(f"Temporary image removed: {temp_image_path}")

        print(f"Report processing complete: {pdf_path}")
        return report_id


# Example CLI testing (not used in Streamlit)
def main():
    input_pdf = r"C:\\SatyamsFolder\\projects\\ML\\MediWay\\data\\1.pdf"
    username = "demo_user"
    processor = MedicalReportProcessor(username=username)
    report_id = processor.process_report(input_pdf, name="Test Name", age=30, gender="Male")
    print("Report ID:", report_id)


if __name__ == "__main__":
    main()
