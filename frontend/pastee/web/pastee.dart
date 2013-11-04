import 'dart:html';
import 'package:polymer/polymer.dart';

void main() {
  initPolymer();

  print('Pastee loaded.');
  var paste = query('paste-element');
  paste.focus();
  paste.editableIs(true);
}
