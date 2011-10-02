"""
Meetup OAuth2 support for Django-Social-Auth.

This adds support for Meetup OAuth service. An application must
be registered first on Meetup.com and the settings MEETUP_CONSUMER_KEY
and MEETUP_CONSUMER_SECRET must be defined with they corresponding
values.
"""

from urllib import urlencode
from urllib2 import urlopen

from django.utils import simplejson

from social_auth.backends import BaseOAuth2, OAuthBackend, USERNAME


MEETUP_SERVER = 'secure.meetup.com'
MEETUP_ACCESS_TOKEN_URL = 'https://%s/oauth2/access' % MEETUP_SERVER
MEETUP_AUTHORIZATION_URL = 'https://%s/oauth2/authorize' % MEETUP_SERVER
MEETUP_CHECK_AUTH = 'https://api.meetup.com/members.json/'


class MeetupBackend(OAuthBackend):
    """Meetup OAuth authentication backend"""
    name = 'meetup'
    EXTRA_DATA = [('id', 'id'), ]

    def get_user_details(self, response):
        """Return user details from Meetup account"""
        full_name = response['name'].strip()
        if len(full_name.split(' ')) > 1:
            last_name = full_name.split(' ')[-1].strip()
            first_name = full_name.replace(last_name, '').strip()
        else:
            first_name = full_name
            last_name = ''
        data = {
            USERNAME: '',
            'email': response.get('email', ''),  # requested but not always supplied
            'fullname': full_name,
            'first_name': first_name,
            'last_name': last_name
        }
        return data


class MeetupAuth(BaseOAuth2):
    """Meetup OAuth authentication mechanism"""
    AUTHORIZATION_URL = MEETUP_AUTHORIZATION_URL
    ACCESS_TOKEN_URL = MEETUP_ACCESS_TOKEN_URL
    SERVER_URL = MEETUP_SERVER
    AUTH_BACKEND = MeetupBackend
    SETTINGS_KEY_NAME = 'MEETUP_CONSUMER_KEY'
    SETTINGS_SECRET_NAME = 'MEETUP_CONSUMER_SECRET'

    def user_data(self, access_token):
        """Return user data provided"""
        params = {
            'access_token': access_token,
            'relation': 'self'
        }
        url = MEETUP_CHECK_AUTH + '?' + urlencode(params)
        try:
            return simplejson.load(urlopen(url))['results'][0]
        except (ValueError, KeyError, IndexError, ):
            return None


# Backend definition
BACKENDS = {
    'meetup': MeetupAuth,
}
