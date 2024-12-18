from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import stripe

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Set your Stripe keys
stripe.api_key = 'sk_test_51QVLuGCWEZDYGYrYs7ThTdidCTi5YLT9rbGPWyYSVFqQcAVLA6Cv30WPJuOcWjJKFNGYlpxhEc5aj48VoAtUtaoo008FSOyqUQ'  # Replace with your Stripe secret key
publishable_key = 'pk_test_51QVLuGCWEZDYGYrYW2eEaAPQejkq0z7I7mrKaP9cWht9gFvDKxoNDuJ0Iz178lkprb0I5mkf0eQpwxACDznEVdgl00tnoJZoUf'  # Replace with your Stripe publishable key


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login if user is not logged in

# Dummy data for trains and users
trains = [
    {'train_no': 101, 'train_name': 'Express - 1', 'available_seats': 50, 'price':12},
    {'train_no': 102, 'train_name': 'Express - 2', 'available_seats': 60, 'price':15},
    {'train_no': 103, 'train_name': 'Express - 3', 'available_seats': 40, 'price':10},
]

users = {}

# User class to work with Flask-Login
class User(UserMixin):
    def __init__(self, id, name, email, phone, password):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.password = password

    def get_id(self):
        return self.id
    
# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Home route
@app.route('/')
@login_required  # Ensure the user is logged in to access this page

def index():
    return render_template('index.html', trains=trains)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users.get(username)
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials, please try again!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()  # Log the user out
    return redirect(url_for('login'))  # Redirect to login page

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        # Check if the username already exists
        if username in users:
            flash("Username already exists, please choose a different one.", "danger")
            return redirect(url_for('register'))
        
        # Hash the password before storing it
        hashed_password = generate_password_hash(password)
       
        # Create the new user object
        new_user = User(username, name, email, phone, hashed_password)
        
        # Add the new user to the 'users' dictionary (this simulates storing user data)
        users[username] = new_user  # Add the new user object

        login_user(new_user)

        flash("Registration successful! You are now logged in.", "success")
        
        # Redirect to the homepage after registration
        return redirect(url_for('index'))
    
    return render_template('register.html')

# User Profile route
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user  # Get the current logged-in user

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        # If password is provided, hash it
        if password:
            hashed_password = generate_password_hash(password)
            user.password = hashed_password
        
        # Update name, email, and phone in the user info
        user.name = name
        user.email = email
        user.phone = phone
        
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

# Booking route
@app.route('/book/<int:train_no>', methods=['GET', 'POST'])
@login_required
def book_ticket(train_no):
    train = next((t for t in trains if t['train_no'] == train_no), None)
    if not train:
        return "Train not found"
        
    
    if request.method == 'POST':
        seats = int(request.form['seats'])
        if seats <= train['available_seats']:
            train['available_seats'] -= seats
            amount = seats * train['price'] * 100 
            return render_template(
                'payment.html',
                train=train,
                quantity=seats,
                amount=amount,
                key=publishable_key,
                current_user=current_user
            )
        else:
            flash("Not enough available seats!", "error")
            return redirect(url_for('book_ticket', train_no=train_no))

    return render_template('booking.html', train=train)

# Route to handle payment
@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    amount = int(request.args.get('amount', 0))  # Get the amount passed in the URL (in decimal)
    
    if request.method == 'POST':
        token = request.form['stripeToken']  # Get the token from the payment form

        try:
            # Create the charge on Stripe's servers
            charge = stripe.Charge.create(
                amount=amount,  
                currency="GBP",  
                description="Railway Ticket Booking",
                source=token,  
            )

            flash("Payment successful! Your seats are booked.", "success")
            return redirect(url_for('index'))
        except stripe.error.StripeError as e:
            flash(f"Error: {e.user_message}", "error")
            return redirect(url_for('payment', amount=amount))

    return render_template('payment.html', amount=amount, key=publishable_key)

if __name__ == '__main__':
    app.run(debug=True)







