Django-Meetup-Auth
==============================

Django-Meetup-Auth is an extension to `Django-Social-Auth <https://github.com/omab/django-social-auth>`_
which adds a backend for Meetup.com.


Requirements
-------------------------------

- Django-Social-Auth >= 0.3.3
    - Django >= 1.2.5
    - Python-OAuth2 >= 1.5.167
    - Python-Openid >= 2.2


API Keys
-------------------------------

In order to use this application you must sign up for OAuth consumer key on
Meetup.com. These should be put into your settings file using the settings::

    MEETUP_CONSUMER_KEY = '' # Your consumer key
    MEETUP_CONSUMER_SECRET = '' # Your consumer secret
