from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    Is_blacklisted = db.Column(db.Boolean, default = False)
    type = db.Column(db.String(), default='general')

class Appointments(db.Model):
    Appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Patient_id = db.Column(db.Integer, db.ForeignKey('patient.Patient_id'), nullable=False)
    Doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.Doctor_id'), nullable=False)
    Date = db.Column(db.String(), nullable=False)
    Time = db.Column(db.String(), nullable=False)
    Status = db.Column(db.String(), default='Booked')
    treatment = db.relationship('Treatment', backref='appointment', cascade='all, delete-orphan')

class Treatment(db.Model):
    Treatment_id = db.Column(db.Integer, primary_key=True)
    Appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.Appointment_id'), nullable=False)
    Tests_done = db.Column(db.String(), nullable=False)
    Diagnosis = db.Column(db.String(), nullable=False)
    Prescription = db.Column(db.String(), nullable=False)
    Medicines = db.Column(db.String(), nullable=False)

class Patient(db.Model):
    Patient_id = db.Column(db.Integer, primary_key=True)
    Patient_name = db.Column(db.String(), nullable=False)
    Doctor_name = db.Column(db.String(), nullable=True)
    Department_name = db.Column(db.String(), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref='patient')
    appointments = db.relationship('Appointments', foreign_keys='Appointments.Patient_id', backref='patient', cascade='all, delete-orphan')

class Doctor(db.Model):
    Doctor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Doctor_name = db.Column(db.String(), nullable=False)
    Department_name = db.Column(db.String(), nullable=False)
    Experience = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='Doctor')
    availability = db.relationship('Doctor_Availability', backref='Doctor', cascade='all, delete-orphan')
    appointments = db.relationship('Appointments', foreign_keys='Appointments.Doctor_id', backref='doctor', cascade='all, delete-orphan')                

class Doctor_Availability(db.Model):
    Availability_id = db.Column(db.Integer, primary_key=True)
    Doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.Doctor_id'), nullable=False)
    Date = db.Column(db.String(), nullable=False)
    Start_time = db.Column(db.String(), nullable=False)
    End_time = db.Column(db.String(), nullable=False)
    Is_available = db.Column(db.Boolean, default=True)

class Department(db.Model):
    Department_id = db.Column(db.Integer, primary_key=True)
    Department_name = db.Column(db.String(), unique=True ,nullable=False)
    Description = db.Column(db.String())
    Doctor_registered = db.Column(db.Integer, default=0)

   
