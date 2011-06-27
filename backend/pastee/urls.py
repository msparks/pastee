from django.conf.urls.defaults import *


urlpatterns = patterns('backend.pastee.views',
  (r'^$', 'index'),
  (r'^submit$', 'submit'),
  (r'^get/(?P<id>[a-zA-Z0-9]+)(?P<raw>/raw)?$', 'get'),

  (r'^api$', 'api'),
  (r'^statistics$', 'statistics'),
  (r'^about$', 'about'),

  (r'^(?P<paste_id>[a-zA-Z0-9]+)/preview$', 'preview')
)
