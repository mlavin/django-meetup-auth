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

    def test_meetup_redirect_url(self):
        """Check redirect to Meetup."""
        response = self.client.get(self.login_url)
        # Don't use assertRedirect because we don't want to fetch the url
        self.assertTrue(response.status_code, 302)
        url = response['Location']
        scheme, netloc, path, params, query, fragment = urlparse(url)
        self.assertEqual('%s://%s%s' % (scheme, netloc, path), 'https://secure.meetup.com/oauth2/authorize')

    def test_callback_url(self):
        """Check redirect callback url."""
        response = self.client.get(self.login_url)
        url = response['Location']
        scheme, netloc, path, params, query, fragment = urlparse(url)
        query_data = parse_qs(query)
        complete_url = reverse(COMPLETE_URL_NAME, kwargs={'backend': 'meetup'})
        self.assertTrue(query_data['redirect_uri'][0].endswith(complete_url))


class AuthCompleteTestCase(DjangoTestCase):
    """Complete login process from Meetup."""

    def setUp(self):
        self.complete_url = reverse(COMPLETE_URL_NAME, kwargs={'backend': 'meetup'})
        self.urlopen_patch = mock.patch('social_auth.backends.urlopen')
        self.urlopen_mock = self.urlopen_patch.start()
        token_data = self.get_access_token()
        self.urlopen_mock.return_value = StringIO(simplejson.dumps(token_data))

    def tearDown(self):
        self.urlopen_patch.stop()

    def get_access_token(self):
        return {
          "access_token": "ACCESS_TOKEN_TO_STORE",
          "expires_in": 3600,
          "refresh_token": "TOKEN_USED_TO_REFRESH_AUTHORIZATION"
        }

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
        with mock.patch('meetup_auth.backend.urlopen') as urlopen:
            user_data = self.get_user_data()
            urlopen.return_value = StringIO(simplejson.dumps(user_data))
            data = {'code': 'FAKEKEY'}
            response = self.client.get(self.complete_url, data)
            self.assertRedirects(response, NEW_USER_REDIRECT)

    def test_new_user_name(self):
        """Check the name set on the newly created user."""
        with mock.patch('meetup_auth.backend.urlopen') as urlopen:
            user_data = self.get_user_data()
            urlopen.return_value = StringIO(simplejson.dumps(user_data))
            data = {'code': 'FAKEKEY'}
            self.client.get(self.complete_url, data)
            new_user = User.objects.latest('id')
            self.assertEqual(new_user.first_name, "Joe")
            self.assertEqual(new_user.last_name, "Smith")

    def test_single_name(self):
        """Process a user with a single word name."""
        with mock.patch('meetup_auth.backend.urlopen') as urlopen:
            user_data = self.get_user_data()
            user_data['results'][0]['name'] = 'Cher'
            urlopen.return_value = StringIO(simplejson.dumps(user_data))
            data = {'code': 'FAKEKEY'}
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
        with mock.patch('meetup_auth.backend.urlopen') as urlopen:
            user_data = self.get_user_data()
            urlopen.return_value = StringIO(simplejson.dumps(user_data))
            data = {'code': 'FAKEKEY'}
            response = self.client.get(self.complete_url, data)
            self.assertRedirects(response, DEFAULT_REDIRECT)

    def test_failed_authentication(self):
        """Failed authentication. Bad data from Meetup."""
        error_data = {
            'error': 'invalid_request'
        }
        self.urlopen_mock.return_value = StringIO(simplejson.dumps(error_data))
        data = {'code': 'FAKEKEY'}
        response = self.client.get(self.complete_url, data)
        self.assertRedirects(response, LOGIN_ERROR_URL)


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
