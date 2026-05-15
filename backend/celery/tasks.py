from backend.models import Appointments, Doctor, Patient, User
from celery import shared_task
import csv
from datetime import datetime
from flask_mail import Message
from flask import current_app

def send_email(to_email, subject, body):
    mail = current_app.extensions['mail']

    msg = Message(subject=subject, recipients=[to_email], body=body, sender="hospital@example.com")

    mail.send(msg)

@shared_task(name='daily_reminder_task')
def daily_reminder_task():
    today = datetime.now().date()

    print(f"[TASK RUNNING] Daily reminder for {today}")

    appointments = Appointments.query.filter_by(Status="Booked").all()

    print(f"[APPOINTMENTS FOUND] {len(appointments)}")

    for appt in appointments:
        try:
            appt_date = datetime.strptime(appt.Date, "%Y-%m-%d").date()
        except:
            continue

        if appt_date == today:
            patient = appt.patient
            user = patient.user
            doctor = appt.doctor

            if user and user.email:
                send_email(user.email, "Appointment Reminder", f"Hello {patient.Patient_name}, you have an appointment with Dr. {doctor.Doctor_name} at {appt.Time}")

@shared_task(name="monthly_report_task")
def monthly_report_task():

    now = datetime.now()
    current_month = now.month
    current_year = now.year

    doctors = Doctor.query.all()

    for doc in doctors:
        monthly_appointments = []

        for appt in doc.appointments:
            try:
                appt_date = datetime.strptime(appt.Date, "%Y-%m-%d")
            except:
                continue

            if appt_date.month == current_month and appt_date.year == current_year:
                monthly_appointments.append(appt)

        html = f"""
        <html>
        <head>
            <title> Monthly Report </title>
        </head>
        <body>
            <h1> Monthly Report - {current_month}/{current_year} </h1>
            <h2> Doctor: Dr. {doc.Doctor_name} </h2>
            <p> Total Appointments: {len(monthly_appointments)} </p>
            <hr>
        """

        for appt in monthly_appointments:
            patient_name = appt.patient.Patient_name

            html += f"""
            <h3> Appointment {appt.Appointment_id}</h3>
            <p> Date: {appt.Date} </p>
            <p> Time: {appt.Time} </p>
            <p> Patient: {patient_name} </p>
            """

            if appt.treatment:
                for t in appt.treatment:
                    html += f"""
                    <p><b> Diagnosis: </b> {t.Diagnosis} </p>
                    <p><b> Tests: </b> {t.Tests_done} </p>
                    <p><b> Prescription: </b> {t.Prescription} </p>
                    <p><b> Medicines: </b> {t.Medicines} </p>
                    """
            else: 
                html += "<p> No treatment data </p>"
            
            html += "<hr>"
        
        html += """
        </body>
        </html>
        """
        import os
        os.makedirs("reports", exist_ok=True)

        filename = f"reports/doctor_{doc.Doctor_id}_report.html"

        with open(filename, "w") as f:
            f.write(html)
        
        print(f"[REPORT GENERATED] {filename}")
        
@shared_task(name="export_csv_task")
def export_csv_task(patient_id):
    appointments = Appointments.query.filter_by(Patient_id=patient_id).all()

    filename = f"patient_{patient_id}.csv"

    filepath = f"exports/{filename}"

    import os
    os.makedirs("exports", exist_ok=True)

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Time", "Doctor", "Status"])

        for a in appointments:
            writer.writerow([a.Date, a.Time, a.Doctor_id, a.Status])
    
    print(f"[CSV READY] {filename}")

    return filename





