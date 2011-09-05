"""
Meetup OAuth support for Django-Social-Auth.

This adds support for Meetup OAuth service. An application must
be registered first on Meetup.com and the settings MEETUP_CONSUMER_KEY
and MEETUP_CONSUMER_SECRET must be defined with they corresponding
values.
"""

from django.utils import simplejson

from social_auth.backends import ConsumerBasedOAuth, OAuthBackend, USERNAME


MEETUP_SERVER = 'api.meetup.com'
MEETUP_REQUEST_TOKEN_URL = 'https://%s/oauth/request/' % MEETUP_SERVER
MEETUP_ACCESS_TOKEN_URL = 'https://%s/oauth/access/' % MEETUP_SERVER
# Note: oauth/authorize forces the user to authorize every time.
#       oauth/authenticate uses their previous selection, barring revocation.
MEETUP_AUTHORIZATION_URL = 'https://www.meetup.com/authenticate/'
MEETUP_CHECK_AUTH = 'https://%s/members.json/?relation=self' % MEETUP_SERVER


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
            USERNAME: response['id'],
            'email': response.get('email', ''),  # requested but not always supplied
            'fullname': full_name,
            'first_name': first_name,
            'last_name': last_name
        }
        return data


class MeetupAuth(ConsumerBasedOAuth):
    """Meetup OAuth authentication mechanism"""
    AUTHORIZATION_URL = MEETUP_AUTHORIZATION_URL
    REQUEST_TOKEN_URL = MEETUP_REQUEST_TOKEN_URL
    ACCESS_TOKEN_URL = MEETUP_ACCESS_TOKEN_URL
    SERVER_URL = MEETUP_SERVER
    AUTH_BACKEND = MeetupBackend
    SETTINGS_KEY_NAME = 'MEETUP_CONSUMER_KEY'
    SETTINGS_SECRET_NAME = 'MEETUP_CONSUMER_SECRET'

    def user_data(self, access_token):
        """Return user data provided"""
        request = self.oauth_request(access_token, MEETUP_CHECK_AUTH, 
            extra_params={'fields': 'email'}
        )
        json = self.fetch_response(request)
        try:
            return simplejson.loads(json)['results'][0]
        except (ValueError, KeyError, IndexError,):
            return None


# Backend definition
BACKENDS = {
    'meetup': MeetupAuth,
}
