#!/usr/bin/python
# -*- coding: utf-8 -*-
from nose.tools import *
import json
import os
import subprocess
import sys
import time
import urllib2

# Global instance of pastee backend process.
PASTEE_PROC = None

# Path to pastee.py, the backend.
PASTEE_PATH = os.path.join(os.path.dirname(__file__),
                           '..', 'pastee', 'pastee.py')

# Localhost URL to backend.
PASTEE_URL = 'http://localhost:8000'


def setup():
  global PASTEE_PROC
  PASTEE_PROC = subprocess.Popen([PASTEE_PATH, '--quiet'])
  print 'Pastee backend started; pid %d' % PASTEE_PROC.pid
  time.sleep(1)


def teardown():
  global PASTEE_PROC
  PASTEE_PROC.terminate()
  PASTEE_PROC.wait()


class Test_Pastee:
  '''End-to-end test for the Pastee backend.

  This performs live tests. See the datastore tests for more information.
  '''
  def test_index(self):
    '''GET request /api/'''
    request = urllib2.Request('%s/api/' % PASTEE_URL)
    response = urllib2.urlopen('%s/api/' % PASTEE_URL)
    assert_equals(response.getcode(), 200)
