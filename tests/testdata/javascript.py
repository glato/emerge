# Borrowed for testing with real test data from the React project.
# https://github.com/facebook/react

JAVASCRIPT_TEST_FILES = {"file1.js": """
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

import ReactVersion from 'shared/ReactVersion';
import {
  REACT_FRAGMENT_TYPE,
  REACT_PROFILER_TYPE,
  REACT_STRICT_MODE_TYPE,
  REACT_SUSPENSE_TYPE,
  REACT_SUSPENSE_LIST_TYPE,
} from 'shared/ReactSymbols';

import {Component, PureComponent} from './ReactBaseClasses';
import {createRef} from './ReactCreateRef';
import {forEach, map, count, toArray, only} from './ReactChildren';
import {
  createElement,
  createFactory,
  cloneElement,
  isValidElement,
  jsx,
} from './ReactElement';
import {createContext} from './ReactContext';
import {lazy} from './ReactLazy';
import forwardRef from './forwardRef';
import memo from './memo';
import chunk from './chunk';
import {
  useCallback,
  useContext,
  useEffect,
  useImperativeHandle,
  useDebugValue,
  useLayoutEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
  useResponder,
  useTransition,
  useDeferredValue,
} from './ReactHooks';
import {withSuspenseConfig} from './ReactBatchConfig';
import {
  createElementWithValidation,
  createFactoryWithValidation,
  cloneElementWithValidation,
  jsxWithValidation,
  jsxWithValidationStatic,
  jsxWithValidationDynamic,
} from './ReactElementValidator';
import ReactSharedInternals from './ReactSharedInternals';
import createFundamental from 'shared/createFundamentalComponent';
import createResponder from 'shared/createEventResponder';
import createScope from 'shared/createScope';
import {
  enableJSXTransformAPI,
  enableDeprecatedFlareAPI,
  enableFundamentalAPI,
  enableScopeAPI,
  exposeConcurrentModeAPIs,
  enableChunksAPI,
  disableCreateFactory,
} from 'shared/ReactFeatureFlags';
const React = {
  Children: {
    map,
    forEach,
    count,
    toArray,
    only,
  },

  createRef,
  Component,
  PureComponent,

  createContext,
  forwardRef,
  lazy,
  memo,

  useCallback,
  useContext,
  useEffect,
  useImperativeHandle,
  useDebugValue,
  useLayoutEffect,
  useMemo,
  useReducer,
  useRef,
  useState,

  Fragment: REACT_FRAGMENT_TYPE,
  Profiler: REACT_PROFILER_TYPE,
  StrictMode: REACT_STRICT_MODE_TYPE,
  Suspense: REACT_SUSPENSE_TYPE,

  createElement: __DEV__ ? createElementWithValidation : createElement,
  cloneElement: __DEV__ ? cloneElementWithValidation : cloneElement,
  isValidElement: isValidElement,

  version: ReactVersion,

  __SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED: ReactSharedInternals,
};

if (!disableCreateFactory) {
  React.createFactory = __DEV__ ? createFactoryWithValidation : createFactory;
}

if (exposeConcurrentModeAPIs) {
  React.useTransition = useTransition;
  React.useDeferredValue = useDeferredValue;
  React.SuspenseList = REACT_SUSPENSE_LIST_TYPE;
  React.unstable_withSuspenseConfig = withSuspenseConfig;
}

if (enableChunksAPI) {
  React.chunk = chunk;
}

if (enableDeprecatedFlareAPI) {
  React.DEPRECATED_useResponder = useResponder;
  React.DEPRECATED_createResponder = createResponder;
}

if (enableFundamentalAPI) {
  React.unstable_createFundamental = createFundamental;
}

if (enableScopeAPI) {
  React.unstable_createScope = createScope;
}

// Note: some APIs are added with feature flags.
// Make sure that stable builds for open source
// don't modify the React object to avoid deopts.
// Also let's not expose their names in stable builds.

if (enableJSXTransformAPI) {
  if (__DEV__) {
    React.jsxDEV = jsxWithValidation;
    React.jsx = jsxWithValidationDynamic;
    React.jsxs = jsxWithValidationStatic;
  } else {
    React.jsx = jsx;
    // we may want to special case jsxs internally to take advantage of static children.
    // for now we can ship identical prod functions
    React.jsxs = jsx;
  }
}

export default React;
""", "file2.js": """
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 *
 * @flow
 */

import {existsSync} from 'fs';
import {basename, join, isAbsolute} from 'path';
import {execSync, spawn} from 'child_process';
import {parse} from 'shell-quote';

function isTerminalEditor(editor: string): boolean {
  switch (editor) {
    case 'vim':
    case 'emacs':
    case 'nano':
      return true;
    default:
      return false;
  }
}

// Map from full process name to binary that starts the process
// We can't just re-use full process name, because it will spawn a new instance
// of the app every time
const COMMON_EDITORS = {
  '/Applications/Atom.app/Contents/MacOS/Atom': 'atom',
  '/Applications/Atom Beta.app/Contents/MacOS/Atom Beta':
    '/Applications/Atom Beta.app/Contents/MacOS/Atom Beta',
  '/Applications/Sublime Text.app/Contents/MacOS/Sublime Text':
    '/Applications/Sublime Text.app/Contents/SharedSupport/bin/subl',
  '/Applications/Sublime Text 2.app/Contents/MacOS/Sublime Text 2':
    '/Applications/Sublime Text 2.app/Contents/SharedSupport/bin/subl',
  '/Applications/Visual Studio Code.app/Contents/MacOS/Electron': 'code',
};

function getArgumentsForLineNumber(
  editor: string,
  filePath: string,
  lineNumber: number,
): Array<string> {
  switch (basename(editor)) {
    case 'vim':
    case 'mvim':
      return [filePath, '+' + lineNumber];
    case 'atom':
    case 'Atom':
    case 'Atom Beta':
    case 'subl':
    case 'sublime':
    case 'wstorm':
    case 'appcode':
    case 'charm':
    case 'idea':
      return [filePath + ':' + lineNumber];
    case 'joe':
    case 'emacs':
    case 'emacsclient':
      return ['+' + lineNumber, filePath];
    case 'rmate':
    case 'mate':
    case 'mine':
      return ['--line', lineNumber + '', filePath];
    case 'code':
      return ['-g', filePath + ':' + lineNumber];
    default:
      // For all others, drop the lineNumber until we have
      // a mapping above, since providing the lineNumber incorrectly
      // can result in errors or confusing behavior.
      return [filePath];
  }
}

function guessEditor(): Array<string> {
  // Explicit config always wins
  if (process.env.REACT_EDITOR) {
    return parse(process.env.REACT_EDITOR);
  }

  // Using `ps x` on OSX we can find out which editor is currently running.
  // Potentially we could use similar technique for Windows and Linux
  if (process.platform === 'darwin') {
    try {
      const output = execSync('ps x').toString();
      const processNames = Object.keys(COMMON_EDITORS);
      for (let i = 0; i < processNames.length; i++) {
        const processName = processNames[i];
        if (output.indexOf(processName) !== -1) {
          return [COMMON_EDITORS[processName]];
        }
      }
    } catch (error) {
      // Ignore...
    }
  }

  // Last resort, use old skool env vars
  if (process.env.VISUAL) {
    return [process.env.VISUAL];
  } else if (process.env.EDITOR) {
    return [process.env.EDITOR];
  }

  return [];
}

let childProcess = null;

export function getValidFilePath(
  maybeRelativePath: string,
  absoluteProjectRoots: Array<string>,
): string | null {
  // We use relative paths at Facebook with deterministic builds.
  // This is why our internal tooling calls React DevTools with absoluteProjectRoots.
  // If the filename is absolute then we don't need to care about this.
  if (isAbsolute(maybeRelativePath)) {
    if (existsSync(maybeRelativePath)) {
      return maybeRelativePath;
    }
  } else {
    for (let i = 0; i < absoluteProjectRoots.length; i++) {
      const projectRoot = absoluteProjectRoots[i];
      const joinedPath = join(projectRoot, maybeRelativePath);
      if (existsSync(joinedPath)) {
        return joinedPath;
      }
    }
  }

  return null;
}

export function doesFilePathExist(
  maybeRelativePath: string,
  absoluteProjectRoots: Array<string>,
): boolean {
  return getValidFilePath(maybeRelativePath, absoluteProjectRoots) !== null;
}

export function launchEditor(
  maybeRelativePath: string,
  lineNumber: number,
  absoluteProjectRoots: Array<string>,
) {
  const filePath = getValidFilePath(maybeRelativePath, absoluteProjectRoots);
  if (filePath === null) {
    return;
  }

  // Sanitize lineNumber to prevent malicious use on win32
  // via: https://github.com/nodejs/node/blob/c3bb4b1aa5e907d489619fb43d233c3336bfc03d/lib/child_process.js#L333
  if (lineNumber && isNaN(lineNumber)) {
    return;
  }

  let [editor, ...args] = guessEditor();
  if (!editor) {
    return;
  }

  if (lineNumber) {
    args = args.concat(getArgumentsForLineNumber(editor, filePath, lineNumber));
  } else {
    args.push(filePath);
  }

  if (childProcess && isTerminalEditor(editor)) {
    // There's an existing editor process already and it's attached
    // to the terminal, so go kill it. Otherwise two separate editor
    // instances attach to the stdin/stdout which gets confusing.
    childProcess.kill('SIGKILL');
  }

  if (process.platform === 'win32') {
    // On Windows, launch the editor in a shell because spawn can only
    // launch .exe files.
    childProcess = spawn('cmd.exe', ['/C', editor].concat(args), {
      stdio: 'inherit',
    });
  } else {
    childProcess = spawn(editor, args, {stdio: 'inherit'});
  }
  childProcess.on('error', function() {});
  childProcess.on('exit', function(errorCode) {
    childProcess = null;
  });
}
""", "file3.js": """
// Test parser also works with double-quote imports
import {sum} from "./math";

export function add10(a) {
  return sum(a, 10);
}
""", "file4.js": """
// Test parser also works with require-style imports
var Reflux = require("./lib/reflux");
var urlb = require('../lib/urlb');

function search(info, offset) {
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

module.exports = {
  search,
  purchaseSearch: Reflux.createAction()
}
"""}
