# Expression Style Guidelines

Sources:

- [Rust Reference - Expressions](https://doc.rust-lang.org/stable/reference/expressions.html)
- [Rust Reference - Underscore Expressions](https://doc.rust-lang.org/stable/reference/expressions/underscore-expr.html)
- [Rust Reference - Patterns](https://doc.rust-lang.org/stable/reference/patterns.html)
- [Rust Reference - Operator Expressions](https://doc.rust-lang.org/stable/reference/expressions/operator-expr.html)
- [Rust Reference - Behavior Not Considered Unsafe](https://doc.rust-lang.org/stable/reference/behavior-not-considered-unsafe.html)
- [Clippy Lints](https://rust-lang.github.io/rust-clippy/master/)
- [PingCAP Rust Style Guide - Expressions and Statements](https://pingcap.github.io/style-guide/rust/exprs.html)

This reference includes only:

- Local expression and statement shape.
- Shadowing and mutability.
- Result-discarding and wildcard patterns.
- Iteration and collection updates.
- Match and condition readability.
- Panic, assertion, and integer arithmetic expression style.

## Source Precedence

Use the Rust Reference as the higher-authority source for language semantics. Treat Clippy as the main source for lint-specific enforcement, and use the PingCAP guide as practical style guidance where it improves readability without conflicting with local references.

When this file overlaps with `lints.md`, `panic-handling.md`, `structured-logging.md`, or `functions.md`, use those focused references for policy-level decisions.

## Debug Output and Logging

Do not leave `println!`, `dbg!`, `eprintln!`, or ad hoc formatted debug output in committed library or application code unless the output is part of the user-visible contract.

Use structured logging for operational events. For short-lived local debugging, remove the temporary output before committing or replace it with a stable event, assertion, test, or error message.

## Expression-Oriented Code

Prefer expression-oriented code when it keeps the data flow direct. Returning an `if`, `match`, block, or iterator expression can be clearer than initializing a mutable variable and assigning it later.

Do not force expression style when it hides control flow. Use statements, explicit temporaries, early returns, or small helper functions when they make validation, branching, or side effects easier to scan.

Avoid putting complex work directly in `if`, `while`, `match`, or guard conditions. Name the condition when it has multiple steps, visible side effects, or domain meaning:

```rust
let should_retry = attempts < max_attempts && error.is_transient();
if should_retry {
    // ...
}
```

## Shadowing and Mutability

Use shadowing when each binding represents the same logical value at a new stage, such as parsing, validating, wrapping, or narrowing a type. Avoid reusing the same name for unrelated values in the same scope.

Prefer a new immutable binding over a long-lived mutable binding when the value changes once. Use `mut` when the variable is intentionally updated over time, especially inside loops or stateful builders.

Minimize the scope of mutable borrows and mutable variables. If a value only needs temporary mutation during construction, use a small block and return the finalized value from that block.

## Functions, Closures, and Receivers

Use a function item instead of a closure when no environment is captured and a named function makes the call site clearer. Use a closure when capture, local context, or inline behavior is the point.

Prefer method-call syntax when the receiver is clear:

```rust
let next = value.clone();
```

Use fully qualified syntax when disambiguating traits, avoiding inference issues, or intentionally showing which trait method is being called.

## Moving and Replacing Values

Use `std::mem::replace`, `std::mem::take`, or type-specific helpers such as `Option::take` when moving a value out of a mutable reference while leaving a valid replacement behind.

Choose the helper that communicates the operation:

- `mem::replace(&mut value, replacement)` when the replacement is explicit.
- `mem::take(&mut value)` when the default value is the right replacement.
- `option.take()` when extracting an optional value and leaving `None`.

## Wildcards and Discarded Results

Do not use `_ = ...` or `let _ = ...` as a lazy way to silence an unused `Result` or other important return value. Explicit discard is fine when ignoring the value is the real intent and no destructor timing matters. For important results, prefer `?`, a meaningful branch, a named discard with explanation, or `expect` when the operation failing would indicate a programming error.

Understand the lifetime difference between `_` and an underscore-prefixed binding:

```rust
let _ = acquire_guard();       // The guard is not bound and drops immediately.
let _guard = acquire_guard();  // The guard is bound and drops at scope end.
```

Use `_name` only when a binding should exist but is intentionally unused, such as a guard whose destructor matters. Use `_` when the value is truly irrelevant and immediate drop is acceptable.

Avoid `_` as an intermediate type in unsafe casts or macros when an explicit type would make the operation safer to review. Type placeholders such as `Vec<_>` are fine when they keep inference readable.

## Type Hints and Conversions

Prefer a local type annotation when it makes inference and ownership clearer:

```rust
let items: Vec<_> = iter.collect();
```

Use turbofish when the type belongs naturally to the method call or a local annotation would be noisy. Avoid type ascription-style patterns that are less idiomatic or harder to scan.

At call sites, use `.into()` when the target type is clear from context. When the target type is not clear, prefer an explicit constructor or conversion path. This does not change trait guidance: implement `From` and `TryFrom` for conversions when those traits fit.

## Collection Updates and Iteration

Use collection entry APIs such as `HashMap::entry` when updating based on whether a key already exists. This avoids duplicate lookups and keeps insert-or-update behavior local to one expression.

Prefer iterator adapters when they express a direct transformation, filter, fold, or collection pipeline. Prefer `for` loops when they make side effects, early exits, mutation, borrowing, or multi-step logic clearer.

Do not use `collect` only to force iteration when the collected value is unused. Use `for_each` for a small side-effecting iterator chain, or a `for` loop when it reads better.

Avoid index-based iteration over collections unless the index itself is part of the logic. Prefer iterators, `enumerate`, windows, chunks, or direct references to elements.

## Match and Condition Shape

Prefer `if let` or `let ... else` for a single interesting pattern. Prefer `match` when multiple cases matter, exhaustiveness is valuable, or the branches are easier to compare side by side.

Use `Option` and `Result` combinators when they keep the happy path and error path clear. Use `match` when combinator chains become indirect, deeply nested, or hard to debug.

Avoid destructuring every public struct field in a pattern unless that complete shape is part of the local requirement. Use `..` for ignored fields so adding a field does not break code unnecessarily.

Prefer explicit enum patterns over a wildcard when adding a new variant should force a compiler error. Use `_` only when all remaining cases are genuinely handled the same way.

Let match ergonomics handle borrowing when possible. Reach for explicit `ref` and `ref mut` patterns only when they make ownership or borrowing more understandable.

Put the positive branch first when both branches are similar. Use a guarded early return when one branch is small and the other contains the main work.

## Panics, Assertions, and Arithmetic

Make panicking behavior visible through naming, documentation, or an explicit `expect` message. Do not hide panics in ordinary-looking helper calls when callers need to know the operation can stop the program.

Use `debug_assert!` for internal invariant checks where skipping the check in optimized builds is acceptable. Use `assert!` when violating the condition is a programming error that should be checked in all builds. Use normal validation and `Result` for recoverable or user-driven failures.

Use ordinary arithmetic operators when overflow is impossible under the operation's invariants. Do not rely on implicit profile-dependent overflow behavior when overflow matters. Choose an explicit method such as `checked_add`, `saturating_add`, `wrapping_add`, or `overflowing_add`.
