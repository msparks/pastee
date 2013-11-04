import 'dart:html';
import 'package:polymer/polymer.dart';

@CustomTag('paste-element')
class PasteElement extends PolymerElement {
  @observable String content = '';

  PasteElement.created() : super.created();

  void editableIs(bool value) {
    $['content'].contentEditable = value ? "true" : "false";
    $['content'].focus();
  }

  void focus() {
    $['content'].focus();
  }
}
