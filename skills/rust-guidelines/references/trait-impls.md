# Trait Implementation Guidelines

Sources:

- [Rust API Guidelines - Interoperability](https://rust-lang.github.io/api-guidelines/interoperability.html)
- [Rust API Guidelines - Predictability](https://rust-lang.github.io/api-guidelines/predictability.html)
- [Rust API Guidelines - Future Proofing](https://rust-lang.github.io/api-guidelines/future-proofing.html)
- [PingCAP Rust Style Guide - Implementing Traits](https://pingcap.github.io/style-guide/rust/traits.html)

This reference includes only:

- [Rust API Guidelines - Interoperability](https://rust-lang.github.io/api-guidelines/interoperability.html)
- [Rust API Guidelines - Predictability](https://rust-lang.github.io/api-guidelines/predictability.html)
- [Rust API Guidelines - Future Proofing](https://rust-lang.github.io/api-guidelines/future-proofing.html)
- [PingCAP Rust Trait Guide](https://pingcap.github.io/style-guide/rust/traits.html)

## Source Precedence

Use the Rust API Guidelines as the higher-authority reference for public API trait behavior. Treat the PingCAP guide as practical style guidance where it does not conflict with official Rust API guidance or the standard library trait contracts.

## Impl Placement and Ordering

Keep implementations close to the type or trait they implement:

- Put inherent `impl` blocks near the concrete type.
- Put blanket impls near the trait definition.
- Group impls for the same trait together.
- Keep all impls in one module when practical, but split very large impls when that improves readability.

When a type has many impls, prefer this rough order:

1. Inherent impls.
2. Important domain trait impls.
3. Marker trait impls, such as `Send`, `Sync`, and `Unpin`.
4. Utility trait impls, such as formatting, conversion, and collection traits.

Multiple inherent impl blocks with the same signature are acceptable when they create useful rustdoc method groups.

## Common Standard Traits

Implement common standard traits when they are semantically valid for the type. This especially applies to public types in published crates, where standard traits improve interoperability.

Common candidates include:

- `Copy` and `Clone` when duplication semantics are clear and cheap enough.
- `Eq`, `PartialEq`, `Ord`, `PartialOrd`, and `Hash` when equality, ordering, and hashing obey the standard contracts.
- `Debug` for public types, with custom redaction for secret-bearing values.
- `Display` only when there is a stable human-readable representation.
- `Default` when there is a clear, unsurprising default value.

Use `Debug` for developer diagnostics and logs, not as user-facing output. Use `Display` or structured rendering for text that users, API clients, or error messages are expected to read.

Prefer `derive` over manual impls when the derived behavior is correct. Use manual impls when the trait contract needs custom semantics, redaction, ordering, or validation.

`Default` and a zero-argument `new()` may coexist. Implement `Default` when the default value is meaningful, and keep `new()` when it improves discoverability or matches constructor conventions.

## Conversion and Borrowing Traits

Prefer standard conversion traits where they fit:

- Implement `From<T>` for infallible conversions.
- Implement `TryFrom<T>` for fallible conversions.
- Do not implement `Into<T>` or `TryInto<T>` directly; they are provided by blanket impls from `From` and `TryFrom`.
- Implement `AsRef<T>` and `AsMut<T>` for cheap reference conversions.

Use `Borrow<T>` only when the borrowed and owned forms have equivalent `Eq`, `Ord`, and `Hash` behavior. `AsRef<T>` is less restrictive and is often the better fit for simple borrowed views.

If `AsMut<T>` is implemented, `AsRef<T>` should usually be implemented as well.

Smart-pointer-like types that implement `Deref` should usually also provide an explicit `AsRef<T>` or `Borrow<T>` conversion when that conversion is semantically valid. Implement `ToOwned` only when there is a natural owned form of the borrowed value.

## Deref and Operators

Implement `Deref` and `DerefMut` only for smart-pointer-like types. Do not use `Deref` as general-purpose implicit coercion or as a shortcut for exposing another type's methods.

Implement operator traits from `std::ops` only when the operation clearly matches the operator's normal meaning. Avoid operator overloading when multiple plausible interpretations exist.

Use `Index` for collection-like types where indexing is expected. Avoid `Index` for arbitrary lookup APIs when panics, missing keys, or non-collection semantics would surprise callers.

## Iterators and Collections

Collection-like types should usually support iteration:

- Provide `iter()` and `iter_mut()` for borrowed iteration when useful.
- Implement `IntoIterator` for consuming iteration.
- Implement `FromIterator` when constructing from an iterator is natural.
- Implement `Extend` for mutable collections that can absorb more items.

When returning iterator adapters from public APIs, avoid exposing brittle concrete adapter stacks unless the exact type is part of the API value. Prefer `impl Iterator` or a named wrapper type when that preserves future flexibility.

## Drop and Unsafe Impls

`Drop` implementations should not intentionally panic or perform fallible or blocking teardown as their only cleanup path. Be careful with implicit panics inside `drop`, such as indexing or unchecked assumptions that can fail.

If shutdown can fail or block, expose an explicit method such as `close()` or `shutdown()` that callers can invoke before drop. That method can return a `Result`; `Drop` should remain best-effort and non-panicking.

Unsafe impls, including unsafe marker trait impls, can create crate-wide soundness obligations. Add them only when the safety argument is clear, local, and documented. Prefer tests or compile-time assertions for important marker trait expectations such as `Send` and `Sync`.
