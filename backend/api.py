from flask import Flask, request, jsonify, session, redirect, render_template
from flask import current_app as app
from backend.models import *
from datetime import datetime
from backend.celery.tasks import export_csv_task
from flask import send_file
import os
from backend.celery.tasks import monthly_report_task
from flask_mail import Message
from flask_mail import Mail

mail = Mail()
cache = app.cache

def availability_cache_key():
    return request.path

def patient_search_cache_key():
    return request.full_path

@app.route('/test-mail')
def test_mail():
    msg = Message(subject="Test Mail", recipients=["test@gamil.com"], body="MailHog is working!", sender="hospital@gmail.com")

    mail.send(msg)
    return "Mail Sent!"

@app.route('/doctor/report')
def doctor_report():
    if session.get('type') != 'doctor':
        return jsonify({"message": "Only Doctors can access this page!"}), 403
    
    user_id = session.get('user_id')

    doctor = Doctor.query.filter_by(user_id=user_id).first()

    if not doctor:
        return {"message": "Doctor not found!"}, 404
    
    filename = f"reports/doctor_{doctor.Doctor_id}_report.html"

    if not os.path.exists(filename):
        monthly_report_task.delay()
        return {"message": "Report is being generated. Try again in few seconds!"}

    return send_file(filename, as_attachment=True)


@app.route('/download')
def download_file_patient():
    if session.get('type') != 'patient':
        return jsonify({"message":"Only Patients can access this page!"}), 403
    
    user_id = session.get('user_id')
    patient = Patient.query.filter_by(user_id=user_id).first()

    filename = f"patient_{patient.Patient_id}.csv"
    filepath = f"exports/{filename}"

    return send_file(filepath, as_attachment=True)

@app.route('/export')
def export():
    if session.get('type') != 'patient':
        return jsonify({"message":"Only Patients can access this page!"})
    
    user_id = session.get('user_id')

    patient = Patient.query.filter_by(user_id=user_id).first()

    if not patient:
        return jsonify({"message":"Patient not found!"}), 404
    
    export_csv_task.delay(patient.Patient_id)

    return {"message":"Export started!"}


@app.route('/task/<task_id>')
def task_status(task_id):
    from celery.result import AsyncResult

    task = AsyncResult(task_id)

    if task.state == "SUCCESS":
        return {
            "status": task.state,
            "download_url": f"/download/{task.result}"
        }

    return {
        "status": task.state
    }

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.json
            username = data.get('username')
            password = data.get('password')

            user = User.query.filter_by(username=username, password=password).first()
            
            if not user:
                return jsonify({"message":"Invalid Credentials"}), 401
            
            if user.Is_blacklisted == True:
                return jsonify({"message": "Blacklisted by the hospital. Login Restricted!"}), 403

            session["user_id"] = user.id
            session["type"] = user.type
            session.permanent = True

            return jsonify({"message":"Login Successful! Redirecting...", "type":user.type})
        except Exception as e:
            print("ERROR:", e)
            return jsonify({"message":"Server Error"}), 500

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/check', methods=['POST'])
def check():
    if "user_id" not in session:
        return jsonify({"message":"User not logged in, please login again!"}), 401
    return jsonify({"user_id":session["user_id"],  "type":session["type"]})

@app.route('/admin_dashboard', methods=['GET'])
def admin():
    if session.get('type') != 'admin':
        return jsonify({"message":"Only Admin can access this page!"}), 401
    return render_template('admin_dashboard.html')

@app.route('/doctor_dashboard', methods=['GET'])
def doctor():
    if session.get('type') != 'doctor':
        return jsonify({"message":"Only Doctors can access this page!"}), 401
    return render_template('doctor_dashboard.html')

@app.route('/patient_dashboard', methods=['GET'])
def patient():
    if session.get('type') != 'patient':
        return jsonify({"message":"Only patients can access this page!"}), 401
    
    return render_template('patient_dashboard.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == "POST":
        try:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            user = User.query.filter_by(email=email).first()
            if user:
                return jsonify({"message":"This user already exists. Kindly login!"}), 400
            new_user = User(username=username, email=email, password=password, type='patient')
            db.session.add(new_user)
            db.session.commit()
            patient = Patient(Patient_name = username, user_id = new_user.id)
            db.session.add(patient)
            db.session.commit()
            return jsonify({"message":"Patient registered successfully! Redirecting..."}), 200
        except Exception as e:
            print("ERROR:", e)
            return jsonify({"message":"Registration Failed. Try Again!"}), 500

    return render_template('register.html')

@app.route('/admin/search')
@cache.cached(timeout = 60, key_prefix = patient_search_cache_key)
def admin_search():
    if session.get('type') != 'admin':
        return jsonify({"message":"Only admins can access this page!"}), 401
    
    search = request.args.get('search')

    doctors = Doctor.query.filter(Doctor.Doctor_name.ilike(f"%{search}%")).all()
    patients = Patient.query.filter(Patient.Patient_name.ilike(f"%{search}%")).all()

    def doctor(d):
        return {
            "Doctor_id": d.Doctor_id,
            "Doctor_name": d.Doctor_name,
            "Department_name": d.Department_name,
        }
    
    def patient(p):
        return {
            "Patient_id": p.Patient_id,
            "Patient_name": p.Patient_name,
        }
    
    return jsonify({
        "doctors": [doctor(d) for d in doctors],
        "patients": [patient(p) for p in patients]
    })

@app.route('/admin/data')
def admin_data():
    if session.get('type') != 'admin':
        return jsonify({"message":"Unauthorized"}), 401
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"message": "Unauthorized"}), 403
    
    this_user = User.query.get(user_id)
    
    all_doc = Doctor.query.all()
    all_pat = Patient.query.all()

    upcoming = Appointments.query.filter_by(Status='Booked').all()
    past = Appointments.query.filter_by(Status = 'Completed').all()

    search = request.args.get('search')

    if search:
        doctors = Doctor.query.filter(Doctor.Doctor_name.ilike(f"%{search}%")).all()
        patients = Patient.query.filter(Patient.Patient_name.ilike(f"%{search}%")).all()
    
    else:
        doctors = Doctor.query.all()
        patients = Patient.query.all()

    counts = {
        "total_doc": len(all_doc),
        "total_pat": len(all_pat),
        "upcoming_count": len(upcoming),
        "past_count": len(past)
    }

    def doctor(d):
        return {
            "Doctor_id": d.Doctor_id,
            "Doctor_name": d.Doctor_name,
            "Department_name": d.Department_name,
            "user_id": d.user_id,
            "blacklisted": d.user.Is_blacklisted if d.user else False
        }
    
    def patient(p):
        return {
            "Patient_id": p.Patient_id,
            "Patient_name": p.Patient_name,
            "user_id": p.user_id,
            "blacklisted": p.user.Is_blacklisted if p.user else False
        }
    
    def appointment(a):
        return {
            "Appointment_id": a.Appointment_id,
            "Patient_id": a.patient.Patient_id,
            "doctor_name": a.doctor.Doctor_name,
            "patient_name": a.patient.Patient_name,
            "Status": a.Status,
            "Date": str(a.Date),
            "department_name": a.doctor.Department_name
        }
    
    return jsonify({
        "this_user": {"username":this_user.username},
        "all_doc": [doctor(d) for d in doctors],
        "all_pat": [patient(p) for p in patients],
        "appointments": [appointment(a) for a in upcoming],
        "past_appointments": [appointment(a) for a in past],
        "count": counts
    }), 200
    
@app.route('/admin/add_doctor', methods=['POST'])
def add_doctor():
    if session.get('type') != 'admin':
        return jsonify({"messsage":"Only Admin can access this page"}), 401
    data = request.json
    user = User(username = data.get('username'), email = data.get('email'), password = data.get('password'), type = 'doctor')
    db.session.add(user)
    db.session.commit()

    doctor = Doctor(Doctor_name = data.get('Doctor_name'), Department_name = data.get('Department_name'), 
                    Experience = data.get('Experience'), user_id = user.id)
    db.session.add(doctor)
    db.session.commit()

    return jsonify({"message": "Doctor added successfully!"}), 200

@app.route('/admin/page/add_doctor')
def add_d():
    if session.get('type') != 'admin':
        return jsonify({"message":"Only admin can access this page!"})
    return render_template('create_doctor.html')

@app.route('/admin/view_appointments')
def view_appointments():
    if session.get('type') != 'admin':
        return jsonify({"message": "Only Admin can access this page!"}), 401
    appointments = Appointments.query.all()
    all_appointments = [{'Appointment_id': a.Appointment_id, 'Patient_id': a.Patient_id, 
                                'Doctor_id': a.Doctor_id, 'Date': str(a.Date), 'Time':a.Time, 
                                'Status':a.Status} for a in appointments]
    return jsonify(all_appointments)

@app.route('/admin/blacklist/<int:user_id>', methods=['PUT'])
def blacklisted(user_id):
    if session.get('type') != 'admin':
        return jsonify({"message":"Only Admin can access this page!"}), 401
    
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message":"This user doesn't exist!"}), 404
    if user.type == 'admin':
        return jsonify({"message": "Cannot blacklist admin!"}), 400
    
    user.Is_blacklisted = True
    db.session.commit()

    return jsonify({"message":f"{user.username} has been blacklisted successfully!"}), 200


@app.route('/admin/search_doctor')
def search_d():
    name = request.args.get('name', '')
    doctors = User.query.filter_by(User.type == 'doctor', User.username.like(f"%{name}%")).all()
    return jsonify({'doctors':[d.username for d in doctors]})

@app.route('/admin/search_patient')
@cache.cached(timeout = 60, key_prefix = patient_search_cache_key)
def search_p():
    name = request.args.get('name')
    patients = User.query.filter_by(User.type == 'patient', User.username.like(f'%{name}%'))
    return {'patients':[p.username for p in patients]}

@app.route('/admin/delete_doctor/<int:user_id>', methods=['DELETE'])
def delete_d(user_id):
    if session.get('type') != 'admin':
        return jsonify({"message":"Only Admin can access this page!"}), 401
    
    user = User.query.get(user_id)
    doctor = Doctor.query.filter_by(user_id=user_id).first()

    if not user:
        return jsonify({"message":"This user doesn't exists!"}), 401
    
    if doctor:
        db.session.delete(doctor)
    
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "Doctor deleted successfully!"}), 200

@app.route('/admin/delete_patient/<int:user_id>', methods=['DELETE'])
def delete_p(user_id):
    if session.get('type') != 'admin':
        return jsonify({"message":"Only admin can access this page"}), 401
    
    user = User.query.get(user_id)
    patient = Patient.query.filter_by(user_id=user_id).first()

    if not user:
        return jsonify({"message":"This user doesn't exist!"}), 404
    
    if user:
        db.session.delete(user)
    
    db.session.delete(user)
    db.session.delete(patient)
    db.session.commit()

    return jsonify({"message": "Patient deleted successfully!"}), 200

@app.route('/admin/edit_doctor/<int:doctor_id>', methods=['PUT'])
def edit_d(doctor_id):
    if session.get('type') != 'admin':
        return jsonify({"message":"Only Admin can access this page!"}), 401
    
    data = request.json
    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return jsonify({"message":"Doctor not found!"}), 404
    
    doctor.Doctor_name = data.get("Doctor_name", doctor.Doctor_name)
    doctor.Department_name = data.get("Department_name", doctor.Department_name)
    doctor.Experience = data.get("Experience", doctor.Experience)
    
    db.session.commit()

    return jsonify({"message":f"Dr. {doctor.Doctor_name}'s profile has been updated successfully!"}), 200

@app.route('/admin/edit_doctor/<int:doctor_id>')
def edit_page1(doctor_id):
    if session.get('type') != 'admin':
        return jsonify({"message":"Only admin can access this page!"}),404
    return render_template('edit_doctor_admin.html')

@app.route('/admin/get_doctor/<int:doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    if session.get('type') != 'admin':
        return jsonify({"message":"Only Admin can access this page!"}), 401
    
    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return jsonify({"message":"Doctor not found!"}), 404

    return jsonify({"Doctor_id":doctor.Doctor_id, "Doctor_name":doctor.Doctor_name, "Department_name": doctor.Department_name, 
                    "Experience":doctor.Experience}), 200

@app.route('/admin/edit_patient/<int:patient_id>', methods=['PUT'])
def edit_p(patient_id):
    if session.get('type') != 'admin':
        return jsonify({"message":"Only Admin can access this page!"}), 401
    
    data = request.json
    patient = Patient.query.get(patient_id)

    if not patient:
        return jsonify({"message":"Patient not found!"}), 404
    
    patient.Patient_name = data.get("Patient_name", patient.Patient_name)
    patient.Doctor_name = data.get("Doctor_name", patient.Doctor_name)
    patient.Department_name = data.get("Department_name", patient.Department_name)

    db.session.commit()

    return jsonify({"message":f"{patient.Patient_name}'s profile has been updated successfully!"}), 200

@app.route('/admin/edit_patient/<int:patient_id>')
def edit_page(patient_id):
    if session.get('type') != 'admin':
        return jsonify({"message":"Only admin can access this page!"}),404
    return render_template('edit_patient_admin.html')

@app.route('/admin/get_patient/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    if session.get('type') != 'admin':
        return jsonify({"message":"Only Admin can access this page!"}), 401
    
    patient = Patient.query.get(patient_id)

    if not patient:
        return jsonify({"message":"Patient not found!"}), 404

    return jsonify({"Patient_id":patient.Patient_id, "Patient_name":patient.Patient_name, "Doctor_name": patient.Doctor_name, 
                    "Department_name":patient.Department_name}), 200

@app.route('/patient/profile/data')
def patient_prof():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    patient = Patient.query.filter_by(user_id=user_id).first()

    return jsonify({"patient_id":patient.Patient_id,
                    "username":user.username,
                    "patient_name":patient.Patient_name})

@app.route('/patient_view_doctor_detail')
def view_doctor_detail():
    doctors = Doctor.query.filter_by(Is_blacklisted = False).all()

    details = []
    for doctor in doctors:
        details.append({"Doctor_id": doctor.Doctor_id, "Doctor_name": doctor.Doctor_name, 
                        "Department_name": doctor.Department_name, "Experience": doctor.Experience})
    return jsonify(details)

@app.route('/patient_search_doctor')
def patient_search():
    name = request.args.get('name')
    doctors = Doctor.query.filter_by(User.type == 'doctor', Doctor.Doctor_name.like(f'%{name}%'))
    return {'doctors':[d.Doctor_name for d in doctors]}

@app.route('/patient/book_appointment', methods=['POST'])
def appointment_book():
    if session.get('type') != 'patient':
        return ({"message": "Only Patients can acccess this page"}), 403
    
    data = request.json

    existing_appointments = Appointments.query.filter_by(Doctor_id = data['Doctor_id'], Date = data['Date'], Time = data['Time'])

    if existing_appointments:
        return jsonify({"message": "The Doctor has already been booked. Kindly check other appointments!"}), 409
    
    appointments = Appointments(Patient_id = data['Patient_id'], Doctor_id = data['Doctor_id'], Date = data['Date'], Time = data['Time'])
    db.session.add(appointments)
    db.session.commit()

    return jsonify({"message":"Appointment booked successfully!"}), 201

@app.route('/patient_cancel_appointment/<int:appointment_id>')
def patient_cancel(appointment_id):
    if session.get('type') != 'patient':
        return jsonify({"message":"Only Patients can access this page"}), 403
    
    appointment = Appointments.query.filter_by(appointment_id)
    appointment.Status = 'Cancelled'
    db.session.commit()
    
    return jsonify({"message":"The appointment has been cancelled successfully!"})

@app.route('/api/patient/history/<int:patient_id>')
def patient_history(patient_id):
    if session.get('type') not in ['admin', 'patient', 'doctor']:
        return jsonify({"message":"Only Patients can access this page!"}), 403
    
    patient = Patient.query.get(patient_id)

    if not patient:
        return jsonify({"message":"Patient not found!"}), 404
    
    appointments = Appointments.query.filter_by(Patient_id=patient.Patient_id).all()

    result = []

    for a in appointments:
        for t in a.treatment:
            result.append({"Treatment_id":t.Treatment_id,"Appointment_id": a.Appointment_id, "Date": a.Date, "Time": a.Time, "Tests_done": t.Tests_done, 
                           "Diagnosis": t.Diagnosis, "Prescription": t.Prescription, "Medicines": t.Medicines, "Patient_name":patient.Patient_name,
                           "Doctor_name":a.doctor.Doctor_name, "Department_name": a.doctor.Department_name})
    return jsonify({"history":result})

@app.route('/patient/history/<int:patient_id>')
def patient_hist(patient_id):
    if session.get('type') != 'patient':
        return jsonify({"message":"Only Patients can access this page!"}), 403
    return render_template('patient_history.html', patient_id=patient_id)

@app.route('/patient/edit_profile/<int:patient_id>', methods=['PUT'])
def edit_patient(patient_id):
    if session.get('type') != 'patient':
        return jsonify({"message":"Only Patients can access this page!"}), 403
    
    data = request.get_json()

    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"message":"Patient not found!"}), 404
    
    user = User.query.get(patient.user_id)
    if not user:
        return jsonify({"message":"User not found!"}), 404
    
    patient.Patient_name = data.get('patient_name', patient.Patient_name)
    
    user.username = data.get('username', user.username)
    user.password = data.get('password', user.password) 

    db.session.commit()

    return jsonify({"message": "Profile updated successfully!"}), 200

@app.route('/patient/edit_profile/<int:patient_id>')
def editP(patient_id):
    if session.get('type') != 'patient':
        return jsonify({"message":"Only Patients can access this page!"}), 403
    return render_template('patient_edit_profile.html')

@app.route('/doctor/data')
def doctor_data():
    if session.get('type') != 'doctor':
        return jsonify({"message":"Only doctors can access this page!"}), 403
    
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    doctor = Doctor.query.filter_by(user_id=user_id).first()

    appointments = Appointments.query.filter_by(Doctor_id=doctor.Doctor_id).all()

    return jsonify({"username": user.username,
                    "doctor": {"Doctor_id":doctor.Doctor_id},
                    "appointments": [{
                        "Appointment_id": a.Appointment_id,
                        "Patient_id": a.Patient_id,
                        "patient":{"Patient_name":a.patient.Patient_name},
                        "Status": a.Status
                    } for a in appointments]
                })

@app.route('/doctor/mark_as_complete/<int:appointment_id>', methods=["POST"])
def complete(appointment_id):
    if session.get('type') != 'doctor':
        return jsonify({"message":"Only doctors can access this page!"}), 403
    
    user_id = session.get('user_id')

    doctor = Doctor.query.filter_by(user_id=user_id).first()
    appointment = Appointments.query.get(appointment_id)

    if not appointment:
        return jsonify({"message":"Appointment not found!"}), 404
    
    if appointment.Doctor_id != doctor.Doctor_id:
        return jsonify({"message":"Unauthorized action!"}), 403
    
    appointment.Status = 'Completed'
    db.session.commit()
    
    return jsonify({"message":"Appointment is marked complete!"}), 200

@app.route('/doctor/cancel/<int:appointment_id>', methods=["POST"])
def cancel(appointment_id):
    if session.get('type') != "doctor":
        return jsonify({"message":"Only doctors can access this page!"}), 403
    
    user_id = session.get('user_id')

    doctor = Doctor.query.filter_by(user_id=user_id).first()
    appointment = Appointments.query.get(appointment_id)

    if not appointment:
        return jsonify({"message":"Appointment not found!"}), 404
    
    if appointment.Doctor_id != doctor.Doctor_id:
        return jsonify({"message":"Unauthorized action!"}), 403
    
    appointment.Status = 'Cancelled'
    db.session.commit()

    return jsonify({"message":"Appointment has been cancelled!"}), 200

@app.route('/doctor/availability/data')
def get_availability():
    if session.get('type') != 'doctor':
        return jsonify({"message":"Only doctors can access this page!"}), 403

    user_id = session.get('user_id')
    doctor = Doctor.query.filter_by(user_id=user_id).first()

    if not doctor:
        return jsonify({"message":"Doctor not found!"}), 404

    availabilities = Doctor_Availability.query.filter_by(Doctor_id=doctor.Doctor_id).all()

    return jsonify({"doctor_id":doctor.Doctor_id,
                    "availabilities": [{
                        "id": a.Availability_id ,
                        "Date": a.Date,
                        "Start_time": a.Start_time,
                        "End_time": a.End_time,
                        "Is_available": a.Is_available
                    } for a in availabilities]
                })

@app.route('/doctor/<int:doctor_id>/provide-a', methods=["GET","POST"])
def provide_availability(doctor_id):

    if request.method == "GET":
        return render_template('doctor_availability.html', doctor_id=doctor_id)
    
    elif request.method == "POST":
        data = request.get_json()

        new = Doctor_Availability(
            Doctor_id = doctor_id,
            Date=data['Date'],
            Start_time=data['Start_time'],
            End_time=data['End_time'],
            Is_available=True
        )

        db.session.add(new)
        db.session.commit()

        cache.clear()

        return jsonify({"message":"Availability added successfully!"}), 200

@app.route('/patient/data')
def patient_data():
    if session.get('type') != 'patient':
        return jsonify({'message':"Only patients can access this page!"}), 403
    
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    patient = Patient.query.filter_by(user_id=user_id).first()

    departments = Department.query.all()
    appointments = Appointments.query.filter_by(Patient_id=patient.Patient_id).all()

    return jsonify({
        "username": user.username,
        "patient_id": patient.Patient_id,
        "departments":[{"Department_id" : d.Department_id, "Department_name": d.Department_name} for d in departments],
        "appointments": [{
            "Appointment_id": a.Appointment_id,
            "Doctor_id": a.Doctor_id,
            "Date": a.Date,
            "Time": a.Time,
            "Status": a.Status,
            "doctor":{
                "Doctor_name": a.doctor.Doctor_name,
                "Department_name": a.doctor.Department_name
            }
        } for a in appointments]
    })

@app.route('/doctor/update/<int:appointment_id>', methods=["POST"])
def update(appointment_id):
    if session.get('type') != 'doctor':
        return jsonify({"message":"Only doctors can access this page!"}), 403
    data = request.get_json()
    
    appointment = Appointments.query.get(appointment_id)

    if not appointment:
        return jsonify({"message":"Appointment not found!"}), 404

    treatment = Treatment(
        Appointment_id = appointment_id,
        Tests_done = data.get('Tests_done'),
        Diagnosis = data.get('Diagnosis'),
        Prescription = data.get('Prescription'),
        Medicines = data.get('Medicines')
    )

    db.session.add(treatment)
    db.session.commit()

    return jsonify({"message":"Updated Successfully"}), 200

@app.route('/doctor/update/<int:appointment_id>', methods=["GET"])
def update1(appointment_id):
    if session.get('type') != 'doctor':
        return jsonify({"message":"Only doctors can access this page!"}), 403
    
    appointment = Appointments.query.get(appointment_id)

    if not appointment:
        return jsonify({"message":"Appointment not found!"}), 404
    
    appointment_data = {
        "Appointment_id":appointment.Appointment_id,
        "Doctor_id":appointment.Doctor_id,
        # "Tests_done":appointment.Tests_done,
        # "Diagnosis": appointment.Diagnosis,
        # "Prescription":appointment.Prescription,
        # "Medicines":appointment.Medicines,
        "Date":appointment.Date,
        "Time":appointment.Time,
        "patient": {
            "Patient_name": appointment.patient.Patient_name if appointment.patient else "Unknown"
        }
    }
    
    return render_template('doctor_update.html', appointment=appointment_data)

@app.route('/department/<dept>/<int:patient_id>')
def department_page(dept, patient_id):
    return render_template('view_details_department.html', dept=dept, patient_id=patient_id)

@app.route('/patient/doctors/<dept>')
def get_doctors(dept):
    doctors = Doctor.query.filter(Doctor.Department_name.ilike(f"%{dept}%")).all()

    return jsonify({
        "doctors": [
            {
                "Doctor_id": d.Doctor_id,
                "Doctor_name": d.Doctor_name,
                "Department_name":d.Department_name,
                "Experience": d.Experience
            }
            for d in doctors
        ]
    })

@app.route('/patient/<int:patient_id>/appointment/<int:doctor_id>', methods=["POST"])
def availability(patient_id, doctor_id):
    if session.get('type') != 'patient':
        return jsonify({"message":"Only patients can access this page!"}), 403
    
    data = request.get_json()

    date = data.get('Date')
    time = data.get('Time')

    existing = Appointments.query.filter_by(Doctor_id=doctor_id, Date=date, Time=time).first()

    if existing:
        return jsonify({"message":"Slot already booked!"}), 400

    new_appointment = Appointments(
        Patient_id = patient_id,
        Doctor_id = doctor_id,
        Date = date,
        Time = time,
        Status = "Booked"
    )

    db.session.add(new_appointment)
    db.session.commit()

    return jsonify({"message":"Appointment booked successfully!"}), 200

@app.route('/patient/<int:patient_id>/appointment/<int:doctor_id>')
def availability1(patient_id, doctor_id):
    if session.get('type') != 'patient':
        return jsonify({"message":"Only patients can access this page!"}), 403
    return render_template('patient_availability.html',patient_id=patient_id, doctor_id=doctor_id)
    

@app.route('/view_details/<dept>/<int:doctor_id>')
def doctor_detail(dept,doctor_id):
    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return jsonify({"message":"Doctor not found!"}), 404
    
    return render_template('view_details_doctor.html', doctor=doctor, department=dept)

@app.route('/patient/<int:patient_id>/availability/<int:doctor_id>')
@cache.cached(timeout = 60, key_prefix = availability_cache_key)
def get_availabilities(patient_id, doctor_id):
    if session.get('type') != 'patient':
        return jsonify({"message":"Only patients can access this page!"}), 403
    
    availabilities = Doctor_Availability.query.filter_by(Doctor_id=doctor_id).all()

    return jsonify({
        "availabilities": [
            {
                "id":a.Availability_id,
                "Date": a.Date,
                "Start_time": a.Start_time,
                "End_time":a.End_time
            }
            for a in availabilities
        ]
    })

@app.route('/patient/<int:patient_id>/cancel_appointment/<int:appointment_id>', methods=["POST"])
def cancel_appointment1(patient_id, appointment_id):
    if session.get('type') != 'patient':
        return jsonify({"message":"Only patients can access this page!"}), 404
    
    appointment = Appointments.query.filter_by(Appointment_id=appointment_id, Patient_id=patient_id).first()

    if not appointment:
        return jsonify({"message":"Appointment not found!"}), 404
    
    appointment.Status = "Cancelled"
    db.session.commit()

    return jsonify({"message":"Appointment cancelled successfully!"})

@app.route('/admin/patient/history/<int:patient_id>')
def admin_patient_history(patient_id):
    if session.get('type') not in ['admin', 'patient']:
        return jsonify({"message":"Only admin and patients can access this page"})
    return render_template('patient_history.html', patient_id=patient_id)

@app.route('/doctor/patient/history/<int:patient_id>')
def doctor_patient_history(patient_id):
    if session.get('type') not in ['doctor', 'patient']:
        return jsonify({"message":"Only doctors and patients can access this page"})
    return render_template('patient_history.html', patient_id=patient_id)
    
    




