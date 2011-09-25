'''Utility functions for dealing with Unix processes.'''
import logging
import os


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
