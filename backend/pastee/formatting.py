import pygments
import pygments.lexers
import pygments.formatters
import pygments.util


def lexers():
  return [lang for (lang, _, _, _) in pygments.lexers.get_all_lexers()]


def lexer_aliases():
  lex = []
  for (_, item_lex, _, _) in pygments.lexers.get_all_lexers():
    lex.extend(item_lex)
  return lex


def lexer_longname(shortname):
  for (longname, item_lex, _, _) in pygments.lexers.get_all_lexers():
    if shortname in item_lex:
      return longname


def lexer_list():
  lex_dict = {}
  for (longname, aliases, _, _) in pygments.lexers.get_all_lexers():
    lex_dict[longname] = aliases[0]
  longnames = lex_dict.keys()
  longnames.sort()
  llist = []
  for ln in longnames:
    llist.append((ln, lex_dict[ln]))
  return llist


def validate_lexer_name(lexer_name):
  if lexer_name not in lexer_aliases():
    return 'text'
  else:
    return lexer_name


def htmlize(text, lexer_name=None):
  if lexer_name is None:
    lexer_name = 'text'
  lexer = pygments.lexers.get_lexer_by_name(lexer_name, stripall=True)
  lexer.encoding = 'utf-8'
  formatter = pygments.formatters.HtmlFormatter(linenos=True, cssclass='syntax')
  html = pygments.highlight(text, lexer, formatter)
  return html
