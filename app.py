from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
import bcrypt
import requests
from pymongo import MongoClient

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to MongoDB
client = MongoClient('mongodb+srv://Team123:Team123@team.jophm.mongodb.net/')  # Replace with your actual connection string
db = client['businessAI']  # Replace with your actual database name
users_collection = db['users']  # Replace 'users' with your actual collection name



def get_business_analysis_api(query):
    url = "https://gpt-4o7.p.rapidapi.com/v1/chat/completions"

    # Define the payload for the API request
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "u r a helpful assistant that always output in json."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "response_format": {"type": "json_object"},
        "store": True,
        "temperature": 1,
        "max_tokens": 2048,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    # Set up headers for the API request
    headers = {
        "x-rapidapi-key": "a7b0734f2amsh73755e653a44facp1ce879jsn6decb4df32a6",
        "x-rapidapi-host": "gpt-4o7.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    # Make the POST request to the API
    response = requests.post(url, json=payload, headers=headers)

    # Check if the response is successful
    if response.status_code == 200:
        try:
            # Parse the JSON response from the API
            response_data = response.json()

            # Extract the response message
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "No valid response.")

            # Split the content into points (assuming each point is on a new line)
            points = content.split("\n")

            # Format the points into a step-by-step list
            formatted_response = "<ul>"
            for point in points:
                if point.strip():  # Skip empty lines
                    formatted_response += f"<li>{point.strip()}</li>"
            formatted_response += "</ul>"

            return formatted_response  # Return as HTML list
        except ValueError:
            return "Error parsing the response from the API."
    else:
        return f"Error {response.status_code}: Unable to fetch data from the API."

# Route for Home Page
@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

# Route for About Page
@app.route('/about')
def about_page():
    return render_template('about.html')

# Route for Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the user already exists
        if users_collection.find_one({'email': email}):
            flash('User already exists. Please try logging in.', 'danger')
            return redirect(url_for('signup'))

        # Hash the password before saving
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert the new user into the database
        users_collection.insert_one({'email': email, 'password': hashed_password.decode('utf-8')})
        flash('Signup successful! Please log in to continue.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Route for Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Retrieve the user from the database
        user = users_collection.find_one({'email': email})

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            flash('Login successful!', 'success')
            return redirect(url_for('index'))

        flash('Invalid email or password. Please try again.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')

# Route for Results Page
@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'POST':
        user_query = request.form.get('query')
        if not user_query:
            return render_template('result.html', response="No query provided.", query="")
        
        result = get_business_analysis_api(user_query)
        
        return render_template('result.html', response=result, query=user_query)
    
    # If GET request, redirect to home
    return redirect(url_for('home_page'))

if __name__ == '__main__':
    app.run(debug=True)
