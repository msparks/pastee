#!/usr/bin/python
# -*- coding: utf-8 -*-
from nose.tools import *
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pastee import formatting


class Test_Formatting:
  def test_lexers(self):
    '''lexers() returns something sane'''
    lexers = formatting.lexers()
    assert_true('Python' in lexers)
    assert_true('Bash' in lexers)
    assert_true('Perl' in lexers)
    assert_true('TeX' in lexers)
    assert_true('C++' in lexers)
    assert_true('Text only' in lexers)

  def test_lexer_aliases(self):
    '''lexer_aliases() returns something sane'''
    aliases = formatting.lexer_aliases()
    assert_true('py' in aliases)
    assert_true('python' in aliases)
    assert_true('bash' in aliases)
    assert_true('pl' in aliases)
    assert_true('tex' in aliases)
    assert_true('cpp' in aliases)
    assert_true('text' in aliases)

  def test_lexer_longname(self):
    '''Convert between aliases and long names'''
    assert_equal(formatting.lexer_longname('py'), 'Python')
    assert_equal(formatting.lexer_longname('cpp'), 'C++')

  def test_lexer_ext(self):
    '''Get file extension for lexer aliases'''
    assert_equal(formatting.lexer_ext('py'), 'py')
    assert_equal(formatting.lexer_ext('python'), 'py')
    assert_equal(formatting.lexer_ext('c++'), 'cpp')
    assert_equal(formatting.lexer_ext('perl'), 'pl')

  def test_validate_lexer_name(self):
    '''Ensure lexer aliases are valid'''
    # Valid lexer aliases.
    assert_equal(formatting.validate_lexer_name('py'), 'py')
    assert_equal(formatting.validate_lexer_name('python'), 'python')
    assert_equal(formatting.validate_lexer_name('pl'), 'pl')

    # Invalid lexer aliases should default to 'text'.
    assert_equal(formatting.validate_lexer_name('INVALID ALIAS'), 'text')
    assert_equal(formatting.validate_lexer_name('foo123'), 'text')
    assert_equal(formatting.validate_lexer_name(u'føøbár'), 'text')

  def htmlize(self):
    '''Basic HTMLization smoke tests'''
    text = u'føøbár'
    html = formatting.htmlize(text)

    # Sanity.
    assert_true(text in html)

    # The basic output structure is an HTML table.
    assert_true('<table>' in html)

    # We expect the 'syntax' CSS class to be used.
    assert_true('class="syntax"' in html)

    # Line numbers should be enabled.
    assert_true('class="linenos"' in html)
