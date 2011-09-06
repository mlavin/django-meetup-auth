from django.conf.urls.defaults import *


handler404 = 'meetup_auth.tests.views.test_404'
handler500 = 'meetup_auth.tests.views.test_500'


urlpatterns = patterns('',
    (r'^social-auth/', include('social_auth.urls')),
    (r'^default/', 'meetup_auth.tests.views.default'),
    (r'^new/', 'meetup_auth.tests.views.new'),
    (r'^error/', 'meetup_auth.tests.views.error'),
)
