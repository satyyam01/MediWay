import sqlite3
import bcrypt
from flask import Flask, jsonify, request

app = Flask(__name__)

class UserDatabase:
    def __init__(self, db_name='users.db'):
        """Initialize database and create users table if not exists"""
        self.db_name = db_name
        self._create_table()

    def _get_connection(self):
        """Create and return a database connection"""
        return sqlite3.connect(self.db_name)

    def _create_table(self):
        """Create users table if not exists"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL
                )
            ''')
            conn.commit()

    def user_exists(self, username):
        """Check if a user exists"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            return cursor.fetchone() is not None

    def register_user(self, username, password, email):
        """Register a new user with hashed password"""
        # Check if user already exists
        if self.user_exists(username):
            return False
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                    (username, hashed_password, email)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def login_user(self, username, password):
        """Verify user credentials"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            if result:
                # Check the provided password against the stored hash
                stored_password = result[0]
                return bcrypt.checkpw(password.encode('utf-8'), stored_password)
            return False

# Initialize UserDatabase
user_db = UserDatabase()

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

@app.route('/register', methods=['POST'])
def register():
    """API Endpoint to register a new user"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({"error": "Missing required fields"}), 400

    if user_db.register_user(username, password, email):
        return jsonify({"message": "User registered successfully"}), 201
    else:
        return jsonify({"error": "Username or email already exists"}), 400

@app.route('/login', methods=['POST'])
def login():
    """API Endpoint to login a user"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    if user_db.login_user(username, password):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

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

if __name__ == '__main__':
    app.run(debug=True)