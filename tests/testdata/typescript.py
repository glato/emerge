# Borrowed for testing with real test data from the Deep copy of Pinterest project.
# https://github.com/angular/angular/blob/master/packages/router/src/router_state.ts
# https://github.com/angular/angular/blob/master/packages/router/src/recognize.ts

TYPESCRIPT_TEST_FILES = {"file1.ts": """
/**
 * @license
 * Copyright Google LLC All Rights Reserved.
 *
 * Use of this source code is governed by an MIT-style license that can be
 * found in the LICENSE file at https://angular.io/license
 */

import {Type} from '@angular/core';
import {BehaviorSubject, Observable} from 'rxjs';
import {map} from 'rxjs/operators';

import {Data, ResolveData, Route} from './config';
import {convertToParamMap, ParamMap, Params, PRIMARY_OUTLET} from './shared';
import {equalSegments, UrlSegment, UrlSegmentGroup, UrlTree} from './url_tree';
import {shallowEqual, shallowEqualArrays} from './utils/collection';
import {Tree, TreeNode} from './utils/tree';

function setRouterState<U, T extends {_routerState: U}>(state: U, node: TreeNode<T>): void {
  node.value._routerState = state;
  node.children.forEach(c => setRouterState(state, c));
}

function serializeNode(node: TreeNode<ActivatedRouteSnapshot>): string {
  const c = node.children.length > 0 ? ` { ${node.children.map(serializeNode).join(', ')} } ` : '';
  return `${node.value}${c}`;
}

/**
 * The expectation is that the activate route is created with the right set of parameters.
 * So we push new values into the observables only when they are not the initial values.
 * And we detect that by checking if the snapshot field is set.
 */
export function advanceActivatedRoute(route: ActivatedRoute): void {
  if (route.snapshot) {
    const currentSnapshot = route.snapshot;
    const nextSnapshot = route._futureSnapshot;
    route.snapshot = nextSnapshot;
    if (!shallowEqual(currentSnapshot.queryParams, nextSnapshot.queryParams)) {
      (<any>route.queryParams).next(nextSnapshot.queryParams);
    }
    if (currentSnapshot.fragment !== nextSnapshot.fragment) {
      (<any>route.fragment).next(nextSnapshot.fragment);
    }
    if (!shallowEqual(currentSnapshot.params, nextSnapshot.params)) {
      (<any>route.params).next(nextSnapshot.params);
    }
    if (!shallowEqualArrays(currentSnapshot.url, nextSnapshot.url)) {
      (<any>route.url).next(nextSnapshot.url);
    }
    if (!shallowEqual(currentSnapshot.data, nextSnapshot.data)) {
      (<any>route.data).next(nextSnapshot.data);
    }
  } else {
    route.snapshot = route._futureSnapshot;

    // this is for resolved data
    (<any>route.data).next(route._futureSnapshot.data);
  }
}

export function equalParamsAndUrlSegments(
    a: ActivatedRouteSnapshot, b: ActivatedRouteSnapshot): boolean {
  const equalUrlParams = shallowEqual(a.params, b.params) && equalSegments(a.url, b.url);
  const parentsMismatch = !a.parent !== !b.parent;

  return equalUrlParams && !parentsMismatch &&
      (!a.parent || equalParamsAndUrlSegments(a.parent, b.parent!));
}
""", "file2.ts": """
import {Type} from '@angular/core';
import {Observable, Observer, of} from 'rxjs';

import {Data, ResolveData, Route, Routes} from './config';
import {ActivatedRouteSnapshot, inheritedParamsDataResolve, ParamsInheritanceStrategy, RouterStateSnapshot} from './router_state';
import {PRIMARY_OUTLET} from './shared';
import {UrlSegment, UrlSegmentGroup, UrlTree} from './url_tree';
import {last} from './utils/collection';
import {getOutlet, sortByMatchingOutlets} from './utils/config';
import {isImmediateMatch, match, noLeftoversInUrl, split} from './utils/config_matching';
import {TreeNode} from './utils/tree';

class NoMatch {}

function newObservableError(e: unknown): Observable<RouterStateSnapshot> {
  // TODO(atscott): This pattern is used throughout the router code and can be `throwError` instead.
  return new Observable<RouterStateSnapshot>((obs: Observer<RouterStateSnapshot>) => obs.error(e));
}

function sortActivatedRouteSnapshots(nodes: TreeNode<ActivatedRouteSnapshot>[]): void {
  nodes.sort((a, b) => {
    if (a.value.outlet === PRIMARY_OUTLET) return -1;
    if (b.value.outlet === PRIMARY_OUTLET) return 1;
    return a.value.outlet.localeCompare(b.value.outlet);
  });
}
""", "file3.ts": """
// Test parser also works with double-quote imports
import {sum} from "./math";

export function add10(a: number): number {
  return sum(a, 10);
}
""", "file4.ts": """
// Test parser also works with require-style imports
var Reflux = require("./lib/reflux");
var urlb = require('../lib/urlb');

export function search(info: Info, offset: number) {
  var url = urlb("/api/transaction-error-mappings", {
    code: info.code,
    message: info.message,
    operation: info.operation,
    unmapped: info.unmapped,
    offset: offset || 0,
    limit: 20
  });

  request.apiRequest("get", url, this.trigger.bind(this, "search"));
}

interface Info {
  code: number;
  message: string;
  operation: string;
  unmapped: boolean;
}

export const purchaseSearch = Reflux.createAction();
"""}
