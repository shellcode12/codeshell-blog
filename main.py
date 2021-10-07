from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
import math
# we want our config files parameters in params

with open('config.json', 'r') as c:
    params = json.load(c)["params"]



app = Flask(__name__)

app.secret_key = 'super-secret-key'

app.config['UPLOAD_IMG_FOLDER'] = params['upload_img_location']
app.config['UPLOAD_FILE_FOLDER'] = params['upload_file_location']

mail=Mail(app)
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']

)


if(params['local_server']):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']




db = SQLAlchemy(app)


# class for defining database table

# sno	name	email	phone_num	mes	date
class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_num = db.Column(db.String(120), nullable=False)
    mes = db.Column(db.String(120), nullable=False)
    date= db.Column(db.String(12), nullable=True)

# class to access posts
class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(15), nullable=False)
    img_file = db.Column(db.String(15), nullable=True)
    filename= db.Column(db.String(15), nullable=False)



@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))

    # [0:params['no_of_posts']]

    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1

    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts']) +int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page-1)
        next = "/?page=" + str(page+1)


    return render_template('index.html', params=params, posts= posts, prev = prev, next = next)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/contact", methods = ['GET','POST'])
def contact():

    if(request.method =='POST'):
        name = request.form.get('name')
        email= request.form.get('email')
        phone= request.form.get('phone')
        message=request.form.get('message')


        entry = Contacts(name = name, email = email , phone_num = phone , mes = message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from'+name,
                          sender= email,
                          recipients = [params['gmail-user']],
                          body = message +"\n" +phone
                          )



    return render_template('contact.html', params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()
    return render_template('post.html', params=params , post=post)


@app.route("/dashboard", methods = ['GET','POST'])
def dashboard():

    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params,posts = posts)


    if request.method =="POST":
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username==params['admin_user'] and userpass == params['admin_password']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts= posts)



    else:
        return render_template('login.html', params=params)

    return render_template('login.html', params=params)




@app.route("/edit/<string:sno>", methods =['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            # tline = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img')
            filename = request.form.get('file')
            date = datetime.now()

            if sno == '0':
                post = Posts(title=box_title, slug=slug, content=content, img_file=img_file, filename=filename,date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.filename = filename
                post.date = date

                db.session.commit()
                return redirect('/edit/'+sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)

@app.route("/imageuploader",methods =['GET','POST'])
def imgupload():
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method=='POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_IMG_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Susscessfully"


@app.route("/fileuploader",methods =['GET','POST'])
def fileupload():
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method=='POST':
            f = request.files['file2']
            f.save(os.path.join(app.config['UPLOAD_FILE_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Susscessfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

app.run(debug=True)