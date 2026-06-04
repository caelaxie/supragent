# Naming Guidelines

Sources:

- [Microsoft Pragmatic Rust Guidelines - Universal Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html)
- [PingCAP Rust Style Guide - Naming](https://pingcap.github.io/style-guide/rust/naming.html)

This reference includes only:

- [Names are Free of Weasel Words (`M-CONCISE-NAMES`)](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html#M-CONCISE-NAMES)
- [PingCAP Rust Naming Guide](https://pingcap.github.io/style-guide/rust/naming.html)

## Names are Free of Weasel Words (M-CONCISE-NAMES)

Symbol names, especially type and trait names, should avoid generic words that do not add meaningful information.

Common weak suffixes include:

- `Service`
- `Manager`
- `Factory`

Prefer names that describe the concrete domain object or behavior. For example, use `Bookings` for an item that handles bookings, and choose a more specific name such as `BookingDispatcher` when the type's role is to submit bookings elsewhere.

Avoid `Manager` unless the type manages a genuinely distinctive lifecycle or coordination responsibility that cannot be named more precisely. Most Rust resource lifecycle behavior should be expressed through ownership, constructors, and `Drop`.

Avoid `Factory` terminology. In Rust, a type that configures construction is usually a `Builder`. If repeatable instantiation is needed as an input, prefer accepting an `impl Fn() -> Foo` over a factory object.

## PingCAP Rust Naming Guide

Prefer names that communicate meaning clearly. Short names are acceptable for very narrow local scopes, such as closure arguments, loop counters, and one-line match arms, but public APIs and broader local scopes should use descriptive English names.

### Casing and Word Choice

Use standard Rust casing:

- Types, traits, and enum variants use `UpperCamelCase`.
- Struct fields, functions, methods, local variables, macros, and modules use `snake_case`.
- Constants and immutable statics use `SCREAMING_SNAKE_CASE`.
- Crate names use `kebab-case` in Cargo metadata and `snake_case` in Rust code. Prefer one-word crate names when practical.

Use full words instead of project-local abbreviations unless the abbreviation is standard in the Rust, database, or domain community. Treat acronyms as words, such as `Sql` or `GrpcType`, not all-caps fragments embedded in identifiers.

When a desired name is a Rust keyword, use a conventional abbreviation such as `ty`, an underscore suffix such as `crate_`, or a raw identifier only when interoperability or generated code requires it.

Use Rust naming conventions at Rust boundaries even when interacting with non-Rust code. Prefer aliases or wrapper types over importing foreign-language naming directly into Rust APIs.

Generic type and lifetime parameters can be short, such as `T` and `'a`, when the meaning is obvious. Use descriptive names when several generic parameters are in scope. Associated types should use descriptive names like other types.

### Method Names

Use `new` for the primary constructor. Use `with_` prefixes for secondary constructors that customize additional state, such as `with_capacity`.

Use conversion names that communicate cost and ownership:

- `as_type` returns a cheap borrowed view, such as `as_str`.
- `into_type` consumes `self` and returns owned data without expensive cloning.
- `to_type` performs a more expensive owned conversion, such as cloning.

For wrapper types, use `into_inner` when consuming the wrapper cannot panic. Use `unwrap` when extracting the inner value may panic. If the wrapper is not consumed and returns a reference, use `get`.

Use `iter` for the default borrowed iteration method. Prefer implementing `IntoIterator` for consuming iteration instead of adding an inherent `into_iter` method.

Avoid getter and setter methods where direct field access or a clearer API shape works better. When getters and setters are used, prefer `foo` and `set_foo`; do not use `get_foo`. Boolean presence checks should use `is_` or `has_` prefixes.

Trait names should prefer verbs, then nouns, then adjectives. Avoid grammatical suffixes such as `-able` when a shorter established Rust-style trait name works.

Use ownership or mutability suffixes only when needed to distinguish method variants. Prefer a single suffix, such as `foo_ref` or `foo_mut`. For mutable views, use `mut` as a prefix inside the conversion name, such as `as_mut_slice`, rather than as a trailing suffix.
