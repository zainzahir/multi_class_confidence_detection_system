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

    def test_ai_model_trainer(self):
        """Test AI model training stats, saving feedback, and retraining endpoints."""
        # Log in as admin
        self.app.post('/login', data={
            'email': 'admin_test@detector.com',
            'password': 'AdminPass123!'
        })
        
        # 1. Check training stats
        stats_res = self.app.get('/admin/training-stats')
        self.assertEqual(stats_res.status_code, 200)
        data = json.loads(stats_res.data)
        self.assertIn('dataset_size', data)
        self.assertIn('accuracy', data)
        
        # 2. Save feedback (correct prediction)
        feedback_res = self.app.post('/admin/save-feedback', data=json.dumps({
            'text': 'This is a brand new test sample for model training.',
            'label': 'High Confidence'
        }), content_type='application/json')
        self.assertEqual(feedback_res.status_code, 200)
        fdata = json.loads(feedback_res.data)
        self.assertTrue(fdata['success'])
        
        # 3. Retrain model
        retrain_res = self.app.post('/admin/retrain')
        self.assertEqual(retrain_res.status_code, 200)
        rdata = json.loads(retrain_res.data)
        self.assertTrue(rdata['success'])
        self.assertIn('accuracy', rdata)
        self.assertIn('dataset_size', rdata)

    def test_password_management(self):
        """Test password change, forgot, and reset flows."""
        # 1. Log in student
        login_res = self.app.post('/login', data={
            'email': 'student_test@detector.com',
            'password': 'StudentPass123!'
        }, follow_redirects=True)
        self.assertIn(b'Student Confidence Detector', login_res.data)
        
        # 2. Change password successfully
        change_res = self.app.post('/change-password', data={
            'current_password': 'StudentPass123!',
            'new_password': 'NewStudentPass123!',
            'confirm_password': 'NewStudentPass123!'
        })
        self.assertEqual(change_res.status_code, 200)
        data = json.loads(change_res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Password changed successfully!')
        
        # 3. Log out
        self.app.get('/logout')
        
        # 4. Try logging in with old password
        login_old = self.app.post('/login', data={
            'email': 'student_test@detector.com',
            'password': 'StudentPass123!'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', login_old.data)
        
        # 5. Log in with new password
        login_new = self.app.post('/login', data={
            'email': 'student_test@detector.com',
            'password': 'NewStudentPass123!'
        }, follow_redirects=True)
        self.assertIn(b'Student Confidence Detector', login_new.data)
        
        # Log out to test forgot/reset password
        self.app.get('/logout')
        
        # 6. Forgot password (request reset token)
        forgot_res = self.app.post('/forgot-password', data={
            'email': 'student_test@detector.com'
        }, follow_redirects=True)
        self.assertEqual(forgot_res.status_code, 200)
        # Should flash success/info message
        self.assertIn(b'Reset link generated successfully', forgot_res.data)
        
        # Retrieve token from db
        with app.app_context():
            user = User.query.filter_by(email='student_test@detector.com').first()
            self.assertIsNotNone(user.reset_token)
            token = user.reset_token
            
        # 7. Reset password using the token
        reset_get = self.app.get(f'/reset-password/{token}')
        self.assertEqual(reset_get.status_code, 200)
        self.assertIn(b'Reset Password', reset_get.data)
        
        reset_post = self.app.post(f'/reset-password/{token}', data={
            'password': 'ResetStudentPass123!',
            'confirm_password': 'ResetStudentPass123!'
        }, follow_redirects=True)
        self.assertEqual(reset_post.status_code, 200)
        self.assertIn(b'Your password has been reset successfully', reset_post.data)
        
        # Verify token is cleared in db
        with app.app_context():
            user = User.query.filter_by(email='student_test@detector.com').first()
            self.assertIsNone(user.reset_token)
            self.assertIsNone(user.reset_token_expiry)
            
        # 8. Log in with the reset password
        login_reset = self.app.post('/login', data={
            'email': 'student_test@detector.com',
            'password': 'ResetStudentPass123!'
        }, follow_redirects=True)
        self.assertIn(b'Student Confidence Detector', login_reset.data)

if __name__ == '__main__':
    unittest.main()
