library paste_element;

import 'package:polymer/polymer.dart';

@CustomTag('paste-element')
class PasteElement extends PolymerElement {
  PasteElement.created() : super.created();

  void editableIs(bool value) {
    $['content'].contentEditable = value ? "true" : "false";
    $['content'].focus();
  }

  void focus() {
    $['content'].focus();
  }

  String get content {
    return $['content'].value;
  }
}
