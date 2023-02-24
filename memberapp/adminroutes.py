from flask import render_template, redirect, flash, session,request,url_for
from sqlalchemy.sql import text
from werkzeug.security import generate_password_hash, check_password_hash

from memberapp import app,db
from memberapp.models import Party,Topics

@app.route('/admin',methods=["POST","GET"])
def admin_home():

    if request.method == "GET":
        return render_template("admin/adminreg.html")
    else:        
        username = request.form.get("username")
        password = request.form.get("pwd")
        #convert the plain password to hashed value and insert into database
        hashed_pwd = generate_password_hash(password)

        #insert into database
        if username != "" or password != "":
            # return ""
            query = f"INSERT INTO admin SET admin_username='{username}', admin_pwd='{hashed_pwd}'"
            # data = (username,password)

            db.session.execute(text(query))
            db.session.commit()
            flash("Registration Successful, Login here")
            return redirect(url_for('admin_home'))
        else:
            flash("Username or Password must be supplied")
            return redirect(url_for('admin_home'))

'''Without Hashed Password'''
# @app.route("/admin/login", methods=["POST","GET"])
# def login():
#     if request.method == "GET":
#         return render_template("admin/adminlogin.html")
#     else:
#         username = request.form.get("username")
#         password = request.form.get("pwd")
#         #write SELECT query
#         query = f"SELECT * FROM admin WHERE username='{username}' AND password='{password}'"
#         result = db.session.execute(text(query))
#         total = result.fetchall()
#         if total: #the login details are correct
#             #log him in by saving his details in session
#             session['loggedin']=username
#             return redirect("/admin/dashboard")
#         elif username == "" or password == "":
#             flash("Username or Password cannont be empty")
#             return redirect("/admin/login")
#         else:
#             flash("Invalid Credentials")
#             return redirect("/admin/login")

@app.route("/admin/login", methods=["POST","GET"])
def login():
    if request.method == "GET": #user refreshes the pagelink or enters with the login url
        return render_template("admin/adminlogin.html") #take him back to the login page
    else:
        username = request.form.get("username") #get username from the input 'name' attribute
        password = request.form.get("pwd") #get password from the input 'name' attribute
        #write SELECT query
        query = f"SELECT * FROM admin WHERE admin_username='{username}'"
        result = db.session.execute(text(query))
        total = result.fetchone()
        if total: #the login username exist
            pwd_indb = total[2] #Position of (hashed) password in the db
            #compare this hashed with the pwd coming from the form
            chk = check_password_hash(pwd_indb,password) #returns True or False

            if chk == True: #login is successful, save his details in a session
                session['loggedin']=username
                return redirect("/admin/dashboard")
            elif username == "" or password == "":
                flash("Username or Password cannont be empty")
                return redirect(url_for('login'))
            else:
                flash("Invalid Credentials")
                return redirect(url_for('login'))
        else:
            flash("Invalid Credentials")
            return redirect(url_for('login'))

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get('loggedin') != None:
        return render_template("admin/admindashboard.html")
    else:
        return redirect("/admin/login")

@app.route("/admin/logout")
def admin_logout():
    if session.get("loggedin") != None:
        session.pop("loggedin",None)
    return redirect('/admin/login')

@app.route("/admin/party",methods=["POST","GET"])
def add_party():
    if session.get("loggedin") == None:
        return redirect(url_for("login"))
    else:
        if request.method == "GET":
            return render_template("admin/adminaddparty.html")
        else:
            pname = request.form.get('partyname')
            code = request.form.get('partycode')
            pcontact = request.form.get('partycontact')
            #INSERT INTO THE PARTY TABLE USING ORM METHOD
            #step1: create an instance of Party (ensure that Party is imported)
            #obj = Classname(column1=value,column2=value)
            p = Party(party_name=pname, party_shortcode=code, party_contact=pcontact)
            #step2: add to session
            db.session.add(p)
            #step3: commit the session
            db.session.commit()
            flash("Party Added")
            return redirect(url_for('parties'))

@app.route('/admin/parties')
def parties():
    if session.get('loggedin') != None:
        #we will fetch from db using ORM method
        #to display the values in the order we choose(how we want it to be ordered)
        data = db.session.query(Party).order_by(Party.party_shortcode).all()
        data = db.session.query(Party).order_by(Party.party_name).all()
        return render_template("admin/all_parties.html",data=data)
    else:
        return render_template("/admin/login")   


@app.route('/admin/topic/delete/<id>')
def delete_post(id):
    topicobj = Topics.query.get_or_404(id)
    db.session.delete(topicobj)
    db.session.commit()
    flash("Successfully deleted!")
    return redirect(url_for("all_topics"))

@app.route('/alltopics')
def all_topics():
    if session.get('loggedin') == None:
        return redirect("/login")
    else:
        # topicsall = db.session.query(Topics).all()
        alltopics = Topics.query.all()
        return render_template("/admin/alltopics.html",alltopics=alltopics)

@app.route('/admin/topic/edit/<id>')
def edit_topic(id):
    if session.get('loggedin') !=None:
        topic_deets = Topics.query.get(id)
        return render_template('/admin/edit_topic.html',topic_deets=topic_deets)
    else:
        return redirect(url_for("login"))

@app.route("/admin/update_topic", methods=["POST"])
def update_topic():
    if session.get('loggedin') !=None:
        newstatus = request.form.get('status')
        topicid = request.form.get('topicid')
        t = Topics.query.get(topicid)
        t.topic_status = newstatus
        db.session.commit()
        flash("Topic successfully updated")
        return redirect(url_for("all_topics"))
    else:
        return redirect("/admin/login")