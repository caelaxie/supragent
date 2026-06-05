# Public Re-Export Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Libraries / Resilience Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/libs/resilience/index.html)

This reference includes only:

- [Don't Glob Re-Export Items (`M-NO-GLOB-REEXPORTS`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/resilience/index.html#M-NO-GLOB-REEXPORTS)

## Don't Glob Re-Export Items (M-NO-GLOB-REEXPORTS)

Avoid public glob re-exports such as `pub use foo::*`, especially when `foo` is another crate. A public glob can accidentally expose new items, leak unintended dependencies into the public API, and make review diffs harder to reason about.

Prefer explicit public re-exports:

```rust
pub use foo::{A, B, C};
```

When an explicit public re-export of a crate-local item should appear as part of the current module's rustdoc surface, pair it with `#[doc(inline)]`; see `references/documentation.md`. This changes documentation presentation only and does not make glob re-exports safer.

Apply this rule to public crate, module, and prelude surfaces. It does not automatically ban private `use foo::*` imports in tests, local modules, or narrow implementation scopes; evaluate those under ordinary readability and lint guidance.

Glob re-exports can be acceptable for bounded technical forwarding, such as platform or HAL modules selected by `cfg`, when every forwarded module is intentionally part of the public surface:

```rust
#[cfg(target_os = "windows")]
pub use windows::*;

#[cfg(target_os = "linux")]
pub use linux::*;
```

When using this exception, keep the forwarded modules small and deliberate so the public API remains reviewable.
