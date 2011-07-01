#!/usr/bin/python
# -*- coding: utf-8 -*-
from nose.tools import *
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pastee import datastore
from pastee import idmanager


class Test_IDManager:
  '''Test for idmanager.IDManager.

  This performs live tests. See the datastore tests for more information.
  '''
  def setup(self):
    self._ds = datastore.Datastore()
    self._testing_prefix = 'pastee:test'
    self._mgr = idmanager.IDManager(self._ds)

  def test_new_id(self):
    '''Create several random IDs'''
    # Create a lot of IDs.
    ids = []
    for i in range(128):
      ids.append(self._mgr.new_id())

    # Ensure they are all unique. This should be guaranteed by new_id().
    assert_true(len(set(ids)) == len(ids))

  def teardown(self):
    '''Clean up.'''
    keys = self._ds.keys()  # only keys starting with the testing prefix
    for key in keys:
      self._ds.delete(key)
