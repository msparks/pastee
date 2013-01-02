/// <reference path="third_party/closure.d.ts" />

goog.provide('paste');

module paste {

export class Paste {
  // Content of the paste.
  content: string;

  // The name of the lexer used to do syntax highlighting of the content.
  lexer: string;
}

// Wrapper for a Paste object.
//
// This container holds metadata needed by the server that must be kept external
// to the Paste itself if the Paste is encrypted.
export class PasteContainer {
  // A Paste object that is possibly encrypted.
  paste: Object;
  paste_encrypted: bool;

  // Time the Paste was created as a Unix epoch.
  creation_time: number;

  // Time the Paste shall expire as a Unix epoch.
  expiration_time: number;
}

}  // module paste
