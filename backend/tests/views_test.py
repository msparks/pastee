#!/usr/bin/python
# -*- coding: utf-8 -*-
from nose.tools import *
import json
import os
import sys
import time

# Set up path to load the Django settings module.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django import http

from pastee import views


class Test_Views:
  '''Test for views.

  This performs live tests. See the datastore tests for more information.
  '''
  def setup(self):
    # Set the testing prefix.
    views.DS.prefix_is('pastee:test')

  def test_index(self):
    '''Test index'''
    # Empty call to /.
    views.index(None)

  def test_new_paste(self):
    '''Submit a new paste'''
    content = u'This is the content føøbár'
    lexer_alias = 'py'
    lexer_name = 'Python'
    ttl = 1234
    ip_address = '4.2.2.2'

    # Create a submit request.
    post_request = http.HttpRequest()
    post_request.POST['content'] = content
    post_request.POST['lexer'] = lexer_alias
    post_request.POST['ttl'] = ttl
    post_request.META['REMOTE_ADDR'] = ip_address

    # Ensure we submitted successfully.
    response = views.submit(post_request)
    assert_equal(response.status_code, 200)  # 200 = OK
    assert_equal(response['Content-Type'], 'application/json')
    response_obj = json.loads(response.content)
    assert_true('id' in response_obj)

    # Request the new paste.
    id = response_obj['id']
    get_request = http.HttpRequest()
    response = views.get(get_request, id)
    assert_equal(response['Content-Type'], 'application/json')
    response_obj = json.loads(response.content)

    # Ensure the returned values match those we inserted.
    assert_equal(response_obj['id'], id)
    assert_equal(response_obj['raw'], content)
    assert_equal(response_obj['lexer'], lexer_name)
    assert_equal(response_obj['ttl'], ttl)

    # Check the creation time.
    created_delta = time.time() - int(response_obj['created'])
    assert_true(created_delta < 5)

  def test_expired_paste(self):
    '''Check paste expiry'''
    ttl = 1

    # Create a new post submission.
    post_request = http.HttpRequest()
    post_request.POST['content'] = 'foo'
    post_request.POST['lexer'] = 'text'
    post_request.POST['ttl'] = ttl
    post_request.META['REMOTE_ADDR'] = '4.2.2.2'

    # Verify successful submission.
    response = views.submit(post_request)
    assert_equal(response.status_code, 200)  # 200 = OK
    assert_equal(response['Content-Type'], 'application/json')
    response_obj = json.loads(response.content)
    assert_true('id' in response_obj)

    # Wait for paste to expire.
    time.sleep(1.1)

    # Request the new paste.
    id = response_obj['id']
    get_request = http.HttpRequest()
    response = views.get(get_request, id)
    assert_equal(response.status_code, 403)  # 403 = Forbidden (expired)
    assert_equal(response['Content-Type'], 'application/json')
    response_obj = json.loads(response.content)
    assert_true('id' in response_obj)
    assert_true('error' in response_obj)

  def teardown(self):
    '''Clean up.'''
    keys = views.DS.keys()  # only keys starting with the testing prefix
    for key in keys:
      views.DS.delete(key)
