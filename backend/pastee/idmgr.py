import random
import math

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


def random_id(size=5):
  id = ''
  for i in range(size):
    id += CHARS[random.randint(0, CHARSPACE - 1)]
  return id


def id_to_int(id):
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


def int_to_id(id_int):
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


def random_unused_id():
  '''Return a new, unused ID.

  Returns:
    id string
  '''
  while True:
    new_id = random_id()
    key = 'paste:metadata:%s' % new_id

    if not datastore.exists(key):
      # Try to reserve this ID. The value does not matter; we only need to lock
      # the key in the datastore.
      old_data = datastore.getset(key, 1)

      if old_data is None:
        # We atomically swapped in a 1, effectively reserving this key.
        break
      else:
        # We thought this key didn't exist, but there's now data in it, so
        # someone else happened to get this key at the same time, and we just
        # overwrote it. Replace their data and try again. This is a race
        # condition, but this is the best we can do without better atomic
        # primitives in the datastore.
        datastore.set(key, old_data)

  return new_id
