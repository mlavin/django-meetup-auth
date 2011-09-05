from django.conf.urls.defaults import *


handler404 = 'meetup_auth.tests.views.test_404'
handler500 = 'meetup_auth.tests.views.test_500'


urlpatterns = patterns('',
    (r'^social-auth/', include('social_auth.urls')),
)
