# Error Type Guidelines

Sources:

- [Microsoft Pragmatic Rust Guidelines - Libraries / UX Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html)
- [Microsoft Pragmatic Rust Guidelines - Application Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/apps/index.html)

This reference includes only:

- [Errors are Canonical Structs (`M-ERRORS-CANONICAL-STRUCTS`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-ERRORS-CANONICAL-STRUCTS)
- [Application Error Handling (`M-APP-ERROR`)](https://microsoft.github.io/rust-guidelines/guidelines/apps/index.html#M-APP-ERROR)

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
- Implement `Display` as a concise description of the current error, including only caller-relevant local context.
- Return the upstream cause from `std::error::Error::source()` when wrapping a lower-level error, unless deliberately rendering that cause in `Display` instead.
- Do not duplicate the source chain or backtrace in normal `Display` output; keep that detail available through `Error::source()`, diagnostic accessors, `Debug`, or reporting layers.
- Implement `std::error::Error`; prefer `Send + Sync` error types where practical.
- Keep construction helpers private or crate-visible when callers should not create arbitrary invalid error states.
- Consider a private `bail!` helper macro only when the crate creates many errors and the macro keeps construction consistent.

## Application Error Handling (M-APP-ERROR)

Application crates, binary crates, and internal crates used exclusively by one application may use application-level error crates such as `anyhow`, `eyre`, or similar instead of defining public error structs for every failure path.

This is a relaxation of the library error guidance, not a replacement for it. Crates used by more than one crate should keep meaningful public error types that implement `std::error::Error`, `Display`, and the other traits callers need for interoperability.

When an application chooses an application-level error crate, use one consistently across application-level code. Do not mix several erased app error types just because individual modules prefer different crates.

Avoid erasing errors at boundaries where callers need to handle recoverable domain cases. If the caller can reasonably branch on a specific condition, keep that condition in a typed error, result enum, status type, or other explicit API contract before converting to the app-level error at the application boundary.
