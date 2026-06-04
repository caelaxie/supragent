# External Type Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Libraries / Interoperability Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/libs/interop/index.html)

This reference includes only:

- [Don't Leak External Types (`M-DONT-LEAK-TYPES`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/interop/index.html#M-DONT-LEAK-TYPES)

## Don't Leak External Types (M-DONT-LEAK-TYPES)

Prefer `std` types in public APIs where possible. In `no_std` or embedded-facing crates, prefer `core` types when that better matches the crate's portability contract.

Any type exposed in a public API becomes part of that API's contract. Exposing a third-party type leaks that dependency into downstream code and can turn dependency upgrades into breaking API changes.

Heuristics:

- Avoid leaking third-party types when a stable `std` or crate-owned wrapper can express the same contract.
- Sibling crates inside an umbrella crate may expose each other's types when the umbrella is the intended user-facing API.
- Feature-gated integrations may expose external types when the feature explicitly opts into that ecosystem, such as `serde`.
- Without a feature gate, expose a third-party type only when it provides substantial interoperability value.

When external errors or values need to cross the boundary, prefer wrapping them in a crate-owned public type and keeping the concrete dependency private.
