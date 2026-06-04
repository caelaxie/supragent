# API UX Abstraction Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Libraries / UX Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html)

This reference includes only these Libraries / UX guidelines:

- [Abstractions Don't Visibly Nest (`M-SIMPLE-ABSTRACTIONS`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-SIMPLE-ABSTRACTIONS)
- [Avoid Smart Pointers and Wrappers in APIs (`M-AVOID-WRAPPERS`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-AVOID-WRAPPERS)
- [Prefer Types over Generics, Generics over Dyn Traits (`M-DI-HIERARCHY`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-DI-HIERARCHY)

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

## Avoid Smart Pointers and Wrappers in APIs (M-AVOID-WRAPPERS)

Do not expose wrapper or smart-pointer choices in public APIs unless the wrapper is fundamental to the API's purpose or a measured performance reason justifies the extra complexity.

Prefer simple public signatures using `&T`, `&mut T`, or `T`. Keep internal ownership, sharing, and mutability mechanics such as `Arc`, `Rc`, `Box`, `Mutex`, or `RefCell` behind crate-owned types and methods.

Review questions:

- Is this wrapper an implementation detail the caller should not need to know?
- Would exposing the wrapper force downstream code to choose the same ownership or synchronization model?
- Could a crate-owned handle, borrowed parameter, builder, or inherent method hide the wrapper while preserving the behavior?
- Is the wrapper central to the library itself, such as a container or smart-pointer crate?

When a trait object or shared dependency is needed, prefer a named wrapper type over exposing `Arc<dyn Trait>` or similar nested wrapper shapes directly.

## Prefer Types over Generics, Generics over Dyn Traits (M-DI-HIERARCHY)

For async dependencies and service composition, prefer concrete types first. If users genuinely need to supply their own behavior, prefer narrow generic traits. Use `dyn Trait` only after concrete types or generics would create worse API nesting or lock in the wrong model.

Escalation order:

1. Use a concrete type when the crate owns the dependency and there is one normal implementation.
2. Use an enum when alternate implementations are mainly for sans-I/O testing or controlled built-in variants.
3. Use one or more narrow traits when users need to provide custom implementations.
4. Use generics over those narrow traits while the generic surface stays simple.
5. Use a named dynamic wrapper when generics become infectious or visibly nested.

Avoid porting interface-heavy designs directly into Rust. A broad async trait plus `Rc<dyn Trait>`, `Arc<dyn Trait>`, or similar public wrapper often creates object-safety, async, composition, and API ergonomics problems.

Keep traits focused on the operation being consumed. If a larger abstraction is needed, compose it from narrower subtraits rather than starting with one broad dependency trait.
