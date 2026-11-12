
import streamlit as st
import sqlite3
import json
from datetime import datetime
from zoneinfo import ZoneInfo

DATABASE = "attendance.db"
TIMEZONE = ZoneInfo("Asia/Dhaka")

st.set_page_config(
    page_title="AI Attendance Dashboard",
    page_icon="📷",
    layout="wide"
)

st.title("📷 AI Face Recognition Attendance")
st.caption("Employee Attendance Management System")

with open("employees.json", "r", encoding="utf-8") as file:
    employees = json.load(file)

today = datetime.now(TIMEZONE).strftime("%Y-%m-%d")

connection = sqlite3.connect(DATABASE)

today_records = connection.execute("""
    SELECT employee_id, employee_name, date, check_in, status
    FROM attendance
    WHERE date = ?
    ORDER BY check_in DESC
""", (today,)).fetchall()

all_records = connection.execute("""
    SELECT employee_id, employee_name, date, check_in, status
    FROM attendance
    ORDER BY date DESC, check_in DESC
""").fetchall()

connection.close()

# Dashboard summary
col1, col2, col3 = st.columns(3)

col1.metric("Registered Employees", len(employees))
col2.metric("Present Today", len(today_records))
col3.metric("Total Attendance Records", len(all_records))

st.divider()

# Today's attendance
st.subheader("Today's Attendance")

if today_records:
    for employee_id, name, date, check_in, status in today_records:
        with st.container(border=True):
            st.write(f"**Employee:** {name}")
            st.write(f"**Employee ID:** {employee_id}")
            st.write(f"**Date:** {date}")
            st.write(f"**Check-in:** {check_in}")
            st.write(f"**Status:** {status}")
else:
    st.info("No attendance recorded today.")

# Attendance history
st.subheader("Attendance History")

if all_records:
    for employee_id, name, date, check_in, status in all_records:
        st.write(
            f"**{name}** ({employee_id}) | "
            f"{date} | {check_in} | {status}"
        )
        st.divider()
else:
    st.info("No attendance history available.")

if st.button("Refresh Dashboard"):
    st.rerun()
