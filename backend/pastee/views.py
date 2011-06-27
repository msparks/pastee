import base64
import json
import pprint
import time

from django import http

import datastore
import formatting
import idmgr

JSON_CONTENT_TYPE = 'application/json'
MAX_LENGTH = 32 * 1024    # 32 KiB
MAX_TTL = 86400 * 365     # 1 year
DEFAULT_TTL = 86400 * 30  # 1 month


def error_response(err_msg, status=403):
  return http.HttpResponse(json.dumps({'error': err_msg}),
                           status=status,
                           content_type=JSON_CONTENT_TYPE)


def index(request):
  return http.HttpResponse('.')


def get(request, id, raw=None):
  raw = (raw is not None)  # convert raw to boolean
  if len(id) > 100:
    return error_response('Invalid ID', status=404)

  # Look up metadata.
  # TODO(ms): Handle expired posts.
  md_key = 'paste:metadata:%s' % id
  md_json = datastore.get(md_key)
  if md_json is None:
    return error_response('Invalid ID', status=404)
  md = json.loads(md_json)

  # Decode content.
  content_key = 'paste:content:%s' % id
  b64_content = datastore.get(content_key)
  if b64_content is None:
    return error_response('Expired', status=403)
  content = base64.b64decode(b64_content)

  if not raw:
    # HTML-ized output.
    lexer = formatting.validate_lexer_name(md.get('lexer', 'text'))
    html = formatting.htmlize(content, lexer)
    return http.HttpResponse(html, content_type='text/html')
  else:
    # Plain text output.
    return http.HttpResponse(content, content_type='text/plain')


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

  # Get an ID for the new paste.
  id = idmgr.random_unused_id()

  # Store the metadata object.
  md_key = 'paste:metadata:%s' % id
  md = {'ttl': ttl,
        'lexer': lexer,
        'ip_address': request.META.get('REMOTE_ADDR'),
        'created': int(time.time())}
  datastore.set(md_key, json.dumps(md))

  # Store the content object.
  content_key = 'paste:content:%s' % id
  datastore.set(content_key, base64.b64encode(content))

  response = {'id': id}
  return http.HttpResponse(json.dumps(response),
                           content_type=JSON_CONTENT_TYPE)
