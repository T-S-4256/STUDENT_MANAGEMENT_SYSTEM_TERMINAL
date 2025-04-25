from flask import Flask, render_template, request, redirect, url_for, Response
import pymongo
import os
from dotenv import load_dotenv
import pandas as pd
import io
from datetime import datetime
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
load_dotenv()

app = Flask(__name__)


# ************************* SET UP DATABASE CONNECTION ******************************
try:
    # CONNECT WITH MONGODB
    Client = pymongo.MongoClient(os.environ.get("mongo_url"))
    # CREATING A DATABASE
    db = Client["S_I_M_S"]
    # CREATING A COLLECTION (TABLE IN MYSQL)
    Student_Coll = db["Student_Data"]
except pymongo.errors.ConnectionError as e:
    print("MongoDB connection failed:", e)


# LOGIN PAGE ROUTE
@app.route("/", methods=["POST", "GET"])
def login():
    print("Home Page Fetched")
    if request.method == "POST":

        # FATCH THE DATA FROM THE FORM
        roll_number = (request.form.get("roll_number")).strip()
        password = (request.form.get("password")).strip()

        # IF THE DATA IS WHITE SPACE THEN RAISE ERROR
        if len(roll_number) == 0 or len(password) == 0:
            print("Invalid Data For Login")
            return render_template(
                "login.html", message="Invalid Data,Please Try Again"
            )

        # CHECK IF ROLL NUMBERAND PASSWORD IS VALID OR NOT
        student = Student_Coll.find_one({"roll_number": roll_number})

        # CHECK IF THE ROLL NUMBER FOUND THEN CHECK FOR PASSWORD
        if student:

            # IF PASSWORD IS CORRECT THEN LOGIN
            if student["password"] == password:
                print("Valid User Login Success")
                if student["type"] == "admin":
                    courses = Student_Coll.distinct("course")
                    print("Coursers : ", courses)
                    courseList = []
                    for i in courses:
                        courseList.append(
                            {
                                "Course": i,
                                "Total": Student_Coll.count_documents({"course": i}),
                                "Topper": Student_Coll.find_one(
                                    {"course": i}, sort=[("marks", -1)]
                                )["full_name"],
                            }
                        )
                    print(courseList)

                    return render_template("adminDash.html", course_detail=courseList)

                else:
                    return render_template("studentDash.html", studentData=student)

            # IF PASSWORD IS INCORRECT
            else:
                print("Invalid Password For Login")
                return render_template("login.html", message="Invalid Password")

        # IF ROLL NUMBER NOT EXIST
        else:
            print("Roll Number Not Exist")
            return render_template("login.html", message="Invalid Roll Number")

    # IF REQUEST METHOD IS NOT A POST METHOD
    return render_template("login.html")


# ADMIN DASHBORD PAGE ROUTE
@app.route("/admin", methods=["POST", "GET"])
def adminDash():
    courses = Student_Coll.distinct("course")
    courseList = []
    for i in courses:
        courseList.append(
            {
                "Course": i,
                "Total": Student_Coll.count_documents({"course": i}),
                "Topper": Student_Coll.find_one({"course": i}, sort=[("marks", -1)])[
                    "full_name"
                ],
            }
        )
    return render_template("adminDash.html", course_detail=courseList, studentData=None)


# REGISTER STUDENT ROUTE
@app.route("/admin/register", methods=["POST", "GET"])
def register():
    print("Register Page Fetched")
    if request.method == "POST":

        full_name = (request.form.get("full_name")).strip()
        if len(full_name) == 0:
            print("Invalid Full Name : ")
            return redirect(url_for("adminDash"))

        father_name = (request.form.get("father_name")).strip()
        if len(father_name) == 0:
            print("Invalid Father's Name : ")
            return redirect(url_for("adminDash"))

        course = request.form.get("course")
        roll_number = "R00" + str(datetime.now().strftime("%Y%m%d"))

        semester = (request.form.get("semester")).strip()
        if len(father_name) == 0:
            print("Invalid Father's Name : ")
            return redirect(url_for("adminDash"))

        contact_number = (request.form.get("contact_number")).strip()
        if len(father_name) == 0:
            print("Invalid Father's Name : ")
            return redirect(url_for("adminDash"))

        email = (request.form.get("email")).strip()
        if len(father_name) == 0:
            print("Invalid Father's Name : ")
            return redirect(url_for("adminDash"))

        profile_photo = request.files.get("profile_photo")
        upload_folder = "static/uploads"
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        profile_photo_path = None

        if profile_photo:
            filename = secure_filename(profile_photo.filename)
            profile_photo_path = os.path.join(upload_folder, filename)
            profile_photo.save(profile_photo_path)

        # CREATING A DICTIONARY FOR STORING STUDENT DATA INTO THE DATABASE
        student = {
            "full_name": full_name,
            "roll_number": roll_number,
            "father_name": father_name,
            "semester": semester,
            "course": course,
            "contact_number": contact_number,
            "email": email,
            "type": "student",
            "profile_photo": profile_photo_path,
        }
        print(student)
        try:
            Student_Coll.insert_one(student)
            print("Data Saved Successfully")
            redirect(url_for("adminDash"))
        except Exception as e:
            print("Not Able To Save The Data")
        return redirect(url_for("adminDash"))
    return redirect(url_for("adminDash"))


# REGISTER MULTIPLE STUDENT ROUTE
@app.route("/admin/register_multiple", methods=["POST", "GET"])
def register_multiple():
    if request.method == "POST":
        file = request.files.get("file_upload")
        filename = secure_filename(file.filename)
        # If the uploaded file is a CSV
        if filename.endswith(".csv"):
            try:
                file_stream = io.StringIO(file.stream.read().decode("utf-8"))
                df = pd.read_csv(file_stream)

                # Print the DataFrame to check the data (you can process it as needed)
                print(df)
                studentList = []
                for index, row in df.iterrows():
                    student = {
                        "full_name": row.get("full_name"),
                        "roll_number": f"R00{datetime.now().strftime('%Y%m%d')}{index:02d}",
                        "father_name": row.get("father_name"),
                        "semester": row.get("semester"),
                        "course": row.get("course"),
                        "contact_number": row.get("contact_number"),
                        "email": row.get("email"),
                        "type": "student",
                        "profile_photo": row.get("profile_photo_path"),
                        "marks": row.get("marks"),
                    }
                    studentList.append(student)
                Student_Coll.insert_many(studentList)
            except Exception as e:
                print("Something Went Wrong !")
        else:
            print("Not Csv File")
            return redirect(url_for("adminDash"))
    return redirect(url_for("adminDash"))


# SEARCH STUDENT ROUTER
@app.route("/admin/search_student", methods=["POST"])
def search_student():
    roll_number = request.form.get("search_roll_number")
    student = Student_Coll.find_one({"roll_number": roll_number})

    # Get course detail for proper re-rendering
    courses = Student_Coll.distinct("course")
    courseList = []
    for i in courses:
        courseList.append(
            {
                "Course": i,
                "Total": Student_Coll.count_documents({"course": i}),
                "Topper": Student_Coll.find_one({"course": i}, sort=[("marks", -1)])[
                    "full_name"
                ],
            }
        )

    if student:
        print("Data : ", student)
        return render_template(
            "adminDash.html", course_detail=courseList, studentData=student
        )
    else:
        return render_template(
            "adminDash.html", course_detail=courseList, message="Invalid Roll Number"
        )


@app.route("/admin/delete_student", methods=["POST"])
def delete_student():
    roll_number = request.form.get("roll_number")
    Student_Coll.delete_one({"roll_number": roll_number})
    print("Deleted student:", roll_number)
    return redirect(url_for("adminDash"))


@app.route("/admin/update_student", methods=["GET", "POST"])
def update_student():
    if request.method == "GET":
        roll_number = request.args.get("roll_number")
        student = Student_Coll.find_one({"roll_number": roll_number})
        return render_template("update_student.html", student=student)

    if request.method == "POST":
        roll_number = request.form.get("roll_number")
        file = request.files.get("marksheet")
        semesterMarks = request.form.get("semesterM")
        filename = secure_filename(file.filename)
        # If the uploaded file is a CSV
        if filename.endswith(".csv"):
            try:
                file_stream = io.StringIO(file.stream.read().decode("utf-8"))
                df = pd.read_csv(file_stream)
                for index, rows in df.iterrows():
                    marks = {
                        "math": (
                            int(rows.get("math").item())
                            if pd.notna(rows.get("math"))
                            else None
                        ),
                        "physics": (
                            int(rows.get("physics").item())
                            if pd.notna(rows.get("physics"))
                            else None
                        ),
                        "chemistry": (
                            int(rows.get("chemistry").item())
                            if pd.notna(rows.get("chemistry"))
                            else None
                        ),
                        "hindi": (
                            int(rows.get("hindi").item())
                            if pd.notna(rows.get("hindi"))
                            else None
                        ),
                        "english": (
                            int(rows.get("english").item())
                            if pd.notna(rows.get("english"))
                            else None
                        ),
                    }
                    Student_Coll.find_one_and_update(
                        {
                            "roll_number": roll_number
                        },  # Use the correct roll_number from the form
                        {
                            "$set": {f"marks.{semesterMarks}": marks}
                        },  # Structure marks by semester
                        upsert=True,  # Consider using upsert if the student might not exist yet
                    )
            except Exception as e:
                print("Somthing Went Wrong In Read Marksheet")
                return redirect(url_for("adminDash"))
        updated_data = {
            "full_name": request.form.get("full_name"),
            "father_name": request.form.get("father_name"),
            "course": request.form.get("course"),
            "semester": request.form.get("semester"),
            "contact_number": request.form.get("contact_number"),
            "email": request.form.get("email"),
        }
        Student_Coll.update_one({"roll_number": roll_number}, {"$set": updated_data})
        return redirect(url_for("adminDash"))


@app.route("/admin/add_marks", methods=["POST", "GET"])
def add_marks():
    print("Add Marksheet Fetched")
    if request.method == "POST":
        file = request.files.get("marksheet_upload")
        filename = secure_filename(file.filename)
        roll_number = request.form.get("roll_number")
        semester_marksheet = request.form.get("marksheet")
        print("Semester : ", semester_marksheet)
        # If the uploaded file is a CSV
        if filename.endswith(".csv"):
            try:
                file_stream = io.StringIO(file.stream.read().decode("utf-8"))
                df = pd.read_csv(file_stream)

                # Print the DataFrame to check the data (you can process it as needed)
                print(df)
                # ADD MARKSHEET TO DATABASE
                for index, rows in df.iterrows():
                    marks = {
                        "math": (
                            int(rows.get("math").item())
                            if pd.notna(rows.get("math"))
                            else None
                        ),
                        "physics": (
                            int(rows.get("physics").item())
                            if pd.notna(rows.get("physics"))
                            else None
                        ),
                        "chemistry": (
                            int(rows.get("chemistry").item())
                            if pd.notna(rows.get("chemistry"))
                            else None
                        ),
                        "hindi": (
                            int(rows.get("hindi").item())
                            if pd.notna(rows.get("hindi"))
                            else None
                        ),
                        "english": (
                            int(rows.get("english").item())
                            if pd.notna(rows.get("english"))
                            else None
                        ),
                    }

                    print(marks)
                    print("Roll no : ", roll_number)
                fetchedData = Student_Coll.find_one_and_update(
                    {
                        "roll_number": roll_number
                    },  # Use the correct roll_number from the form
                    {
                        "$set": {f"marks.{semester_marksheet}": marks}
                    },  # Structure marks by semester
                    upsert=True,  # Consider using upsert if the student might not exist yet
                )
                print("Fetched : ", fetchedData)
            except Exception as e:
                print("Error on Add Marksheet : ", e)
        return redirect(url_for("adminDash"))
    return redirect(url_for("adminDash"))


@app.route("/student", methods=["POST", "GET"])
def studentDash():
    print("student Dash Fetched")
    if request.method == "POST":
        print("Good Job")
    return render_template("studentDash.html")


@app.route("/student/get_result", methods=["POST", "GET"])
def get_result():
    print("get_result Fetched ")
    if request.method == "GET":
        semester = request.args.get("semester")
        roll_number = request.args.get("roll_number")
        print("student : ", roll_number, " : ", semester)
        student = Student_Coll.find_one({"roll_number": roll_number})
        if student:
            try:
                result = student["marks"][semester]
                print("result : ", result)
            except Exception as e:
                print("No REsult Found")
                return render_template(
                    "studentDash.html", message="No Result Found", studentData=student
                )
            return render_template(
                "studentDash.html", result=result, studentData=student
            )
        print("No Student Found ")
        return render_template("studentDash.html")
    print("Not A POst MEthod ")
    return render_template("studentDash.html")


@app.route("/student/update_password", methods=["POST", "GET"])
def update_password():
    print("Update Password Fetched ")
    if request.method == "POST":
        roll_number = request.form.get("roll_number")
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        print("OLD : ", old_password)
        print("New : ", new_password)
        print("Roll No : ", roll_number)
        print("Confim : ", confirm_password)

        student = Student_Coll.find_one({"roll_number": roll_number}, {})
        if student:
            if student["password"] == old_password:
                if new_password == confirm_password:
                    Student_Coll.update_one(
                        {"roll_number": roll_number},  # Find the student by roll number
                        {"$set": {"password": new_password}},  # Set the new password
                    )
                    print("Update Successfully")
                    return render_template(
                        "studentDash.html",
                        studentData=student,
                        message="Password Updated Successfully",
                    )
                else:
                    print("New Password Is Miss Matching")
                    return render_template(
                        "studentDash.html",
                        studentData=student,
                        message="New Passwords Are Not Matching",
                    )
            else:
                print("Incorrect Password")
                return render_template(
                    "studentDash.html",
                    studentData=student,
                    message="Incorrect Password",
                )
        print("Invalid Roll Number")
        return render_template(
            "studentDash.html", studentData=student, message="Invalid Roll Number"
        )
    return render_template("studentDash", studentData=student)


@app.route("/student/download_result", methods=["GET"])
def download_result():
    roll_number = request.args.get("roll_number")
    semester = request.args.get("semester")

    print("Roll : ", roll_number, " : ", semester)
    student = Student_Coll.find_one({"roll_number": roll_number})
    if not student or "marks" not in student or semester not in student["marks"]:
        return "No result found for download", 404

    result = student["marks"][semester]

    # Create CSV content
    output = []
    output.append(["Subject", "Marks", "Grade"])
    for subject, mark in result.items():
        grade = "N/A"
        if mark is not None:
            if mark > 90:
                grade = "O"
            elif mark > 80:
                grade = "A"
            elif mark > 60:
                grade = "B"
            else:
                grade = "C"
        output.append(
            [subject.capitalize(), mark if mark is not None else "N/A", grade]
        )

    total = sum(mark for mark in result.values() if mark is not None)
    output.append(["Total", total, ""])
    output.append(["Result", "Pass" if total > 300 else "Fail", ""])

    # Create a response with CSV mimetype
    def generate():
        for row in output:
            yield ",".join(str(cell) for cell in row) + "\n"

    filename = f"{roll_number}_{semester}_result.csv"
    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# Function to send the OTP via email
def send_email(receiver_email, otp):
    sender_email = "Mr.satyam824@gmail.com"  # Replace with your email
    sender_password = (
        "miuz meur fadb dieh"  # Replace with your email password or App Password
    )

    # Setup the MIME
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Your OTP for Forgot Password"

    # Body of the email
    body = f"Your OTP for resetting the password is: {otp}"
    message.attach(MIMEText(body, "plain"))

    # Sending the email via Gmail's SMTP server
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)  # Use Gmail SMTP server
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print("OTP sent to email successfully!")
    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")
        return False
    return True


def generate_otp():
    otp = random.randint(100000, 999999)  # Generate a 6-digit OTP
    return otp


@app.route("/forgot_password", methods=["POST", "GET"])
def forgot_password():
    print("forgot_password Page Fetched")
    if request.method == "POST":
        roll_number = request.form.get("roll_number")
        email = request.form.get("email")
        print("email: ", email, " : roll_number: ", roll_number)

        # Find the student by roll_number
        student = Student_Coll.find_one({"roll_number": roll_number})

        if student:
            # Check if the email matches the student's email
            if student["email"] == email:
                otp = generate_otp()  # Generate OTP
                print(f"Generated OTP: {otp}")

                # Send OTP to the student's email
                if send_email(email, otp):
                    # You can store the OTP in a session or database for further validation
                    print(f"OTP {otp} sent to {email}")
                    # You can either redirect to a password reset page or return a message
                    Student_Coll.find_one_and_update(
                        {"roll_number": roll_number}, {"$set": {"otp": otp}}
                    )
                    return render_template(
                        "forgot_password.html",
                        message=f"OTP Sent To {email}",
                        otp_sent=student,
                    )
                else:
                    return "Failed to send OTP. Please try again later."
            else:
                return "Invalid email address."
        else:
            return "Student not found."
    return render_template("forgot_password.html")  # Display the forgot password form


@app.route("/forgot_password/verify_otp", methods=["POST", "GET"])
def verify_otp():
    print("Verify Otp Fetched")
    if request.method == "POST":
        userOTP = request.form.get("otp")
        roll_number = request.form.get("roll_number")
        student = Student_Coll.find_one({"roll_number": roll_number})
        print(userOTP, " : ", roll_number, " : ", student)
        if student:
            print(student["otp"], "==", userOTP)
            if str(student["otp"]) == str(userOTP):
                return render_template("forgot_password.html", otpVarified=student)
        return render_template("forgot_password.html", message="Incorrect Roll Number")
    return render_template("forgot_password.html")


@app.route("/forgot_password/reset_password", methods=["POST", "GET"])
def reset_password():
    print("reset route fetched")
    if request.method == "POST":
        roll_number = request.form.get("roll_number")
        newPass = request.form.get("new_password")
        conPass = request.form.get("confirm_password")
        print(newPass, " : ", conPass, " : ", roll_number)
        if newPass == conPass:
            student = Student_Coll.find_one({"roll_number": roll_number})
            try:
                Student_Coll.find_one_and_update(
                    {"roll_number": roll_number}, {"$set": {"password": newPass}}
                )
                return render_template(
                    "forgot_password.html", message="Password Updated Successfully"
                )
            except Exception as e:
                print("Not Able To Update the Password ")
                return render_template(
                    "forgot_password.html", message="Something Went Wrong"
                )
        return render_template(
            "forgot_password.html", otpVarified=student, message="Something Went Wrong"
        )
    return render_template(
        "forgot_password.html", otpVarified=student, message="Only POST Method Allowed"
    )



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
