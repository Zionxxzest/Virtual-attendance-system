
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

DATABASE = "attendance.db"
TIMEZONE = ZoneInfo("Asia/Dhaka")


def get_connection():
    return sqlite3.connect(DATABASE)


def create_attendance_table():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT NOT NULL,
            status TEXT NOT NULL,
            UNIQUE(employee_id, date)
        )
    """)

    connection.commit()
    connection.close()


def mark_attendance(employee_id, employee_name):
    now = datetime.now(TIMEZONE)

    attendance_date = now.strftime("%Y-%m-%d")
    check_in_time = now.strftime("%H:%M:%S")

    connection = get_connection()

    cursor = connection.execute("""
        INSERT OR IGNORE INTO attendance
        (employee_id, employee_name, date, check_in, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        employee_id,
        employee_name,
        attendance_date,
        check_in_time,
        "Present"
    ))

    connection.commit()
    saved = cursor.rowcount == 1
    connection.close()

    if saved:
        print(f"Attendance recorded: {employee_name} at {check_in_time}")
        return True

    print(f"Already marked today: {employee_name}")
    return False


if __name__ == "__main__":
    create_attendance_table()
    print("Attendance database ready!")
