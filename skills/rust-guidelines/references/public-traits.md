# Public Trait Implementations

Source: [Microsoft Pragmatic Rust Guidelines - Universal Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html)

This reference includes only:

- [Public Types are `Debug` (`M-PUBLIC-DEBUG`)](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html#M-PUBLIC-DEBUG)
- [Public Types Meant to be Read are `Display` (`M-PUBLIC-DISPLAY`)](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html#M-PUBLIC-DISPLAY)

## Public Types are `Debug` (M-PUBLIC-DEBUG)

All public types exposed by a crate should implement `Debug`.

Use `#[derive(Debug)]` for ordinary data types. For types that can hold secrets or other sensitive data, implement `Debug` manually, redact the sensitive fields, and add regression tests that prove the rendered output does not leak the original secret.

Checklist:

- Derive `Debug` for public structs and enums unless custom rendering is required.
- Redact secret-bearing fields in manual `Debug` implementations.
- Test redaction behavior with representative secret values.

## Public Types Meant to be Read are `Display` (M-PUBLIC-DISPLAY)

Public types expected to be read by upstream consumers should implement `Display`.

This especially applies to:

- Error types, because `std::error::Error` requires `Display`.
- Wrappers around string-like data.

`Display` output should follow Rust formatting customs for human-readable text, including the expected treatment of newlines and escape sequences. Apply the same sensitive-data redaction discipline used for `Debug` when a readable representation could expose secrets.
