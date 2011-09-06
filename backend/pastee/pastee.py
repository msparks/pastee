#!/usr/bin/python
import errno
import json
import logging
import optparse
import os
import pprint
import select
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
import scrubber

JSON_CONTENT_TYPE = 'application/json'

# Settings and defaults.
MAX_LENGTH = getattr(settings, 'MAX_LENGTH', 128)           # 128 KiB
MAX_TTL = getattr(settings, 'MAX_TTL', 86400 * 365)         # 1 year
DEFAULT_TTL = getattr(settings, 'DEFAULT_TTL', 86400 * 30)  # 1 month

# Test mode: keys created with the test mode prefix are removed upon shutdown.
TEST_MODE = False
TEST_MODE_PREFIX = 'pastee:test'

# Our child process pids.
CHILDREN = []

# Our pidfile.
PIDFILE = None

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

  # No content means the paste has already expired.
  if saved_paste.content() is None:
    raise InvalidIDError

  # Check for TTL expiry. If content exists, the paste may be pending
  # expiration.
  if saved_paste.expired():
    # Paste is pending expiration (content needs to be deleted).
    scrubber_obj = scrubber.Scrubber(ds)
    scrubber_obj.scrub(saved_paste)
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
  elif len(content) > (MAX_LENGTH * 1024):  # KiB
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


def write_pidfile(path):
  '''Write this process's pid to a pidfile.

  Args:
    path: file path to write

  Raises:
    IOError on open() or write() failure
  '''
  if path is None:
    return
  logging.debug('Writing pidfile')
  fh = open(path, 'w')
  fh.write(str(os.getpid()))
  fh.close()


def kill_pidfile(path):
  '''Removes a pidfile.

  Args:
    path: file path to delete

  Raises:
    OSError on failure
  '''
  if path is None:
    return
  if not os.path.exists(path):
    logging.info('Pidfile does not exist; ignoring.')
    return
  logging.debug('Removing pidfile')
  os.unlink(path)


def kill_existing_instance(pidfile):
  '''Sends a SIGTERM to an existing server instance.

  This is a no-op if the pidfile does not exist.

  Args:
    pidfile: path to pidfile containing the pid

  Raises:
    IOError on open() or read() failure
    OSError on any other error except 'No such process'
  '''
  if not os.path.isfile(pidfile):
    logging.info('pidfile does not exist. Assuming server is not running.')
    return

  fh = open(pidfile, 'r')
  pid = fh.read()
  fh.close()

  pid = int(pid.strip())
  logging.info('Sending TERM signal to pid %d' % pid)
  try:
    os.kill(pid, signal.SIGTERM)
  except OSError, e:
    if e.errno == errno.ESRCH:
      logging.info('Pid %d is not alive; ignoring.' % pid)
      return
    else:
      raise

  # Wait a second for the process to die to avoid a race on the pidfile. If we
  # continue too fast, we will write our pid to the pidfile and the dying
  # process will delete it. This also gives the other server a chance to clean
  # up and release the server ports.
  # TODO(ms): Is there something more reliable to use here?
  time.sleep(1)


def daemonize():
  '''Fork into the background.

  When this function returns, the process will be running in the background.

  Raises:
    OSError on any system call failure
  '''
  # This function is implemented based on the guidelines in "Advanced
  # Programming in the Unix Environment", 2e, by W. Richard Stevens.
  pid = os.fork()
  if pid > 0:
    # We're the parent. Exit.
    # _exit() abruptly exits without calling cleanup routines. We will give
    # this responsibility to the child.
    os._exit(0)

  # Child.
  os.setsid()  # create new session; ditch controlling tty

  # Find the maximum number of file descriptors.
  import resource
  maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
  if (maxfd == resource.RLIM_INFINITY):
    maxfd = 1024

  # Iterate through and close all file descriptors.
  for fd in range(0, maxfd):
    try:
      os.close(fd)
    except OSError:  # fd wasn't open to begin with (ignored)
      pass

  # Attach stdin (0), stdout (1) and stderr (2) to /dev/null.
  os.open(os.devnull, os.O_RDWR)  # fd 0
  os.dup2(0, 1)                   # fd 1 (stdout)
  os.dup2(0, 2)                   # fd 2 (stderr)


def cleanup_and_exit(code=0):
  '''Perform necessary cleanup tasks and exit.

  Args:
    code: exit code
  '''
  if not TEST_MODE:
    logging.info('Cleaning up.')

  # Kill children.
  for pid in CHILDREN:
    try:
      os.kill(pid, signal.SIGTERM)
    except OSError:
      pass  # it's okay if they're already dead

  # Clean up test mode keys.
  if TEST_MODE and DS.prefix() == TEST_MODE_PREFIX:
    keys = DS.keys()  # only keys starting with the testing prefix
    for key in keys:
      DS.delete(key)

  # Remove pidfile.
  if PIDFILE is not None:
    try:
      kill_pidfile(PIDFILE)
    except IOError, e:
      logging.error('Error while deleting pidfile: %s' % e)

  # Exit.
  logging.info('Exiting.')
  sys.exit(0)


def shutdown_handler(signum, frame):
  if not TEST_MODE:
    logging.info('Caught signal %d; shutting down.' % signum)
  cleanup_and_exit()


def install_signal_handlers():
  signal.signal(signal.SIGBUS, shutdown_handler)
  signal.signal(signal.SIGINT, shutdown_handler)
  signal.signal(signal.SIGQUIT, shutdown_handler)
  signal.signal(signal.SIGSEGV, shutdown_handler)
  signal.signal(signal.SIGTERM, shutdown_handler)


def main():
  # Set up logging.
  _fmt = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  logging.basicConfig(level=logging.INFO, format=_fmt)
  root_logger = logging.getLogger()

  # Option parser for commandline options.
  parser = optparse.OptionParser()
  parser.add_option('-d', '--debug', dest='debug',
                    action='store_true', default=False,
                    help='Enable debug output')
  parser.add_option('-l', '--host', dest='host', default='localhost',
                    help='Listening server hostname')
  parser.add_option('-c', '--children', type='int', dest='children', default=1,
                    help='Number of child servers to fork')
  parser.add_option('-p', '--port', type='int', dest='port', default=8000,
                    help='Listening server port')
  parser.add_option('-q', '--quiet', dest='quiet',
                    action='store_true', default=False,
                    help='Suppress output to stderr and stdout')
  parser.add_option('-r', '--reloader', dest='reloader',
                    action='store_true', default=False,
                    help='Turn on auto-reloader')
  parser.add_option('--daemonize', dest='daemonize',
                    action='store_true', default=False,
                    help='Run in the background')
  parser.add_option('--pidfile', dest='pidfile', default=None,
                    help='Write main process pid to this path')
  parser.add_option('--restart', dest='restart',
                    action='store_true', default=False,
                    help='(Re)start the server. Requires --pidfile')
  parser.add_option('--test', dest='test',
                    action='store_true', default=False,
                    help='Test mode: created keys will be removed on shutdown')

  # Parse commandline options.
  (options, args) = parser.parse_args()

  # --restart requires --pidfile.
  if options.restart and not options.pidfile:
    parser.error('--restart option requires --pidfile')

  # Adjust backend settings from options.
  if options.debug:
    root_logger.setLevel(logging.DEBUG)
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
  kwargs['host'] = options.host
  kwargs['port'] = options.port

  # Kill existing instance if --restart was specified.
  if options.restart:
    kill_existing_instance(options.pidfile)

  # Fork to the background if --daemonize is specified.
  if options.daemonize:
    root_logger.info('Daemonizing...')
    daemonize()

  # Write pidfile if requested.
  if options.pidfile is not None:
    global PIDFILE
    PIDFILE = options.pidfile
    write_pidfile(PIDFILE)

  # Prefork and spawn multiple children to handle requests.
  for i in range(options.children):
    pid = os.fork()
    if pid == 0:
      # We're the child. Run the server.
      try:
        kwargs['port'] += i  # ports must be different for children
        bottle.run(server='tornado', **kwargs)
      except select.error, e:
        num, msg = e
        if num == 4:  # 'Interrupted system call'
          pass
        else:
          raise

      # Done.
      sys.exit(0)
    else:
      # We're the parent.
      global CHILDREN
      CHILDREN.append(pid)

  # Install signal handlers in the master process.
  install_signal_handlers()

  # Wait for children.
  try:
    os.wait()
  except KeyboardInterrupt:
    pass
  else:
    logging.info('All children are dead.')

  # Cleanup and exit.
  cleanup_and_exit()


if __name__ == '__main__':
  main()
