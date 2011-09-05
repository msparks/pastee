import redis


class Datastore(object):
  '''Abstract wrapper for a key-value store.'''
  def __init__(self):
    '''Constructor.'''
    self._conn = redis.Redis()
    self._prefix = u''

  def _key(self, key):
    '''Returns 'key' with the prefix prepended, if any.'''
    if self._prefix == '':
      return key
    return u'%s:%s' % (self._prefix, key)

  def prefix(self):
    '''Returns the key prefix.'''
    return self._prefix

  def prefix_is(self, prefix):
    '''Sets the key prefix.

    All keys will be prefixed with this value and a colon before being inserted
    into the underlying datastore. Other methods use the prefix to set and get
    keys from the datastore.

    Args:
      prefix: new prefix to use
    '''
    self._prefix = prefix

  def value(self, key):
    '''Returns the value with given key, or None if the key does not exist.

    Args:
      key: key of value to retrieve

    Returns:
      string value or None
    '''
    value = self._conn.get(self._key(key))
    if value:
      value = value.decode('utf-8')
    return value

  def value_is(self, key, value):
    '''Sets the value for the key in the datastore.

    Args:
      key: string key
      value: stringifiable value
    '''
    self._conn.set(self._key(key), value)

  def nxvalue_is(self, key, value):
    '''Sets the value for 'key' if 'key' does not exist.

    Args:
      key: string key
      value: stringifiable value

    Raises:
      KeyError if the given key already exists. In this case, the existing
      value is not modified.
    '''
    success = self._conn.setnx(self._key(key), value)
    if not success:
      raise KeyError, 'key already exists'

  def ttl(self, key):
    '''Returns the TTL (in seconds) for a key.

    Args:
      key: string key

    Returns:
      TTL in seconds, or None if the key does not exist or does not have a TTL.
    '''
    return self._conn.ttl(self._key(key))

  def ttl_is(self, key, ttl):
    '''Sets the TTL (time to live) of a key.

    The TTL is removed automatically if this key's value is later updated.

    Args:
      key: string key
      ttl: Time to live in seconds, or None for no expiry.

    Returns:
      True on success (key exists and TTL was set)
    '''
    if ttl is None:
      return self._conn.persist(self._key(key))
    else:
      return self._conn.expire(self._key(key), ttl)

  def delete(self, key):
    '''Deletes a key.

    Args:
      key: key to delete

    Returns:
      True on success (key existed)
    '''
    return self._conn.delete(self._key(key))

  def keys(self, pattern=None):
    '''Returns a list of keys matching pattern.

    Args:
      pattern: string pattern; can have '*' and '?'

    Returns:
      list of matching keys
    '''
    if pattern is None:
      pattern = '*'
    keys = self._conn.keys(self._key(pattern))

    # Remove prefix from all keys.
    prefix = self._key('')
    keys = [x.decode('utf-8')[len(prefix):] for x in keys]
    return keys

  def exists(self, key):
    '''Check if a key exists.

    Args:
      key: key to check for existence

    Returns:
      True if key exists
    '''
    return self._conn.exists(self._key(key))

  def set_key_is(self, name, key):
    '''Add a key to a set.

    Args:
      name: string name of set
      key: string key to add to the set

    Returns:
      True if successful
    '''
    return self._conn.sadd(self._key(name), self._key(key))

  def set_key_delete(self, name, key):
    '''Delete a key from a set.

    Args:
      name: string name of set
      key: string key to remove from the set.

    Returns:
      True if successful
    '''
    return self._conn.srem(self._key(name), self._key(key))

  def set_keys(self, name):
    '''Return all keys in a set.

    Args:
      name: string name of set

    Returns:
      list of keys
    '''
    keys = self._conn.smembers(self._key(name))

    # Remove prefix from all keys.
    prefix = self._key('')
    keys = [x.decode('utf-8')[len(prefix):] for x in keys]
    return keys
