import os,random,string,json,requests
#random is a model in python
from sqlalchemy import or_
from flask import render_template, redirect, flash, session,request,url_for

from werkzeug.security import generate_password_hash, check_password_hash

from memberapp import app,db,csrf
from memberapp.models import User,Party,Topics,Contact,Comments,Lga,State,Donation,Payment
from memberapp.forms import ContactForm


def generate_name():
    filename = random.sample(string.ascii_lowercase,10) #this will return a list
    return ''.join(filename) #here we join every member of the list "filename"


#create the routes
@app.route("/")
def home():
    # return app.config["SERVER_ADDRESS"]
    contact = ContactForm()
    #connect to the endpoint to get the list of properties in JSON format,
    #Convert to python dictionary and pass it to our template
    try:
        response = requests.get("http://127.0.0.1:8020/api/v1.0/listall")
        if response:
            rspjson = json.loads(response.text)
        else:
            rspjson = dict()
    except:
        rspjson = dict()
    return render_template("user/home.html", contact=contact,rspjson=rspjson)

@app.route("/ajaxcontact",methods=['POST'])
def contact_ajax():
    form = ContactForm()
    if form.validate_on_submit():
        email = request.form.get('email')
        msg = request.form.get('message')
        #insert into database and send the feedback to AJAX/Javascript
        return f"{email} and {msg}"
    else:
        return "You need to complete the form"
    
#payment
@app.route("/donate",methods=["POST","GET"])
def donate():
    if session.get('user') != None:
        deets= User.query.get(session.get('user'))
    else:
        deets=None    
    if request.method =='GET':
        return render_template('user/donation_form.html',deets=deets)
    else:
        #retrieve the form data and insert into Donation table
        amount = request.form.get('amount')
        fullname = request.form.get('fullname')
        d = Donation(don_donor=fullname,don_amt=amount,don_userid=session.get('user'))
        db.session.add(d); db.session.commit()
        session['donation_id'] = d.don_id
        #Generate the ref no and keep in session
        refno = int(random.random()*100000000)
        session['reference'] = refno
        return  redirect("/confirm") 
 
@app.route('/confirm',methods=['POST','GET'])
def confirm():
    if session.get('donation_id')!= None:
        if request.method =='GET':  
            donor = db.session.query(Donation).get(session['donation_id'])
            return render_template('user/confirm.html',donor=donor,refno=session['reference'])
        else:
            p = Payment(pay_donid=session.get('donation_id'),pay_ref=session['reference'])
            db.session.add(p);db.session.commit()
            
            don = Donation.query.get(session['donation_id'])#details of the donation
            donor_name = don.don_donor
            amount = don.don_amt * 100
            headers = {"Content-Type": "application/json","Authorization":"Bearer sk_live_252a73a0b20a5a1694cb73c25d4da58a8f7dc563"}
            data={"amount":amount,"reference":session['reference'],"email":donor_name}
            
            response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, data=json.dumps(data))
            rspjson= json.loads(response.text)
            if rspjson['status'] == True:
                url = rspjson['data']['authorization_url']
                return redirect(url)
            else:
                return redirect('/confirm')
    else:
        return redirect('/donate')
    
@app.route('/paystack')
def paystack():
    refid = session.get('reference')
    if refid ==None:
        return redirect('/')
    else:
        #connect to paystack verify
        headers={"Content-Type": "application/json","Authorization":"Bearer sk_live_252a73a0b20a5a1694cb73c25d4da58a8f7dc563"}
        verifyurl= "https://api.paystack.co/transaction/verify/"+str(refid)
        response= requests.get(verifyurl, headers=headers)
        rspjson = json.loads(response.text)
        if rspjson['status']== True:
            #payment was successful
            return rspjson
        else:
            #payment was not successful
            return "payment was not successful"

@app.route('/signup')
def user_signup():
    partyname = db.session.query(Party).all()
    return render_template("user/signup.html",partyname=partyname)

@app.route("/register", methods=["POST"])
def register():
    email = request.form.get("email")
    password = request.form.get("pwd")
    party_id = request.form.get("party")
    hashed_pwd = generate_password_hash(password)
    
    if party_id !="" and email !="" and password !="":
        u = User(user_fullname = "", user_email=email, user_pwd=hashed_pwd, user_partyid=party_id)
        db.session.add(u)
        db.session.commit() 
        #Keep user_id in session
        userid = u.user_id
        session['user']= userid
        return redirect(url_for('dashboard'))
        # return "Done"
    else:
        flash("You must complete all fields")
        return redirect(url_for("signup"))

@app.route("/check_username", methods=["POST","GET"])
def check_username():
    if request.method == "GET":
        return "Please complete the form normally"
    else:
        email = request.form.get("email")
        fetchemail = db.session.query(User).filter(User.user_email==email).first()
        if fetchemail == None:
            sendback = {'status':1, 'feedback':"Email is available, please register"} 
            return json.dumps(sendback)
        else:
            sendback = {'status':0, 'feedback':"Email address already registered, please click <a href='/login'>here</a> to login"}
            return json.dumps(sendback)

@app.route("/profile/dashboard")
def dashboard():
    #protect this route so only logged in users can get here
    if session.get('user') != None:
        #retrive the details of the logged in user
        id = session['user']
        deets = db.session.query(User).get(id)
        return render_template('user/dashboard.html',deets=deets)
    else:
        return redirect(url_for("user_login"))
        
@app.route("/login", methods=["POST","GET"])
def user_login():
    if request.method == "GET":
        return render_template("user/login.html")
    else:
        #retrieve the form data
        email = request.form.get('email')
        password = request.form.get("pwd")
        #run a query to know if the email exists on the database
        deets = db.session.query(User).filter(User.user_email==email).first()
        #compare the password coming from the form with the hashed password in the db
        if deets != None:
            pwd_indb = deets.user_pwd
            #compare with the plain password from the form with hash pwd in db
            chk = check_password_hash(pwd_indb,password)
            if chk:
                userid = deets.user_id
                session['user'] = userid
                return redirect(url_for("dashboard"))
                #we should log the person in
            else:
                flash("Invalid Password")
                return redirect(url_for('user_login'))
        else:
            flash("Invalid Email")
            return redirect(url_for('user_login'))
        
@app.route("/demo", methods=["POST","GET"])
def demo():
    # if request.method =='GET':     
        
    #     return render_template("user/test.html")
    # else:
    #     #retrieve form data 
    #     file = request.files.get('pix')
    #     picture_name = file.filename
    #     file.save("membapp/static/uploads/"+picture_name)
    #     return f'{picture_name}'
    
    data= db.session.query(Party).filter(Party.party_id == 1).all()
    data= db.session.query(Party).get(1)
    data = db.session.query(User).all()
    data = db.session.query(Party).filter(Party.party_id >1, Party.party_id <=6).all()#This is the same as this below
    data = db.session.query(Party).filter(Party.party_id >1).filter(Party.party_id <=6).all()

    # log = db.session.query(User).filter(User.user_username == email).filter(User.user_pwd == password).first() #(.first() gives us None...While .all() gives an empty list) if the username and password doesn't exist
    '''data = db.session.query(User,Party).join(Party).all() #to join 2 tables together and get elements from each that matches eachother.'''
    data1 = db.session.query(User.user_fullname,Party.party_name,Party.party_shortcode,Party.party_contact).join(Party).all() #to join specific data from 2 tables together and get elements from each that matches eachother.
    data = User.query.join(Party).add_columns(Party).all()
    data = User.query.join(Party).filter(Party.party_name=='Labour Party').add_columns(Party).all()
    data = Party.query.join(User).filter(User.user_fullname.like("%Williams")).add_columns(User).all()
    data = Party.query.join(User).filter(User.user_fullname.ilike("%Williams")).add_columns(User).all()
    '''Using and and or'''
    data = Party.query.join(User).filter(or_(User.user_fullname == "%Williams", Party.party_name=="PDP")).add_columns(User).all()

    data = User.query.filter(Party.party_id==1).first()

    data = db.session.query(Party).filter(Party.party_id==1).first()

    data= db.session.query(User).get(1)
    

    data = User.query.join(Party).filter(Party.party_id==1).add_columns(Party).all()
    data = User.query.join(Party).filter(Party.party_id.like("%")).add_columns(Party).all()

    data = db.session.query(User, Party).join(Party).all()

    # x= datum.user_fullname

    return render_template("user/test.html",data=data)

@app.route("/homelayout")
def form_layout():
    return render_template('user/home_layout.html')

@app.route('/signout')
def user_logout():
    #pop the session and redirect to homepage
    if session.get('user') !=None:
        session.pop('user',None)
        return redirect(url_for('user_login'))

@app.route("/load_lga/<stateid>")
def load_lga(stateid):
    lgas = db.session.query(Lga).filter(Lga.lga_stateid==stateid).all()
    data2send = "<select class='form-control border-success'>"
    for s in lgas:
        data2send = data2send+"<option>"+s.lga_name +"</option>"
    data2send = data2send + "</select>"
    # stateid = request.args.get("stateid")
    return data2send

@app.route('/profile',methods=["POST","GET"])
def profile():
    id = session.get('user')
    if id ==None:
        return redirect(url_for('user_login'))
    else:
        if request.method =="GET":
            allstates = db.session.query(State).all()
            deets = db.session.query(User).filter(User.user_id==id).first()
            allparties = Party.query.all()
            return render_template('user/profile.html',deets=deets,allstates=allstates,allparties=allparties)
        else: #form was submitted
            fullname = request.form.get('fullname')
            phone = request.form.get('phone')
            #update the db using ORM methof
            userobj = db.session.query(User).get(id)
            userobj.user_fullname = fullname
            userobj.user_phone = phone
            db.session.commit()
            flash("Profile Updated!")
            return redirect("/profile")

@app.route('/profile/picture', methods=["POST","GET"])
def profile_picture():
    if session.get('user') ==None:
        return redirect(url_for('user_login'))
    else:
        if request.method == 'GET':
            return render_template('user/profile_picture.html')
        else:
            #retrieve the file
            file = request.files['pix']

            filename = file.filename #to know the filename
            filetype = file.mimetype #the type of file
            allowed = ['.png','.jpg','.jpeg']
            if filename !="":
                name,ext = os.path.splitext(filename) #import 'os' on line 1
                if ext.lower() in allowed: #convert file ext to lowercase, just to be sure
                    newname = generate_name()+ext
                    file.save("memberapp/static/uploads/"+newname) #save in this location
                    # user = db.session.query(User).get(id)
                    # user.user_pix = newname
                    db.session.commit()
                    return redirect(url_for('dashboard'))
                else:
                    return "File not allowed"
            else:
                flash("Please choose a File")
                return "Form was submitted here"

@app.route("/blog")
def post():
    articles = db.session.query(Topics).filter(Topics.topic_status=='1').all()
    return render_template("user/blog.html",articles=articles)

@app.route("/blog/<id>/")
def blog_details(id):
    # blog_deets = db.session.query(Topics).filter(Topics.topic_id==id).first()
    # # blog_deets = db.session.query(Topics).get()
    blog_deets= Topics.query.get_or_404(id)
    return render_template('user/blog_details.html',blog_deets=blog_deets)

@app.route('/sendcomment')
def sendcomment():
    id=session.get('user')
    if id:
        #retrive the data coming from the request
        # message = request.args.get('comments')
        message = request.args.get('message')
        userid = request.args.get('userid')
        topicid = request.args.get('topicid')

        comment = Comments(comment_text=message, comment_userid=userid, comment_topicid=topicid)
        db.session.add(comment)
        db.session.commit()

        commenter = comment.commentby.user_fullname
        dateposted = comment.comment_date
        sendback = f"{message} <br> by {commenter} on {dateposted}"
        return sendback
    else:
        return "You need to be logged in to make comments"

@app.route("/newtopic",methods=["POST","GET"])
def newtopic():
    if session.get("user") !=None:
        if request.method == "GET":
            return render_template("user/newtopic.html")
        else:
            #retrive form data and validate
            content = request.form.get('content')
            if len(content) > 0:
                t = Topics(topic_title=content, topic_userid=session['user'])
                db.session.add(t)
                db.session.commit()
                if t.topic_id: #means a topic id has been created as a result of the post
                    flash("<div class='alert alert-success'>Post successfully submitted for approval</div>")
                else:
                    flash("<div class='alert alert-danger'>OOps, something went wrong. Please try again</div>")
            else:
                flash("<div class='alert alert-danger'>You cannot submit an empty post</div>")
            return redirect("/blog")
    else:
        return redirect(url_for("user_login"))

@app.route('/contact',methods=["POST","GET"])
def  contact_us():
    contact = ContactForm()
    if request.method =="GET":
        return render_template("user/contactus.html",contact=contact)
    else:
        if contact.validate_on_submit():
            upload = request.files['screenshot']
            email = request.form.get('email')
            msg = contact.message.data #like the above, retrive message from input
            data = Contact(msg_email=email, msg_content=msg)
            db.session.add(data)
            db.session.commit()
            flash("<div class='alert alert-success'>Thank you for contacting us</div>")
            return redirect(url_for("contact_us"))
        else:
            return render_template("user/contactus.html",contact=contact)

