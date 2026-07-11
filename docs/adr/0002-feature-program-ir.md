# 0002 — Feature Program IR as the core editable artifact

Status: Accepted

## Context
The defining requirement is that AI-generated parts stay **editable, parametric, and reproducible**. Two obvious representations fail this: a **mesh** loses design intent and can't be re-parameterised; **LLM-written CAD code** is non-deterministic, unsafe to re-run, and hard to diff or edit reliably.

## Decision
Adopt a **Feature Program IR** (`efir/1`): a serialisable, ordered, parametric recipe of features (sketch → extrude → hole → fillet → pattern…) with symbolic parameters and constraints. The AI and UI manipulate the IR; the CAD kernel **compiles** the IR to geometry. Parameter changes and AI edits are IR operations, enabling deterministic partial rebuilds, diffs, and undo/redo.

## Consequences
**Positive:** models stay editable + reproducible; kernel-agnostic (swap CadQuery later behind the port); AI edits are inspectable diffs, not opaque geometry; deterministic → golden/property-testable; enables partial re-execution for performance.
**Negative:** we must build and maintain a template/feature library and a compiler; some novel shapes won't map cleanly to IR features (handled by a sandboxed, parametrised code-feature fallback).
**Neutral:** introduces an IR schema that must be versioned and codegen'd across TS/Python.

## Alternatives considered
- **Store meshes:** rejected — not editable.
- **Store generated code:** rejected — non-deterministic, unsafe, poor diff/edit story.
- **B-rep only (STEP) as source of truth:** loses the parametric recipe and AI-editability; we keep STEP as an export/analysis output, not the editable source.
