# Data Type Guidelines

Sources:

- [Rust API Guidelines - Future Proofing](https://rust-lang.github.io/api-guidelines/future-proofing.html)
- [PingCAP Rust Style Guide - Data](https://pingcap.github.io/style-guide/rust/data.html)

This reference includes only:

- [Rust API Guidelines - Future Proofing](https://rust-lang.github.io/api-guidelines/future-proofing.html)
- [PingCAP Rust Data Guide](https://pingcap.github.io/style-guide/rust/data.html)

## Generic Data Types

Keep generic data type definitions as flexible as possible. Put strict bounds on `impl` blocks, methods, and functions rather than on the concrete type unless the bound is intrinsic to the type definition.

Avoid duplicating derivable bounds on data structures. Do not write bounds such as `T: Clone + Debug + PartialEq` on a struct just because the struct derives those traits; derive expansion already creates the right conditional impls.

Acceptable type-level bounds include:

- Lifetime bounds required by the data representation.
- `?Sized`.
- Bounds needed to name an associated type used by a field.
- Bounds required by a `Drop` implementation.

Avoid default generic parameters unless the default is used in the vast majority of real call sites, such as a hasher parameter for a hash table or a test-only override point.

Use type aliases for common generic shapes when they improve readability, such as a crate-local `Result<T>` alias. Do not use aliases to hide important ownership, error, or performance semantics.

## Invariants and Representation

Use Rust types to make invalid states hard or impossible to represent. Prefer structs, enums, tuples, associated types, and newtypes that encode the valid state space directly instead of relying on comments or runtime checks spread through callers.

Use the newtype pattern when two values share the same representation but carry different meaning or behavior. This is especially useful for IDs, units, domain values, and wrapper types that need controlled construction or trait implementations.

## Structs

Prefer small structs composed into larger structs over large flat structs. Smaller structures are often easier to borrow independently, test, validate, and evolve.

Choose public fields deliberately. Public fields are appropriate for transparent, passive data carriers with no cross-field invariants and little need to hide representation. Prefer private fields when:

- Multiple fields participate in an invariant.
- Construction or mutation must validate values.
- The type may need representation changes without breaking callers.
- Adding, removing, or changing fields should remain possible.

If all fields on a public struct are public, adding a new field is a breaking change for struct literal callers. Prefer private fields and constructor methods for public API types that need future evolution.

Use `struct Foo;` for empty structs. Avoid `struct Foo {}` and `struct Foo();` unless a macro or compatibility constraint requires that shape.

For `repr(C)` structs, field order is part of the external contract. For ordinary Rust structs where order is unconstrained, group fields for readability first and consider layout only when profiling or FFI requirements justify it.

Restrict tuple structs to one-field wrappers or cases where the field meaning is obvious. Use named fields when several values share a type or the values form a logical unit.

## Enums

Enums can have many variants when that matches the domain. Watch the size of variants: an enum is at least large enough to hold its largest variant, so variants with very different payload sizes can be inefficient.

Keep variant payloads small. If a variant needs several fields or a complex nested payload, move those fields into a named struct and use that struct as the variant payload. Naming the struct after the variant usually keeps the API easy to scan.

Prefer plain empty variants such as `Foo` over `Foo()` or `Foo {}`.

Use an intrinsic `None` or `Err` variant only when absence or failure is a stable state of the enum's own domain model. Use `Option<T>` or `Result<T, E>` when absence or failure is contextual to a particular operation.

## Tuples and Unions

Use tuples for temporary groupings of logically separate values, especially when the tuple is immediately destructured. Prefer named structs for logical units of data, and avoid multi-element tuples where several elements have the same type.

Use `union` only for FFI or low-level representation work that genuinely requires C-like union behavior. Prefer Rust enums for ordinary Rust code.

## Builders

Use simple constructors for simple data. Use a builder when concrete data has complex internals, many optional settings, or enough construction permutations that constructor names and positional parameters become hard to read.

Avoid introducing a builder for one or two simple constructors. Builders should reduce real construction complexity, not add ceremony.
