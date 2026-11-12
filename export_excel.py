import sqlite3
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

DATABASE = "attendance.db"
EXCEL_FILE = "attendance.xlsx"

connection = sqlite3.connect(DATABASE)

cursor = connection.execute("""
    SELECT employee_id, employee_name, date, check_in, status
    FROM attendance
    ORDER BY date DESC, check_in DESC
""")

records = cursor.fetchall()
connection.close()

workbook = Workbook()
sheet = workbook.active
sheet.title = "Attendance"

# Add headings
headers = [
    "Employee ID",
    "Employee Name",
    "Date",
    "Check-in Time",
    "Status"
]

sheet.append(headers)

# Style headings
for cell in sheet[1]:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(
        start_color="1F4E78",
        end_color="1F4E78",
        fill_type="solid"
    )
    cell.alignment = Alignment(horizontal="center")

# Add attendance records
for record in records:
    sheet.append(list(record))

# Adjust column widths
widths = [18, 22, 18, 20, 15]

for index, width in enumerate(widths, start=1):
    sheet.column_dimensions[
        sheet.cell(row=1, column=index).column_letter
    ].width = width

# Save Excel file
workbook.save(EXCEL_FILE)

print("Excel report created successfully!")
print("File:", EXCEL_FILE)
print("Total records:", len(records))