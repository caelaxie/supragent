# Naming Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Universal Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html)

This reference includes only:

- [Names are Free of Weasel Words (`M-CONCISE-NAMES`)](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html#M-CONCISE-NAMES)

## Names are Free of Weasel Words (M-CONCISE-NAMES)

Symbol names, especially type and trait names, should avoid generic words that do not add meaningful information.

Common weak suffixes include:

- `Service`
- `Manager`
- `Factory`

Prefer names that describe the concrete domain object or behavior. For example, use `Bookings` for an item that handles bookings, and choose a more specific name such as `BookingDispatcher` when the type's role is to submit bookings elsewhere.

Avoid `Manager` unless the type manages a genuinely distinctive lifecycle or coordination responsibility that cannot be named more precisely. Most Rust resource lifecycle behavior should be expressed through ownership, constructors, and `Drop`.

Avoid `Factory` terminology. In Rust, a type that configures construction is usually a `Builder`. If repeatable instantiation is needed as an input, prefer accepting an `impl Fn() -> Foo` over a factory object.
