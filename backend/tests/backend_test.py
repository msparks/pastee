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
  def request(self, path, data=None, expected_status=200, expected_type=None):
    '''Sends a request to /api/<path> and asserts the expected status.

    Args:
      path: path after /api/
      data: data dictionary to pass (makes the request a POST)
      expected_status: numeric HTTP code to assert on response
      expected_type: expected content type string (defaults to json)

    Returns:
      urllib2.urlopen()'d response object
    '''
    class NullHTTPErrorProcessor(urllib2.HTTPErrorProcessor):
      def http_response(self, request, response):
        return response
    opener = urllib2.build_opener(NullHTTPErrorProcessor())

    if data is not None:
      # Convert data if necessary.
      for key in data.keys():
        if type(data[key]) == unicode:
          data[key] = data[key].encode('utf-8')
      data = urllib.urlencode(data)

    request = urllib2.Request('%s/api/%s' % (PASTEE_URL, path), data=data)
    response = opener.open(request)
    assert_equal(response.getcode(), expected_status)

    if expected_type is None:
      expected_type = 'application/json; charset=UTF8'
      assert_equal(response.headers['Content-Type'], expected_type)

    return response

  def test_index(self):
    '''GET request /api/'''
    self.request('', expected_type='text/html; charset=UTF8')

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
    response = self.request('submit', data=data)
    response_obj = json.loads(response.read())
    assert_true('id' in response_obj)

    # Request the new paste.
    id = response_obj['id']
    response = self.request('get/%s' % id)
    response_obj = json.loads(response.read())

    # Ensure the returned values match those we inserted.
    assert_equal(response_obj['raw'], content)
    assert_equal(response_obj['lexer'], lexer_name)
    assert_equal(response_obj['ttl'], ttl)

    # Check the creation time.
    created_delta = time.time() - int(response_obj['created'])
    assert_true(created_delta < 5)

  def test_expiry(self):
    '''Check paste expiry'''
    content = u'This is the content føøbár'
    lexer_alias = 'text'
    lexer_name = 'Text only'
    ttl = 1

    # Create a submit request.
    data = {'content': content.encode('utf-8'),
            'lexer': lexer_alias,
            'ttl': ttl}
    response = self.request('submit', data=data)
    response_obj = json.loads(response.read())
    assert_true('id' in response_obj)

    # Wait for the paste to expire.
    time.sleep(1.1)

    # Request the new paste.
    id = response_obj['id']
    response = self.request('get/%s' % id, expected_status=404)  # not found
    response_obj = json.loads(response.read())
    assert_true('id' in response_obj)
    assert_true('error' in response_obj)
    assert_equal(response_obj['id'], id)

  def test_large_paste(self):
    '''Check content size limits'''
    limit = 128 * 1024  # 128 KiB

    content = 'a' * limit
    lexer_alias = 'text'
    lexer_name = 'Text only'

    # Create a submit request for 'just small enough' content.
    data = {'content': content,
            'lexer': lexer_alias}
    response = self.request('submit', data=data)
    response_obj = json.loads(response.read())
    assert_true('id' in response_obj)  # successful paste

    # Try again with one extra character (over the limit).
    data = {'content': content + 'a',
            'lexer': lexer_alias}
    response = self.request('submit', data=data, expected_status=403)

  def test_no_content(self):
    '''Submit a paste with no content'''
    # Try small content first.
    data = {'content': 'x'}
    response = self.request('submit', data=data, expected_status=200)

    # Try empty content.
    data = {'content': ''}
    response = self.request('submit', data=data, expected_status=403)

    # Try no content.
    data = { }
    response = self.request('submit', data=data, expected_status=403)
