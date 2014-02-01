import 'dart:html';
import 'package:polymer/polymer.dart';

import 'paste_element.dart';

void saveClicked(final Event event, PasteElement pasteElement) {
  print('save: ' + pasteElement.content);
}

void main() {
  initPolymer();

  PasteElement pasteElement;

  print('Pastee loaded.');
  pasteElement = querySelector('#main');
  pasteElement.focus();
  pasteElement.editableIs(true);

  querySelector('#save').onClick.listen(
      (event) => saveClicked(event, pasteElement));
}
