from flask import Flask, render_template, request, jsonify, session, redirect, flash, url_for 
from flask_cors import CORS
from pymysql import connections
from s3_service import uploadToS3, getProgressionReports
import os
import boto3
from config import *
import datetime
import secrets

app = Flask(__name__)
CORS(app)
app.secret_key = secrets.token_hex(16)
bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')


@app.route('/studentRegistration.html', methods=['GET','POST'])
def studentRegistration():
    return render_template('studentRegistration.html')

@app.route('/viewDetail.html', methods=['GET','POST'])
def viewDetail():
    student_data = getStudentByID()
    return render_template('viewDetail.html', student_data=student_data)

@app.route('/companyApply.html',methods=['GET','POST'])
def companyApply():
    #Fetch all companies
    apply = companyApplyDisplay()

    return render_template('companyApply.html',apply=apply)
    return render_template('companyApply.html',apply=modified_companies)

@app.route('/manage.html', methods=['GET','POST'])
def manage():
    students = getStudent()
    report_data_list = displayReport()
    #return render_template('manage.html',students=students)
    return render_template('manage.html',students=students, report_data_list=report_data_list)

@app.route('/companyRegistration.html', methods= ['GET','POST'])
def companyRegistration():
    return render_template('companyRegistration.html')


@app.route('/manageCompany.html', methods=['GET'])
def manageCompany():
    companies = getCompany()
    return render_template('manageCompany.html', companies=companies)

@app.route('/login.html',methods=['GET','POST'])
def login():
    return render_template('login.html')

@app.route('/studentLogin.html',methods=['GET','POST'])
def login2():
    return render_template('studentLogin.html')

@app.route('/lectureLogin.html',methods=['GET','POST'])
def login3():
    return render_template('lectureLogin.html')

@app.route('/companyLogin.html',methods=['GET','POST'])
def login4():
    return render_template('companyLogin.html')

@app.route('/index.html',methods=['GET','POST'])
def index():
    return render_template('index.html')

@app.route('/companyStudent.html',methods=['GET'])
def companyStudent():
    company_data = displayCompanyInfo()
    student_data_list = displayStudentCompanyInfo()
    return render_template('companyStudent.html', company_data = company_data, student_data_list = student_data_list)

@app.route("/adminlogin",methods=['POST'])
def adminlogin():
    admin_id = request.form['admin_id']
    admin_password = request.form['admin_password']

    query = "SELECT * FROM admin_user where admin_id = %s AND admin_password = %s"
    cursor = db_conn.cursor()
    cursor.execute(query, (admin_id, admin_password))

    # Fetch the first row (if any) that matches the query
    admin_data_list = cursor.fetchall()
    cursor.close()

    if admin_data_list:
        admin_data = admin_data_list[0]
        # The login is successful; store user information in the session
        admin = dict(zip([column[0] for column in cursor.description], admin_data))
        session["user"] = {"admin_id": admin["admin_id"], "role": "admin"}
        flash("Login successful!", "success")
        #return "done!"
        return render_template("index.html")
    else:
        flash("Login failed. Invalid username or password","error")

    return render_template("login.html")

@app.route("/studentlogin",methods=['POST'])
def studentlogin():
    studentID = request.form['studentID']
    studentNric = request.form['studentNric']

    query = "SELECT * FROM student where studentID = %s AND studentNric = %s"
    cursor = db_conn.cursor()
    cursor.execute(query, (studentID, studentNric))

    # Fetch the first row (if any) that matches the query
    student_data_list = cursor.fetchall()
    cursor.close()

    if student_data_list:
        student_data = student_data_list[0]
        # The login is successful; store user information in the session
        student = dict(zip([column[0] for column in cursor.description], student_data))
        session["user"] = {"studentID": student["studentID"], "role": "student"}
        flash("Login successful!", "success")
        #return "done!"
        return render_template("index.html")
    else:
        flash("Login failed. Invalid username or password","error")

    return render_template("login.html") 

@app.route("/lecturelogin",methods=['POST'])
def lecturelogin():
    lecturerID = request.form['lecturerID']
    lecturerpassword = request.form['lecturerpassword']

    query = "SELECT * FROM lecturer_user where lecturerID = %s AND lecturerpassword = %s"
    cursor = db_conn.cursor()
    cursor.execute(query, (lecturerID, lecturerpassword))

    # Fetch the first row (if any) that matches the query
    lecture_data_list = cursor.fetchall()
    cursor.close()

    if lecture_data_list:
        lecture_data = lecture_data_list[0]
        # The login is successful; store user information in the session
        lecture = dict(zip([column[0] for column in cursor.description], lecture_data))
        session["user"] = {"lecturerID": lecture["lecturerID"], "role": "lecturer"}
        flash("Login successful!", "success")
        #return "done!"
        return render_template("index.html")
    else:
        flash("Login failed. Invalid username or password","error")

    return render_template("login.html")

@app.route("/companylogin", methods=['POST'])
def companylogin():
    archiveCompanyID = request.form['archiveCompanyID']

    # Modify the SQL query to select from the "archive_company" table
    query = "SELECT * FROM archive_company WHERE archiveCompanyID = %s"
    cursor = db_conn.cursor()
    cursor.execute(query, (archiveCompanyID))

    # Fetch the first row (if any) that matches the query
    company_data_list = cursor.fetchall()
    cursor.close()

    if company_data_list:
        company_data = company_data_list[0]
        # The login is successful; store user information in the session
        company = dict(zip([column[0] for column in cursor.description], company_data))
        # Update the session key to use "company_id" and "company" role
        session["user"] = {"archiveCompanyID": company["archiveCompanyID"], "role": "company"}
        flash("Login successful!", "success")
        #return "done!"
        #print(f"Session data after login: {session}")
        return render_template("index.html")
    else:
        flash("Login failed. Company haven being approved", "error")

    return render_template("login.html")

@app.route('/logout', methods=['GET'])
def logout():
    # Remove the 'user' session data
    session.pop('user', None)
    flash('You have been logged out', 'success')
    return render_template("index.html")

@app.route("/addLecturer",methods=['POST'])
def addLecturer():
    lecturerID = request.form['lecturerID']
    lecturerName = request.form['lecturerName']
    lecturerUsername = request.form['lecturerUsername']
    lecturerPassword = request.form['lecturerPassword']

     #Insert Query
    insert_query = "INSERT INTO lecturer_user VALUES (%s, %s, %s, %s)"
    #Setup Cursor
    cursor = db_conn.cursor()

    try:
        #Run Query
        cursor.execute(insert_query,(lecturerID,lecturerName,lecturerUsername,lecturerPassword))
        #Save DB
        db_conn.commit()
        print("Successfully Saved Into Database")

        return "Successfully Saved Into Database"
        #If error occurs during query then we catch it into here
    except Exception as e:
        print(str(e))
        return "An error has occured"
    finally:
        cursor.close()


@app.route("/getLecturer", methods=['GET'])
def getLecturer():
    lecturerID = request.args.get('lecturerID')
        #Insert Query
    query = "SELECT * FROM lecturer_user WHERE lecturerID = %s"
    #Setup Cursor
    cursor = db_conn.cursor()

    try:
        #Run Query
        cursor.execute(query,lecturerID)
        result = cursor.fetchone()
        #Save DB
        #db_conn.commit()
        #print("Successfully Saved Into Database")

        return jsonify(result)
        #If error occurs during query then we catch it into here
    except Exception as e:
        print(str(e))
        return "An error has occured"
    finally:
        cursor.close()


@app.route("/addAdmin", methods=['POST'])
def add_admin():
    admin_id = request.form['admin_id']
    admin_name = request.form['admin_name']
    admin_password = request.form['admin_password']

    #Insert Query
    insert_query = "INSERT INTO admin_user VALUES (%s, %s, %s)"
    #Setup Cursor
    cursor = db_conn.cursor()

    try:
        #Run Query
        cursor.execute(insert_query,(admin_id,admin_name,admin_password))
        #Save DB
        db_conn.commit()
        print("Successfully Saved Into Database")

        return "Successfully Saved Into Database"
        #If error occurs during query then we catch it into here
    except Exception as e:
        print(str(e))
        return "An error has occured"
    finally:
        cursor.close()

@app.route("/getAdmin", methods=['GET'])
def getAdmin():
    admin_id = request.args.get('admin_id')
        #Insert Query
    query = "SELECT * FROM admin_user WHERE admin_id = %s"
    #Setup Cursor
    cursor = db_conn.cursor()

    try:
        #Run Query
        cursor.execute(query,admin_id)
        result = cursor.fetchone()
        #Save DB
        #db_conn.commit()
        #print("Successfully Saved Into Database")

        return jsonify(result)
        #If error occurs during query then we catch it into here
    except Exception as e:
        print(str(e))
        return "An error has occured"
    finally:
        cursor.close()


@app.route("/addCompany", methods=['POST'])
def addCompany():
    company_id = request.form['company_id']
    company_name = request.form['company_name']
    company_mobileNumber = request.form['company_mobileNumber']
    company_address = request.form['company_address']
    company_website = request.form['company_website']
    company_email = request.form['company_email']
    company_position = request.form['company_position']
    company_duration = int(request.form['company_duration'])
    company_wage = float(request.form['company_wage'])

    # Insert Query with placeholders (use %s for both integer and float)
    insert_query = "INSERT INTO company VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

    # Setup Cursor
    cursor = db_conn.cursor()
        
    try:
        # Execute Query with values as a tuple
        cursor.execute(insert_query, (
            company_id, company_name, company_mobileNumber, company_address, company_website,
            company_email, company_position, company_duration, company_wage
        ))

        # Commit changes to the database
        db_conn.commit()
        cursor.close()

        return render_template("registrationSuccess.html")
    except Exception as e:
        print(str(e))
        return "An error has occurred"
    finally:
        cursor.close()


@app.route("/getCompany", methods=['GET'])
def getCompany():
    # Insert Query
    #query = "SELECT company_id, company_name, company_address, company_email, company_wage FROM company"
    query = "SELECT * FROM company"
    # Setup Cursor
    cursor = db_conn.cursor()

    try:
        # Run Query
        cursor.execute(query)
        companies = cursor.fetchall()  # Use fetchone to get a single row
        #print(result)
        #return jsonify(companies)
        return companies
        #return render_template('manageCompany.html', companies = companies)
    except Exception as e:
        print(str(e))
        return "An error has occurred"
    finally:
        cursor.close()


@app.route("/addStudent", methods=['POST'])
def addStudent():
    studentID = request.form['studentID']
    studentCohort = request.form['studentCohort']
    internshipSession = int(request.form['internshipSession'])
    studentName = request.form['studentName']
    studentNric = request.form['studentNric']
    studentGender = request.form['studentGender']
    studentProgramme = request.form['studentProgramme']
    studentEmail = request.form['studentEmail']
    studentMobileNumber = request.form['studentMobileNumber']
    supervisorName = request.form['supervisorName']
    supervisorEmail = request.form['supervisorEmail']
    appliedCompanyName = request.form['appliedCompanyName']
    appliedCompanyEmail = request.form['appliedCompanyEmail']

    # Insert Query with placeholders (use %s for both integer and float)
    insert_query = "INSERT INTO student VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    # Setup Cursor
    cursor = db_conn.cursor()
    
    try:
        # Execute Query with values as a tuple
        cursor.execute(insert_query, (
            studentID, studentCohort, internshipSession, studentName, studentNric,
            studentGender, studentProgramme, studentEmail, studentMobileNumber,
            supervisorName, supervisorEmail, appliedCompanyName, appliedCompanyEmail
        ))

        # Commit changes to the database
        db_conn.commit()
        cursor.close()

        return render_template('registrationSuccess.html')
    except Exception as e:
        print(str(e))
        return "An error has occurred"
    finally:
        cursor.close()


@app.route("/getStudent", methods=['GET'])
def getStudent():
    #studentID = request.args.get('studentID')
        #Insert Query
    query = "SELECT * FROM student"
    #Setup Cursor
    cursor = db_conn.cursor()

    try:
        #Run Query
        cursor.execute(query)
        students = cursor.fetchall()
        return students
        #Save DB
        #db_conn.commit()
        #print("Successfully Saved Into Database")
        #return jsonify(result)
        #If error occurs during query then we catch it into here
    except Exception as e:
        print(str(e))
        return "An error has occured"
    finally:
        cursor.close()

@app.route("/getStudentByID", methods=['GET'])
def getStudentByID():
    studentID = session.get('user', {}).get('studentID')
    if not studentID:
        return "Missing studentID parameter", 400

    # Use a prepared statement to prevent SQL injection
    query = "SELECT * FROM student WHERE studentID = %s"
    cursor = db_conn.cursor()
    
    try:
        cursor.execute(query, (studentID,))
        student = cursor.fetchone()

        if student:
            # Convert the student data to a dictionary for JSON response
            student_data = {
                'studentID': student[0],
                'cohort': student[1],
                'internshipSession': student[2],
                'studentName': student[3],
                'studentNric': student[4],
                'studentGender': student[5],
                'studentProgramme': student[6],
                'studentEmail': student[7],
                'studentMobileNumber': student[8],
                'supervisorName': student[9],
                'supervisorEmail': student[10],
                'appliedCompanyName': student[11],
                'appliedCompanyEmail': student[12]
            }
            # Return the student data as a JSON response
            #return jsonify(student_data)
            return student_data
        else:
            # Return a 404 error if the student is not found
            return "Student not found", 404

    except Exception as e:
        print(str(e))
        # Return a 500 error if an exception occurs
        return "An error has occurred", 500
    finally:
        cursor.close()

@app.route("/deleteStudent",methods=['POST'])
def deleteStudent():
    studentID = request.form.get('studentID')
    query = "DELETE FROM student WHERE studentID = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(query,studentID)
        #students = cursor.fetchone()
        db_conn.commit()
        return render_template('index.html')
    except Exception as e:
        print(str(e))
        return "An error has occured"
    finally:
        cursor.close()

@app.route("/editStudent", methods=['POST'])
def editStudent():
    #data = request.get_json()  # Get JSON data from the request
    studentID = request.form.get('studentID')
    editedStudentName = request.form['editedStudentName']
    editedStudentNric = request.form['editedStudentNric']
    editedStudentEmail = request.form['editedStudentEmail']
    editedStudentMobileNumber = request.form['editedStudentMobileNumber']

    # Define the SQL query to update the student data
    query = "UPDATE student SET studentName = %s, studentNric = %s,  studentEmail = %s, studentMobileNumber = %s WHERE studentID = %s"
    cursor = db_conn.cursor()

    try:
        # Execute the SQL query with the provided data
        cursor.execute(query, (editedStudentName, editedStudentNric, editedStudentEmail, editedStudentMobileNumber, studentID))
        
        # Commit the changes to the database
        db_conn.commit()
        
        # Return a success message (you can customize this)
        #return jsonify({"message": "Data has been updated successfully!"}), 200
        return render_template("index.html")
    except Exception as e:
        print(str(e))
        # Return an error message (you can customize this)
        return jsonify({"error": "An error has occurred"}), 500
    finally:
        cursor.close()

@app.route("/companyApprove", methods=['POST'])
def companyApprove():
    # Get the data from the form
    admin_id = request.form.get('admin_id')
    company_id = request.form.get('company_id')
    
    query = "SELECT company_id, company_name, company_mobileNumber, company_address, company_website, company_email, company_wage FROM company WHERE company_id = %s"
    cursor = db_conn.cursor()
    
    cursor.execute(query, (company_id))
    company_data = cursor.fetchone()
    
    if company_data:
        # Extract data from the company_data tuple
        company_id, company_name, company_mobileNumber, company_address, company_website, company_email, company_wage = company_data

        # Define the status and current date
        approveStatus = "approved"
        approveDate = datetime.datetime.now()

        # Insert the data into the 'archive_company' table
        archive_query = """
            INSERT INTO archive_company (
                archiveCompanyID,
                archiveCompanyName,
                archiveCompanyMobileNumber,
                archiveCompanyAddress,
                archiveCompanyWebsite,
                archiveCompanyEmail,
                archiveCompanyWage,
                archiveApprovalDate,     
                archiveAdminID,    
                archiveCompanyStatus    
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(archive_query, (
            company_id, company_name, company_mobileNumber, company_address,
            company_website, company_email, company_wage,approveDate, 
            admin_id, approveStatus))

        # Remove the company record from the 'company' table
        delete_query = "DELETE FROM company WHERE company_id = %s"
        cursor.execute(delete_query, (company_id))
        
        # Commit the changes to the database
        db_conn.commit()

    cursor.close()

    return render_template("index.html")

@app.route("/companyReject",methods=['POST'])
def companyReject():
    company_id = request.form.get('company_id')
    admin_id = request.form.get('admin_id')
    approveDate = datetime.datetime.now()
    approveStatus = "rejected"

    # Define the SQL query to insert a new record into adminCompany
    rejectquery = "INSERT INTO adminCompany (admin_id, company_id, approveDate, approveStatus) VALUES (%s, %s, %s, %s)"
    deletequery = "DELETE FROM company WHERE company_id = %s"  
    cursor = db_conn.cursor()

    try:
        # Execute the SQL query with the provided data
        cursor.execute(rejectquery, (admin_id, company_id, approveDate, approveStatus))
        
        cursor.execute(deletequery, company_id)
        # Commit the changes to the database
        db_conn.commit()

        # Return a success message
        #return jsonify({"message": "Company has been approved successfully!"}), 200
        return render_template("index.html")
    except Exception as e:
        print(str(e))
        # Return an error message if an exception occurs
        return jsonify({"error": "An error has occurred"}), 500
    finally:
        cursor.close()

@app.route("/companyApply", methods=['GET'])
def companyApplyDisplay():
    query = "SELECT * FROM archive_company"
    #Setup Cursor
    cursor = db_conn.cursor()

    try:
        #Run Query
        cursor.execute(query)
        apply = cursor.fetchall()
        return apply
        #Save DB
        #db_conn.commit()
        #print("Successfully Saved Into Database")
        #return jsonify(apply)
        #If error occurs during query then we catch it into here
    except Exception as e:
        print(str(e))
        return "An error has occured"
    finally:
        cursor.close()

@app.route("/studentApply", methods=['POST'])
def studentApply():
    studentID = request.form.get('studentID')
    companyID = request.form.get('companyID')
    appliedDate = datetime.datetime.now()
    appliedStatus = "applied"

    # Check if the student has already applied to this company
    checkQuery = "SELECT * FROM appliedCompany WHERE studentID = %s AND companyID = %s"
    cursor = db_conn.cursor()
    cursor.execute(checkQuery, (studentID, companyID))
    existing_application = cursor.fetchone()

    if existing_application:
        # The student has already applied
        return "Applied"

    # Insert the new application record
    applyQuery = "INSERT INTO appliedCompany (studentID, companyID, appliedDate, appliedStatus) VALUES (%s, %s, %s, %s)"
    try:
        cursor.execute(applyQuery, (studentID, companyID, appliedDate, appliedStatus))
        db_conn.commit()
        # Return 'Applied' to indicate a successful application
        return "Applied"
    except Exception as e:
        print(str(e))
        # Return an error message if an exception occurs
        return "Error Applying"
    finally:
        cursor.close()

@app.route("/companyStudentInfo",methods=['GET'])
def displayCompanyInfo():
    archiveCompanyID = session.get('user', {}).get('archiveCompanyID')
    if not archiveCompanyID:
        return "Missing companyID parameter", 400

    # Use a prepared statement to prevent SQL injection
    query = "SELECT * FROM archive_company WHERE archiveCompanyID = %s"
    cursor = db_conn.cursor()
    
    try:
        cursor.execute(query, (archiveCompanyID,))
        company = cursor.fetchone()

        if company:
            # Convert the student data to a dictionary for JSON response
            company_data = {
                'archiveCompanyID': company[0],
                'archiveCompanyName': company[1],
            }
            # Return the student data as a JSON response
            #return jsonify(company_data)
            return company_data
        else:
            # Return a 404 error if the student is not found
            return "Company not found", 404

    except Exception as e:
        print(str(e))
        # Return a 500 error if an exception occurs
        return "An error has occurred", 500
    finally:
        cursor.close()

@app.route("/studentCompanyInfo",methods=['GET'])
def displayStudentCompanyInfo():
    archiveCompanyID = session.get('user', {}).get('archiveCompanyID')
    if not archiveCompanyID:
        return "Missing companyID parameter", 400
    
    studentQuery = """
    SELECT *
    FROM student AS s
    JOIN appliedCompany AS ac ON s.studentID = ac.studentID
    WHERE ac.companyID = %s
    """
    cursor = db_conn.cursor()

    try:
        cursor.execute(studentQuery, (archiveCompanyID,))
        students = cursor.fetchall()

        student_data_list = []

        for student in students:
            student_data = {
                'studentID': student[0],
                'studentName': student[3],
                'studentNric': student[4],
                'studentMobileNumber': student[8],
                'studentEmail': student[7],
                'supervisorName': student[9],
                'supervisorEmail': student[10],
            }
            student_data_list.append(student_data)

        if student_data_list:
            return student_data_list
        else:
            return "No students found for this company", 404

    except Exception as e:
        print(str(e))
        # Return a 500 error if an exception occurs
        return "An error has occurred", 500
    finally:
        cursor.close()

@app.route("/uploadForm",methods=['POST'])
def uploadAcceptanceForm():
    studentID = session.get('user', {}).get('studentID')
    if not studentID:
        return "Missing studentID parameter", 400
    
    companyAcceptanceForm = request.files['companyAcceptanceForm']
    if companyAcceptanceForm.filename.split('.')[1] != 'pdf':
        status = "Error: File is not pdf"
        print(status)
        return status
    
    letterIndemnity = request.files['letterIndemnity']
    if letterIndemnity.filename.split('.')[1] != 'pdf':
        status = "Error: File is not pdf"
        print(status)
        return status

    acknowledgmentForm = request.files['acknowledgmentForm']
    if acknowledgmentForm.filename.split('.')[1] != 'pdf':
        status = "Error: File is not pdf"
        print(status)
        return status
    
    hireEvidence = request.files['hireEvidence']
    if hireEvidence.filename.split('.')[1] != 'pdf':
        status = "Error: File is not pdf"
        print(status)
        return status

    fileQuery = """
    UPDATE student 
    SET companyAcceptanceForm = %s, letterIndemnity = %s, acknowledgmentForm = %s, hireEvidence = %s 
    WHERE studentID = %s
    """
    cursor = db_conn.cursor()
    print("hi")
    try:
        cursor.execute(fileQuery,(companyAcceptanceForm,letterIndemnity,acknowledgmentForm,hireEvidence,studentID))
        acceptanceFilePath = f'students/{studentID}/companyAcceptanceForm.pdf'
        letterPath = f'students/{studentID}/letterOfIndemnity.pdf'
        acknowledgmentPath = f'students/{studentID}/acknowledgmentForm.pdf'
        evidencePath = f'students/{studentID}/hireEvidence.pdf'
        uploadToS3(companyAcceptanceForm,acceptanceFilePath)
        uploadToS3(letterIndemnity,letterPath)
        uploadToS3(acknowledgmentForm,acknowledgmentPath)
        uploadToS3(hireEvidence,evidencePath)
        db_conn.commit()
        return render_template("index.html")
    except Exception as e:
        print(str(e))
        # Return a 500 error if an exception occurs
        return "An error has occurred", 500
    finally:
        cursor.close()

@app.route('/displayReport', methods=['GET'])
def displayReport():
    studentID = request.args.get('studentID')
    if not studentID:
        return "Missing studentID parameter", 400

    reports = getProgressionReports(studentID)

    report_data_list = []

    if reports:
        report_names = ["Company Acceptance Form", "Letter of Indemnity", "Parent Acknowledgment Form", "Hire Evidence"]

        for i in range(len(reports)):
            report_data = {"name": report_names[i], "url": str(reports[i])}  # Ensure URL is a string
            report_data_list.append(report_data)
            
    print(report_data_list)
    return report_data_list

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)


