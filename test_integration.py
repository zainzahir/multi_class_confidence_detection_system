import unittest
import json
from app import app, db, User, ResponseHistory, validate_registration_no

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app = app.test_client()
        
        # Create all tables in the memory database
        with app.app_context():
            db.create_all()
            
            # Create a default admin user
            admin = User(
                name='Admin Test',
                email='admin_test@detector.com',
                role='admin'
            )
            admin.set_password('AdminPass123!')
            db.session.add(admin)
            
            # Create a default student user
            student = User(
                name='Student Test',
                email='student_test@detector.com',
                role='student',
                registration_no='2024-CS-123',
                section='A',
                semester='4th'
            )
            student.set_password('StudentPass123!')
            db.session.add(student)
            
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_registration_validation(self):
        """Test registration number validation patterns."""
        # Valid format
        valid, msg = validate_registration_no('2024-CS-147')
        self.assertTrue(valid)
        
        # Invalid format
        valid, msg = validate_registration_no('24-CS-147')
        self.assertFalse(valid)
        
        # Invalid year range (before 2001)
        valid, msg = validate_registration_no('1999-CS-147')
        self.assertFalse(valid)
        
        # Invalid year range (future year)
        valid, msg = validate_registration_no('2035-CS-147')
        self.assertFalse(valid)
        
        # Invalid department
        valid, msg = validate_registration_no('2024-XX-147')
        self.assertFalse(valid)
        
        # Invalid roll number digits
        valid, msg = validate_registration_no('2024-CS-14')
        self.assertFalse(valid)

    def test_registration_flow(self):
        """Test user registration flow."""
        # Valid student registration
        response = self.app.post('/register', data={
            'name': 'New Student',
            'email': 'new_student@detector.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'registration_no': '2025-SE-999',
            'section': 'B',
            'semester': '1st'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Account created successfully', response.data)
        
        # Duplicate registration number
        response = self.app.post('/register', data={
            'name': 'Duplicate Reg Student',
            'email': 'dup_reg@detector.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'registration_no': '2025-SE-999',
            'section': 'B',
            'semester': '1st'
        }, follow_redirects=True)
        self.assertIn(b'Registration number is already registered', response.data)

        # Non-matching passwords
        response = self.app.post('/register', data={
            'name': 'Different Pass Student',
            'email': 'diff_pass@detector.com',
            'password': 'Password123!',
            'confirm_password': 'Password1234!',
            'registration_no': '2025-CE-111',
            'section': 'C',
            'semester': '2nd'
        }, follow_redirects=True)
        self.assertIn(b'Passwords do not match', response.data)

    def test_login_logout_flow(self):
        """Test login and logout flow."""
        # Incorrect login (when not authenticated yet)
        response = self.app.post('/login', data={
            'email': 'student_test@detector.com',
            'password': 'wrong_password'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', response.data)

        # Correct student login
        response = self.app.post('/login', data={
            'email': 'student_test@detector.com',
            'password': 'StudentPass123!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Student Confidence Detector', response.data)  # On student home page
        
        # Logout
        response = self.app.get('/logout', follow_redirects=True)
        self.assertIn(b'You have been logged out', response.data)

    def test_access_control(self):
        """Test admin dashboard access control."""
        # Unauthenticated access to admin dashboard should redirect to login
        response = self.app.get('/admin', follow_redirects=True)
        self.assertIn(b'Please login to access this page', response.data)
        
        # Log in as Student
        self.app.post('/login', data={
            'email': 'student_test@detector.com',
            'password': 'StudentPass123!'
        }, follow_redirects=True)
        
        # Student attempting to access admin dashboard should be denied
        response = self.app.get('/admin', follow_redirects=True)
        self.assertIn(b'Access denied. Admin only', response.data)
        
        # Log out student and log in as Admin
        self.app.get('/logout', follow_redirects=True)
        self.app.post('/login', data={
            'email': 'admin_test@detector.com',
            'password': 'AdminPass123!'
        }, follow_redirects=True)
        
        # Admin should successfully access admin dashboard
        response = self.app.get('/admin', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin Dashboard', response.data)

    def test_prediction_endpoint(self):
        """Test confidence prediction POST request."""
        # Login student
        self.app.post('/login', data={
            'email': 'student_test@detector.com',
            'password': 'StudentPass123!'
        })
        
        # Successful prediction request
        response = self.app.post('/predict', data=json.dumps({
            'text': 'I am absolutely sure about this answer and have complete understanding of the topic.'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('label', data)
        self.assertIn('confidence', data)
        self.assertIn('color', data)
        self.assertIn('message', data)
        
        # Check prediction history exists
        with app.app_context():
            histories = ResponseHistory.query.all()
            self.assertEqual(len(histories), 1)
            self.assertEqual(histories[0].predicted_label, data['label'])
            self.assertEqual(histories[0].source, 'Web')

        # Empty/short text validation
        response = self.app.post('/predict', data=json.dumps({
            'text': 'short'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Please enter at least 10 characters', response.data)

if __name__ == '__main__':
    unittest.main()
