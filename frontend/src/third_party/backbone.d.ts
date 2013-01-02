// This is a mostly complete declaration of backbone.js API. Some methods may be
// unintentionally missing. Missing methods and attributes should be added as
// needed.

declare module Backbone {
  export class Events {
    listenTo(other: any, event: any, callback: () => any): void;
  }

  export class Collection {
    constructor(models?: any[], opts?: any);
    initialize(models?: any[], opts?: any);

    toJSON(): any;

    // Subset of the underscore.js methods.
    create(attribtes, options?: any): Collection;
    each(f: (elem: any) => void): void;
    fetch(opts?: any): void;
    last(): any;
    last(n: number): any[];
    filter(f: (elem: any) => any): Collection;
    without(array: any[], ...values: any[]): Collection;

    length: number;
    model: any;
  }

  export class Model {
    constructor(attributes?, options?);
    initialize(attributes?, options?);

    change(): void;
    changedAttributes(attributes?: any): any;
    clear(options?: any): void;
    clone(): Model;
    defaults(): any;
    destroy(options?: any): void;
    escape(attribute: string): any;
    fetch(options?: any): void;
    get(attribute: string): any;
    has(attribute: string): bool;
    hasChanged(attribute?: string): bool;
    isNew(): bool;
    previous(attribute: string): any;
    previousAttributes(): any;
    save(attributes?: any, options?: any): void;
    set(attribute: string, value: any): void;
    set(attributes: Object): void;
    sync(method: string, model: Model, options?: any): void;
    toJSON(): any;
    unset(attribute: string, options?: any): void;
    url(): string;
    urlRoot(): string;
    validate(attributes: any): any;

    attributes: any;
    cid: string;
    id: any;
    idAttribute: string;
  }

  export class View extends Events {
    constructor(options?);
    initialize(options?);

    $(selector: string): any;
    delegateEvents(events: any): void;
    make(tagName: string, attributes?, content?): View;
    remove(): void;
    render(): View;
    setElement(element: any): void;
    undelegateEvents(): void;

    $el: any;
    attributes: any;
    el: any;
    events: any;
    model: Model;
    tagName: string;
  }
}
