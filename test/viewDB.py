import sqlite3

# Connect to the database
conn = sqlite3.connect("../medical_reports_new.db")
cursor = conn.cursor()

# Fetch and print Patients table
print("Patients Table:")
cursor.execute("SELECT * FROM Patients")
patients = cursor.fetchall()
for row in patients:
    print(row)

# Fetch and print Tests table
print("\nTests Table:")
cursor.execute("SELECT * FROM Tests")
tests = cursor.fetchall()
for row in tests:
    print(row)

# Close the connection
conn.close()
