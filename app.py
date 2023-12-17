import requests
from flask import Flask, request, render_template,redirect, session, url_for, flash, send_from_directory, jsonify 
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from paystackapi.paystack import Paystack
import re



import os
from werkzeug.utils import secure_filename



# Import the whole module
import datetime
# Use the function as datetime.datetime.utcnow
now = datetime.datetime.utcnow()

# Import only the class
from datetime import datetime
# Use the function as datetime.utcnow
now = datetime.utcnow()

import random

from flask_mail import Mail, Message





app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fintech.db'
app.secret_key = "89iudh8789f7bd89789f7d9yf787d97f987d897f29"
paystack_secret_key = os.getenv("PAYSTACK_SECRET_KEY")
paystack = Paystack(secret_key=paystack_secret_key)
db = SQLAlchemy(app)



# Your existing code here...

# Configure the mail settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] =  587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'c02474094@gmail.com'
app.config['MAIL_PASSWORD'] = 'ahyvweniwvpghfqw'


# Initialize the mail object
mail = Mail(app)



app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/img'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

app.config['BLOG'] = "static/blog"
app.config['ALLOWED_EXTENSIONS'] = {'PNG', 'jpg', 'jpeg', 'gif', 'pdf'}




class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    phone_number= db.Column(db.Integer, nullable = False)
    email = db.Column(db.String, nullable=False, unique=True)
    account_number = db.Column(db.String, nullable=False , unique=True)
    cash = db.Column(db.Integer, nullable=False, default=20000)
    profile_pic = db.Column(db.String)
    cash_history = db.relationship('CashHistory', backref='user', lazy=True)
    
   

    def __str__(self):
     return '<User %r>' % self.username

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    logged_in_user = db.Column(db.String, db.ForeignKey('user.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Transaction %r>' % self.id


class Comments(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    
    user = db.Column(db.String, nullable = False)
    image = db.Column(db.String, nullable = False)
    content = db.Column(db.String, nullable = False)
    
    def __str__(self):
        return '<Comments %r>' % self.content
    
class CashHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cash = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable = False )
    image = db.Column(db.String, nullable = False )
    content = db.Column(db.String, nullable = False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# to use transaction class
# paystack.transaction.list()

# # to use customer class
# paystack.customer.get(transaction_id)

# # to use plan class
# paystack.plan.get(plan_id)

# # to use subscription class
# paystack.subscription.list()
    

# import requests
# import json

# url = "https://api.paystack.co/transfer"
# headers = {
#     "Authorization": "Bearer YOUR_SECRET_KEY",
#     "Content-Type": "application/json"
# }

# data = {
#     "source": "balance",
#     "reason": "Savings",
#     "amount": 30000,
#     "recipient": "RCP_1a25w1h3n0xctjg"
# }

# response = requests.post(url, headers=headers, data=json.dumps(data))

# print(response.json())


@app.route("/access")
def access():
    return render_template("paystack.html")



@app.route('/pay', methods=['POST'])
def pay():
    # Get the credit card details submitted by the form
    email = request.form['email']
    amount = request.form['amount']  # amount in kobo
    
    # Find the user in the database
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('user not found')
        return redirect("/access")

    # Set up a dictionary with the parameters you want to send to Paystack
    payload = {
        "email": email,
        "amount": amount
    }

    headers = {
        'Authorization': f'Bearer {paystack_secret_key}',
        'Content-Type': 'application/json',
    }

    # Send a POST request to Paystack's charge endpoint
    response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, json=payload)

    # If the request was successful, get the authorization URL from the response and redirect the user to it
    if response.status_code == 200:
        data = response.json()
        return redirect(data['data']['authorization_url'])
    else:
        return 'An error occurred while trying to process the payment.'
    

@app.route('/payment_callback')
def payment_callback():
    # Get the transaction reference from the URL
    transaction_reference = request.args.get('reference')

    headers = {
        'Authorization':  f'Bearer {paystack_secret_key}',
        'Content-Type': 'application/json',
    }

    # Verify the transaction
    response = requests.get(f'https://api.paystack.co/transaction/verify/{transaction_reference}', headers=headers)

    if response.status_code == 200:
        data = response.json()
        status = data['data']['status']
        if status == 'success':
            # The transaction was successful
            # You can now update your records and notify the user
            user = User.query.filter_by(email=data['data']['customer']['email']).first()
            if user:
                transaction_amount = int(data['data']['amount']) / 100  # Convert amount back to original currency
                user.cash -= transaction_amount
                transaction = Transaction(logged_in_user=user.id, amount=transaction_amount)
                cash_history = CashHistory(user_id=user.id, cash=user.cash)
                db.session.add(transaction)
                db.session.add(cash_history)
                db.session.commit()

            return 'Payment was successful.'
        else:
            # The transaction failed
            return 'Payment failed.'
    else:
        return 'Could not verify payment.'

@app.route('/cash_history/<username>')
def cash_history(username):
    user = User.query.filter_by(username=username).first()
    if user:
        cash_history = user.cash_history
        return render_template('cash_history.html', cash_history=cash_history)
    else:
        return 'User not found.'
    
@app.route('/transactions')
def transactions():
    # Get all transactions
    transactions = Transaction.query.all()

    # Pass the transactions to the template
    return render_template('transactions.html', transactions=transactions)


   

@app.route("/", methods=['GET'])
def walletpage():
    if not session.get("user"):
        return redirect("/signin")
    
    logged_in_user = session.get("user")
    user = User.query.filter_by(username=logged_in_user['username']).first()
    username = user.username
    account_number = user.account_number
    cash = user.cash

    # Query the Transaction model for transactions related to the user
    transactions = Transaction.query.filter_by(sender_id=user.id).all()

    data = {
        'labels': ['Optimum value', 'intermediate', 'medium', username],
        'values': [200000,  160000, 100000, cash]
    }
    
    copied  = {'value':account_number}
    
    

    
    return render_template("index.html", user=user, username=username, account_number=account_number, cash=cash, data=data, copied=copied, transactions=transactions)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/blog/<filename>')
def blog_file(filename):
    return send_from_directory(app.config['BLOG'], filename) 


@app.route("/users")
def user():
    if not session.get("user"):
        return redirect("/signin")
    users = User.query.all()
    # comments = Comments.query.all()
    Comment = Comments.query.all()
    image = User.query.first()
    return render_template("user.html", users = users, image = image, Comment =  Comment, user = user)



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
           
@app.route("/comments", methods=["POST"])
def comments():
    
    if request.method == "POST":
        
       content = request.form  
       logged_in_user = session.get('user')
       user =  User.query.filter_by(username = logged_in_user['username']).first()
       username = user.username
       image = user.profile_pic
       data = content['comment'] 
       if data.strip() == "":
            flash("empty user input ")
            return redirect("/users")
       comments = Comments(content = data, user= username, image = image )   
       db.session.add(comments) 
       db.session.commit()
       return redirect("/users")
      
      
    
    
    

@app.route("/userprofile")
def userprofile():
 if not session.get('user'):
     return redirect('/signin')
 logged_in_user = session.get('user')
 user = User.query.filter_by(username=logged_in_user['username']).first()
 username = user.username
 email = user.email
 phonenumber = user.phone_number
 cash = user.cash
 data = {
          'labels': ['Optimum value', 'intermediate', 'medium', username],
        'values': [200000,  160000, 100000, cash]
    }
 return render_template('account.html', user = user, username=username, email = email, phonenumber = phonenumber, data = data) 
 
 
 






 
    




    

        





@app.route('/viewprofile/<username>')
def viewprofile(username):
    if not session.get('user'):
        return redirect("/signin")
    user = User.query.filter_by(username = username).first()
    username = user.username
    phonenumber = user.phone_number
    if not user:
        flash('User not found', 'danger')
        return redirect('/usermessage')
    return render_template('userinfo.html', user = user , username = username, phonenumber = phonenumber)
    












@app.route("/transaction_history", methods=['GET'])
def transaction_history():
    # Check if user is logged in
    if not session.get('user'):
        return redirect("/signin")
    logged_in_user = session.get('user')
    user = User.query.filter_by(username=logged_in_user['username']).first()
    username = user.username

    # Check if user exists in the database
    if user is None:
        return "User not found", 404

    # Get transactions and order them by timestamp
    sent_transactions = Transaction.query.filter_by(sender_id=user.id).order_by(Transaction.timestamp.desc()).all()
    for transaction in sent_transactions:
        transaction.receiver_username = User.query.get(transaction.receiver_id).username
    received_transactions = Transaction.query.filter_by(receiver_id=user.id).order_by(Transaction.timestamp.desc()).all()
    for transaction in received_transactions:
        transaction.sender_username = User.query.get(transaction.sender_id).username

    return render_template("transaction_history.html",  username = username, 
                           sent_transactions=sent_transactions,
                           received_transactions=received_transactions)



@app.route("/about")
def aboutpage():
    if not session.get('user'):
        return redirect("/signin")
    return render_template("about.html")



@app.route("/admin" , methods = ['GET', 'POST'])
def admin():
    if request.method == "GET":
        return render_template("/admin.html")
    if request.method == "POST":
        data = request.form
        name = 'munachimso'
        passw = 'Onewithgod'
        username = data["username"]
        password = data["password"]
        if username == name and password == passw:
            flash("Dev_admin welcome to your app feel free to make  app updates ")
            return redirect("/adminpost")
        else:
          flash("This page is only mearnt for the tech administrator")
          return redirect("/admin")


     
@app.route("/adminpost", methods=["GET","POST"])
def adminpost():
  if request.method == "GET":
        return render_template('adminpost.html')
  if request.method == "POST":
    def allowed_file(filename):
      return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    data = request.form 
    title = data['title']
    image = request.files['image']
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['BLOG'], filename))
    content = data['content']
    blog = Blog( title = title , image = filename , content = content  )
    db.session.add(blog)
    db.session.commit()
    return redirect("/blog")  




@app.route("/blog")
def blog():
    blog = Blog.query.order_by(Blog.timestamp.desc()).all()
    # blog = Blog.query.order_by(Blog.timestamp).all()
    return render_template('blog.html', blog=blog)
        
          
            
   
@app.route("/send_cash", methods=['GET','POST'])
def send_cash():
 if not session.get('user'):
     return redirect("/signin")
 if request.method == "GET":
        return render_template('send_money.html')
 if request.method == "POST":
      
        data = request.form
        logged_in_user = session.get('user')
        sender = User.query.filter_by(username=logged_in_user['username']).first()
        # sender = User.query.filter_by(username=data['sender']).first() this was a test
        # username = sender.username
        receiver = User.query.filter_by(account_number=data['receiver']).first()
        amount = data['amount']
        if receiver is None:
            flash('Input A valid  user_account_number ')
            return redirect("/send_cash")
        if amount is  None:
            return "NUll or invalid amount"
        amountparse = int(amount)
        sender.cash -= amountparse
        receiver.cash += amountparse
      
        if sender.cash == amountparse or sender.cash <= 0:
           flash('insufficient funds') 
           return redirect("/send_cash")
   
        if receiver == sender:
            flash('You cant send cash to yourself') 
            return redirect("/send_cash")
           
   
   
        if  receiver is None:
            return "You didn'nt input a valid username"
       
      
         


        transaction = Transaction(sender_id=sender.id, receiver_id=receiver.id, amount=amountparse)
        
       
        if not sender :
            return 'THIS IS NOT THE LOGGED_IN_USER'
        else:

          db.session.add(transaction)
          db.session.commit()
          return  redirect("/")





# def send_email_notification(user, amount):
#     # Create the email message
#     msg = Message('Payment Confirmation', sender='support@MONRCH.com', recipients=[user.email])
#     msg.body = f'Hello {user.username},\\n\\nYou have successfully funded your account with {amount} naira. Your current cash balance is {user.cash} naira.\\n\\nThank you for using MONRCH.\\n\\nBest regards,\\nThe MONRCH Team'
    
#     # Send the email
#     mail.send(msg)
 



 


    

MIN_ACCOUNT_NUMBER = 10000
MAX_ACCOUNT_NUMBER = 10000000000000
INITIAL_CASH = 20000
ERROR_MESSAGE = "Invalid credentials. Please try again."

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
@app.route("/signup", methods = ['GET', 'POST'])
def signuppage():
    if  session.get('user'):
        flash("User is still loggend in")
        return redirect("/")
    if request.method == 'GET':
        return render_template('signup.html')
    if request.method == 'POST':
        data = request.form
        username = data['username']
        password = data['password']
        phone_number = data['phone_number']
        email = data['email']
        security = generate_password_hash(password)
        account_number = random.randint(MIN_ACCOUNT_NUMBER, MAX_ACCOUNT_NUMBER)
        cash = INITIAL_CASH
        file = request.files['file']
        if file  and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        user = User(username = username, password = security, phone_number = phone_number, email = email, account_number = account_number, cash = cash, profile_pic=filename)
        existing_user = User.query.filter_by(username = username).first()
        existing_acct = User.query.filter_by(account_number = account_number).first()
        existing_email = User.query.filter_by(email= email).first()
        existing_phone = User.query.filter_by(phone_number = phone_number).first()
        if existing_user or existing_acct or existing_email or existing_phone:
             flash(f"{ERROR_MESSAGE}", 'error')
             return render_template("signup.html")
        regex_pattern = r'^\+(?:[0-9] ?){6,14}[0-9]$'
        
        if re.match(regex_pattern, phone_number):
            print("Phone number with country code matched successfully!")
        else:
            flash("Please write your phonenumber with country code.")
            return redirect("/signup")
        # if not existing_user and not existing_acct and not existing_email and not existing_phone:
        #     msg = Message('Hello', sender = 'c02474094@gmail.com', recipients = [email])
        #     msg.body = "Hello " + username + ", thank you for signing up to MONRCH!"
        #     mail.send(msg)
        db.session.add(user)
        db.session.commit()
        return redirect("/userprofile")
    
    
@app.route("/signin", methods=['GET',"POST"])
def handle_signin():
    if  session.get('user'):
        flash("User is still loggend in")
        return redirect("/")
    if request.method == "GET":
        return render_template("login.html")
    
    if request.method == "POST":
        data = request.form
        username = data['username']
        password = data['password']
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User those not exist")
            # Redirect the user back to the signup page
            return redirect("/signup")
        if check_password_hash(user.password, password):
            session['user'] = {
                "username": user.username
            }
            logged_in_user = session.get('user')
            user = User.query.filter_by(username=logged_in_user['username']).first()
            email = user.email
            flash("Welcome Back login successful")
            # msg = Message('Hello', sender = 'c02474094@gmail.com', recipients = [email])
            # msg.body = "Hello " + username + ", thank you for logging in to MONRCH!"
            # mail.send(msg)
            return redirect("/userprofile")
        flash("You are not logged in")
        return redirect("/signin")
    
@app.get("/logout")
def handles_logout():
    if session.get("user"):
      logged_in_user = session.get("user")
      user = User.query.filter_by(username=logged_in_user['username']).first()
      username = user.username
      flash(f"{username} Your session have been logout, Hoping to see you next time ")
    session.pop("user") 
    return redirect("/userprofile")


if __name__ == "__main__":
    app.run(port=3000, debug=True) 




