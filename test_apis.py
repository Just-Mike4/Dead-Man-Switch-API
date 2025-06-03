
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import AccessToken

from unittest import mock
import requests

# Assuming models are in 'switch.models' and 'auth' is Django's built-in User
# Adjust imports if your app structure is different (e.g., 'dms.switch.models')
from switch.models import Switch, Action, CheckIn


User = get_user_model()

class DMSSystemAPITestCase(APITestCase):
    def setUp(self):
        # Create a test user
        self.username = "testuser"
        self.email = "test@example.com"
        self.password = "strong_password123"
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password
        )

        # Generate a JWT token for the test user for authenticated requests
        self.access_token = str(AccessToken.for_user(self.user))
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        # Define common URLs (using assumed names based on DRF conventions and context)
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.switches_list_create_url = reverse('switch-list')
        self.actions_url = reverse('action-list')
        self.my_status_url = reverse('user-status')
        self.password_reset_url = reverse('password-reset-request')
        self.webhook_test_url = reverse('webhook-test')

        # Ensure default Action types exist for tests
        Action.objects.get_or_create(type='email', defaults={'description': 'Email'})
        Action.objects.get_or_create(type='webhook', defaults={'description': 'Webhook'})

    def tearDown(self):
        # APITestCase handles transactions, so explicit cleanup is often not needed
        pass

    # --- User Authentication & Management Tests ---

    def test_user_registration_success(self):
        url = self.register_url
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "new_strong_password" # As per requirement documentation
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("username", response.data)
        self.assertIn("email", response.data)
        self.assertIn("token", response.data)
        self.assertEqual(response.data['username'], "newuser")
        self.assertEqual(response.data['email'], "newuser@example.com")
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_user_registration_fail_existing_username(self):
        url = self.register_url
        data = {
            "username": self.username, # Existing username
            "email": "another@example.com",
            "password1": "new_strong_password"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_user_registration_fail_existing_email(self):
        url = self.register_url
        data = {
            "username": "anotheruser",
            "email": self.email, # Existing email
            "password1": "new_strong_password"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_user_registration_fail_invalid_password_format_or_strength(self):
        # Assuming Django's password validators would reject a weak password,
        # or if password1 is too short/missing from request body.
        url = self.register_url
        data = {
            "username": "shortpassuser",
            "email": "shortpass@example.com",
            "password1": "123" # Too short/weak password
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password1", response.data) # Or "password" if serializer maps password1 to password

    def test_user_login_success(self):
        url = self.login_url
        data = {
            "email": self.email,
            "password": self.password
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIsInstance(response.data['token'], str)
        self.assertGreater(len(response.data['token']), 0)

    def test_user_login_fail_invalid_credentials(self):
        url = self.login_url
        data = {
            "email": self.email,
            "password": "wrong_password"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_user_login_fail_missing_fields(self):
        url = self.login_url
        data = {"email": self.email} # Missing password
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    @mock.patch('django.core.mail.send_mail')
    def test_password_reset_request_success(self, mock_send_mail):
        url = self.password_reset_url
        data = {"email": self.email}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data['message'], "Password reset link sent")
        mock_send_mail.assert_called_once()
        self.assertIn(self.email, mock_send_mail.call_args[0]) # Verify recipient

    def test_password_reset_request_fail_non_existent_email(self):
        url = self.password_reset_url
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data) # Assuming serializer returns this error
        self.assertIn("User with this email does not exist.", response.data['email'][0])

    @mock.patch('django.core.mail.send_mail')
    def test_password_reset_confirm_success(self, mock_send_mail):
        # Generate a valid uid and token programmatically
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        confirm_url = reverse('password-reset-confirm', kwargs={'uid': uid, 'token': token})
        new_password = "new_strong_password_123"
        data = {"new_password": new_password}

        response = self.client.post(confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data['message'], "Password has been reset")

        # Verify password actually changed by trying to log in with new password
        login_data = {"email": self.email, "password": new_password}
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_password_reset_confirm_fail_invalid_token_or_uid(self):
        # Test with invalid uid
        confirm_url = reverse('password-reset-confirm', kwargs={'uid': 'invaliduid', 'token': 'validtoken'})
        data = {"new_password": "new_password"}
        response = self.client.post(confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

        # Test with invalid token
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        confirm_url = reverse('password-reset-confirm', kwargs={'uid': uid, 'token': 'invalidtoken'})
        response = self.client.post(confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_my_status_success(self):
        email_action = Action.objects.get(type='email')
        webhook_action = Action.objects.get(type='webhook')

        # Create switches for the user, one active and one triggered
        Switch.objects.create(
            user=self.user,
            title="Active Switch",
            message="Email!",
            inactivity_duration_days=7,
            action=email_action,
            last_checkin=timezone.now()
        )
        # Create a triggered switch
        triggered_switch = Switch.objects.create(
            user=self.user,
            title="Triggered Switch",
            message="Webhook!",
            inactivity_duration_days=3,
            action=webhook_action,
            last_checkin=timezone.now() - timedelta(days=5),
            status='triggered'
        )
        # Create another active switch with a very recent checkin to verify 'last_checkin'
        recent_checkin_switch = Switch.objects.create(
            user=self.user,
            title="Very Recent Switch",
            message="New email!",
            inactivity_duration_days=1,
            action=email_action,
            last_checkin=timezone.now()
        )

        response = self.client.get(self.my_status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("active_switches", response.data)
        self.assertIn("triggered_switches", response.data)
        self.assertIn("last_checkin", response.data)
        self.assertEqual(response.data['active_switches'], 2) # Two active switches
        self.assertEqual(response.data['triggered_switches'], 1) # One triggered switch
        # last_checkin should be from the most recent checkin
        self.assertIsNotNone(response.data['last_checkin'])

    def test_my_status_no_switches(self):
        response = self.client.get(self.my_status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_switches'], 0)
        self.assertEqual(response.data['triggered_switches'], 0)
        self.assertIsNone(response.data['last_checkin'])

    def test_my_status_unauthenticated(self):
        self.client.credentials() # Clear credentials
        response = self.client.get(self.my_status_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    # --- Dead Man's Switch Management Tests ---

    def test_create_switch_success_email_action(self):
        action_type = "email"
        action_target = "recipient@example.com"
        data = {
            "title": "My Test Switch",
            "message": "This is a test message.",
            "inactivity_duration_days": 14,
            "action_type": action_type,
            "action_target": action_target
        }
        response = self.client.post(self.switches_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data['title'], "My Test Switch")
        self.assertEqual(response.data['action_type'], action_type)
        self.assertEqual(response.data['action_target'], action_target)
        self.assertEqual(Switch.objects.count(), 1)
        self.assertEqual(Action.objects.count(), 2) # Email and Webhook actions should already exist from setUp

        switch = Switch.objects.get(id=response.data['id'])
        self.assertIsNotNone(switch.action)
        self.assertEqual(switch.action.type, action_type)
        self.assertEqual(switch.action.target, action_target)
        self.assertEqual(switch.user, self.user)
        self.assertIsNotNone(switch.last_checkin)
        self.assertEqual(switch.status, 'active')

    def test_create_switch_success_webhook_action(self):
        action_type = "webhook"
        action_target = "http://example.com/test-webhook"
        data = {
            "title": "Webhook Switch",
            "message": "Send webhook",
            "inactivity_duration_days": 30,
            "action_type": action_type,
            "action_target": action_target
        }
        response = self.client.post(self.switches_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['action_type'], action_type)
        self.assertEqual(response.data['action_target'], action_target)

    def test_create_switch_fail_unauthenticated(self):
        self.client.credentials() # Clear credentials
        data = {
            "title": "Unauthorized Switch",
            "message": "...",
            "inactivity_duration_days": 1,
            "action_type": "email",
            "action_target": "a@b.com"
        }
        response = self.client.post(self.switches_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Switch.objects.count(), 0)

    def test_create_switch_fail_missing_required_fields(self):
        # Missing 'title'
        data = {
            "message": "Invalid test",
            "inactivity_duration_days": 1,
            "action_type": "email",
            "action_target": "a@b.com"
        }
        response = self.client.post(self.switches_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_create_switch_fail_invalid_inactivity_duration(self):
        # Inactivity duration must be at least 1 day
        data = {
            "title": "Test", "message": "Test", "inactivity_duration_days": 0,
            "action_type": "email", "action_target": "a@b.com"
        }
        response = self.client.post(self.switches_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inactivity_duration_days", response.data)

    def test_create_switch_fail_invalid_action_type(self):
        data = {
            "title": "Test", "message": "Test", "inactivity_duration_days": 1,
            "action_type": "sms", # Invalid action type
            "action_target": "12345"
        }
        response = self.client.post(self.switches_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("action_type", response.data)

    def test_create_switch_fail_invalid_action_target_for_email(self):
        # Email action with a non-email target (e.g., a URL)
        data = {
            "title": "Test", "message": "Test", "inactivity_duration_days": 1,
            "action_type": "email",
            "action_target": "http://not-an-email.com"
        }
        response = self.client.post(self.switches_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("action_target", response.data)

    def test_create_switch_fail_invalid_action_target_for_webhook(self):
        # Webhook action with an invalid URL target (malformed or just an email)
        data = {
            "title": "Test", "message": "Test", "inactivity_duration_days": 1,
            "action_type": "webhook",
            "action_target": "invalid-url-string"
        }
        response = self.client.post(self.switches_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("action_target", response.data) # Assuming URLField validator or similar

    def test_list_switches_success(self):
        email_action = Action.objects.get(type='email')
        webhook_action = Action.objects.get(type='webhook')

        # Create switches for the test user
        Switch.objects.create(user=self.user, title="My Switch 1", message="M1", inactivity_duration_days=7, action=email_action)
        Switch.objects.create(user=self.user, title="My Switch 2", message="M2", inactivity_duration_days=14, action=webhook_action)

        # Create a switch for another user (should not be listed for self.user)
        another_user = User.objects.create_user(username="other", email="other@example.com", password="pwd")
        Switch.objects.create(user=another_user, title="Other's Switch", message="Msg", inactivity_duration_days=1, action=email_action)

        response = self.client.get(self.switches_list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Check if the correct switches are returned (order might vary)
        titles = {s['title'] for s in response.data}
        self.assertIn("My Switch 1", titles)
        self.assertIn("My Switch 2", titles)
        self.assertNotIn("Other's Switch", titles)

    def test_list_switches_unauthenticated(self):
        self.client.credentials() # Clear credentials
        response = self.client.get(self.switches_list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_switch_success(self):
        email_action = Action.objects.get(type='email')
        switch = Switch.objects.create(user=self.user, title="Retrieve Me", message="Msg", inactivity_duration_days=7, action=email_action)
        url = reverse('switch-detail', kwargs={'pk': switch.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], switch.pk)
        self.assertEqual(response.data['title'], "Retrieve Me")
        self.assertIn('last_checkin', response.data) # Should be part of response structure

    def test_retrieve_switch_fail_not_found(self):
        url = reverse('switch-detail', kwargs={'pk': 999}) # Non-existent ID
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_switch_fail_unauthenticated(self):
        email_action = Action.objects.get(type='email')
        switch = Switch.objects.create(user=self.user, title="Retrieve Me", message="Msg", inactivity_duration_days=7, action=email_action)
        self.client.credentials() # Clear credentials
        url = reverse('switch-detail', kwargs={'pk': switch.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_switch_fail_another_user_switch(self):
        email_action = Action.objects.get(type='email')
        another_user = User.objects.create_user(username="other", email="other@example.com", password="pwd")
        switch_other = Switch.objects.create(user=another_user, title="Other's Switch", message="Msg", inactivity_duration_days=1, action=email_action)

        url = reverse('switch-detail', kwargs={'pk': switch_other.pk})
        response = self.client.get(url)
        # DRF's object level permissions (e.g., IsOwnerOrReadOnly) often return 404 for objects
        # that don't belong to the user, to prevent enumeration attacks.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_switch_success(self):
        email_action = Action.objects.get(type='email')
        switch = Switch.objects.create(user=self.user, title="Original Title", message="Original Message", inactivity_duration_days=7, action=email_action)
        url = reverse('switch-detail', kwargs={'pk': switch.pk})
        update_data = {"title": "New Title", "inactivity_duration_days": 10}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "New Title")
        self.assertEqual(response.data['inactivity_duration_days'], 10)
        self.assertEqual(response.data['message'], "Original Message") # Message should be unchanged

        switch.refresh_from_db()
        self.assertEqual(switch.title, "New Title")
        self.assertEqual(switch.inactivity_duration_days, 10)
        self.assertEqual(switch.message, "Original Message")

    def test_patch_switch_fail_unauthenticated(self):
        email_action = Action.objects.get(type='email')
        switch = Switch.objects.create(user=self.user, title="Original Title", message="Original Message", inactivity_duration_days=7, action=email_action)
        url = reverse('switch-detail', kwargs={'pk': switch.pk})
        update_data = {"title": "New Title"}
        self.client.credentials() # Clear credentials
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_switch_fail_invalid_data(self):
        email_action = Action.objects.get(type='email')
        switch = Switch.objects.create(user=self.user, title="Original Title", message="Original Message", inactivity_duration_days=7, action=email_action)
        url = reverse('switch-detail', kwargs={'pk': switch.pk})
        update_data = {"inactivity_duration_days": 0} # Invalid value
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inactivity_duration_days", response.data)

    def test_patch_switch_fail_another_user_switch(self):
        email_action = Action.objects.get(type='email')
        another_user = User.objects.create_user(username="other", email="other@example.com", password="pwd")
        switch_other = Switch.objects.create(user=another_user, title="Other's Switch", message="Msg", inactivity_duration_days=1, action=email_action)

        url = reverse('switch-detail', kwargs={'pk': switch_other.pk})
        update_data = {"title": "Attempted Change"}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_switch_success(self):
        email_action = Action.objects.get(type='email')
        switch = Switch.objects.create(user=self.user, title="Delete Me", message="Msg", inactivity_duration_days=7, action=email_action)
        url = reverse('switch-detail', kwargs={'pk': switch.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Switch.objects.filter(pk=switch.pk).exists())
        # Assuming Action is OneToOne and set to CASCADE on delete, action should be deleted too.
        # If Action is not unique per switch, it might not be deleted.
        self.assertFalse(Action.objects.filter(pk=switch.action.pk).exists())


    def test_delete_switch_fail_unauthenticated(self):
        email_action = Action.objects.get(type='email')
        switch = Switch.objects.create(user=self.user, title="Delete Me", message="Msg", inactivity_duration_days=7, action=email_action)
        url = reverse('switch-detail', kwargs={'pk': switch.pk})
        self.client.credentials() # Clear credentials
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Switch.objects.filter(pk=switch.pk).exists())

    def test_delete_switch_fail_not_found(self):
        url = reverse('switch-detail', kwargs={'pk': 999}) # Non-existent ID
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_switch_fail_another_user_switch(self):
        email_action = Action.objects.get(type='email')
        another_user = User.objects.create_user(username="other", email="other@example.com", password="pwd")
        switch_other = Switch.objects.create(user=another_user, title="Other's Switch", message="Msg", inactivity_duration_days=1, action=email_action)

        url = reverse('switch-detail', kwargs={'pk': switch_other.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Switch.objects.filter(pk=switch_other.pk).exists())

    def test_checkin_switch_success(self):
        email_action = Action.objects.get(type='email')
        # Create a switch with an older last_checkin
        old_checkin_time = timezone.now() - timedelta(days=5)
        switch = Switch.objects.create(
            user=self.user,
            title="Check-in Test",
            message="Msg",
            inactivity_duration_days=7,
            action=email_action,
            last_checkin=old_checkin_time
        )
        url = reverse('switch-checkin', kwargs={'pk': switch.pk})
        response = self.client.post(url, format='json') # POST with empty body, or {}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data['message'], "Check-in successful. Next trigger reset.")

        switch.refresh_from_db()
        self.assertGreater(switch.last_checkin, old_checkin_time) # Last checkin should be updated
        self.assertLessEqual(timezone.now() - switch.last_checkin, timedelta(seconds=5)) # Should be very recent

        # Verify a CheckIn record is created
        self.assertEqual(CheckIn.objects.filter(switch=switch).count(), 1)
        checkin_record = CheckIn.objects.get(switch=switch)
        self.assertLessEqual(timezone.now() - checkin_record.timestamp, timedelta(seconds=5))

    def test_checkin_switch_fail_unauthenticated(self):
        email_action = Action.objects.get(type='email')
        switch = Switch.objects.create(user=self.user, title="Check-in Test", message="Msg", inactivity_duration_days=7, action=email_action)
        url = reverse('switch-checkin', kwargs={'pk': switch.pk})
        self.client.credentials() # Clear credentials
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_checkin_switch_fail_not_found(self):
        url = reverse('switch-checkin', kwargs={'pk': 999}) # Non-existent ID
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_checkin_switch_fail_another_user_switch(self):
        email_action = Action.objects.get(type='email')
        another_user = User.objects.create_user(username="other", email="other@example.com", password="pwd")
        switch_other = Switch.objects.create(user=another_user, title="Other's Switch", message="Msg", inactivity_duration_days=1, action=email_action)

        url = reverse('switch-checkin', kwargs={'pk': switch_other.pk})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    # --- Actions Tests ---

    def test_list_actions_success(self):
        response = self.client.get(self.actions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        expected_actions = [
            {'type': 'email', 'description': 'Email'},
            {'type': 'webhook', 'description': 'Webhook'}
        ]
        # Sort both lists by 'type' to ensure consistent comparison order
        self.assertEqual(sorted(response.data, key=lambda x: x['type']), sorted(expected_actions, key=lambda x: x['type']))

    def test_list_actions_unauthenticated(self):
        self.client.credentials() # Clear credentials
        response = self.client.get(self.actions_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    # --- Utilities Tests ---

    @mock.patch('requests.post')
    def test_webhook_test_success(self, mock_requests_post):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.text = "Webhook received!"
        mock_requests_post.return_value = mock_response

        url_to_test = "http://mocked-webhook.com/test"
        data = {"url": url_to_test}
        response = self.client.post(self.webhook_test_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
        self.assertIn("response", response.data)
        self.assertEqual(response.data['status'], 200)
        self.assertEqual(response.data['response'], "Webhook received!")
        # Assuming a default timeout of 5 seconds is used in implementation
        mock_requests_post.assert_called_once_with(url_to_test, timeout=5)

    @mock.patch('requests.post')
    def test_webhook_test_fail_invalid_url_format(self, mock_requests_post):
        data = {"url": "invalid-url"}
        response = self.client.post(self.webhook_test_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("url", response.data)
        mock_requests_post.assert_not_called()

    @mock.patch('requests.post')
    def test_webhook_test_fail_webhook_returns_error_status(self, mock_requests_post):
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error from Webhook"
        mock_requests_post.return_value = mock_response

        url_to_test = "http://mocked-webhook.com/error"
        data = {"url": url_to_test}
        response = self.client.post(self.webhook_test_url, data, format='json')
        # The test endpoint itself returns 200 OK because the test call was successful,
        # but the *webhook's* status and response are captured.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 500)
        self.assertEqual(response.data['response'], "Internal Server Error from Webhook")
        mock_requests_post.assert_called_once_with(url_to_test, timeout=5)

    @mock.patch('requests.post')
    def test_webhook_test_fail_connection_error_to_webhook(self, mock_requests_post):
        mock_requests_post.side_effect = requests.exceptions.ConnectionError("Failed to connect to webhook")

        url_to_test = "http://non-existent-domain.com/test"
        data = {"url": url_to_test}
        response = self.client.post(self.webhook_test_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Failed to connect to webhook", response.data['error'])
        mock_requests_post.assert_called_once_with(url_to_test, timeout=5)

    @mock.patch('requests.post')
    def test_webhook_test_fail_timeout_error_to_webhook(self, mock_requests_post):
        mock_requests_post.side_effect = requests.exceptions.Timeout("Request timed out")

        url_to_test = "http://slow-webhook.com/test"
        data = {"url": url_to_test}
        response = self.client.post(self.webhook_test_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Request timed out", response.data['error'])
        mock_requests_post.assert_called_once_with(url_to_test, timeout=5)

    def test_webhook_test_unauthenticated(self):
        self.client.credentials() # Clear credentials
        data = {"url": "http://example.com/test"}
        response = self.client.post(self.webhook_test_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
