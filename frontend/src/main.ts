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
    return this;
  }
}

export function main() {
  var container = new paste.PasteContainer();

  var containerView = new PasteContainerView({
    model: container
  });

  container.set('attribute', 'value');
}

}  // module pastee

goog.exportSymbol('pastee.main', pastee.main);
