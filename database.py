import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)

def fetch_patient_data(lab_no):
    """Fetch patient and test data from the database using Lab No."""
    conn = sqlite3.connect("medical_reports_new.db")
    cursor = conn.cursor()

    # Fetch Patient Details
    cursor.execute("SELECT * FROM Patients WHERE lab_no = ?", (lab_no,))
    patient = cursor.fetchone()

    if not patient:
        conn.close()
        return None

    patient_id = patient[0]  # Primary Key of the patient

    # Fetch Tests Data
    cursor.execute("SELECT test_name, result, unit, reference_interval, reference_interval_upper FROM Tests WHERE patient_id = ?", (patient_id,))
    tests = cursor.fetchall()

    conn.close()

    return {
        "Patient Details": {
            "Name": patient[1],
            "Age": patient[2],
            "Gender": patient[3],
            "Lab Number": patient[4],
            "Collected Date": patient[5],
            "Reported Date": patient[6]
        },
        "Tests": [
            {
                "Name": test[0],
                "Value": test[1],
                "Unit": test[2],
                "Reference Interval": f"{test[3]} - {test[4]}" if test[4] else test[3]
            }
            for test in tests
        ]
    }

@app.route('/fetch-report', methods=['GET'])
def get_report():
    """API Endpoint to fetch medical reports by Lab Number."""
    lab_no = request.args.get('lab_no')

    if not lab_no:
        return jsonify({"error": "Missing lab_no parameter"}), 400

    report_data = fetch_patient_data(lab_no)

    if report_data is None:
        return jsonify({"error": "No report found for the given Lab Number"}), 404

    return jsonify(report_data)

if __name__ == '__main__':  # Correct
    app.run(debug=True)