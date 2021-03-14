# Borrowed for testing with real test data from the swift-project.
# https://github.com/apple/swift

CPP_TEST_FILES = {"file1.cpp": """
//===--- ConcreteDeclRef.cpp - Reference to a concrete decl ---------------===//
//
// This source file is part of the Swift.org open source project
//
// Copyright (c) 2014 - 2017 Apple Inc. and the Swift project authors
// Licensed under Apache License v2.0 with Runtime Library Exception
//
// See https://swift.org/LICENSE.txt for license information
// See https://swift.org/CONTRIBUTORS.txt for the list of Swift project authors
//
//===----------------------------------------------------------------------===//
//
// This file implements the ConcreteDeclRef class, which provides a reference to
// a declaration that is potentially specialized.
//
//===----------------------------------------------------------------------===//

#include "swift/AST/ASTContext.h"
#include "swift/AST/ConcreteDeclRef.h"
#include "swift/AST/Decl.h"
#include "swift/AST/GenericSignature.h"
#include "swift/AST/ProtocolConformance.h"
#include "swift/AST/SubstitutionMap.h"
#include "swift/AST/Types.h"
#include "llvm/Support/raw_ostream.h"
using namespace swift;

ConcreteDeclRef ConcreteDeclRef::getOverriddenDecl() const {
  auto *derivedDecl = getDecl();
  auto *baseDecl = derivedDecl->getOverriddenDecl();

  auto baseSig = baseDecl->getInnermostDeclContext()
      ->getGenericSignatureOfContext();
  auto derivedSig = derivedDecl->getInnermostDeclContext()
      ->getGenericSignatureOfContext();

  SubstitutionMap subs;
  if (baseSig) {
    Optional<SubstitutionMap> derivedSubMap;
    if (derivedSig)
      derivedSubMap = getSubstitutions();
    subs = SubstitutionMap::getOverrideSubstitutions(baseDecl, derivedDecl,
                                                     derivedSubMap);
  }
  return ConcreteDeclRef(baseDecl, subs);
}

void ConcreteDeclRef::dump(raw_ostream &os) const {
  if (!getDecl()) {
    os << "**NULL**";
    return;
  }

  getDecl()->dumpRef(os);

  // If specialized, dump the substitutions.
  if (isSpecialized()) {
    os << " [with ";
    getSubstitutions().dump(os, SubstitutionMap::DumpStyle::Minimal);
    os << ']';
  }
}

void ConcreteDeclRef::dump() const {
  dump(llvm::errs());
}
""", "file2.cpp": """
//===--- Effects.cpp - Effect Checking ASTs -------------------------------===//
//
// This source file is part of the Swift.org open source project
//
// Copyright (c) 2014 - 2018 Apple Inc. and the Swift project authors
// Licensed under Apache License v2.0 with Runtime Library Exception
//
// See https://swift.org/LICENSE.txt for license information
// See https://swift.org/CONTRIBUTORS.txt for the list of Swift project authors
//
//===----------------------------------------------------------------------===//
//
//  This file implements some logic for rethrows and reasync checking.
//
//===----------------------------------------------------------------------===//

#include "swift/AST/ASTContext.h"
#include "swift/AST/Effects.h"
#include "swift/AST/Evaluator.h"
#include "swift/AST/Decl.h"
#include "swift/AST/ProtocolConformanceRef.h"
#include "swift/AST/Type.h"
#include "swift/AST/Types.h"
#include "swift/AST/TypeCheckRequests.h"
#include "llvm/ADT/ArrayRef.h"
#include "llvm/Support/raw_ostream.h"

using namespace swift;

bool AnyFunctionType::hasEffect(EffectKind kind) const {
  switch (kind) {
  case EffectKind::Throws: return getExtInfo().isThrowing();
  case EffectKind::Async: return getExtInfo().isAsync();
  }
  llvm_unreachable("Bad effect kind");
}

void swift::simple_display(llvm::raw_ostream &out, const EffectKind kind) {
  switch (kind) {
  case EffectKind::Throws: out << "throws"; return;
  case EffectKind::Async: out << "async"; return;
  }
  llvm_unreachable("Bad effect kind");
}

void swift::simple_display(llvm::raw_ostream &out,
                           const PolymorphicEffectRequirementList list) {
  for (auto req : list.getRequirements()) {
    simple_display(out, req);
    out << "\n";
  }

  for (auto conf : list.getConformances()) {
    simple_display(out, conf.first);
    out << " : ";
    simple_display(out, conf.second);
    llvm::errs() << "\n";
  }
}

PolymorphicEffectRequirementList 
ProtocolDecl::getPolymorphicEffectRequirements(EffectKind kind) const {
  return evaluateOrDefault(getASTContext().evaluator,
    PolymorphicEffectRequirementsRequest{kind, const_cast<ProtocolDecl *>(this)},
    PolymorphicEffectRequirementList());
}

bool ProtocolDecl::hasPolymorphicEffect(EffectKind kind) const {
  switch (kind) {
  case EffectKind::Throws:
    return getAttrs().hasAttribute<swift::AtRethrowsAttr>();
  case EffectKind::Async:
    return getAttrs().hasAttribute<swift::AtReasyncAttr>();
  }
  llvm_unreachable("Bad effect kind");
}

bool AbstractFunctionDecl::hasEffect(EffectKind kind) const {
  switch (kind) {
  case EffectKind::Throws:
    return hasThrows();
  case EffectKind::Async:
    return hasAsync();
  }
  llvm_unreachable("Bad effect kind");
}

bool AbstractFunctionDecl::hasPolymorphicEffect(EffectKind kind) const {
  switch (kind) {
  case EffectKind::Throws:
    return getAttrs().hasAttribute<swift::RethrowsAttr>();
  case EffectKind::Async:
    return getAttrs().hasAttribute<swift::ReasyncAttr>();
  }
  llvm_unreachable("Bad effect kind");
}

PolymorphicEffectKind
AbstractFunctionDecl::getPolymorphicEffectKind(EffectKind kind) const {
  return evaluateOrDefault(getASTContext().evaluator,
    PolymorphicEffectKindRequest{kind, const_cast<AbstractFunctionDecl *>(this)},
    PolymorphicEffectKind::Invalid);
}

void swift::simple_display(llvm::raw_ostream &out,
                           PolymorphicEffectKind kind) {
  switch (kind) {
  case PolymorphicEffectKind::None:
    out << "none";
    break;
  case PolymorphicEffectKind::ByClosure:
    out << "by closure";
    break;
  case PolymorphicEffectKind::ByConformance:
    out << "by conformance";
    break;
  case PolymorphicEffectKind::Always:
    out << "always";
    break;
  case PolymorphicEffectKind::Invalid:
    out << "invalid";
    break;
  }
}

bool ProtocolConformanceRef::hasEffect(EffectKind kind) const {
  if (!isConcrete()) { return true; }
  return evaluateOrDefault(getRequirement()->getASTContext().evaluator,
     ConformanceHasEffectRequest{kind, getConcrete()},
     true);
}
"""}
