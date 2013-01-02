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

export function main() {
  var p = new paste.Paste();
  p.content = 'foo bar this is a paste';
  p.lexer = 'text';

  var password: string = 'password';
  var cyphertext: string = sjcl.encrypt(password, JSON.stringify(p));

  var pc = new paste.PasteContainer();
  pc.paste = JSON.parse(cyphertext);
  pc.paste_encrypted = true;

  var now = new Date();
  pc.creation_time = now.valueOf() / kNumMillisPerSecond;

  var ttl_days: number = 30;
  var expiration_date = new Date(now.valueOf() + ttl_days * kNumSecondsPerDay);
  pc.expiration_time = expiration_date.valueOf() / kNumMillisPerSecond;

  console.log(JSON.stringify(pc));
}

}  // module pastee

goog.exportSymbol('pastee.main', pastee.main);
