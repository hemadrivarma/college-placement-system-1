from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SECRET_KEY'] = 'placement123'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    department = db.Column(db.String(50))
    cgpa=db.Column(db.Float)
    password = db.Column(db.String(100))

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100))
    job_role = db.Column(db.String(100))
    package = db.Column(db.String(20))
    eligibility = db.Column(db.Float)   
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))

    status = db.Column(db.String(20))

    student = db.relationship('Student', backref='applications')
    company = db.relationship('Company', backref='applications')     



@app.route('/')
def home():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        department = request.form["department"]
        cgpa = request.form["cgpa"]
        password = request.form["password"]

        student = Student(
            fullname=fullname,
            email=email,
            phone=phone,
            department=department,
            cgpa=float(cgpa),
            password=password
        )

        db.session.add(student)
        db.session.commit()

        flash("Registration Successful! Please Login.", "success")
        return redirect("/login")

    return render_template("register.html")



@app.route('/dashboard')
def dashboard():

    # Check if student is logged in
    if 'student_id' not in session:
        return redirect('/login')

    # Get logged-in student
    student = Student.query.get(session['student_id'])

    # Search text
    search = request.args.get('search', '').strip()

    # Show only companies for which student is eligible
    if search:
        companies = Company.query.filter(
            Company.company_name.ilike(f"%{search}%"),
            Company.eligibility <= student.cgpa
        ).all()
    else:
        companies = Company.query.filter(
            Company.eligibility <= student.cgpa
        ).all()

    # Get student's applications
    apps = Application.query.filter_by(
        student_id=session['student_id']
    ).all()

    applications = {}

    for app in apps:
        applications[app.company_id] = app.status

    total_companies = len(companies)
    total_applied = len(apps)
    approved = len([a for a in apps if a.status == "Approved"])
    rejected = len([a for a in apps if a.status == "Rejected"])
    pending = len([a for a in apps if a.status == "Pending"])           

    return render_template(
        'dashboard.html',
        student=student,
        companies=companies,
        applications=applications,
        total_companies=total_companies,
        total_applied=total_applied,
        approved=approved,
        rejected=rejected,
        pending=pending
        
    )
@app.route('/profile')
def profile():

    if 'student_id' not in session:
        return redirect('/login')

    student = Student.query.get(session['student_id'])

    return render_template("profile.html", student=student)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():

    if 'student_id' not in session:
        return redirect('/login')

    student = Student.query.get(session['student_id'])

    if request.method == 'POST':
        student.fullname = request.form['fullname']
        student.email = request.form['email']
        student.phone = request.form['phone']
        student.department = request.form['department']
        student.cgpa = float(request.form['cgpa'])

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect('/profile')

    return render_template("edit_profile.html", student=student)     

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/admin")

        flash("Invalid Admin Login!", "danger")

    return render_template("admin_login.html")    

@app.route('/admin')
def admin():

    if "admin" not in session:
        return redirect("/admin_login")

    students = Student.query.all()

    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_applications = Application.query.count()
    selected_students = Application.query.filter_by(status="Approved").count()

    return render_template(
        "admin.html",
        students=students,
        total_students=total_students,
        total_companies=total_companies,
        total_applications=total_applications,
        selected_students=selected_students
    )


@app.route('/admin_logout')
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin_login")


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    student = Student.query.get_or_404(id)

    if request.method == "POST":
        student.fullname = request.form['fullname']
        student.email = request.form['email']
        student.phone = request.form['phone']
        student.department = request.form['department']

        db.session.commit()

        return redirect('/admin')

    return render_template("edit.html", student=student) 

@app.route('/delete/<int:id>')
def delete(id):
    student = Student.query.get_or_404(id)

    # Delete applications of this student
    Application.query.filter_by(student_id=id).delete()

    db.session.delete(student)
    db.session.commit()

    return redirect('/admin')     

@app.route('/delete_company/<int:id>')
def delete_company(id):
    company = Company.query.get_or_404(id)
    db.session.delete(company)
    db.session.commit()
    return redirect('/companies')

@app.route('/edit_company/<int:id>', methods=['GET', 'POST'])
def edit_company(id):
    company = Company.query.get_or_404(id)

    if request.method == "POST":
        company.company_name = request.form['company_name']
        company.job_role = request.form['job_role']
        company.package = request.form['package']
        company.eligibility = request.form['eligibility']

        db.session.commit()
        return redirect('/companies')

    return render_template("edit_company.html", company=company) 

@app.route('/company', methods=['GET', 'POST'])
def company():

    if request.method == "POST":

        company = Company(
            company_name=request.form["company_name"],
            job_role=request.form["job_role"],
            package=request.form["package"],
            eligibility=float(request.form["eligibility"])
        )

        db.session.add(company)
        db.session.commit()

        return redirect("/companies")

    return render_template("company.html")    
@app.route('/companies')
def companies():

    companies = Company.query.all()

    return render_template("companies.html", companies=companies)

@app.route('/apply/<int:company_id>')
def apply(company_id):

    existing = Application.query.filter_by(
        student_id= session['student_id'],
        company_id=company_id,
    ).first()

    if existing:
        return redirect('/dashboard')

    application = Application(
        student_id=session['student_id'],
        company_id=company_id,
        status="Pending"
    )

    db.session.add(application)
    db.session.commit()

    print(Application.query.all())

    return redirect('/dashboard')  
@app.route('/applications')
def applications():
    applications = Application.query.all()
    print(applications)   # Add this line
    return render_template(
        "applications.html",
        applications=applications
    )

@app.route('/approve/<int:id>')
def approve(id):
    application = Application.query.get(id)
    application.status = "Approved"
    db.session.commit()
    return redirect('/applications')
@app.route('/reject/<int:id>')
def reject(id):
    application = Application.query.get(id)
    application.status = "Rejected"
    db.session.commit()
    return redirect('/applications')    

@app.route('/test')
def test():
    companies = Company.query.all()
    print(companies)
    return str(companies) 
with app.app_context():
    db.create_all()   

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        student = Student.query.filter_by(email=email).first()

        print("Email entered:", email)

        if student:
            print("Password in DB:", student.password)
            print("Password entered:", password)
        else:
            print("Student not found")

        if student and student.password == password:
            session["student_id"] = student.id
            flash("Login Successful!", "success")
            return redirect("/dashboard")

        flash("Invalid Email or Password!", "danger")
        return redirect("/login")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")   

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():

    if 'student_id' not in session:
        return redirect('/login')

    student = Student.query.get(session['student_id'])

    if request.method == "POST":

        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if student.password != old_password:
            flash("Old Password is incorrect!", "danger")
            return redirect("/change_password")

        if new_password != confirm_password:
            flash("New Password and Confirm Password do not match!", "danger")
            return redirect("/change_password")

        student.password = new_password
        db.session.commit()

        flash("Password Changed Successfully!", "success")
        return redirect("/logout")

    return render_template("change_password.html")

                  

if __name__ == "__main__":
    app.run(debug=True) 
