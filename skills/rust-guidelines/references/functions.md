# Function Signature Guidelines

Sources:

- [Rust API Guidelines - Interoperability](https://rust-lang.github.io/api-guidelines/interoperability.html)
- [Rust API Guidelines - Predictability](https://rust-lang.github.io/api-guidelines/predictability.html)
- [Rust API Guidelines - Type Safety](https://rust-lang.github.io/api-guidelines/type-safety.html)
- [Rust API Guidelines - Dependability](https://rust-lang.github.io/api-guidelines/dependability.html)
- [PingCAP Rust Style Guide - Functions](https://pingcap.github.io/style-guide/rust/functions.html)

This reference includes only:

- Function and method placement.
- Constructor shape.
- Parameter ownership and borrowing.
- Return ownership.
- Argument meaning and validation.
- Generic parameter tradeoffs.
- Inline annotation guidance.

## Source Precedence

Use the Rust API Guidelines as the higher-authority reference for public API behavior. Treat the PingCAP guide as practical style guidance where it aligns with official Rust API guidance, standard library trait contracts, and established crate conventions.

## Function Size

Prefer short functions and methods. Split large functions when the extracted parts have meaningful names or isolate a real subtask. If extraction only hides control flow behind vague helper names, consider introducing a small domain type or state object whose methods own the complexity.

Do not use `#[inline]`, `#[inline(always)]`, or `#[inline(never)]` as routine style. Add inline annotations only when profiling, benchmarking, or a documented public API constraint justifies the choice.

## Placement and Receivers

Prefer a method when there is a clear receiver. If an operation primarily uses `self`, `&self`, or `&mut self`, put it on the type.

Use associated functions for construction and operations that are logically part of the type's public API. Prefer a regular module function when the operation has no receiver and does not directly construct the type; see `regular-functions.md` for that boundary.

Private static helpers usually do not need to live in an `impl` block. Modules are the ordinary privacy boundary in Rust, so a private free function is often clearer than `Type::private_helper(...)`.

## Constructors

Use inherent constructors for ordinary construction:

- Implement `Default` when there is a meaningful, unsurprising default value.
- Use `new` for the primary constructor when it improves discoverability or matches local convention.
- Use `with_` names for a small number of secondary constructors with clear roles, such as `with_capacity`.
- Use a builder when construction has many optional settings, several construction permutations, or long positional argument lists.

`Default` and a zero-argument `new()` may coexist when both help callers. Avoid treating either one as mandatory boilerplate.

## Parameter Ownership

If a function needs to take ownership of an argument, accept the argument by value. Do not accept `&T` and immediately clone it unless the borrowed shape is required by a broader trait or compatibility contract.

If a function only needs to inspect an argument, prefer a borrowed parameter or a flexible borrowed view such as `impl AsRef<Path>`, `impl AsRef<str>`, or `impl AsRef<[u8]>` when callers naturally have multiple input shapes.

For generic synchronous I/O helpers, accept the reader or writer by value with the relevant trait bound:

```rust
fn read_config<R: std::io::Read>(mut reader: R) -> std::io::Result<Config> {
    // ...
}
```

References can implement these traits too, so callers can still pass `&mut reader` when they need to keep using the original value.

Use `Box<T>`, `Rc<T>`, `Arc<T>`, or other wrappers in parameters only when the wrapper itself is part of the semantic contract, such as shared ownership, dynamic dispatch, pinning, or heap allocation.

## Return Ownership

Prefer returning values directly. Avoid returning `Box<T>`, `Rc<T>`, `Arc<T>`, or other wrappers unless allocation, sharing, dynamic dispatch, pinning, or identity is part of the API contract.

For iterators and adapters, prefer `impl Iterator` or a named wrapper type over exposing brittle concrete adapter stacks in public APIs.

## Argument Meaning and Validation

Use argument types that communicate meaning. Prefer domain structs, newtypes, enums, ranges, and standard wrapper types over ambiguous positional primitives when the values can be confused.

Avoid public boolean parameters when an enum would make call sites clearer or leave room for future behavior. Use `Option<T>` when absence is truly part of the operation contract, not as a substitute for a named configuration type.

Prefer compile-time validation through the type system when the constraint is stable and worth the caller burden. Use runtime validation for contextual constraints or cases where a stronger type would make common calls worse.

## Generic Parameters

Use generic parameters and `impl Trait` when they give callers meaningful flexibility. Do not add generics only to hide trivial conversions at the call site.

For single, simple bounds, prefer `impl Trait` in parameter position. For complex bounds, repeated bounds, associated type constraints, or function traits, prefer explicit type parameters with a `where` clause.

Choose the closure trait that matches how the function uses the callback:

- Use `Fn` when the function only calls the callback without mutable capture or consumption.
- Use `FnMut` when the callback needs mutable captured state.
- Use `FnOnce` when the function consumes the callback or calls it at most once in a way that may consume captured values.

More than a few generic parameters is a design smell. Consider splitting the function, adding a small parameter object, moving behavior into a trait with associated types, or naming an intermediate type.
