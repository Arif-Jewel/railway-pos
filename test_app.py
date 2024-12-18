import unittest
from unittest.mock import patch  # Importing patch for mocking
from app import app, users, trains, User
from werkzeug.security import generate_password_hash


class RailwayAppTest(unittest.TestCase):

    def setUp(self):
        # Setup the app for testing
        self.app = app.test_client()
        self.app.testing = True

        # Clear and add test train data
        trains.clear()  # Clear existing trains to avoid conflicts
        trains.extend([
            {'train_no': 101, 'train_name': 'Express - 1', 'available_seats': 50, 'price': 12},
            {'train_no': 102, 'train_name': 'Express - 2', 'available_seats': 60, 'price': 15},
            {'train_no': 103, 'train_name': 'Express - 3', 'available_seats': 40, 'price': 10},
        ])

        # Add a test user
        hashed_password = generate_password_hash("password123")
        test_user = User("testuser", "Test User", "test@example.com", "1234567890", hashed_password)
        users["testuser"] = test_user

    def test_register(self):
        response = self.app.post('/register', data={
            'username': 'newuser',
            'password': 'password123',
            'name': 'New User',
            'email': 'newuser@example.com',
            'phone': '0987654321'
        }, follow_redirects=True)
        self.assertIn(b'Registration successful', response.data)

    def test_login(self):
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Welcome', response.data)

    def test_profile_update(self):
        self.app.post('/login', data={'username': 'testuser', 'password': 'password123'})
        response = self.app.post('/profile', data={
            'name': 'Updated User',
            'email': 'updated@example.com',
            'phone': '1111111111',
            'password': ''
        }, follow_redirects=True)
        self.assertIn(b'Profile updated successfully', response.data)

    def test_book_ticket(self):
    # Log in first
        self.app.post('/login', data={'username': 'testuser', 'password': 'password123'})

    # Test booking with valid seat number
        response = self.app.post('/book/101', data={'seats': 2}, follow_redirects=True)

    # Debug: Print response content if test fails
        if b'Proceed to Payment' not in response.data:
            print(response.data)

    # Check for the expected result
        self.assertIn(b'Please Pay', response.data)

    @patch('stripe.Charge.create')  # Mocking Stripe's Charge.create method
    def test_payment(self, mock_charge_create):
        # Mock the Stripe API response
        mock_charge_create.return_value = {
            'id': 'ch_test_123',
            'status': 'succeeded'
        }

        # Log in first
        self.app.post('/login', data={'username': 'testuser', 'password': 'password123'})

        # Test payment
        response = self.app.post(
            '/payment',
            data={'stripeToken': 'test_token'},
            query_string={'amount': 2400},
            follow_redirects=True
        )

        # Verify that Stripe API was called with the correct parameters
        mock_charge_create.assert_called_once_with(
            amount=2400,
            currency="GBP",
            description="Railway Ticket Booking",
            source='test_token'
        )

        # Assert response contains success message
        self.assertIn(b'Payment successful', response.data)


if __name__ == '__main__':
    unittest.main()
