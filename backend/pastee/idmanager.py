import math
import random

import datastore

CHARS = 'abcdefghjkmnpqrstuvwxyz23456789'
CHARMAP = {'a': 0,
           'b': 1,
           'c': 2,
           'd': 3,
           'e': 4,
           'f': 5,
           'g': 6,
           'h': 7,
           'j': 8,
           'k': 9,
           'm': 10,
           'n': 11,
           'p': 12,
           'q': 13,
           'r': 14,
           's': 15,
           't': 16,
           'u': 17,
           'v': 18,
           'w': 19,
           'x': 20,
           'y': 21,
           'z': 22,
           '2': 23,
           '3': 24,
           '4': 25,
           '5': 26,
           '6': 27,
           '7': 28,
           '8': 29,
           '9': 30}
CHARSPACE = len(CHARS)


class IDManager(object):
  '''Class to manage allocation of paste IDs.'''
  def __init__(self, ds):
    '''Constructor.

    Args:
      ds: datstore.Datastore object
    '''
    self._ds = ds

  @staticmethod
  def _random_id(size=5):
    id = ''
    for i in range(size):
      id += CHARS[random.randint(0, CHARSPACE - 1)]
    return id

  @staticmethod
  def _id_to_int(id):
    max_power = len(id) - 1
    integer = 0
    for i in range(0, len(id)):
      char = id[max_power - i]
      try:
        value = CHARMAP[char]
      except KeyError:
        return 0
      integer += value * math.pow(CHARSPACE, i)
    return int(integer)

  @staticmethod
  def _int_to_id(id_int):
    i = 0
    A = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    if id_int < CHARSPACE and id_int >= 0:
      return CHARS[id_int]
    while id_int > 0:
      A[i] = CHARS[id_int % CHARSPACE]
      id_int /= CHARSPACE
      i += 1
    A = A[0:i]
    A.reverse()
    return ''.join(A)

  def new_id(self):
    '''Return a new, unused paste ID.

    The returned ID is guaranteed not to previously exist. When this method
    returns, a metadata placeholder will exist for the new ID.

    Returns:
    id string
    '''
    while True:
      new_id = self._random_id()
      key = 'metadata:%s' % new_id

      try:
        # Try to reserve this ID. The value does not matter; we only need to
        # lock the key in the datastore.
        self._ds.nxvalue_is(key, 1)
      except KeyError:
        # This ID already exists. Try again.
        continue
      else:
        # We reserved this ID. We're done.
        return new_id
