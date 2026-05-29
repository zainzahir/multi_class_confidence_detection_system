from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pickle
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from config import Config

# ─── App Setup ───────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'
login_manager.login_message_category = 'info'

# ─── NLTK Downloads ─────────────────────────────────────────────────────────

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# ─── Database Models ─────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)  # Nullable for Google OAuth users
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' or 'admin'
    registration_no = db.Column(db.String(50), unique=True, nullable=True)
    section = db.Column(db.String(10), nullable=True)
    semester = db.Column(db.String(10), nullable=True)
    is_google_user = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Password Reset fields
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    responses = db.relationship('ResponseHistory', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)


class ResponseHistory(db.Model):
    __tablename__ = 'response_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    input_text = db.Column(db.Text, nullable=False)
    predicted_label = db.Column(db.String(50), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(20), default='Web')  # 'Web' or 'Email'
    email_subject = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─── Load ML Model ──────────────────────────────────────────────────────────

def load_model():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, 'model.pkl')
    with open(model_path, 'rb') as file:
        saved_objects = pickle.load(file)
    return saved_objects

saved_objects = load_model()
model = saved_objects['model']
vectorizer = saved_objects['vectorizer']
label_mapping = saved_objects['label_mapping']
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

# ─── NLP Helpers ─────────────────────────────────────────────────────────────

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    words = nltk.word_tokenize(text)
    words = [stemmer.stem(word) for word in words if word not in stop_words]
    return ' '.join(words)


def predict_confidence(text):
    processed_text = preprocess_text(text)
    text_features = vectorizer.transform([processed_text])
    prediction_numeric = model.predict(text_features)[0]
    reverse_mapping = {v: k for k, v in label_mapping.items()}
    predicted_label = reverse_mapping[prediction_numeric]
    probabilities = model.predict_proba(text_features)[0]
    confidence_score = max(probabilities) * 100
    
    color_map = {
        'High Confidence': '#28a745',
        'Medium Confidence': '#ffc107',
        'Low Confidence': '#dc3545'
    }
    
    return {
        'label': predicted_label,
        'confidence': round(confidence_score, 2),
        'color': color_map[predicted_label],
        'message': get_message(predicted_label)
    }


def get_message(label):
    messages = {
        'High Confidence': "🌟 Excellent! You show strong understanding and clarity in your response.",
        'Medium Confidence': "📚 Good attempt! With a bit more practice, you'll master this topic.",
        'Low Confidence': "💪 Don't worry! Everyone learns at their own pace. Keep practicing!"
    }
    return messages.get(label, "Keep learning and improving!")

# ─── Validation Helpers ──────────────────────────────────────────────────────

VALID_SECTIONS = ['A', 'B', 'C', 'D']
VALID_SEMESTERS = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th']
VALID_DEPARTMENTS = ['CS', 'CE', 'SE']


def validate_registration_no(reg_no):
    """Validate registration number format: YYYY-DD-XXX"""
    pattern = r'^(\d{4})-(CS|CE|SE)-(\d{3})$'
    match = re.match(pattern, reg_no.upper())
    
    if not match:
        return False, 'Invalid format. Use YYYY-DD-XXX (e.g., 2024-CS-147)'
    
    year = int(match.group(1))
    current_year = datetime.now().year
    
    if year < 2001 or year > current_year:
        return False, f'Year must be between 2001 and {current_year}'
    
    return True, 'Valid'

# ─── Routes: Authentication ─────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email_input = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email_input or not password:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email_input).first()
        
        if user and user.check_password(password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email_input = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        registration_no = request.form.get('registration_no', '').strip().upper()
        section = request.form.get('section', '').strip()
        semester = request.form.get('semester', '').strip()
        
        # Validation
        errors = []
        
        if not all([name, email_input, password, confirm_password, registration_no, section, semester]):
            errors.append('All fields are required.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        # Validate registration number
        is_valid, msg = validate_registration_no(registration_no)
        if not is_valid:
            errors.append(f'Registration Number: {msg}')
        
        if section not in VALID_SECTIONS:
            errors.append('Invalid section selected.')
        
        if semester not in VALID_SEMESTERS:
            errors.append('Invalid semester selected.')
        
        # Check for duplicate email
        if User.query.filter_by(email=email_input).first():
            errors.append('Email is already registered.')
        
        # Check for duplicate registration number
        if User.query.filter_by(registration_no=registration_no).first():
            errors.append('Registration number is already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('register'))
        
        # Create user
        user = User(
            name=name,
            email=email_input,
            role='student',
            registration_no=registration_no,
            section=section,
            semester=semester
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login/google', methods=['POST'])
def google_login():
    """Handle Google Sign-In token verification."""
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        
        data = request.get_json()
        token = data.get('credential', '')
        
        if not token:
            return jsonify({'error': 'No credential provided'}), 400
        
        client_id = app.config.get('GOOGLE_CLIENT_ID', '')
        if not client_id:
            return jsonify({'error': 'Google Sign-In is not configured'}), 400
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
        
        google_email = idinfo.get('email', '').lower()
        google_name = idinfo.get('name', 'Google User')
        
        if not google_email:
            return jsonify({'error': 'Could not retrieve email from Google'}), 400
        
        # Check if user exists
        user = User.query.filter_by(email=google_email).first()
        
        if user:
            login_user(user)
            redirect_url = url_for('admin_dashboard') if user.role == 'admin' else url_for('home')
            return jsonify({'success': True, 'redirect': redirect_url})
        else:
            # Auto-register as student (they'll need to complete profile)
            user = User(
                name=google_name,
                email=google_email,
                role='student',
                is_google_user=True
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return jsonify({
                'success': True,
                'redirect': url_for('complete_profile'),
                'message': 'Please complete your profile.'
            })
            
    except ValueError as e:
        return jsonify({'error': f'Invalid Google token: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Google login error: {str(e)}'}), 500


@app.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    """For Google OAuth users who need to fill in registration details."""
    if current_user.registration_no:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        registration_no = request.form.get('registration_no', '').strip().upper()
        section = request.form.get('section', '').strip()
        semester = request.form.get('semester', '').strip()
        
        errors = []
        
        is_valid, msg = validate_registration_no(registration_no)
        if not is_valid:
            errors.append(f'Registration Number: {msg}')
        
        if section not in VALID_SECTIONS:
            errors.append('Invalid section selected.')
        
        if semester not in VALID_SEMESTERS:
            errors.append('Invalid semester selected.')
        
        if User.query.filter(User.registration_no == registration_no, User.id != current_user.id).first():
            errors.append('Registration number is already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('complete_profile'))
        
        current_user.registration_no = registration_no
        current_user.section = section
        current_user.semester = semester
        db.session.commit()
        
        flash('Profile completed successfully!', 'success')
        return redirect(url_for('home'))
    
    return render_template('register.html', complete_profile=True)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─── Routes: Password Management ─────────────────────────────────────────────

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Handle password change requests from logged in users."""
    try:
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'All fields are required.'}), 400
            
        if not current_user.check_password(current_password):
            return jsonify({'success': False, 'message': 'Incorrect current password.'}), 400
            
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match.'}), 400
            
        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters long.'}), 400
            
        current_user.set_password(new_password)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password changed successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


def send_reset_email(to_email, reset_url):
    """SMTP email sending helper."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    sender_email = app.config.get('TEACHER_EMAIL', '')
    sender_password = app.config.get('TEACHER_EMAIL_PASSWORD', '')
    
    if not sender_email or not sender_password:
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Student Confidence Detector <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = "Password Reset Request"
        
        body = f"""Hello,

You requested a password reset for your Student Confidence Detector account.
Please click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.
If you did not make this request, simply ignore this email.

Regards,
AI Support Team"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[ERROR] SMTP Send failed: {str(e)}")
        return False


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email_input = request.form.get('email', '').strip().lower()
        if not email_input:
            flash('Please enter your email address.', 'error')
            return redirect(url_for('forgot_password'))
            
        user = User.query.filter_by(email=email_input).first()
        if user:
            import secrets
            from datetime import datetime, timedelta
            
            # Generate token and expiry
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Create reset URL
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Send Email
            email_sent = send_reset_email(user.email, reset_url)
            
            if email_sent:
                flash('A password reset link has been sent to your email.', 'success')
            else:
                # Fallback message for environments blocking SMTP (like PythonAnywhere Free Tier)
                flash(f'Reset link generated successfully! (SMTP block fallback - Reset URL: {reset_url})', 'info')
        else:
            # For security reasons, don't reveal that the user does not exist
            flash('If the email is registered, a reset link has been sent.', 'success')
            
        return redirect(url_for('login'))
        
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    from datetime import datetime
    user = User.query.filter(User.reset_token == token, User.reset_token_expiry > datetime.utcnow()).first()
    
    if not user:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not password or not confirm_password:
            flash('All fields are required.', 'error')
            return render_template('reset_password.html', token=token)
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('reset_password.html', token=token)
            
        # Update password and clear token
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Your password has been reset successfully! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html', token=token)

# ─── Routes: Student Dashboard ──────────────────────────────────────────────

@app.route('/')
@login_required
def home():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    # Get student's prediction history
    history = ResponseHistory.query.filter_by(user_id=current_user.id)\
        .order_by(ResponseHistory.created_at.desc()).all()
    
    return render_template('index.html', history=history)


@app.route('/predict', methods=['POST'])
@login_required
def predict():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text or len(text.strip()) == 0:
            return jsonify({'error': 'Please enter some text to analyze'}), 400
        
        if len(text) < 10:
            return jsonify({'error': 'Please enter at least 10 characters for better analysis'}), 400
        
        result = predict_confidence(text)
        
        # Save to history
        history = ResponseHistory(
            user_id=current_user.id,
            input_text=text[:2000],
            predicted_label=result['label'],
            confidence_score=result['confidence'],
            source='Web'
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─── Routes: Admin Dashboard ────────────────────────────────────────────────

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('home'))
    
    # Gather statistics
    total_students = User.query.filter_by(role='student').count()
    total_predictions = ResponseHistory.query.count()
    
    avg_confidence_result = db.session.query(db.func.avg(ResponseHistory.confidence_score)).scalar()
    avg_confidence = round(avg_confidence_result, 2) if avg_confidence_result else 0
    
    email_predictions = ResponseHistory.query.filter_by(source='Email').count()
    
    stats = {
        'total_students': total_students,
        'total_predictions': total_predictions,
        'avg_confidence': avg_confidence,
        'email_predictions': email_predictions
    }
    
    # Get all students
    students = User.query.filter_by(role='student').order_by(User.created_at.desc()).all()
    
    # Get all predictions with user info
    predictions = ResponseHistory.query.join(User)\
        .order_by(ResponseHistory.created_at.desc()).all()
    
    return render_template('admin_dashboard.html', stats=stats, students=students, predictions=predictions)


@app.route('/admin/sync-emails', methods=['POST'])
@login_required
def sync_emails():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    from email_sync import fetch_and_classify_emails
    results = fetch_and_classify_emails(app, db, User, ResponseHistory, predict_confidence)
    
    return jsonify(results)

# ─── Database Initialization ────────────────────────────────────────────────

def seed_admin():
    """Create a default admin account if none exists."""
    admin = User.query.filter_by(email='zainzahir.pk@gmail.com').first()
    if not admin:
        admin = User(
            name='Admin',
            email='zainzahir.pk@gmail.com',
            role='admin'
        )
        admin.set_password('ZainAdmin123!')
        db.session.add(admin)
        db.session.commit()
        print("[SUCCESS] Default admin account created: zainzahir.pk@gmail.com / ZainAdmin123!")


# ─── Create .env template if it doesn't exist ───────────────────────────────

def create_env_template():
    import os
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""# Flask Secret Key (change this in production!)
SECRET_KEY=your-secret-key-change-me

# Google OAuth Client ID (optional, for "Sign in with Google")
GOOGLE_CLIENT_ID=

# IMAP Email Settings (for email sync feature)
IMAP_SERVER=imap.gmail.com
TEACHER_EMAIL=
TEACHER_EMAIL_PASSWORD=
""")
        print("[INFO] Created .env template file. Please configure your settings.")


# ─── Initialize Database at Import Time ─────────────────────────────────────

with app.app_context():
    db.create_all()
    seed_admin()


# ─── Main ───────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    create_env_template()
    app.run(debug=True, host='127.0.0.1', port=5000)