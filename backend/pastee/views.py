import json
import pprint
import time

from django import http
from .. import settings

import datastore
import formatting
import paste

JSON_CONTENT_TYPE = 'application/json'
MAX_LENGTH = 32 * 1024    # 32 KiB
MAX_TTL = 86400 * 365     # 1 year
DEFAULT_TTL = 86400 * 30  # 1 month

# Datastore instance.
DS = datastore.Datastore()
KEY_PREFIX = u'pastee'
if getattr(settings, 'SITE_PREFIX', '') != '':
  KEY_PREFIX = u'%s:%s' % (KEY_PREFIX, getattr(settings, 'SITE_PREFIX'))
DS.prefix_is(KEY_PREFIX)


def error_response(err_msg, status=403):
  return http.HttpResponse(json.dumps({'error': err_msg}),
                           status=status,
                           content_type=JSON_CONTENT_TYPE)


def index(request):
  return http.HttpResponse('.')


def get(request, id, mode=None):
  raw = (mode == '/raw')
  download = (mode == '/download')
  if len(id) > 100:
    return error_response('Invalid ID', status=404)

  # Lookup saved paste.
  # TODO(ms): Handle expired posts.
  try:
    saved_paste = paste.Paste(DS, id=id)
  except KeyError:
    return error_response('Invalid ID', status=404)

  # Decode content.
  content = saved_paste.content()
  if content is None:
    return error_response('Expired', status=403)

  if raw:
    # Plain text output.
    return http.HttpResponse(content, content_type='text/plain')
  elif download:
    # Download.

    # Lookup file extension for lexer.
    lexer_alias = saved_paste.lexer_alias()
    filename = 'pastee-%s.%s' % (id, formatting.lexer_ext(lexer_alias))

    response = http.HttpResponse(content,
                                 content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response
  else:
    # HTML-ized output.
    lexer_alias = formatting.validate_lexer_name(saved_paste.lexer_alias())
    html = formatting.htmlize(content, lexer_alias)
    data = {'id': id,
            'created': saved_paste.created(),
            'lexer': formatting.lexer_longname(lexer_alias),
            'lexer_alias': lexer_alias,
            'ttl': saved_paste.ttl(),
            'html': html,
            'raw': content}
    return http.HttpResponse(json.dumps(data), content_type=JSON_CONTENT_TYPE)


def submit(request):
  err_msg = None

  # Extract data.
  content = request.POST.get('content', '')
  try:
    ttl = int(request.POST.get('ttl', DEFAULT_TTL))
  except TypeError:
    err_msg = 'Expected integer for ttl'
  lexer = request.POST.get('lexer', '')

  # Validate request.
  if content == '':
    err_msg = 'Content must not be empty'
  elif ttl <= 0 or ttl > MAX_TTL:
    err_msg = 'TTL out of range'
  elif len(lexer) > 30:
    err_msg = 'Invalid lexer'
  elif len(content) > MAX_LENGTH:
    err_msg = 'Content too large'

  # Handle errors.
  if err_msg:
    return http.HttpResponse(json.dumps({'error': err_msg}),
                             status=403,
                             content_type=JSON_CONTENT_TYPE)

  # Create paste.
  new_paste = paste.Paste(DS)
  new_paste.ttl_is(ttl)
  new_paste.lexer_alias_is(lexer)
  new_paste.ip_address_is(request.META.get('REMOTE_ADDR'))
  new_paste.content_is(content)

  # Save paste.
  new_paste.save_state_is(paste.Paste.SaveStates.CLEAN)

  response = {'id': new_paste.id()}
  return http.HttpResponse(json.dumps(response),
                           content_type=JSON_CONTENT_TYPE)
