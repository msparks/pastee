from django.conf.urls.defaults import *


urlpatterns = patterns('backend.pastee.views',
  (r'^api/$', 'index'),
  (r'^api/submit$', 'submit'),
  (r'^api/get/(?P<id>[a-zA-Z0-9]+)(?P<mode>/(raw|download))?$', 'get'),
)
