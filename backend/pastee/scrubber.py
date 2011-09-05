#!/usr/bin/python
'''Scrubs expired pastes.'''
import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import settings

from pastee import datastore
from pastee import paste


class Scrubber(object):
  '''Helper to remove sensitive information from expired pastes.'''
  def __init__(self, ds):
    '''Constructor.

    Args:
      ds: datastore.Datastore instance
    '''
    self._ds = ds

  def active_paste_ids(self):
    '''Returns a list of unexpired pastes IDs.

    These pastes are in the 'unexpired' set. They may have been scrubbed
    already.

    Returns:
      list of string IDs
    '''
    keys = self._ds.set_keys('set:unexpired')
    ids = []
    for key in keys:
      if key.startswith('paste:'):
        k, id = key.split(':')
        ids.append(id)
    return ids

  def scrub(self, pst):
    '''Removes all sensitive information from the paste if it has expired.

    This is a no-op if the paste is still active or the paste has already been
    scrubbed.

    Args:
      pst: paste.Paste object to reap
    '''
    if not pst.expired():
      return

    # If content doesn't exist, paste is already scrubbed.
    if pst.content() is None:
      return

    # Remove content.
    pst.content_is(None)

    # Remove IP address.
    pst.ip_address_is(None)

    # Commit.
    # The paste is automatically removed from the 'unexpired' set on save.
    pst.save_state_is(paste.Paste.SaveStates.CLEAN)


def main():
  # Datastore instance.
  ds = datastore.Datastore()
  key_prefix = u'pastee'
  if getattr(settings, 'SITE_PREFIX', '') != '':
    key_prefix = u'%s:%s' % (key_prefix, getattr(settings, 'SITE_PREFIX'))
  ds.prefix_is(key_prefix)

  # Scrubber instance.
  scrubber = Scrubber(ds)

  print 'Key prefix: %s' % key_prefix
  print 'Loading unexpired paste IDs...'
  ids = scrubber.active_paste_ids()

  print 'Pastes found: %d' % len(ids)

  num_expired = 0

  for i, id in enumerate(ids):
    try:
      pst = paste.Paste(ds, id=id)
    except KeyError:
      print 'Warning: KeyError raised for ID %s' % id
      continue

    if pst.content() is None:
      continue  # already scrubbed

    if pst.expired():
      scrubber.scrub(pst)
      num_expired += 1

  print 'Pastes expired: %d' % num_expired


if __name__ == '__main__':
  main()
