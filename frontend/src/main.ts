/// <reference path="paste.d.ts" />
/// <reference path="third_party/backbone.d.ts" />
/// <reference path="third_party/closure.d.ts" />
/// <reference path="third_party/jquery.d.ts" />
/// <reference path="third_party/sjcl.d.ts" />

goog.require('paste');

goog.provide('pastee.main');

// Approximate number of seconds in one Earth day.
var kNumSecondsPerDay: number = 86400;
var kNumMillisPerSecond: number = 1000;

module pastee {

class PasteContainerView extends Backbone.View {
  initialize() {
    this.listenTo(this.model, 'change', this.render);
  }

  render() {
    console.log('PasteContainerView render()');
    $('#viewpaste').show();

    var is_encrypted: bool = this.model.get('paste_encrypted');
    if (typeof is_encrypted !== 'undefined' &&
        !is_encrypted) {
      var p: paste.Paste = this.model.get('paste');
      $('.viewpastebox').html(p.content);
    } else {
      console.log('encrypted or unknown');
    }

    return this;
  }
}

export function main() {
  var p = new paste.Paste();
  p.content = 'foo';
  p.lexer = 'text';

  var container = new paste.PasteContainer();

  var containerView = new PasteContainerView({
    model: container
  });

  container.set({
    paste: p,
    paste_encrypted: false
  });
}

}  // module pastee

goog.exportSymbol('pastee.main', pastee.main);
