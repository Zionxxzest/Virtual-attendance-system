import sqlite3

DATABASE = "attendance.db"

connection = sqlite3.connect(DATABASE)

cursor = connection.execute("""
    SELECT employee_id, employee_name, date, check_in, status
    FROM attendance
    ORDER BY date DESC, check_in DESC
""")

records = cursor.fetchall()
connection.close()

print("\n========== ATTENDANCE REPORT ==========\n")

if not records:
    print("No attendance records found.")

else:
    for record in records:
        employee_id, name, date, check_in, status = record

        print("--------------------------------------")
        print("Employee ID :", employee_id)
        print("Name        :", name)
        print("Date        :", date)
        print("Check-in    :", check_in)
        print("Status      :", status)

print("\n======================================")
print("Total records:", len(records))