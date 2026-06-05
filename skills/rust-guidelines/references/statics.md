# Static State Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Libraries / Resilience Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/libs/resilience/index.html)

This reference includes only:

- [Avoid Statics (`M-AVOID-STATICS`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/resilience/index.html#M-AVOID-STATICS)

## Avoid Statics (M-AVOID-STATICS)

Avoid `static` and thread-local state in libraries when correctness depends on every caller seeing one consistent value. Rust can link multiple versions of the same crate into one dependency graph, so a crate-local static can be duplicated in ways users do not expect.

Watch for statics that hold:

- Mutable counters, registries, caches, feature flags, configuration, or handles whose value affects correctness.
- State that is read by several public entry points and expected to be globally consistent.
- Test-sensitive state that makes unit tests order-dependent or hard to isolate.

Prefer explicit state:

- Pass a crate-owned handle, service object, runtime, or context through construction.
- Store shared state behind a cloneable public handle when callers need to pass it around.
- Let callers own configuration or registries when application-level consistency matters.

This is not a blanket ban on `const` items or immutable statics. Constants and immutable statics are fine when they represent fixed values, lookup tables, or other data where duplicate instances cannot change behavior.

Performance-only statics can be acceptable when duplicate instances across crate versions do not affect correctness. If a static is only a memoized optimization, document or structure it so correctness does not depend on sharing that exact instance.
