---
name: rust-guidelines
description: Rust project engineering guidelines. Always use in Rust projects and worktrees, including Cargo crates and workspaces, when writing, reviewing, refactoring, debugging, testing, documenting, or configuring Rust code; editing Cargo.toml, Cargo.lock, rustfmt, clippy, rust-toolchain, build.rs, benches, examples, tests, or CI for Rust; designing Rust APIs, error handling, async/concurrency, ownership/lifetimes, unsafe code, FFI, performance-sensitive code, or crate/module boundaries.
---

# Rust Guidelines

## Purpose

Use this skill as the entry point for Rust project work.

This scaffold intentionally does not define Rust-specific rules yet. Add detailed material later as focused files under `references/`.

## References

Load reference files only when they are relevant to the task. Keep each reference one level deep under `references/` and link it from this section after adding it.

- `references/lints.md`: compiler lint, Clippy lint, and lint override guidance from Microsoft Pragmatic Rust Guidelines.
- `references/construction.md`: builder and cascaded initialization guidance from Microsoft Pragmatic Rust Guidelines.
- `references/error-types.md`: canonical public error struct and upstream-cause guidance from Microsoft Pragmatic Rust Guidelines.
- `references/external-types.md`: public API external type leakage guidance from Microsoft Pragmatic Rust Guidelines.
- `references/api-ergonomics.md`: flexible parameter trait and inherent functionality guidance from Microsoft Pragmatic Rust Guidelines.
- `references/magic-values.md`: documented magic value guidance from Microsoft Pragmatic Rust Guidelines.
- `references/naming.md`: concise type and trait naming, Rust casing, constructor, conversion, getter, iterator, and ownership-variant naming guidance from Microsoft Pragmatic Rust Guidelines, the Rust API Guidelines, and the PingCAP Rust Style Guide.
- `references/panic-handling.md`: panic versus recoverable error guidance from Microsoft Pragmatic Rust Guidelines.
- `references/public-traits.md`: public `Debug` and `Display` implementation guidance from Microsoft Pragmatic Rust Guidelines.
- `references/regular-functions.md`: regular function versus associated function guidance from Microsoft Pragmatic Rust Guidelines.
- `references/resilience.md`: mockable I/O, mockable system calls, and feature-gated test utility guidance from Microsoft Pragmatic Rust Guidelines.
- `references/send-types.md`: public `Send` compatibility guidance from Microsoft Pragmatic Rust Guidelines.
- `references/simple-abstractions.md`: public API abstraction, wrapper exposure, service handle, and dependency hierarchy guidance from Microsoft Pragmatic Rust Guidelines.
- `references/structured-logging.md`: structured logging and message-template guidance from Microsoft Pragmatic Rust Guidelines.
