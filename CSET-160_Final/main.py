from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from sqlalchemy import create_engine, text
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

def login_required(
    f,
):  # redirects to login if not logged in, idk what it does otherwise
    # Decorate routes to require login.

    # http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


#configure application
app = Flask(__name__)

#configure session to use file system
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# connection string is in the format mysql://user:password@server/database
conn_str = "mysql://root:ethanpoe125@localhost/accounts"
engine = create_engine(conn_str) # echo=True tells you if connection is successful or not
conn = engine.connect()

@app.route("/")
def main_page():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        #store login info
        username = request.form.get("username")
        password = request.form.get("password")
        
        #check all info exists
        if not username or not password:
            return apology("missing information", 400)
        
        #call username and check password
        params = {"username":username, "password":password}
        users = conn.execute(text("select * from base_user where email_address = :username"), params).all()
        user_password = conn.execute(text("select user_password from base_user where email_address = :username"), params).all()

        if len(users) != 1 or not check_password_hash(user_password[0][0], password):
            return apology("invalid username and or password", 400)

        #determine if teacher
        db_teachers_id = conn.execute(text("select * from teachers where email_address = :username"), {"username":username}).all()
        if len(db_teachers_id) > 0:
            session["isTeacher"] = True
        else:
            session["isTeacher"] = False

        session["user_id"] = username
        session["loggedIn"] = True
        return render_template("index.html")
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "POST":
        #store all data
        username = request.form.get("username")
        password = request.form.get("password")
        check_password = request.form.get("confirmation")
        radio = request.form.get("radio")

        #make sure all info exists
        if not username or not password or not check_password or not radio:
            return apology("Missing information")

        #check if username already exists
        params = {"username":username}
        users = conn.execute(text("select * from base_user where email_address = :username"), params).all()
        if len(users) > 0:
            return apology("user exists already", 400)
        
        #check confirmation password
        if password != check_password:
            return apology("passwords don't match", 400)

        #generate hash and store in database
        hashed = generate_password_hash(password)
        params = {"username":username, "hashed":hashed}
        conn.execute(text("insert into base_user values (:username, :hashed)"), params)
        conn.commit()
        
        #check radio and store in database
        if (request.form.get("radio") == "teacher"):
            conn.execute(text("insert into teachers (email_address) values (:username)"), request.form)
            conn.commit()
        else:
            conn.execute(text("insert into students (email_address) values (:username)"), request.form)
            conn.commit()
        return render_template("login.html")
    
    else:
        return render_template("register.html")

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return render_template("index.html")



@app.route("/accounts")
@login_required
def get_accounts():
    accounts = conn.execute(text("select * from base_user")).all() # Executes the string in SQL
    flag = 0
    return render_template("accounts.html", accounts=accounts, flag=flag)

@app.route("/accounts/teachers")
@login_required
def get_teachers():
    accounts = conn.execute(text("select * from teachers order by teacher_id asc")).all() # Executes the string in SQL
    if isinstance(accounts[0][0], int):
        flag = 1
    return render_template("accounts.html", accounts=accounts, flag=flag)

@app.route("/accounts/students")
@login_required
def get_students():
    accounts = conn.execute(text("select * from students order by student_id asc")).all() # Executes the string in SQL
    if isinstance(accounts[0][0], int):
        flag = 1
    return render_template("accounts.html", accounts=accounts, flag=flag)

@app.route("/tests", methods=["GET", "POST"])
@login_required
def show_tests():
    if request.method == "POST":
        #code for taking test
        return render_template("tests.html")
    
    else:
        tests = {}
        #get all teachers
        teachers = conn.execute(text("select email_address from teachers")).all() # Executes the string in SQL
        for teacher in teachers:
            params = {"email":teacher[0]}
            teacher_tests = conn.execute(text("select test_id, test_name from tests where email_address = :email"), params).all()
            if len(teacher_tests) > 0:
                tests[teacher[0]] = teacher_tests
        return render_template("tests.html", tests=tests)

@app.route("/tests/create", methods=["GET", "POST"])
@login_required
def make_tests():
    if request.method == "POST":
        #Add making test question stuff
        test_id = conn.execute(text("select test_id from tests where test_name=:testname"), request.form).all() # test_id[0][0] is the ID
        question = request.form.get("question")
        true_id = test_id[0][0]
        params = {"test_id":true_id, "question_name":question}
        conn.execute(text("insert into questions (question_name, test_id) values (:question_name, :test_id)"), params)
        conn.commit()
        return render_template("test_create.html")
    else:
        return render_template("test_create.html")
    
@app.route("/tests/create/newtest", methods=["POST"])
@login_required
def make_new_test():
    params = {"testname":request.form.get("testname"), "email":session["user_id"]}
    conn.execute(text("insert into tests (test_name, email_address) values (:testname, :email)"),params)
    conn.commit()
    return redirect("/tests/create")
    
@app.route("/tests/edit", methods=["GET", "POST"])
@login_required
def edit_tests():
        if request.method == "POST":
            #collect all answers and store
            max_id = conn.execute(text("select max(question_id) from questions")).all()[0][0]

            #loop through and call id numbers to get all answers
            for i in range(max_id + 1):
                answer = request.form.get(str(i))
                if answer:
                    params = {"id":i}
                    question = conn.execute(text("select * from questions where question_id = :id"), params).all()
                    sec_para = {"ques":request.form.get(str(question[0][0])), "tes_id":question[0][2], "id_q":question[0][0]}
                    print(sec_para)
                    conn.execute(text("update questions set question_name = :ques, test_id = :tes_id where question_id = :id_q"), sec_para)
                    conn.commit()
            tests = conn.execute(text("select * from tests")).all() #tests[0][0] references the ID
            questions = conn.execute(text("select * from questions")).all()
            return render_template("edit_test.html", questions=questions, tests=tests)
        else:
            tests = conn.execute(text("select * from tests")).all() #tests[0][0] references the ID
            questions = conn.execute(text("select * from questions")).all()
            return render_template("edit_test.html", questions=questions, tests=tests)

@app.route("/tests/edit/testName", methods=["POST"])
@login_required
def edit_test_name(): # This is a dummy page to help edit the test name
    #collect all answers and store
    max_id = conn.execute(text("select max(test_id) from tests")).all()[0][0]

    #loop through and call id numbers to get all answers
    for i in range(max_id + 1):
        answer = request.form.get(str(i))
        if answer:
            params = {"id":i}
            test = conn.execute(text("select * from tests where test_id = :id"), params).all()
            params = {"new_name":request.form.get(str(i)), "id":i}
            conn.execute(text("update tests set test_name = :new_name where test_id = :id"), params)
            conn.commit()
    return redirect("/tests/edit")
    
@app.route("/tests/delete", methods=["GET", "POST"])
@login_required
def delete_tests():
    if request.method == "POST":
        #get max test_id
        max_id = conn.execute(text("select max(test_id) from tests")).all()[0][0]

        #loop through and call id numbers to find which test was deleted
        for i in range(max_id + 1):
            test_name = request.form.get(str(i))
            print(str(i))
            print(test_name)
            if test_name:
                #execute delete functions
                params = {"test_id":str(i)}
                conn.execute(text("delete from tests where test_id = :test_id"), params)
                conn.commit()
                conn.execute(text("delete from questions where test_id = :test_id"), params)
                conn.commit()

        #render delete_test page again
        tests = {}
        #get all teachers
        teacher = session["user_id"]
        params = {"email":teacher}
        teachers = conn.execute(text("select email_address from teachers where email_address = :email"), params).all() # Executes the string in SQL
        
        for teacher in teachers:
            params = {"email":teacher[0]}
            teacher_tests = conn.execute(text("select test_id, test_name from tests where email_address = :email"), params).all()
            if len(teacher_tests) > 0:
                tests[teacher[0]] = teacher_tests
        return render_template("delete_tests.html", tests=tests, max_id = max_id)
    else:
        tests = {}
        #get all teachers
        teacher = session["user_id"]
        params = {"email":teacher}
        teachers = conn.execute(text("select email_address from teachers where email_address = :email"), params).all() # Executes the string in SQL
        
        for teacher in teachers:
            params = {"email":teacher[0]}
            teacher_tests = conn.execute(text("select test_id, test_name from tests where email_address = :email"), params).all()
            if len(teacher_tests) > 0:
                tests[teacher[0]] = teacher_tests
        return render_template("delete_tests.html", tests=tests)

@app.route("/tests/view", methods=["GET", "POST"])
@login_required
def take_tests():
    if request.method == "POST":
        max_id = conn.execute(text("select max(test_id) from tests")).all()[0][0]

        #loop through and call id numbers to find which test was deleted
        for i in range(max_id + 1):
            test_name = request.form.get(str(i))
            if test_name:
                params = {"test_id":str(i)}
                questions = conn.execute(text("select * from questions where test_id = :test_id"), params).all()
        return render_template("testing.html", questions=questions)
    else:
        tests = {}
        #get all teachers
        teachers = conn.execute(text("select email_address from teachers")).all() # Executes the string in SQL
        print(teachers)

        for teacher in teachers:
            params = {"email":teacher[0], "student_email":session["user_id"]}
            teacher_tests = conn.execute(text("select test_id, test_name from tests where email_address = :email and test_id not in (select test_id from test_taken where email_address = :student_email)"), params).all()
            if len(teacher_tests) > 0:
                tests[teacher[0]] = teacher_tests
        return render_template("take_tests.html", tests=tests)
    
@app.route("/tests/submit", methods=["GET", "POST"])
@login_required
def test_submission():
    if request.method == "POST":
        #collect all answers and store
        max_id = conn.execute(text("select max(question_id) from questions")).all()[0][0]
        test_id = request.form.get("test_id")

        #insert into test_taken 
        params = {"test_id":test_id, "email":session["user_id"]}
        conn.execute(text("insert into test_taken (test_id, email_address) values (:test_id, :email)"), params)
        conn.commit()
        test_taken_id = conn.execute(text("select test_taken_id from test_taken where test_id=:test_id and email_address=:email"), params).all()
        #loop through and call id numbers to get all answers
        for i in range(max_id + 1):
            answer = request.form.get(str(i))
            if answer:
                params = {"question_id":str(i), "answer":answer, "email":session["user_id"], "test_taken_id":test_taken_id[0][0]}
                conn.execute(text("insert into test_answer (answer, question_id, email_address, test_taken_id) values (:answer, :question_id, :email, :test_taken_id)"), params)
                conn.commit()
                
        return render_template("take_tests.html")
    else:
        tests = {}
        #get all teachers
        teachers = conn.execute(text("select email_address from teachers")).all() # Executes the string in SQL
        
        for teacher in teachers:
            params = {"email":teacher[0]}
            teacher_tests = conn.execute(text("select test_id, test_name from tests where email_address = :email"), params).all()
            if len(teacher_tests) > 0:
                tests[teacher[0]] = teacher_tests
        return render_template("take_tests.html", tests=tests)
    
@app.route("/grades", methods=["GET", "POST"])
@login_required
def view_taken_tests():
    if request.method == "POST":
        #determine which test and by whom
        #loop through all possible test_taken id's until the one submitted is found
        test_picked = request.form.get("test_id")
        #get all answers for this taken test and break loop
        params = {"test_taken_id":test_picked}
        answers = conn.execute(text("select answer_id, test_answer.answer, test_answer.email_address, questions.question_name, test_answer.test_taken_id, test_answer.test_taken_id from test_answer join questions on (test_answer.question_id = questions.question_id) having test_taken_id = :test_taken_id"), params).all()
        return render_template("grade_test.html", answers=answers)
    
    else:
        params = {"email":session["user_id"]}
        tests = conn.execute(text("select test_taken.test_id, test_name, test_taken.email_address, test_taken.test_taken_id from test_taken join tests on (test_taken.test_id = tests.test_id) where tests.email_address = :email"), params).all()
        return render_template("view_taken_tests.html", tests=tests)  

@app.route("/grades_submit", methods=["GET", "POST"])
@login_required
def submit_grades():
    score = request.form.get("grade")
    test_taken_id = request.form.get("test_taken_id")
    params = {"id":test_taken_id}
    student_email = conn.execute(text("select email_address from test_taken where test_taken_id = :id"), params).all()[0][0]
    params = {"grade":score, "test_taken_id":test_taken_id, "user_id":student_email}
    already_graded = conn.execute(text("select * from grades where test_taken_id = :test_taken_id and email_address = :user_id"), params).all()
    if len(already_graded) > 0:
        conn.execute(text("update grades set grade = :grade where test_taken_id = :test_taken_id and email_address = :user_id"), params)       
        conn.commit()
    else:
        conn.execute(text("insert into grades (grade, email_address, test_taken_id) values (:grade, :user_id, :test_taken_id)"), params)       
        conn.commit()
    return redirect("/grades")

@app.route("/tests/grades", methods=["GET", "POST"])
@login_required
def view_student_grades():
    user = session["user_id"]
    params = {"user_id":user}
    grades = conn.execute(text("select grade_id, grade, test_name, grades.email_address from grades join test_taken on (test_taken.test_taken_id = grades.test_taken_id) join tests on (tests.test_id = test_taken.test_id) having grades.email_address = :user_id"), params).all()
    return render_template("view_grades.html", grades=grades)

@app.route("/test/all")
@login_required
def view_all_tests_taken():
    info_tests = conn.execute(text("select tests.test_id, test_name, grade_id, grade from tests join test_taken on (test_taken.test_id = tests.test_id) join grades on (grades.test_taken_id = test_taken.test_taken_id)")).all()
    tests = conn.execute(text("select * from tests")).all()
    number_of_students = []
    for i in tests:
        number = 0
        for v in info_tests:
            if i[1] == v[1]:
               number += 1 
        number_of_students.append(number)
    student_grade = conn.execute(text("select test_name, grades.email_address, grade from tests join test_taken on (test_taken.test_id = tests.test_id) join grades on (grades.test_taken_id = test_taken.test_taken_id)"))
    return render_template("view_tests.html", tests=tests, number_of_students=number_of_students, test_length=len(tests), student_grade=student_)




#apology, will be called if error happens
def apology(message, code=400):
    # Render message as an apology to user.
    def escape(s):
        # Escape special characters.

        # https://github.com/jacebrowning/memegen#special-characters

        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code

if __name__ == '__main__':
    app.run(debug=True) # Auto restarts cause of debug mode when changes to code are made