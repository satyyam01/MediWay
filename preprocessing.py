#!/usr/bin/env python3
"""
Medical Report PDF Processor
This script extracts information from medical report PDFs, parses the text,
and stores the extracted data in a SQLite database.
"""

import os
import re
import sqlite3
from pdf2image import convert_from_path
from PIL import Image
import pytesseract


# Uncomment the line below if using Windows and specify your Tesseract path
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class MedicalReportProcessor:

    # Add this method to your existing MedicalReportProcessor class
    def _get_connection(self):
        """Helper method to get a database connection."""
        return sqlite3.connect(self.db_name, timeout=10)


    def __init__(self, db_name="medical_reports.db"):
        """Initialize the processor with database settings."""
        self.db_name = db_name
        self._create_or_verify_db()

    def _create_or_verify_db(self):
        """Create the database schema if it doesn't exist or verify its structure."""
        # First check if database exists
        db_exists = os.path.exists(self.db_name)

        # Connect to database
        conn = sqlite3.connect(self.db_name, timeout=10)
        cursor = conn.cursor()

        if not db_exists:
            # Create new database with our schema
            self._create_tables(cursor)
            print("New database created with required schema.")
        else:
            # Verify existing database structure and alter if needed
            self._verify_and_update_schema(cursor)

        conn.commit()
        cursor.close()
        conn.close()

    def _create_tables(self, cursor):
        """Create the database tables with the correct schema."""
        # Create Patients table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age TEXT,
            gender TEXT,
            lab_no TEXT,
            collected_date TEXT,
            reported_date TEXT
        )
        """)

        # Create Tests table with correct column names
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            test_name TEXT,
            result TEXT,
            unit TEXT,
            reference_interval TEXT,
            reference_interval_upper TEXT,
            FOREIGN KEY (patient_id) REFERENCES Patients (id)
        )
        """)

    def _verify_and_update_schema(self, cursor):
        """Check if the database has the required structure and update if needed."""
        # Check Tests table columns
        cursor.execute("PRAGMA table_info(Tests)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        # Determine what columns we need
        needed_columns = {
            'reference_interval': 'TEXT',
            'reference_interval_upper': 'TEXT',
            'bio_ref_interval_lower': 'TEXT',
            'bio_ref_interval_upper': 'TEXT'
        }

        # Check which columns exist
        for col_name, col_type in needed_columns.items():
            if col_name not in column_names:
                try:
                    cursor.execute(f"ALTER TABLE Tests ADD COLUMN {col_name} {col_type}")
                    print(f"Added missing column: {col_name}")
                except sqlite3.Error as e:
                    print(f"Error adding column {col_name}: {e}")

        print("Database schema verification complete.")

    def extract_first_page_as_image(self, pdf_file, output_file):
        """Extract the first page of a PDF and save it as an image."""
        try:
            # Convert the first page of the PDF to an image
            images = convert_from_path(pdf_file, dpi=300, first_page=1, last_page=1)

            # Save the first page as a PNG image
            images[0].save(output_file, "PNG")
            print(f"First page successfully saved as an image: {output_file}")
            return True
        except Exception as e:
            print(f"Error extracting PDF page: {e}")
            return False

    def extract_text_from_image(self, image_file):
        """Extract text from an image using OCR."""
        try:
            # Open the image using PIL
            image = Image.open(image_file)

            # Extract text using pytesseract
            extracted_text = pytesseract.image_to_string(image)
            print("Text extraction complete.")
            return extracted_text
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return None

    def parse_report_text(self, text):
        """Parse the extracted text into structured data."""
        # Split into lines for processing
        lines = text.split('\n')

        # Extract Patient Details
        patient_details = {}
        for line in lines:
            if "Name :" in line:
                name_match = re.search(r"Name :\s*(.+?)(\sLab|$)", line)
                patient_details["Name"] = name_match.group(1).strip() if name_match else None
            if "Lab No. :" in line:
                lab_no_match = re.search(r"Lab No. :\s*(\d+)", line)
                patient_details["Lab No"] = lab_no_match.group(1).strip() if lab_no_match else None
            if "Age :" in line:
                age_match = re.search(r"Age :\s*(\d+)", line)
                patient_details["Age"] = age_match.group(1).strip() if age_match else None
            if "Gender :" in line:
                gender_match = re.search(r"Gender :\s*(.+)", line)
                patient_details["Gender"] = gender_match.group(1).strip() if gender_match else None
            if "Collected :" in line:
                collected_match = re.search(r"Collected :\s*(.+?)\s", line)
                patient_details["Collected"] = collected_match.group(1).strip() if collected_match else None
            if "Reported :" in line:
                reported_match = re.search(r"Reported :\s*(.+?)\s", line)
                patient_details["Reported"] = reported_match.group(1).strip() if reported_match else None

        # Extract Tests
        tests = []
        for line in lines:
            # Skip lines that are clearly irrelevant
            if any(keyword in line for keyword in ["Lab No. :", "Page :"]):
                continue

            # Match test details with enhanced regex for reference intervals
            match = re.match(r"(.+?)\s+([\d.]+)\s+(\w+/?.*?)\s+([<>]?\d+\.?\d*\s*-?\s*\d*\.?\d*)", line)
            if match:
                test_name = match.group(1).strip()
                result = match.group(2).strip()
                unit = match.group(3).strip()
                ref_interval = match.group(4).strip()

                # Check for ranges and single values
                range_match = re.match(r"([<>]?\d+\.?\d*)\s*-\s*(\d+\.?\d*)", ref_interval)
                if range_match:
                    lower_bound = range_match.group(1)
                    upper_bound = range_match.group(2)
                else:
                    # Handle single values with < or >
                    single_match = re.match(r"([<>])(\d+\.?\d*)", ref_interval)
                    if single_match:
                        symbol = single_match.group(1)
                        value = single_match.group(2)
                        if symbol == "<":
                            # For < values, set lower bound to NA and upper bound to value
                            lower_bound = "NA"
                            upper_bound = value
                        else:  # Must be >
                            lower_bound = value
                            upper_bound = None
                    else:
                        # Regular single value
                        lower_bound = ref_interval
                        upper_bound = None

                test = {
                    "Name": test_name,
                    "Result": result,
                    "Unit": unit,
                    "Reference Interval": {"Lower": lower_bound, "Upper": upper_bound}
                }
                tests.append(test)

        print("Text parsing complete.")
        return {
            "Patient Details": patient_details,
            "Tests": tests
        }

    def insert_data(self, data):
        """Insert the parsed data into the database."""
        try:
            conn = sqlite3.connect(self.db_name, timeout=10)
            cursor = conn.cursor()

            # Insert Patient Details
            patient = data["Patient Details"]
            print("Inserting patient data...")
            cursor.execute("""
            INSERT INTO Patients (name, age, gender, lab_no, collected_date, reported_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                patient.get("Name"),
                patient.get("Age"),
                patient.get("Gender"),
                patient.get("Lab No"),
                patient.get("Collected"),
                patient.get("Reported")
            ))
            patient_id = cursor.lastrowid  # Get the auto-generated patient ID
            print(f"Patient data inserted, Patient ID: {patient_id}")

            # Insert Tests (excluding the last test if it's incomplete)
            if data["Tests"]:
                for test in data["Tests"][:-1]:  # Exclude the last entry which might be incomplete
                    print(f"Inserting test data for {test.get('Name')}...")

                    # Check which columns exist by querying database pragmas
                    cursor.execute("PRAGMA table_info(Tests)")
                    columns = [col[1] for col in cursor.fetchall()]

                    # Adapt our query based on available columns
                    if 'bio_ref_interval_lower' in columns and 'bio_ref_interval_upper' in columns:
                        cursor.execute("""
                        INSERT INTO Tests (patient_id, test_name, result, unit, bio_ref_interval_lower, bio_ref_interval_upper)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            patient_id,
                            test.get("Name"),
                            test.get("Result"),
                            test.get("Unit"),
                            test["Reference Interval"].get("Lower"),
                            test["Reference Interval"].get("Upper")
                        ))
                    else:
                        # Fallback to using reference_interval columns
                        cursor.execute("""
                        INSERT INTO Tests (patient_id, test_name, result, unit, reference_interval, reference_interval_upper)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            patient_id,
                            test.get("Name"),
                            test.get("Result"),
                            test.get("Unit"),
                            test["Reference Interval"].get("Lower"),
                            test["Reference Interval"].get("Upper")
                        ))

                    print(f"Test data inserted for {test.get('Name')}")

            conn.commit()
            print("Data committed to the database.")

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def print_data(self):
        """Fetch and print the stored data from the database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Fetch and print Patient Data
        cursor.execute("SELECT * FROM Patients")
        patients = cursor.fetchall()
        print("\nPatients Data:")
        for patient in patients:
            print(patient)

        # Fetch and print Test Data
        cursor.execute("SELECT * FROM Tests")
        tests = cursor.fetchall()
        print("\nTests Data:")
        for test in tests:
            print(test)

        cursor.close()
        conn.close()

    def process_report(self, pdf_path, temp_image_path="temp_page.png"):
        """Process a medical report PDF file end-to-end."""
        print(f"Processing report: {pdf_path}")

        # Extract the first page as an image
        if not self.extract_first_page_as_image(pdf_path, temp_image_path):
            return False

        # Extract text from the image
        text = self.extract_text_from_image(temp_image_path)
        if not text:
            return False

        # Parse the text
        parsed_data = self.parse_report_text(text)

        # Insert data into the database
        self.insert_data(parsed_data)

        # Clean up temporary image file
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            print(f"Temporary image removed: {temp_image_path}")

        print(f"Report processing complete: {pdf_path}")
        return True


def main():
    """Main function to run the script."""
    # Define input PDF file path
    input_pdf = r"C:\SatyamsFolder\projects\ML\MediWay\data\1.pdf"  # Replace with your PDF file path

    # Create processor instance with a new database name to avoid conflicts
    processor = MedicalReportProcessor(db_name="medical_reports_new.db")

    # Process the report
    processor.process_report(input_pdf)

    # Print the stored data to verify insertion
    processor.print_data()


if __name__ == "__main__":
    main()