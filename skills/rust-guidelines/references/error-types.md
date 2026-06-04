# Error Type Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Libraries / UX Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html)

This reference includes only:

- [Errors are Canonical Structs (`M-ERRORS-CANONICAL-STRUCTS`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-ERRORS-CANONICAL-STRUCTS)

## Errors are Canonical Structs (M-ERRORS-CANONICAL-STRUCTS)

Prefer situation-specific public error structs over broad public error enums. A simple crate can expose one `Error` type; a larger crate can expose focused types such as `AccessError`, `ConfigurationError`, or `DownloadError`.

Error structs should carry the information needed for debugging and handling:

- A captured `Backtrace`.
- The upstream cause when one exists.
- Helper methods for caller-relevant context.

Use an internal `ErrorKind` enum when one public error type must represent several related failure modes. Keep that enum private unless exposing every variant is a deliberate public API commitment. Prefer stable helper predicates or accessors such as `is_io()`, `is_protocol()`, or `config_file()` for behavior callers can rely on.

Avoid collapsing unrelated operations into one global error type just to reduce type count. Prefer distinct error types when the failure domains do not overlap, but keep reusable error types for genuinely shared situations such as parsing similar input formats.

Implementation checklist:

- Capture the backtrace where the error is created, including `From<UpstreamError>` conversions.
- Implement `Display` with a summary, backtrace, and cause/context information.
- Implement `std::error::Error`.
- Keep construction helpers private or crate-visible when callers should not create arbitrary invalid error states.
- Consider a private `bail!` helper macro only when the crate creates many errors and the macro keeps construction consistent.
