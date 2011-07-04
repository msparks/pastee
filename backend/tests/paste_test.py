#!/usr/bin/python
# -*- coding: utf-8 -*-
from nose.tools import *
import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pastee import datastore
from pastee import paste


class Test_Paste:
  '''Test for paste.Paste.

  This performs live tests. See the datastore tests for more information.
  '''
  def setup(self):
    self._ds = datastore.Datastore()
    self._testing_prefix = 'pastee:test'
    self._paste = paste.Paste(self._ds)

  def _test_attribute(self, attr_name, value):
    attr_get_func = getattr(self._paste, attr_name)
    attr_set_func = getattr(self._paste, '%s_is' % attr_name)

    # Set the value.
    attr_set_func(value)
    assert_equal(attr_get_func(), value)

    # Changes have not yet been committed.
    assert_equal(self._paste.save_state(), paste.Paste.SaveStates.DIRTY)

    # Commit the changes.
    self._paste.save_state_is(paste.Paste.SaveStates.CLEAN)
    assert_equal(self._paste.save_state(), paste.Paste.SaveStates.CLEAN)

    # Retrieve the results.
    new_paste = paste.Paste(self._ds, id=self._paste.id())
    new_attr_get_func = getattr(new_paste, attr_name)
    assert_equal(new_attr_get_func(), value)

  def test_lexer_alias(self):
    '''Save and retrieve lexer alias'''
    for alias in ('text', 'py', 'pl'):
      self._test_attribute('lexer_alias', alias)

  def test_ttl(self):
    '''Save and retrieve TTL'''
    for ttl in (30, 60, 3000, 42.4342):
      self._test_attribute('ttl', ttl)

  def test_ip_address(self):
    '''Save and retrieve IP address'''
    for ip in ('4.2.2.2', '8.8.4.4'):
      self._test_attribute('ip_address', ip)

  def test_content(self):
    '''Save and retrieve paste content'''
    content = 'This is paste content'
    self._test_attribute('content', content)

  def test_id(self):
    '''Ensure new IDs are unique'''
    ids = []
    for i in range(128):
      new_paste = paste.Paste(self._ds)
      ids.append(new_paste.id())
    assert_equal(len(set(ids)), len(ids))

  def test_save_state(self):
    '''Ensure intentionally unsaved data is not committed'''
    # Paste object is dirty.
    self._paste.lexer_alias_is('py')

    # Paste object should hold lock, but datastore should not have an object.
    assert_raises(KeyError, paste.Paste, self._ds, id=self._paste.id())

    # Commit and load the saved paste.
    self._paste.save_state_is(paste.Paste.SaveStates.CLEAN)
    paste_after_save = paste.Paste(self._ds, id=self._paste.id())
    assert_equal(paste_after_save.lexer_alias(), self._paste.lexer_alias())

    # Change the lexer again, changing the state to dirty.
    self._paste.lexer_alias_is('pl')
    paste_before_next_commit = paste.Paste(self._ds, id=self._paste.id())
    assert_not_equals(paste_before_next_commit, self._paste.lexer_alias())

  def test_created(self):
    '''Check creation time'''
    # Created time is now.
    creation_delta = time.time() - self._paste.created()
    assert_true(creation_delta < 3)

  def teardown(self):
    '''Clean up.'''
    keys = self._ds.keys()  # only keys starting with the testing prefix
    for key in keys:
      self._ds.delete(key)
