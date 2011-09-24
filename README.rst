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

.. versionadded:: 0.2

Django-Meetup-Auth uses the OAuth 2.0 endpoints which means you must include a
Redirect URI when registering your applicaion with Meetup.com. For more detail
please see the `Meetup API documentation <http://www.meetup.com/meetup_api/auth/#oauth2server-auth-success>`_.


Installation
-------------------------------

To install django-meetup-auth via pip::

    pip install django-meetup-auth

Or you can from the latest version from Github manually::

    git clone git://github.com/mlavin/django-meetup-auth.git
    cd django-meetup-auth
    python setup.py install

or via pip::

    pip install -e git+https://github.com/mlavin/django-meetup-auth.git

Once you have the app installed you must include in your settings::

    INSTALLED_APPS = (
        ...
        'social_auth',
        'meetup_auth',
        ...
    )

    AUTHENTICATION_BACKENDS = (
        ...
        'meetup_auth.backend.MeetupBackend',
        ...
    )

    SOCIAL_AUTH_IMPORT_BACKENDS = (
        ...
        'meetup_auth',
        ...    
    )

Please refer to the `Django-Social-Auth <http://django-social-auth.readthedocs.org/>`_
documentation for additional information.


Questions or Issues?
-------------------------------

If you have questions, issues or requests for improvements please let me know on
`Github <https://github.com/mlavin/django-meetup-auth/issues>`_.
