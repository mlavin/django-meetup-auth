from StringIO import StringIO
from urlparse import urlparse, parse_qs

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase as DjangoTestCase

import mock


class FakeToken(object):
    """
    Can use Mock here because it will be saved in the session and Mock
    objects cannot be pickled.
    """
    key = 'FAKEKEY'
    secret = 'FAKESECRET'
    verifier = ''

    def to_string(self):
        return 'FAKETOKEN'


class AuthStartTestCase(DjangoTestCase):
    """Test login via Meetup."""

    def setUp(self):
        self.login_url = reverse('socialauth_begin', kwargs={'backend': 'meetup'})
        self.request_token_patch = mock.patch('meetup_auth.backend.MeetupAuth.unauthorized_token')
        self.request_token_mock = self.request_token_patch.start()
        self.request_token_mock.return_value = FakeToken()

    def tearDown(self):
        self.request_token_patch.stop()

    def test_meetup_redirect_url(self):
        """Check redirect to Meetup."""
        response = self.client.get(self.login_url)
        # Don't use assertRedirect because we don't want to fetch the url
        self.assertTrue(response.status_code, 302)
        url = response['Location']
        scheme, netloc, path, params, query, fragment = urlparse(url)
        self.assertEqual('%s://%s%s' % (scheme, netloc, path), 'https://www.meetup.com/authenticate/')

    def test_callback_url(self):
        """Check redirect callback url."""
        response = self.client.get(self.login_url)
        url = response['Location']
        scheme, netloc, path, params, query, fragment = urlparse(url)
        query_data = parse_qs(query)
        complete_url = reverse('socialauth_complete', kwargs={'backend': 'meetup'})
        self.assertTrue(query_data['oauth_callback'][0].endswith(complete_url))


class AuthCompleteTestCase(DjangoTestCase):
    """Complete login process from Meetup."""

    def test_new_user(self):
        """Login for the first time via Meetup."""
        pass

    def test_existing_user(self):
        """Login with an existing user via Meetup."""
        pass


class OAuthTestCase(DjangoTestCase):
    """Validate OAuth calls."""
    
    def setUp(self):
        self.oauth_request_patch = mock.patch('social_auth.backends.OAuthRequest')
        self.oauth_token_patch = mock.patch('social_auth.backends.Token')
        self.oauth_request_mock = self.oauth_request_patch.start()
        self.oauth_token_mock = self.oauth_token_patch.start()

    def tearDown(self):
        self.oauth_request_patch.stop()
        self.oauth_token_patch.start()

    def test_request_token(self):
        """Check url for getting request (unauthorized) token."""
        from meetup_auth.backend import MeetupAuth
        with mock.patch('social_auth.backends.urlopen') as urlopen:
            urlopen.return_value = StringIO('FAKETOKEN')
            request = mock.MagicMock()
            redirect = 'http://example.com'
            token = MeetupAuth(request, redirect).unauthorized_token()
        mock_from_consumer_and_token = self.oauth_request_mock.from_consumer_and_token
        call_args, call_kwargs = mock_from_consumer_and_token.call_args
        self.assertEqual(call_kwargs['http_url'], 'https://api.meetup.com/oauth/request/')

    def test_auth_url(self):
        pass

    def test_access_token(self):
        pass


class ContribAuthTestCase(DjangoTestCase):
    """Validate contrib.auth calls."""
    
    def test_has_get_user(self):
        """Authentication backend must define a get_user method."""
        from meetup_auth.backend import MeetupBackend
        get_user = getattr(MeetupBackend, 'get_user', None)
        self.assertTrue(get_user, "Auth backend must define get_user")
        self.assertTrue(callable(get_user), "get_user should be a callable")

    def test_get_existing_user(self):
        """Get existing user by id."""
        from meetup_auth.backend import MeetupBackend
        user = User.objects.create_user(username='test', password='test', email='')
        result = MeetupBackend().get_user(user.id)
        self.assertEqual(result, user)

    def test_get_non_existing_user(self):
        """User ids which don't exist should return none."""
        from meetup_auth.backend import MeetupBackend
        result = MeetupBackend().get_user(100)
        self.assertEqual(result, None)

    def test_authenticate(self):
        """Authentication backend must define a authenticate method."""
        from meetup_auth.backend import MeetupBackend
        authenticate = getattr(MeetupBackend, 'authenticate', None)
        self.assertTrue(authenticate, "Auth backend must define authenticate")
        self.assertTrue(callable(authenticate), "authenticate should be a callable")
