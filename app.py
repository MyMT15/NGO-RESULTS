from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
import pandas as pd
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import string

# Load environment variables
load_dotenv()

# Constants
SCHOOL_NAME = "AKSHARA BHARATAM SOCIETY"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create serializer for password reset tokens
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        return serializer.dumps(self.username, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token):
        try:
            username = serializer.loads(token, salt='password-reset-salt', max_age=1800)
        except:
            return None
        return User.query.filter_by(username=username).first()

# Create all tables and admin user
with app.app_context():
    db.create_all()
    # Create admin user if it doesn't exist
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(username='admin', email='admin@example.com')
        admin_user.set_password('ABS123@')
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully!")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    father_name = db.Column(db.String(100))
    mother_name = db.Column(db.String(100))
    school_name = db.Column(db.String(200))
    village = db.Column(db.String(100))
    results = db.relationship('Result', backref='student', lazy=True)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(2), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    uniform_grade = db.Column(db.String(1))
    activities_grade = db.Column(db.String(1))
    digital_class_grade = db.Column(db.String(1))
    written_skills_grade = db.Column(db.String(1))
    speaking_skills_grade = db.Column(db.String(1))

def calculate_grade(marks):
    if marks >= 23:
        return 'A+'
    elif marks >= 20:
        return 'A'
    elif marks >= 18:
        return 'B+'
    elif marks >= 15:
        return 'B'
    elif marks >= 13:
        return 'C+'
    elif marks >= 10:
        return 'C'
    elif marks >= 8:
        return 'D'
    else:
        return 'N/A'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        student = Student.query.filter_by(phone_number=phone_number).first()
        if student:
            max_marks_dict = {'Maths': 30, 'English': 10, 'Physics': 20, 'Chemistry': 20, 'Biology': 20, 'Social': 20}
            max_total = sum(max_marks_dict.get(result.subject, 20) for result in student.results) if student.results else 0
            total_marks = sum([result.marks for result in student.results]) if student.results else 0
            # Calculate rank
            students = Student.query.all()
            student_totals = []
            for s in students:
                s_total = sum([r.marks for r in s.results]) if s.results else 0
                student_totals.append((s.id, s_total))
            # Sort by total marks descending
            student_totals.sort(key=lambda x: x[1], reverse=True)
            rank = None
            for idx, (sid, total) in enumerate(student_totals, 1):
                if sid == student.id:
                    rank = idx
                    break
            qualified = rank is not None and rank <= 30
            return render_template('results.html', 
                                student=student,
                                max_marks=max_marks_dict,
                                max_total=max_total,
                                total_marks=total_marks,
                                rank=rank,
                                qualified=qualified,
                                calculate_grade=calculate_grade,
                                school_name=student.school_name or SCHOOL_NAME)
        else:
            flash('No results found for the given phone number.', 'error')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Debug print
        print(f"Login attempt - Username: {username}")
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print("Login failed - User not found")
            flash('Invalid username or password', 'error')
            return render_template('login.html')
        
        if user.check_password(password):
            print("Login successful")
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin'))
        else:
            print("Login failed - Invalid password")
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filename)
                try:
                    # Read the file based on its extension
                    if file.filename.endswith('.csv'):
                        df = pd.read_csv(filename)
                    else:
                        df = pd.read_excel(filename)

                    success_count = 0
                    error_count = 0

                    for _, row in df.iterrows():
                        try:
                            # Map columns
                            name = str(row['Student Name']).strip()
                            father_name = str(row['Father Name']).strip()
                            mother_name = str(row['Mother Name']).strip() if 'Mother Name' in row else ''
                            school_name = str(row['School Name']).strip()
                            phone_number = str(row['Phone Number']).strip()
                            village = str(row['Village']).strip()
                            subjects = ['Maths', 'Physics', 'Chemistry', 'Biology', 'Social', 'English']
                            total_marks = 0
                            marks_dict = {}
                            for subject in subjects:
                                marks = float(row[subject]) if subject in row and pd.notnull(row[subject]) else 0
                                marks_dict[subject] = marks
                                total_marks += marks
                            # Optional: validate total marks
                            # Create or update student
                            student = Student.query.filter_by(name=name, phone_number=phone_number).first()
                            if not student:
                                student = Student(name=name, father_name=father_name, mother_name=mother_name, school_name=school_name, phone_number=phone_number, village=village)
                                db.session.add(student)
                                db.session.commit()
                            else:
                                # Update missing fields if needed
                                updated = False
                                if not student.father_name and father_name:
                                    student.father_name = father_name
                                    updated = True
                                if not student.mother_name and mother_name:
                                    student.mother_name = mother_name
                                    updated = True
                                if not student.school_name and school_name:
                                    student.school_name = school_name
                                    updated = True
                                if not student.village and village:
                                    student.village = village
                                    updated = True
                                if updated:
                                    db.session.commit()
                            # Add/Update results for each subject
                            for subject, marks in marks_dict.items():
                                # Check if result already exists for this student and subject
                                result = Result.query.filter_by(student_id=student.id, subject=subject).first()
                                grade = calculate_grade(marks)
                                if not result:
                                    result = Result(subject=subject, marks=marks, grade=grade, student=student)
                                    db.session.add(result)
                                else:
                                    result.marks = marks
                                    result.grade = grade
                                db.session.commit()
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            continue
                    os.remove(filename)
                    flash(f'Successfully imported {success_count} students. {error_count} errors occurred.', 'success')
                except Exception as e:
                    flash(f'Error processing file: {str(e)}', 'error')
                return redirect(url_for('admin'))
            else:
                flash('Invalid file type. Please upload a CSV or Excel file.', 'error')
                return redirect(url_for('admin'))
        # Handle manual form submission
        name = request.form.get('name')
        phone_number = request.form.get('phone_number')
        subject = request.form.get('subject')
        marks = float(request.form.get('marks'))
        school_name = request.form.get('school_name')
        
        # Validate marks are within range (0-25)
        if marks < 0 or marks > 25:
            flash('Marks must be between 0 and 25.', 'error')
            return redirect(url_for('admin'))
        
        student = Student.query.filter_by(name=name, phone_number=phone_number).first()
        if not student:
            student = Student(name=name, phone_number=phone_number, school_name=school_name)
            db.session.add(student)
            db.session.commit()
        elif not student.school_name and school_name:
            student.school_name = school_name
            db.session.commit()
        
        # Calculate grade based on marks (out of 25)
        grade = calculate_grade(marks)
        result = Result(subject=subject, marks=marks, grade=grade, student=student)
        db.session.add(result)
        db.session.commit()
        
        flash('Result added successfully!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('admin.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        
        if user:
            try:
                token = user.get_reset_token()
                reset_url = url_for('reset_password', token=token, _external=True)
                
                msg = Message('Password Reset Request',
                            sender=app.config['MAIL_USERNAME'],
                            recipients=[user.email])
                msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request then simply ignore this email.
'''
                mail.send(msg)
                flash('Password reset instructions have been sent to your email.', 'success')
            except Exception as e:
                print(f"Email sending error: {str(e)}")
                flash('Unable to send email. Please contact the administrator.', 'error')
        else:
            flash('Username not found.', 'error')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html')
        
        user.set_password(password)
        db.session.commit()
        flash('Your password has been updated.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3000, debug=True) 