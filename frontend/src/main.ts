/// <reference path="paste.d.ts" />
/// <reference path="third_party/backbone.d.ts" />
/// <reference path="third_party/closure.d.ts" />
/// <reference path="third_party/hljs.d.ts" />
/// <reference path="third_party/jquery.d.ts" />
/// <reference path="third_party/sjcl.d.ts" />

goog.require('paste');

goog.provide('pastee.main');

// Approximate number of seconds in one Earth day.
var kNumSecondsPerDay: number = 86400.0;

var kNumSecondsPerHour: number = 3600.0;
var kNumMillisPerSecond: number = 1000.0;

module pastee {

class TimeToLiveView extends Backbone.View {
  initialize() {
    this.listenTo(this.model, 'change:expiration_time', this.render);
  }

  render() {
    console.log('TimeToLiveView render()');

    // Epoch when the paste expires.
    var expirationTime: number = this.model.get('expiration_time');
    // Seconds since the Unix epoch.
    var nowEpoch: number = (new Date()).valueOf() / kNumMillisPerSecond;
    // Time to live in days.
    // TODO(ms): Break down by hour/minute/second.
    var ttlDays: number = (expirationTime - nowEpoch) / kNumSecondsPerDay;

    // TODO(ms): Need better formatting.
    $('.viewttl').html(Math.round(ttlDays * 1000) / 1000 + ' days');

    return this;
  }
}

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

      $('.viewid').html(this.model.get('id'));
      $('.viewinfo').show();
      $('.viewpastebox pre code').html(p.content);
      $('.viewpastebox pre code').each(function(i, e) {
        hljs.highlightBlock(e, null, false);
      });

      var lexer: string = $('.viewpastebox pre code').attr('class');
      console.log('lexer used: ' + lexer);
    } else {
      console.log('encrypted or unknown');
    }

    return this;
  }
}

export function main() {
  var p = new paste.Paste();
  p.content = "int main() {\n  printf(\"foo\\n\");\n  return 0;\n}";
  p.lexer = 'text';

  var container = new paste.PasteContainer();

  var containerView = new PasteContainerView({
    model: container
  });
  var timeToLiveView = new TimeToLiveView({
    model: container
  });

  container.set({
    id: '39rzrv',
    paste: p,
    paste_encrypted: false,
    expiration_time: 1420542903
  });
}

}  // module pastee

goog.exportSymbol('pastee.main', pastee.main);
