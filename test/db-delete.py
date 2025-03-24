import sqlite3


#database delete

# Connect to SQLite database
conn = sqlite3.connect("../new_medical_reports.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM Patients")
cursor.execute("DELETE FROM Tests")
conn.commit()

conn.close()
