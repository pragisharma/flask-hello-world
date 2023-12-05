# we love standard libraries!
import json
import os
import sqlite3

# # other libraries~~
from flask import Flask, redirect, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

# internal imports :0 
from db import init_db_command
from user import User

# config (can also hard code here, but prob dont b/c of security)
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# user session management setup stuff 
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# db setup 
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    print("db already created")
    pass

# oauth 2 client setup T-T 
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper which gets info from user from our db!!


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route("/")
def index():
    if current_user.is_authenticated: ## ty Flask-Login :D 
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'
    
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()
## could implement error handling here in case google fails us (or the user) ;-;


@app.route("/login")
def login():
    # google login url 
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # this library lets us ask google to give permission to get user 
    # profile info (basically getting info from google w users consent)
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

# this happens when google sends back the unique code (asking for permission to use users info)
@app.route("/login/callback")
def callback():
    code = request.args.get("code")
    # find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user 
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    #  send a request to get tokens! yay tokens~!! T-T
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    # parse tokens... oauthlib to the rescue! 
    client.parse_request_body_response(json.dumps(token_response.json()))

    # google gave us tokens for the users profile info (pfp + email)

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # confirm email verification
    # yay if user has a google acct, they authorize with our app
    # and we verify the email through goooogleee pls work!!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400
    # Create a user in your db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required # "decorator" (only logged-in users can use this )
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(ssl_context="adhoc")
   
    
# done done! code ends here... 

###############################################################
# @app.route('/')
# def home():
#     return 'Hello, World!'

# @app.route('/about')
# def about():
#     return 'About'

##############
# export FLASK_APP=index.py
# python3 -m flask run