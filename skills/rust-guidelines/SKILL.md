---
name: rust-guidelines
description: Rust project engineering guidelines. Use in Rust projects and worktrees when writing, reviewing, refactoring, debugging, testing, documenting, or configuring Rust code. Apply the focused local references for covered topics, and use current official Rust docs when a task needs behavior or subdomain detail not covered here.
---

# Rust Guidelines

## Purpose

Use this skill as the entry point for Rust project work. It provides focused repo-local policy for covered topics; it is not a complete Rust encyclopedia.

Detailed Rust guidance lives in focused files under `references/`. Load only the references relevant to the current Rust task. When the current compiler, standard library, Cargo, Clippy, async runtime, FFI, or other external behavior matters and no local reference covers it, use Context7 or first-party docs before relying on memory.

## Work Loop

1. Identify the Rust scope.
- Inspect the relevant `Cargo.toml`, workspace layout, toolchain, rustfmt/clippy config, and existing test or CI commands before changing code.
- If the task is review-only, identify which crate, module, API boundary, or diff is being reviewed.

2. Load only relevant references.
- Use the reference index below to pick the smallest matching set.
- If several references overlap, prefer the most specific file for the decision and use broader files only for context.

3. Preserve local design.
- Follow existing crate style, public API compatibility, error conventions, feature flags, module boundaries, and test layout unless the task requires a deliberate change.
- Prefer small, typed, maintainable Rust over broad abstractions or dependency additions.

4. Test behavior proportionally.
- Add a regression test when fixing a bug and the project shape makes that practical.
- For API, unsafe, concurrency, or error-handling changes, include compile-time assertions, unit tests, integration tests, Miri, or focused examples when they are the right proof.

5. Verify before reporting.
- Run repo-specific checks when documented.
- Otherwise choose the narrowest meaningful checks from `cargo fmt --check`, `cargo clippy --all-targets --all-features`, and `cargo test --all-features`.
- If a check is too broad, unavailable, or irrelevant to the touched crate, run the closest targeted command and report the unverified surface.

## References

Load reference files only when they are relevant to the task. Keep each reference one level deep under `references/` and link it from this section after adding it.

- `references/lints.md`: compiler lint, Clippy lint, and lint override guidance from Microsoft Pragmatic Rust Guidelines.
- `references/construction.md`: builder and cascaded initialization guidance from Microsoft Pragmatic Rust Guidelines.
- `references/data.md`: generic data bounds, strong type family, public field tradeoffs, struct, enum, tuple, union, newtype, invariant, and builder guidance from the Rust API Guidelines, the PingCAP Rust Style Guide, and Microsoft Pragmatic Rust Guidelines.
- `references/documentation.md`: rustdoc summary sentence, module documentation, re-export presentation, public examples, and canonical doc section guidance from Microsoft Pragmatic Rust Guidelines and the Rust API Guidelines.
- `references/error-types.md`: error API boundaries, `Result` versus `Option`, canonical public error struct, upstream-cause, trait-object bounds, and application-level error crate guidance from the Rust API Guidelines, Microsoft Pragmatic Rust Guidelines, and the PingCAP Rust Style Guide.
- `references/expressions.md`: local expression shape, shadowing, discarded results, iteration, match and condition readability, and assertion and arithmetic guidance from the Rust Reference, Clippy, and the PingCAP Rust Style Guide.
- `references/external-types.md`: public API external type leakage guidance from Microsoft Pragmatic Rust Guidelines.
- `references/functions.md`: function and method placement, constructor shape, parameter ownership, return ownership, argument meaning, generic parameters, trait API shape, associated type guidance, and inline annotation guidance from the Rust API Guidelines and the PingCAP Rust Style Guide.
- `references/api-ergonomics.md`: flexible parameter trait and inherent functionality guidance from Microsoft Pragmatic Rust Guidelines.
- `references/magic-values.md`: documented magic value guidance from Microsoft Pragmatic Rust Guidelines.
- `references/naming.md`: concise type and trait naming, Rust casing, constructor, conversion, getter, iterator, and ownership-variant naming guidance from Microsoft Pragmatic Rust Guidelines, the Rust API Guidelines, and the PingCAP Rust Style Guide.
- `references/panic-handling.md`: panic versus recoverable error guidance from Microsoft Pragmatic Rust Guidelines.
- `references/performance.md`: benchmark-first optimization, allocation, copying, visible expensive behavior, synchronization cost, concurrency, and input-size guidance from the PingCAP Rust Style Guide and Rust standard library documentation.
- `references/public-traits.md`: public `Debug` and `Display` implementation guidance from Microsoft Pragmatic Rust Guidelines.
- `references/reexports.md`: public glob re-export and explicit re-export guidance from Microsoft Pragmatic Rust Guidelines.
- `references/regular-functions.md`: regular function versus associated function guidance from Microsoft Pragmatic Rust Guidelines.
- `references/resilience.md`: mockable I/O, mockable system calls, and feature-gated test utility guidance from Microsoft Pragmatic Rust Guidelines.
- `references/send-types.md`: public `Send` compatibility guidance from Microsoft Pragmatic Rust Guidelines.
- `references/simple-abstractions.md`: public API abstraction, wrapper exposure, service handle, and dependency hierarchy guidance from Microsoft Pragmatic Rust Guidelines.
- `references/statics.md`: static and thread-local global state guidance from Microsoft Pragmatic Rust Guidelines.
- `references/structured-logging.md`: structured logging and message-template guidance from Microsoft Pragmatic Rust Guidelines.
- `references/trait-impls.md`: trait implementation ordering, common standard traits, conversion traits, `Deref`, operators, iterators, `Drop`, and unsafe impl guidance from the Rust API Guidelines and the PingCAP Rust Style Guide.
- `references/unsafe-code.md`: unsafe code justification, soundness, unsafe marker semantics, safety documentation, performance, abstraction, and FFI guidance from Microsoft Pragmatic Rust Guidelines and the Rust API Guidelines.
