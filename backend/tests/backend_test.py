#!/usr/bin/python
# -*- coding: utf-8 -*-
from nose.tools import *
import json
import os
import subprocess
import sys
import time
import urllib
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
  PASTEE_PROC = subprocess.Popen([PASTEE_PATH, '--quiet', '--test'])
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
    response = urllib2.urlopen(request)
    assert_equal(response.getcode(), 200)

  def test_submit_post(self):
    '''Submit a new paste'''
    content = u'This is the content føøbár'
    lexer_alias = 'py'
    lexer_name = 'Python'
    ttl = 1234

    # Create a submit request.
    data = {'content': content.encode('utf-8'),
            'lexer': lexer_alias,
            'ttl': ttl}
    request = urllib2.Request('%s/api/submit' % PASTEE_URL,
                              data=urllib.urlencode(data))
    response = urllib2.urlopen(request)
    assert_equal(response.getcode(), 200)  # 200 = OK
    assert_equal(response.headers['Content-Type'],
                 'application/json; charset=UTF8')
    response_obj = json.loads(response.read())
    assert_true('id' in response_obj)

    # Request the new paste.
    id = response_obj['id']
    get_request = urllib2.Request('%s/api/get/%s' % (PASTEE_URL, id))
    response = urllib2.urlopen(get_request)
    assert_equal(response.headers['Content-Type'],
                 'application/json; charset=UTF8')
    response_obj = json.loads(response.read())

    # Ensure the returned values match those we inserted.
    assert_equal(response_obj['id'], id)
    assert_equal(response_obj['raw'], content)
    assert_equal(response_obj['lexer'], lexer_name)
    assert_equal(response_obj['ttl'], ttl)

    # Check the creation time.
    created_delta = time.time() - int(response_obj['created'])
    assert_true(created_delta < 5)
