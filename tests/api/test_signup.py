from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

class SignupAPITests(APITestCase):
    def test_signup_successful(self):
        url = reverse('api:signup')
        data = {
            'email': 'newuser@example.com',
            'password': 'securepassword123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], 'newuser@example.com')
        self.assertIn('token', response.data['data'])
        self.assertIn('username', response.data['data'])
        
        # Verify user created in DB
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.username, response.data['data']['username'])
        self.assertEqual(user.role, User.RoleChoices.PATIENT)

    def test_signup_existing_email(self):
        # Create an existing user
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        url = reverse('api:signup')
        data = {
            'email': 'existing@example.com',
            'password': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Should raise validation error on email field
        self.assertIn('email', response.data)

    def test_signup_and_then_login(self):
        # Signup
        signup_url = reverse('api:signup')
        signup_data = {
            'email': 'loginuser@example.com',
            'password': 'loginpass123'
        }
        signup_response = self.client.post(signup_url, signup_data, format='json')
        self.assertEqual(signup_response.status_code, status.HTTP_201_CREATED)
        
        # Login
        login_url = reverse('api:login')
        login_data = {
            'email': 'loginuser@example.com',
            'password': 'loginpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertTrue(login_response.data['success'])
        self.assertIn('token', login_response.data['data'])
        self.assertEqual(login_response.data['data']['token'], signup_response.data['data']['token'])
