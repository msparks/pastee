import redis


_ds_conn = None


def connection():
  global _ds_conn
  if _ds_conn is None:
    _ds_conn = redis.Redis()
  return _ds_conn


def set(key, *args):
  # Mangle key.
  key = 'pastee:%s' % key

  c = connection()
  return c.set(key, *args)


def get(key, *args):
  # Mangle key.
  key = 'pastee:%s' % key

  c = connection()
  return c.get(key, *args)


def exists(key, *args):
  # Mangle key.
  key = 'pastee:%s' % key

  c = connection()
  return c.exists(key, *args)


def getset(key, *args):
  # Mangle key.
  key = 'pastee:%s' % key

  c = connection()
  return c.getset(key, *args)
