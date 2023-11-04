import base64
from datetime import datetime
from SportyBuddies import app
from flask import Response, jsonify, render_template,request, redirect, url_for
from flask_login import LoginManager,login_user, logout_user, current_user
import mysql.connector


 
db = mysql.connector.connect(
    host = "localhost",
    user = "root",
    passwd = "",
    database = "sportybuddies"
)
app.secret_key = "secret"
 
login_manager = LoginManager()
login_manager.init_app(app)
 
class User:
    def __init__(self, user_id):
        self.id = user_id

        
    @property
    def is_active(self):
        # Add logic to determine if the user is considered active
        return True

    @property
    def is_authenticated(self):
        # Add logic to determine if the user is authenticated
        return True

    @property
    def is_anonymous(self):
        return False


    def get_id(self):
        return str(self.id)
 


@login_manager.user_loader
def load_user(user_id):
    cursor = db.cursor()
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    
    cursor.close()
    if user:
        return User(user[0])
    return None
 
@app.route('/upload_photo',methods=['POST'])
def upload_photo():
    
    if 'photo' not in request.files:
        return redirect(request.url)
    photo = request.files['photo']
    
    if photo.filename == '':
        return redirect(request.url)
    
    if photo:
        photo_data = photo.read()
        cursor=db.cursor()
        cursor.execute("UPDATE users SET photo=%s WHERE user_id=%s", (photo_data,current_user.id))
        db.commit()
        cursor.close()
    
    return redirect(url_for('user_profile'))

@app.route('/user_profile')
def user_profile():
    if current_user.is_authenticated==False:
        return redirect(url_for('login'))

    cursor = db.cursor()

    cursor.execute("SELECT name FROM users WHERE user_id = %s", (current_user.id,))
    username = cursor.fetchone()[0]

    cursor.execute("SELECT sport_id FROM user_sports WHERE user_id = %s", (current_user.id,))
    results=cursor.fetchall()
    user_sports=[result[0] if result[0]>0 else 0 for result in results[:15]]
    sports=[0]*15
    for i in user_sports:
        if i>0:
            sports[i-1]=i
            

    return render_template(
        'user_profile.html',
       result = username,
       user_sports=sports,
    )

@app.route('/get_user_photo')
def get_user_photo():
    cursor = db.cursor()
    cursor.execute("SELECT photo FROM users WHERE user_id = %s", (current_user.id,))
    photo_data=cursor.fetchone()[0]
    cursor.close()

    # Return the photo as a response
    return Response(photo_data, content_type='image/jpeg')  # Adjust content_type as needed

@app.route('/update_user_sports',methods=['POST'])
def update_user_sports():
    sport_id = request.form.get('sportId')
    is_checked = request.form.get('isChecked')
    
    cursor = db.cursor()
    if is_checked == 'true':
        cursor.execute("INSERT INTO user_sports (user_id,sport_id) VALUES (%s,%s)", 
                       (current_user.id,sport_id))
    else:
        cursor.execute("DELETE FROM user_sports WHERE user_id = %s AND sport_id=%s", 
                       (current_user.id,sport_id))
        
    db.commit()
    cursor.close()
    return jsonify({'status': 'success'})

@app.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        age = request.form['age']
        gender = request.form['gender']
        description = request.form['description']
        password = request.form['password']

        
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (email, password, name, age, gender, info) VALUES (%s, %s, %s, %s, %s, %s)",
                       (email, password, username, age, gender, description))
        db.commit()
        cursor.close()
        
        return redirect(url_for("login"))
    
    return render_template("register.html")
 
 
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = db.cursor()
        cursor.execute("SELECT user_id FROM users WHERE name = %s AND password = %s", (username, password))
        user_id = cursor.fetchone()
        cursor.close()
        if user_id:
            user = User(user_id[0])
            login_user(user)
            return redirect(url_for('home'))
        
    return render_template('login.html')
 
 
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route('/')
@app.route('/home')
def home():
    if current_user.is_authenticated:
        cursor = db.cursor()
        cursor.execute("SELECT name FROM users WHERE user_id = %s", (current_user.id,))
        username = cursor.fetchone()[0]
        cursor.close()
    else:
        username=None
    
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
        user_info=username
    )

@app.route('/contact')
def contact():
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )

