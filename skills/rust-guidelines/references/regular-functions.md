# Regular Function Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Universal Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html)

This reference includes only:

- [Prefer Regular over Associated Functions (`M-REGULAR-FN`)](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html#M-REGULAR-FN)

## Prefer Regular over Associated Functions (M-REGULAR-FN)

Use associated functions primarily for instance creation and other operations that clearly belong to the type.

Keep these in an `impl Type` block:

- Constructors such as `new`, `with_capacity`, `from_*`, or domain-specific constructors such as `open` and `connect`.
- Methods with an actual receiver, such as `&self`, `&mut self`, or `self`.
- Associated trait functions required by a trait contract.

Prefer a regular module function when the operation does not have a clear receiver and does not directly construct the type. This keeps call sites idiomatic and avoids making a type look responsible for unrelated computation.

Example decision:

```rust
struct Database;

impl Database {
    fn new() -> Self {
        Self
    }

    fn query(&self) {
        // Uses the database receiver.
    }
}

fn check_parameters(value: &str) {
    // No database receiver needed.
}
```
