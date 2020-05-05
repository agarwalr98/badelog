from flask import Flask,url_for,render_template,request,  redirect,url_for, flash,abort, logging, session
from flask_login import LoginManager , login_required , UserMixin , login_user
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, IntegerField  
from flask_mail import Mail, Message
from itsdangerous import URLSafeSerializer, SignatureExpired
import pathlib
from functools import wraps
from passlib.context import CryptContext
from flask_mysqldb import MySQL 
cryptcontext = CryptContext(schemes=["sha256_crypt", "md5_crypt", "des_crypt"])


app = Flask(__name__)

# Uncomment this if database is on your localsystem
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ALUMNI'

# Uncomment this database is on server 
# app.config['MYSQL_HOST'] = 'remotemysql.com'
# app.config['MYSQL_USER'] = 'qmrpgUAerV'
# app.config['MYSQL_PASSWORD'] = 'GS5zKM8g2w'
# app.config['MYSQL_DB'] = 'qmrpgUAerV'

# object of MySql
mysql = MySQL(app)

app.config['SECRET_KEY'] = 'secret_key'
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
string = ""                 #LoggedIn webmail 

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized. Please log in.', 'danger')
            return redirect(url_for('login'))
    return wrap


@login_manager.user_loader
def load_user(user_id):
    return None

class MyForm(Form):
    email = StringField(u'First Name', validators=[validators.input_required()])
    last_name  = StringField(u'Last Name', validators=[validators.optional()])
    
class User(UserMixin):
    def __init__(self , first , last , email , password , id , active=False):
        self.id = id
        self.first = first
        self.last = last
        self.email = email
        self.password = password
        self.active = active

    def get_id(self):
        return self.id

    def is_active(self):
        return self.active

    def get_auth_token(self):
        return make_secure_token(self.email , key='secret_key')

class UsersRepository:

    def __init__(self):
        self.users = dict()
        self.users_id_dict = dict()
        self.identifier = 0
    
    def save_user(self, user):
        self.users_id_dict.setdefault(user.id, user)
        self.users.setdefault(user.email, user)

    def get_email(self, email):
        return self.users.get(email)    
    
    def get_user_by_id(self, userid):
        return self.users_id_dict.get(userid)
    
    def next_index(self):
        self.identifier +=1
        return self.identifier

users_repository = UsersRepository()

# Mail server (gmail) setup
# Allow your gmail account to mail through some secured app.
# Click at https://www.google.com/settings/security/lesssecureapps.
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] =465                                    # Port used for SSL gmail
app.config['MAIL_USERNAME'] = 'agarwal.r1998@gmail.com'           #use your gmail ID
app.config['MAIL_PASSWORD'] = ''	             #Use Password of gmail ID
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail=Mail(app)

flag =1 
def globally_change():
    global  flag 
    flag = 1
    
@app.route("/", methods=['GET' , 'POST'])
def login():
    
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']   
        registeredUser = users_repository.get_email(email)
        print(registeredUser)

        # set the connection to database.
        cur = mysql.connection.cursor()
        result =cur.execute("select Email, password from Login L where L.Email=%s", [ email])
        query1_result = cur.fetchone ()
        
        if result>0:
            query1_email = query1_result[0]
            query1_password = query1_result[1]
            
            # if registeredUser != None and registeredUser.password == password and registeredUser.active == True:
            if email== query1_email and cryptcontext.verify(password, query1_password ):
                globally_change()
                # print("value of flasg is :;",flag)
                print('Logged in..')
                global string
                string = email
                username = email
                session['logged_in']=True
                session['email']= email
                # login_user(registeredUser)
                return redirect(url_for('login_page'))
            else:
                error = "Invalid user and password"
                return render_template("home.html", error= error)
        
        else:
            error = "Invalid user and password"
            return render_template("home.html", error= error)    
            # return abort(401)
             # pyautogui.alert('Please signup first!', "alert")  # always returns "OK"
            # return render_template("home.html")
    else:
        return render_template("home.html", error=None)

@app.route("/login_page")
def login_page():
    print("flag is ",flag)
    if flag == 1:
        # flash("Logged in")
        return render_template("login.html" )
    else:
        return "Please Login first"

@app.route('/logout')
def logout():
    session.clear()
    return "logout successfully"

@app.route("/signup",methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Fetch form data
        global first_db
        global last_db
        global email_
        global password_db
        userDetails = request.form
        firstName = userDetails['firstName']
        first_db = firstName
        lastName = userDetails['lastName']
        last_db = lastName
        email = userDetails['email']
        email_ = email
        password = userDetails['password']
        print("email is: ", email_, password)
        password_db = cryptcontext.hash(str(password)) 
        new_user = User(firstName , lastName , email , password , users_repository.next_index())
        users_repository.save_user(new_user)
        
        return redirect(url_for('verification_page'))

    return render_template("signup.html")

@app.route("/forgot",methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        # Fetch form data
        global email
        email = request.form['email']
        global string
        string = email
        registeredUser = users_repository.get_email(email)
        print(registeredUser)
        if registeredUser is None:
            return render_template("not_registered_user.html")
        else:
            return redirect(url_for('forgotemail'))
        new_user = User(firstName , lastName , email , password , users_repository.next_index())
        users_repository.save_user(new_user)
    return render_template("forgot_email.html")

@app.route("/forgotemail")
def forgotemail():  
    global random_URL
    random_URL = URLSafeSerializer('secret_key')
    global token
    token = random_URL.dumps(string, salt='email-confirm')
    #Put email ID of sender in <sender>
    msg = Message('Email confirmation', sender = 'agarwal.r1998@gmail.com', recipients = [string])
    msg.body = "Reset your password by clicking the link: "
    domain = "http://localhost:5000/reset/"
    msg.body += domain
    msg.body += token
    mail.send(msg)
    return "Please see your email for password reset"
    
new_password=""
@app.route('/reset/<token_recv>',methods=['GET', 'POST'])
def password_change(token_recv):
    try:
        email = random_URL.loads(token_recv, salt='email-confirm')
        cur = mysql.connection.cursor()
        print("email is ",email)
        if request.method == 'POST':
            global new_password
            new_password = request.form['password1']
            new_password = CryptContext.hash(str(new_password))
            # cur.execute("Delete from Login")
            cur.execute("Update Login SET password=(%s) Where Email=(%s)",(new_password, email))
            mysql.connection.commit()
            cur.close()
        registeredUser = users_repository.get_email(email)
    except SignatureExpired :
        return '<h2>The token is expired!</h2>'
    print(new_password)
    registeredUser = users_repository.get_email(email)
    registeredUser.password = new_password
    #set registered user to be active means user's account is verified.
    registeredUser.active = True
    return render_template("new_password.html")

token=""
random_URL = URLSafeSerializer('secret_key')
@app.route("/verification_page")
def verification_page():
    global random_URL
    random_URL = URLSafeSerializer('secret_key')
    global token
    token = random_URL.dumps(string, salt='email-confirm')
    #Put email ID of sender in <sender>
    msg = Message('Email confirmation', sender = 'agarwal.r1998@gmail.com'  , recipients = [string])
    msg.body = "Activate your account by clicking the link: "
    domain = "http://localhost:5000/confirm_email/"
    msg.body += domain
    msg.body += token
    mail.send(msg)
    return "Please see your email for verification"
    
@app.route('/confirm_email/<token_recv>')
def confirm_email(token_recv):
    try:
        email = random_URL.loads(token_recv, salt='email-confirm')
        cur = mysql.connection.cursor()
        print("email is ",email_ )
        cur.execute("Delete from Login")
        cur.execute("INSERT INTO Login(Email, FirstName,LastName,password) VALUES(%s,%s, %s,%s)",(email_,first_db,last_db,password_db))
        mysql.connection.commit()
        cur.close()
    except SignatureExpired :
        return '<h2>The token is expired!</h2>'
    registeredUser = users_repository.get_email(email)
    #set registered user to be active means user's account is verified.
    registeredUser.active = True
    return '<h2>Your Email is verified!</h2>'

alumni_no = 'b15100'

list1 = ""
@app.route('/profile/<enroll_no>')
def profile_page(enroll_no):
    global alumni_no
    alumni_no = enroll_no
    return render_template('profile.html')

final_result=""
@app.route("/login_page/alumni", methods=['GET', 'POST'])
def alumniLogin(): 
    if request.method == 'POST': 
        # # Fetch form data
        # global first_db
        # global last_db
        # global email_
        # global password_db
        passout_year = request.form['passout_year']
        degree = request.form['degree']
        branch = request.form['branch']
        current_state = request.form['current_state']
        company_name = request.form['company_name']
        location = request.form['location']
        position = request.form['position']
        field_of_work = request.form['field_of_work']
        company = request.form['company']
        position_in_opportunities = request.form['position_in_opportunities'] 
        field = request.form['field']
        alumni_filter = request.form
        print(alumni_filter)
        print("alumni filter")
        print(alumni_filter['degree'])
        cur = mysql.connection.cursor()
        query1 = ("SELECT EnrollmentNumber from Alumni A Where A.PassoutYear={} AND A.Degree='{}' AND A.CurrentState='{}' AND A.Branch='{}' ").format(passout_year, degree,current_state, branch)
        query2 = ("SELECT EnrollmentNumber from Worked_In W Where W.CompanyName='{}' AND W.Location='{}' AND W.Position='{}' AND W.Field_of_work='{}' ").format(company_name, location, position, field_of_work)
        query3 = ("SELECT EnrollmentNumber from Opportunities_for_hiring O Where O.Company='{}' AND O.Position='{}' AND O.Field='{}'").format(company, position_in_opportunities, field)
        query1 = query1.replace("=All","!=''")
        query1 = query1.replace("='All'","!=''")
        query2 = query2.replace("=All","!=''")
        query2 = query2.replace("='All'","!=''")
        query3 = query3.replace("=All","!=''")
        query3 = query3.replace("='All'","!=''")
        
        print(query1)
        print(query2)
        print(query3)
        cur.execute(query1)
        result1 = cur.fetchall()
        cur.execute(query2)
        result2 = cur.fetchall()
        cur.execute(query3)
        result3 = cur.fetchall()
        print(result1)
        print(result2)
        print(result3)
        global final_result
        final_result = (set(result1).intersection(result2))
        final_result = (set(final_result).intersection(result3))
        print(final_result)
        # list1 = cur.execute(("SELECT EnrollmentNumber from Alumni A Where A.PassoutYear={} AND A.Degree='{}' AND A.CurrentState='Job' AND A.Branch='CSE' ").format(alumni_filter['passout_year'], alumni_filter['degree']))
        # print(list1)
        # list = cur.execute(("SELECT EnrollmentNumber from Alumni A Where A.PassoutYear={} AND A.Degree={} AND A.CurrentState=Job AND A.Branch=CSE ").format(alumni_filter['passout_year'], alumni_filter['degree'],alumni_filter['current_state'],alumni_filter['branch']))

        mysql.connection.commit()
        cur.close()
        # firstName = userDetails['firstName']
        # first_db = firstName
        # lastName = userDetails['lastName']
        # last_db = lastName
        # email = userDetails['email']
        # email_ = email
        print("alumni filter")
        # print(email_)
        # global string
        # string = email
        # password = userDetails['password'] 
        # password_db = password
        # new_user = User(firstName , lastName , email , password , users_repository.next_index())
        # users_repository.save_user(new_user)
        # return redirect(url_for('verification_page'))
    if flag == 1:
        return render_template("alumni.html", filter=final_result)
    else:
        return "Please Login first"
    
""" 
Return the condition of the query
Ex: Select * from Login Where Email = '*******'
    Here, condition on the above query is "Where Email = '*******'" .
"""
def GetCondition_On_Query(  dictionary_for_column):
    condition_on_query=""
    if len(dictionary_for_column)!=0 :
        condition_on_query=  " WHERE"
    index = 0
    for column in dictionary_for_column: 
        if len(dictionary_for_column) -1==index:
            condition_on_query =condition_on_query + " " +str(column) + "=" + "'{}'".format(dictionary_for_column[column])
        else:
            condition_on_query =condition_on_query + " " +str(column) + "=" + "'{}'".format(dictionary_for_column[column]) + " AND"
        index =index+ 1
    print("Condition on query is ", condition_on_query)
    return condition_on_query
        
        
students = []
output= []
# dictionary to select the tables whihc need to be queried.
dictionary = {"All" :["FirstYearStudent", "SecondYearStudent", "ThirdYearStudent", "FourthYearStudent"], "First":["FirstYearStudent"], "Second":["SecondYearStudent"], "Third":["ThirdYearStudent"], "Fourth":["FourthYearStudent"]}
dictionary_for_column = {}
@app.route("/login_page/students",methods=['GET','POST'])
def adminLogin():
    global students
    global output
    students = []
    dictionary_for_column ={}
    output =[]
    
    if request.method == 'POST':
        btech = request.form
        if btech['submit']== "submit":
            
            btech_year = btech['btech_year']
            branch = btech['branch']
            room_no = btech['room_no']
            hostels = btech['hostels']
            print("Branch- "+ branch + ", Room No- "+ room_no + ", Hostels-  "+ hostels)
            
            # conditions[Where clause] to use in MySQL queries
            if branch!="All":
                dictionary_for_column['Branch']= branch
            if room_no!="All":
                dictionary_for_column['Room_No']= room_no
            if hostels!="All":
                dictionary_for_column['Hostels']= hostels
            
            condition_on_query = GetCondition_On_Query(dictionary_for_column)
            cur = mysql.connection.cursor()
            for student_batch in dictionary[btech_year] :
                query = "select * from {}".format(student_batch)
                query = query + condition_on_query
                # query1 = query.replace("='All'","!=''")
                print("Query: ", query)
                cur.execute(query)

                result = cur.fetchall()
                students.append(list(result))
            # print(len(students))
            print(students)
            # for temp in students:
            #     student_list.append(temp)
            return render_template("students.html",students=students)
        elif btech['submit']=="Click here!":
            # import ./Scrapers/ImportData
            
            import os
            os.system('python ./Scrapers/ImportData.py')
            cur = mysql.connection.cursor()
            for student_batch in dictionary["All"]:
                filename = str(pathlib.Path(__file__).parent.absolute()) + "/Scrapers/" + str(student_batch) +".csv"
                query = "LOAD DATA LOCAL INFILE '{}' INTO TABLE {}  FIELDS TERMINATED BY "'","'" LINES TERMINATED BY 'newline' IGNORE 1 ROWS;".format(filename , student_batch)
                print(query)
                result = cur.execute( query)
                print(result)
            cur.close()
            output.append("Database has been updated!")
            return render_template("students.html", output=output)
        
    if flag == 1:
        return render_template("students.html")
    else:
        return "Please Login first" 

@app.route("/login_page/faculty")
def studentLogin():
    if flag == 1 :
        return render_template("faculty.html")
    else:
        return "Please Login first"

@app.context_processor
def context_processor():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Alumni Where EnrollmentNumber=%s",[alumni_no])
    alumni_basic_information = cur.fetchall()
    cur.execute("SELECT * FROM Contact_Details Where EnrollmentNumber=%s",[alumni_no])
    contact_deatils = cur.fetchall()
    cur.execute("SELECT * FROM Worked_In Where EnrollmentNumber=%s",[alumni_no])
    Worked_In = cur.fetchall()
    cur.execute("SELECT * FROM Higher_Studies Where EnrollmentNumber=%s",[alumni_no])
    Higher_Studies = cur.fetchall()
    cur.execute("SELECT * FROM Semester_Exchange Where EnrollmentNumber=%s",[alumni_no])
    sem_exchange = cur.fetchall()
    cur.execute("SELECT * FROM Contributed_To Where EnrollmentNumber=%s",[alumni_no])
    contribution = cur.fetchall()
    cur.close()
    return dict(students = students,username=string, alumni=alumni_basic_information, contact=contact_deatils, work=Worked_In, study=Higher_Studies, sem_exchange=sem_exchange, contribution=contribution)
    
if __name__ == "__main__":
    app.run(debug=True)
