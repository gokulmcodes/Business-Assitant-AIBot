from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import bcrypt
import requests
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'your_secret_key'

client = MongoClient('mongodb+srv://Team123:Team123@team.jophm.mongodb.net/')
db = client['businessAI']
users_collection = db['users']

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'mounicababe@gmail.com'
SENDER_PASSWORD = 'ervz jofn inod pamu'

def get_business_analysis_api(query):
    url = "https://free-chatgpt-api.p.rapidapi.com/chat-completion-one"
    params = {"prompt": query}
    headers = {
        "x-rapidapi-key": "a7b0734f2amsh73755e653a44facp1ce879jsn6decb4df32a6",
        "x-rapidapi-host": "free-chatgpt-api.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        try:
            response_data = response.json()
            content = response_data.get("response", "No valid response.")
            content = content.replace("###", "").replace("**", "")
            business_keywords = ["business", "strategy", "market", "startup", "economy", "finance", "investment"]
            if any(keyword in content.lower() for keyword in business_keywords):
                lines = content.split("\n")
                cleaned_content = "<br>".join([line.strip() for line in lines if line.strip()])
                return cleaned_content
            else:
                return "Error: This query is not related to business."
        except ValueError:
            return "Error parsing the response from the API."
    else:
        return f"Error {response.status_code}: Unable to fetch data from the API."

def send_email(name, email, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = 'mounicababe@gmail.com'
        msg['Subject'] = f"Contact Form Submission from {name}"
        body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, msg['To'], text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/features')
def features_page():
    return render_template('features.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if users_collection.find_one({'email': email}):
            flash('User already exists. Please try logging in.', 'danger')
            return redirect(url_for('signup'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({'email': email, 'password': hashed_password.decode('utf-8')})
        flash('Signup successful! Please log in to continue.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users_collection.find_one({'email': email})

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            flash('Login successful!', 'success')
            return redirect(url_for('index'))

        flash('Invalid email or password. Please try again.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    popup_message = None
    popup_status = None

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        if send_email(name, email, message):
            popup_message = "Email sent successfully!"
            popup_status = "success"
        else:
            popup_message = "Error sending email."
            popup_status = "error"

    return render_template('contact.html', popup_message=popup_message, popup_status=popup_status)

@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'POST':
        user_query = request.form.get('query')
        if not user_query:
            return render_template('result.html', response="No query provided.", query="")
        
        result = get_business_analysis_api(user_query)
        return render_template('result.html', response=result, query=user_query)

    return render_template('result.html', response="Reloading the page...", query="")

if __name__ == '__main__':
    app.run(debug=True)
