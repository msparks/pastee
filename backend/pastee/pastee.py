#!/usr/bin/python
import json
import optparse
import os
import pprint
import signal
import sys
import time

import bottle

# Using a relative import causes a problem with nosetests. Add a path instead.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import settings

import datastore
import formatting
import paste

JSON_CONTENT_TYPE = 'application/json'
MAX_LENGTH = 32 * 1024    # 32 KiB
MAX_TTL = 86400 * 365     # 1 year
DEFAULT_TTL = 86400 * 30  # 1 month

# Test mode: keys created with the test mode prefix are removed upon shutdown.
TEST_MODE = False
TEST_MODE_PREFIX = 'pastee:test'

# Datastore instance.
DS = datastore.Datastore()
KEY_PREFIX = u'pastee'
if getattr(settings, 'SITE_PREFIX', '') != '':
  KEY_PREFIX = u'%s:%s' % (KEY_PREFIX, getattr(settings, 'SITE_PREFIX'))
DS.prefix_is(KEY_PREFIX)


class InvalidIDError(Exception):
  '''Exception class for an invalid paste ID.'''
  pass


def error_response(err_msg, status=403, id=None):
  data = {'error': err_msg}
  if id is not None:
    data['id'] = id
  bottle.response.content_type = '%s; charset=UTF8' % JSON_CONTENT_TYPE
  bottle.response.status = status
  return json.dumps(data)


def validated_paste(ds, id):
  '''Looks up a Paste with 'id' from datastore 'ds'.

  Args:
    ds: datastore.Datastore object
    id: string paste ID

  Raises:
    InvalidIDError if id is invalid or paste has expired.

  Returns:
    paste.Paste object
  '''
  if len(id) > 100:
    raise InvalidIDError

  # Lookup saved paste.
  try:
    saved_paste = paste.Paste(ds, id=id)
  except KeyError:
    raise InvalidIDError

  # No content is a sign of expiry.
  if saved_paste.content() is None:
    raise InvalidIDError

  # Check for TTL expiry.
  # NOTE(ms): Lack of content should not be the only indicator of expiry, as
  #   the deletion daemon might not have run yet for this paste.
  if saved_paste.created() + saved_paste.ttl() <= time.time():
    raise InvalidIDError

  return saved_paste


@bottle.route('/api/')
def index():
  return '.'


@bottle.route('/api/get/:id')
def get(id):
  try:
    saved_paste = validated_paste(DS, id)
  except InvalidIDError:
    return error_response('Invalid ID', status=404, id=id)

  content = saved_paste.content()

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

  bottle.response.content_type = '%s; charset=UTF8' % JSON_CONTENT_TYPE
  return json.dumps(data)


@bottle.route('/api/get/:id/raw')
def get_raw(id):
  try:
    saved_paste = validated_paste(DS, id)
  except InvalidIDError:
    return error_response('Invalid ID', status=404, id=id)

  content = saved_paste.content()

  # Plain text output.
  bottle.response.content_type = 'text/plain; charset=UTF8'
  return content


@bottle.route('/api/get/:id/download')
def get_download(id):
  try:
    saved_paste = validated_paste(DS, id)
  except InvalidIDError:
    return error_response('Invalid ID', status=404, id=id)

  content = saved_paste.content()

  # Lookup file extension for lexer.
  lexer_alias = saved_paste.lexer_alias()
  filename = 'pastee-%s.%s' % (id, formatting.lexer_ext(lexer_alias))

  bottle.response.content_type = 'application/octet-stream; charset=UTF8'
  bottle.response.headers['Content-Disposition'] = \
      'attachment; filename=%s' % filename

  return content


@bottle.post('/api/submit')
def submit():
  err_msg = None

  # Extract data.
  content = bottle.request.POST.get('content', '')
  try:
    ttl = int(bottle.request.POST.get('ttl', DEFAULT_TTL))
  except TypeError:
    err_msg = 'Expected integer for ttl'
  lexer = bottle.request.POST.get('lexer', '')

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
    return error_response(err_msg, status=403)

  # Create paste.
  new_paste = paste.Paste(DS)
  new_paste.ttl_is(ttl)
  new_paste.lexer_alias_is(lexer)
  new_paste.ip_address_is(bottle.request.environ.get('REMOTE_ADDR'))
  new_paste.content_is(content)

  # Save paste.
  new_paste.save_state_is(paste.Paste.SaveStates.CLEAN)

  response = {'id': new_paste.id()}
  bottle.response.content_type = '%s; charset=UTF8' % JSON_CONTENT_TYPE
  return json.dumps(response)


def shutdown_handler(signum, frame):
  print 'caught signal %d; shutting down' % signum
  if TEST_MODE and DS.prefix() == TEST_MODE_PREFIX:
    keys = DS.keys()  # only keys starting with the testing prefix
    for key in keys:
      DS.delete(key)


def main():
  # Install signal handlers.
  signal.signal(signal.SIGBUS, shutdown_handler)
  signal.signal(signal.SIGINT, shutdown_handler)
  signal.signal(signal.SIGQUIT, shutdown_handler)
  signal.signal(signal.SIGSEGV, shutdown_handler)
  signal.signal(signal.SIGTERM, shutdown_handler)

  # Option parser for commandline options.
  parser = optparse.OptionParser()
  parser.add_option('-r', '--reloader', dest='reloader',
                    action='store_true', default=False,
                    help='Turn on auto-reloader')
  parser.add_option('-d', '--debug', dest='debug',
                    action='store_true', default=False,
                    help='Enable debug output')
  parser.add_option('-q', '--quiet', dest='quiet',
                    action='store_true', default=False,
                    help='Suppress output to stderr and stdout')
  parser.add_option('--test', dest='test',
                    action='store_true', default=False,
                    help='Test mode: created keys will be removed on shutdown')

  # Parse commandline options.
  (options, args) = parser.parse_args()

  # Adjust backend settings from options.
  if options.debug:
    bottle.debug(True)
  if options.test:
    # Enable test mode.
    global TEST_MODE
    TEST_MODE = True
    DS.prefix_is(TEST_MODE_PREFIX)

  # Translate optparse options to bottle options.
  kwargs = { }
  kwargs['quiet'] = options.quiet
  kwargs['reloader'] = options.reloader

  # Run server.
  bottle.run(host='localhost', port=8000, **kwargs)


if __name__ == '__main__':
  main()