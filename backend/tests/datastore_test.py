#!/usr/bin/python
# -*- coding: utf-8 -*-
from nose.tools import *
import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pastee import datastore


class Test_Datastore:
  '''Test for pastee.datastore.

  This does both unit tests of code as well as live tests on a real
  datastore. A running instance of Redis is needed to pass the live tests in
  this suite.
  '''
  def setup(self):
    self._ds = datastore.Datastore()
    self._testing_prefix = 'pastee:test'

  def test_construct(self):
    '''Simple construction test'''
    assert_equal(type(self._ds), datastore.Datastore)

  def test_prefix(self):
    '''Set and get prefix'''
    # Empty prefix by default.
    assert_equal(self._ds.prefix(), '')

    # Check ascii and unicode strings.
    prefixes = ('foo', '1234', 'baz1234', u'føøbár')
    for prefix in prefixes:
      self._ds.prefix_is(prefix)
      assert_equal(self._ds.prefix(), prefix)
      assert_equal(self._ds._key('bar'), u'%s:bar' % prefix)

  def test_value(self):
    '''Live test: value() and value_is()'''
    # Use a specific testing prefix so we can clean up.
    self._ds.prefix_is(self._testing_prefix)

    # Ensure we can set and retrieve values, including unicode.
    kv = {'foo': 'bar',
          'baz1': 'quux1',
          'unicode!': u'føø/bár',
          u'føø/bárkey': 'string value'}
    for (key, value) in kv.items():
      self._ds.value_is(key, value)
      assert_equal(self._ds.value(key), value)

  def test_nxvalue(self):
    '''Live test: nxvalue_is()'''
    self._ds.prefix_is(self._testing_prefix)

    # Create a key.
    key = 'my_foo_key'
    self._ds.value_is(key, 'value')

    # nxvalue_is should fail because key exists.
    assert_raises(KeyError, self._ds.nxvalue_is, key, 'new value')

    # It should succeed on a non-existent key.
    self._ds.nxvalue_is('another key', 'another value')

  def test_exists(self):
    '''Live test: exists()'''
    self._ds.prefix_is(self._testing_prefix)
    keys = ('foo', 'bar', 'baz', 'quux', u'føø/bárkey')
    for key in keys:
      self._ds.value_is(key, 'value')
      assert_true(self._ds.exists(key))
      assert_true(key in self._ds.keys())

  def test_delete(self):
    '''Live test: delete()'''
    self._ds.prefix_is(self._testing_prefix)
    keys = ('foo', 'bar', 'baz', 'quux', u'føø/bárkey')
    for key in keys:
      self._ds.value_is(key, 'value')
      assert_true(self._ds.exists(key))
      assert_true(self._ds.delete(key))
      assert_false(self._ds.exists(key))

  def test_ttl(self):
    '''Live test: ttl() and ttl_is()'''
    self._ds.prefix_is(self._testing_prefix)

    # Create two keys: one will persist, one will expire.
    key_long = 'foo long'
    key_short = 'foo short'
    for key in (key_short, key_long):
      self._ds.value_is(key, 'value')

    # Set an expiration on both keys.
    ttl = 1  # seconds
    for key in (key_short, key_long):
      assert_true(self._ds.ttl_is(key, ttl))

    # Query expiration. Should not have changed in a short timeframe.
    for key in (key_short, key_long):
      assert_equals(self._ds.ttl(key), 1)

    # Remove expiration on the key to persist.
    assert_true(self._ds.ttl_is(key_long, None))

    # Wait for a short period. Expiring Key should be removed.
    time.sleep(2)
    assert_false(self._ds.exists(key_short))
    assert_true(self._ds.exists(key_long))

  def teardown(self):
    '''Clean up.'''
    # Set the prefix correctly, else we end up clearing the datastore entirely.
    self._ds.prefix_is(self._testing_prefix)
    keys = self._ds.keys()  # only keys starting with the testing prefix
    for key in keys:
      self._ds.delete(key)
