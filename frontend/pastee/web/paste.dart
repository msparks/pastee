import 'package:polymer/polymer.dart';

@CustomTag('paste-element')
class PasteElement extends PolymerElement {
  @observable String content = 'content';

  PasteElement.created() : super.created();
}