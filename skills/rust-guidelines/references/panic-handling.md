# Panic Handling Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Universal Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html)

This reference includes only:

- [Panic Means 'Stop the Program' (`M-PANIC-IS-STOP`)](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html#M-PANIC-IS-STOP)
- [Detected Programming Bugs are Panics, Not Errors (`M-PANIC-ON-BUG`)](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html#M-PANIC-ON-BUG)

## Panic Means 'Stop the Program' (M-PANIC-IS-STOP)

Treat panic as a request for immediate program termination. Do not use panics as recoverable errors, upstream error communication, or routine handling for expected runtime conditions.

Valid panic cases are tied to programming errors or explicit stop-the-program requests, such as:

- An impossible internal invariant was violated.
- A const-context operation cannot return a recoverable error.
- The API intentionally exposes an `unwrap`-style operation.
- A poisoned lock indicates another thread has already panicked.

## Detected Programming Bugs are Panics, Not Errors (M-PANIC-ON-BUG)

When code detects an unrecoverable programming bug, panic instead of introducing an error type that callers cannot meaningfully handle.

Use `Result` for recoverable or user-driven failures, such as parsing invalid input. Use panic for contract violations and broken invariants when continuing would make the program state misleading or inconsistent.

When the boundary is unclear, prefer designs that are correct by construction. Use the type system to make invalid states unrepresentable where practical, and reserve runtime panics for the cases that remain true programming errors.
