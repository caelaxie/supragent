# Type Construction Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Libraries / UX Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html)

This reference includes only:

- [Complex Type Construction has Builders (`M-INIT-BUILDER`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-INIT-BUILDER)
- [Complex Type Initialization Hierarchies are Cascaded (`M-INIT-CASCADED`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-INIT-CASCADED)

## Complex Type Construction has Builders (M-INIT-BUILDER)

Use inherent constructors for simple construction cases. When a type could support four or more arbitrary initialization permutations, provide a builder instead of adding many `new_*`, `with_*`, or long optional-parameter variants.

Builder conventions:

- Name the builder after the target type, such as `FooBuilder`.
- Expose the builder from the target type with `Foo::builder(...)`.
- Do not expose a competing public `FooBuilder::new()` when `Foo::builder(...)` is the intended entry point. If compatibility or established crate style requires one, document it as a local exception.
- Make setter methods chainable.
- Name setter methods after the value they set, such as `timeout(...)`, not `set_timeout(...)`.
- End construction with `.build()`.

Pass required parameters when creating the builder, not through optional setter methods. For multiple required parameters, prefer a dedicated dependencies struct and accept it with `deps: impl Into<Deps>` so callers can use a tuple, a single dependency, or an explicit struct while the API stays evolvable.

For runtime-specific construction, provide explicit builder entry points such as `builder_tokio(deps)` or `builder_smol(deps)`. The runtime choice should be visible in the API surface and type checked at compile time.

## Complex Type Initialization Hierarchies are Cascaded (M-INIT-CASCADED)

Avoid constructors with four or more loosely related parameters. Long positional lists are easy to mix up and hard to scan, especially when several parameters share primitive types.

Group parameters into semantic helper types instead:

- Replace `new(bank_name, customer_name, currency_name, currency_amount)` with `new(account, amount)`.
- Move validation and construction for grouped values onto the helper type.
- Prefer domain-specific newtypes when primitive values can be confused.

Cascading initialization should make invalid or ambiguous calls harder to write. The top-level constructor should read in domain terms, while lower-level helper constructors own the details of building each grouped value.
