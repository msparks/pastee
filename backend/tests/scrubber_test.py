#!/usr/bin/python
# -*- coding: utf-8 -*-
from nose.tools import *
import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pastee import datastore
from pastee import paste
from pastee import scrubber


class Test_Scrubber:
  '''Test for scrubber.Scrubber.

  This performs live tests. See the datastore tests for more information.
  '''
  def setup(self):
    self._ds = datastore.Datastore()
    self._ds.prefix_is('pastee:test')
    self._scrubber = scrubber.Scrubber(self._ds)

  def teardown(self):
    '''Clean up.'''
    keys = self._ds.keys()  # only keys starting with the testing prefix
    for key in keys:
      self._ds.delete(key)

  def test_scrub(self):
    '''Scrub many pastes'''
    ttl = 3600
    content = u'This is the content'
    ip_address = '4.2.2.2'
    lexer_alias = 'py'

    # Create an unexpired paste.
    active = paste.Paste(self._ds)
    active.ttl_is(ttl)
    active.content_is(content)
    active.ip_address_is(ip_address)
    active.lexer_alias_is(lexer_alias)
    active.save_state_is(paste.Paste.SaveStates.CLEAN)

    # Create two expired pastes.
    expired_a = paste.Paste(self._ds)
    expired_a.ttl_is(0)
    expired_a.content_is(content)
    expired_a.ip_address_is(ip_address)
    expired_a.lexer_alias_is(lexer_alias)
    expired_a.save_state_is(paste.Paste.SaveStates.CLEAN)

    expired_b = paste.Paste(self._ds)
    expired_b.ttl_is(0)
    expired_b.content_is(content)
    expired_b.ip_address_is(ip_address)
    expired_b.lexer_alias_is(lexer_alias)
    expired_b.save_state_is(paste.Paste.SaveStates.CLEAN)

    # Before scrubbing, all pastes are considered unexpired.
    expected_ids = (active.id(), expired_a.id(), expired_b.id())
    actual_ids = self._scrubber.active_paste_ids()
    assert_equal(sorted(actual_ids), sorted(actual_ids))

    # Try scrubbing all pastes.
    all_ids = expected_ids
    for id in all_ids:
      pst = paste.Paste(self._ds, id=id)
      self._scrubber.scrub(pst)

    # Only the expired pastes should have been scrubbed. Further, all sensitive
    # information should have been removed.
    reloaded_a = paste.Paste(self._ds, id=expired_a.id())
    assert_equal(reloaded_a.ttl(), 0)
    assert_equal(reloaded_a.content(), None)
    assert_equal(reloaded_a.ip_address(), None)
    assert_equal(reloaded_a.lexer_alias(), lexer_alias)

    reloaded_b = paste.Paste(self._ds, id=expired_b.id())
    assert_equal(reloaded_b.ttl(), 0)
    assert_equal(reloaded_b.content(), None)
    assert_equal(reloaded_b.ip_address(), None)
    assert_equal(reloaded_b.lexer_alias(), lexer_alias)

    # The active paste should have been untouched.
    reloaded_active = paste.Paste(self._ds, id=active.id())
    assert_equal(reloaded_active.ttl(), ttl)
    assert_equal(reloaded_active.content(), content)
    assert_equal(reloaded_active.ip_address(), ip_address)
    assert_equal(reloaded_active.lexer_alias(), lexer_alias)

    # After scrubbing, only the active paste should remain 'unexpired'.
    expected_ids = (active.id(),)
    actual_ids = self._scrubber.active_paste_ids()
    assert_equal(sorted(actual_ids), sorted(actual_ids))
