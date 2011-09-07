from StringIO import StringIO
from urlparse import urlparse, parse_qs

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase as DjangoTestCase
from django.utils import simplejson
from django.utils.importlib import import_module

import mock
from social_auth.models import UserSocialAuth
from social_auth import version as VERSION


if VERSION[1] == 3:
    DEFAULT_REDIRECT = getattr(settings, 'LOGIN_REDIRECT_URL', '')
    LOGIN_ERROR_URL = getattr(settings, 'LOGIN_ERROR_URL', settings.LOGIN_URL)
    NEW_USER_REDIRECT = DEFAULT_REDIRECT
    BEGIN_URL_NAME = 'begin'
    COMPLETE_URL_NAME = 'complete'
else:
    DEFAULT_REDIRECT = getattr(settings, 'SOCIAL_AUTH_LOGIN_REDIRECT_URL', '') or getattr(settings, 'LOGIN_REDIRECT_URL', '')
    LOGIN_ERROR_URL = getattr(settings, 'LOGIN_ERROR_URL', settings.LOGIN_URL)
    NEW_USER_REDIRECT = getattr(settings, 'SOCIAL_AUTH_NEW_USER_REDIRECT_URL', '')
    BEGIN_URL_NAME = 'socialauth_begin'
    COMPLETE_URL_NAME = 'socialauth_complete'


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


def meetup_user_response():
    return {
        "zip": "27511",
        "lon": "-78.77999877929688",
        "photo_url": "http://photos1.meetupstatic.com/photos/member/6/f/f/member_8675309.jpeg",
        "link": "http://www.meetup.com/members/8675309",
        "state": "NC",
        "lang": "en_US",
        "city": "Cary",
        "country": "us",
        "id": "8675309",
        "visited": "2011-09-06 16:23:35 EDT",
        "topics": [ ],
        "joined": "Sat May 21 23:45:46 EDT 2011",
        "bio": "",
        "name": "Joe Smith",
        "lat": "35.7599983215332"
    }


class AuthStartTestCase(DjangoTestCase):
    """Test login via Meetup."""

    def setUp(self):
        self.login_url = reverse(BEGIN_URL_NAME, kwargs={'backend': 'meetup'})
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
        complete_url = reverse(COMPLETE_URL_NAME, kwargs={'backend': 'meetup'})
        self.assertTrue(query_data['oauth_callback'][0].endswith(complete_url))


class AuthCompleteTestCase(DjangoTestCase):
    """Complete login process from Meetup."""

    def setUp(self):
        self.complete_url = reverse(COMPLETE_URL_NAME, kwargs={'backend': 'meetup'})
        self.access_token_patch = mock.patch('social_auth.backends.ConsumerBasedOAuth.access_token')
        self.access_token_mock = self.access_token_patch.start()
        self.access_token_mock.return_value = FakeToken()
        self.oauth_token_patch = mock.patch('oauth2.Token.from_string')
        self.oauth_token_mock = self.oauth_token_patch.start()
        self.oauth_token_mock.return_value = FakeToken()

        # Ugly hack to make sessions work
        # See https://code.djangoproject.com/ticket/10899
        from django.conf import settings
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()  # we need to make load() work, or the cookie is worthless
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
        session = self.client.session
        session['meetupunauthorized_token_name'] = 'FAKETOKEN'
        session.save()

    def tearDown(self):
        self.access_token_patch.stop()
        self.oauth_token_patch.stop()

    def get_user_data(self):
        """
        Mimics data returned for a particular users data.
        See http://www.meetup.com/meetup_api/docs/members/
        """
        user = meetup_user_response()
        data = {
            "results": [user, ],
            "meta": {
                "lon": "",
                "count": 1,
                "signed_url": "http://api.meetup.com/members?relation=self&order=name&offset=0&callback=jsonp1315340626452&format=json&page=20&sig_id=15710541&sig=7e75212aa3267174464194228791d7b0ce3851ca",
                "link": "https://api.meetup.com/members",
                "next": "",
                "total_count": 1,
                "url": "https://api.meetup.com/members?key=XXX&relation=self&order=name&offset=0&callback=jsonp1315340626452&format=json&page=20&sign=true",
                "id": "",
                "title": "Meetup Members",
                "updated": "Thu Aug 11 21:29:17 EDT 2011",
                "description": "API method for accessing members of Meetup Groups",
                "method": "Members",
                "lat": ""
            }
        }
        return data

    def test_new_user(self):
        """Login for the first time via Meetup."""
        with mock.patch('social_auth.backends.ConsumerBasedOAuth.fetch_response') as urlopen:
            user_data = self.get_user_data()
            urlopen.return_value = simplejson.dumps(user_data)
            data = {'oauth_token': 'FAKEKEY'}
            response = self.client.get(self.complete_url, data)
            self.assertRedirects(response, NEW_USER_REDIRECT)

    def test_new_user_name(self):
        """Check the name set on the newly created user."""
        with mock.patch('social_auth.backends.ConsumerBasedOAuth.fetch_response') as urlopen:
            user_data = self.get_user_data()
            urlopen.return_value = simplejson.dumps(user_data)
            data = {'oauth_token': 'FAKEKEY'}
            self.client.get(self.complete_url, data)
            new_user = User.objects.latest('id')
            self.assertEqual(new_user.first_name, "Joe")
            self.assertEqual(new_user.last_name, "Smith")

    def test_single_name(self):
        """Process a user with a single word name."""
        with mock.patch('social_auth.backends.ConsumerBasedOAuth.fetch_response') as urlopen:
            user_data = self.get_user_data()
            user_data['results'][0]['name'] = 'Cher'
            urlopen.return_value = simplejson.dumps(user_data)
            data = {'oauth_token': 'FAKEKEY'}
            self.client.get(self.complete_url, data)
            new_user = User.objects.latest('id')
            self.assertEqual(new_user.first_name, "Cher")
            self.assertEqual(new_user.last_name, "")

    def test_existing_user(self):
        """Login with an existing user via Meetup."""
        user = User.objects.create_user(username='test', password='test', email='')
        social_user = UserSocialAuth.objects.create(
            user=user, provider='meetup', uid='8675309'
        )
        with mock.patch('social_auth.backends.ConsumerBasedOAuth.fetch_response') as urlopen:
            user_data = self.get_user_data()
            urlopen.return_value = simplejson.dumps(user_data)
            data = {'oauth_token': 'FAKEKEY'}
            response = self.client.get(self.complete_url, data)
            self.assertRedirects(response, DEFAULT_REDIRECT)

    def test_failed_authentication(self):
        """Failed authentication. Bad data from Meetup."""
        with mock.patch('social_auth.backends.ConsumerBasedOAuth.fetch_response') as urlopen:
            # Blank response
            urlopen.return_value = ''
            data = {'oauth_token': 'FAKEKEY'}
            response = self.client.get(self.complete_url, data)
            self.assertRedirects(response, LOGIN_ERROR_URL)


class OAuthTestCase(DjangoTestCase):
    """Validate OAuth calls."""
    
    def setUp(self):
        self.oauth_request_patch = mock.patch('social_auth.backends.ConsumerBasedOAuth.oauth_request')
        self.oauth_token_patch = mock.patch('oauth2.Token.from_string')
        self.oauth_request_mock = self.oauth_request_patch.start()
        self.oauth_token_mock = self.oauth_token_patch.start()

    def tearDown(self):
        self.oauth_request_patch.stop()
        self.oauth_token_patch.start()

    def test_request_token(self):
        """Check url for getting request (unauthorized) token."""
        from meetup_auth.backend import MeetupAuth
        with mock.patch('social_auth.backends.ConsumerBasedOAuth.fetch_response') as urlopen:
            urlopen.return_value = 'FAKETOKEN'
            request = mock.MagicMock()
            redirect = 'http://example.com'
            token = MeetupAuth(request, redirect).unauthorized_token()
            self.oauth_request_mock.assert_called_with(token=None, url='https://api.meetup.com/oauth/request/')

    def test_access_token(self):
        """Check url for getting access token."""
        from meetup_auth.backend import MeetupAuth
        with mock.patch('social_auth.backends.ConsumerBasedOAuth.fetch_response') as urlopen:
            urlopen.return_value = 'FAKETOKEN'
            request = mock.MagicMock()
            redirect = 'http://example.com'
            token = mock.MagicMock()
            acces_token = MeetupAuth(request, redirect).access_token(token)
            self.oauth_request_mock.assert_called_with(token, 'https://api.meetup.com/oauth/access/')


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

    def test_authenticate_existing_user(self):
        """Authenticate an existing user."""
        from meetup_auth.backend import MeetupBackend
        user = User.objects.create_user(username='test', password='test', email='')
        social_user = UserSocialAuth.objects.create(
            user=user, provider='meetup', uid='8675309'
        )
        response = meetup_user_response()
        result = MeetupBackend().authenticate(response=response, meetup=True)
        self.assertEqual(result, user)

    def test_authenticate_non_existing_user(self):
        """Authenticate a new user creating that user."""
        from meetup_auth.backend import MeetupBackend
        response = meetup_user_response()
        result = MeetupBackend().authenticate(response=response, meetup=True)
        self.assertTrue(result)
        if hasattr(result, 'is_new'):
            self.assertTrue(result.is_new)
