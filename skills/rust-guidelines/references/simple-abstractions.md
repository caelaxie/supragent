# Simple Abstraction Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Libraries / UX Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html)

This reference includes only:

- [Abstractions Don't Visibly Nest (`M-SIMPLE-ABSTRACTIONS`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-SIMPLE-ABSTRACTIONS)

## Abstractions Don't Visibly Nest (M-SIMPLE-ABSTRACTIONS)

Public service-like API types should keep visible type signatures shallow. Avoid requiring callers to name or store nested crate-owned generic types such as `Service<Backend<Store>>`.

Prefer concrete, crate-owned facade types when the public type is a primary dependency, app handle, service handle, or other type callers are expected to pass around. One visible generic level can be acceptable when it carries clear user value; nested crate-owned parameters usually mean implementation composition is leaking into the public API.

Generics remain appropriate for containers, smart pointers, iterators, and "bring your own type" APIs where `T` is supplied by the caller. Even then, keep the parameter count, nesting, and bounds modest.

Review questions:

- Will downstream users need to name this type in fields, variables, trait impls, or function signatures?
- Are the generic parameters crate-owned implementation details instead of user-provided data types?
- Do the bounds or associated traits introduce complex errors or spread through caller code?
- Does the parameterization affect inference in other types or functions?

Default to public service API types with no self-chosen generic nesting. If nesting is unavoidable, keep it to one visible level and hide deeper composition behind a named type, builder, enum, or trait wrapper.
