# Magic Value Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Universal Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html)

This reference includes only:

- [Magic Values are Documented (`M-DOCUMENTED-MAGIC`)](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html#M-DOCUMENTED-MAGIC)

## Magic Values are Documented (M-DOCUMENTED-MAGIC)

Hardcoded magic values in production code should be documented when their meaning, impact, or external dependency is not obvious from the surrounding code.

Prefer named constants over inline values. The name should explain what the value represents, and the nearby documentation or comment should explain:

- Why the value was chosen.
- Non-obvious side effects if the value changes.
- External systems, protocols, policies, or limits that interact with the value.

Inline comments are acceptable for narrow local values. Use a named constant with a doc comment when the value is reused, part of a public or cross-module contract, or likely to be tuned later.

Example:

```rust
/// Large enough for the upstream server to finish normal exports.
///
/// Setting this too low can abort valid requests. Based on the
/// documented timeout behavior of the upstream export API.
const UPSTREAM_EXPORT_TIMEOUT: Duration = Duration::from_secs(60 * 60 * 24);
```
