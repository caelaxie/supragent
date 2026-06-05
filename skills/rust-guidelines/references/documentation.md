# Documentation Guidelines

Sources:

- [Microsoft Pragmatic Rust Guidelines - Documentation](https://microsoft.github.io/rust-guidelines/guidelines/docs/index.html)
- [Rust API Guidelines - Documentation](https://rust-lang.github.io/api-guidelines/documentation.html)

This reference includes only:

- [First Sentence is One Line; Approx. 15 Words (`M-FIRST-DOC-SENTENCE`)](https://microsoft.github.io/rust-guidelines/guidelines/docs/index.html#M-FIRST-DOC-SENTENCE)
- [Has Comprehensive Module Documentation (`M-MODULE-DOCS`)](https://microsoft.github.io/rust-guidelines/guidelines/docs/index.html#M-MODULE-DOCS)
- [Documentation Has Canonical Sections (`M-CANONICAL-DOCS`)](https://microsoft.github.io/rust-guidelines/guidelines/docs/index.html#M-CANONICAL-DOCS)
- [Mark `pub use` Items with `#[doc(inline)]` (`M-DOC-INLINE`)](https://microsoft.github.io/rust-guidelines/guidelines/docs/index.html#M-DOC-INLINE)
- [All items have a rustdoc example (`C-EXAMPLE`)](https://rust-lang.github.io/api-guidelines/documentation.html#c-example)
- [Function docs include error, panic, and safety considerations (`C-FAILURE`)](https://rust-lang.github.io/api-guidelines/documentation.html#c-failure)

## First Sentence is One Line; Approx. 15 Words (M-FIRST-DOC-SENTENCE)

Public API documentation should start with a short summary sentence. Rustdoc extracts the first sentence into module and item summaries, so that sentence should be useful when read without the rest of the documentation.

Treat the Microsoft 15-word target as a skimmability guideline, not a hard lint. The summary should usually fit on one line in rustdoc, but clarity wins over mechanical word counting.

Good first sentences:

- State what the item is or does.
- Avoid setup, caveats, implementation detail, and examples.
- Use the item name only when it helps the sentence read naturally.
- Leave longer technical explanation for later paragraphs.

For public modules, combine this with module-level `//!` documentation. The first module sentence should summarize what the module contains; later text can explain when to use it, important interactions between items, examples, observable side effects, and relevant implementation details.

## Has Comprehensive Module Documentation (M-MODULE-DOCS)

Public library modules should have `//!` module documentation. The first sentence should follow the summary-sentence guidance above and describe what the module contains.

Use module documentation for navigation and context that individual item docs cannot express well:

- What the module contains.
- When to use the module and, when useful, when not to use it.
- How the main items interact.
- Examples that show the module-level workflow.
- Subsystem specifications, protocols, formats, or invariants owned by the module.
- Observable side effects and the guarantees made about them.
- Relevant implementation details, such as underlying system APIs.

Keep the level of detail proportional to the public surface. A small module may need only a short summary and a few pointers, while a module that defines a subsystem should explain the model readers need before browsing individual items.

Do not duplicate every item-level doc in the module docs. Put cross-item relationships, high-level behavior, examples, side effects, and invariants at the module level; keep per-item arguments, return values, panics, errors, and safety obligations with the item that owns them.

## Documentation Has Canonical Sections (M-CANONICAL-DOCS)

Public library item documentation should start with a summary sentence. Extended documentation and examples are strongly encouraged, especially for APIs whose behavior, failure modes, or usage patterns are not obvious from the signature alone.

Use the standard rustdoc sections that apply to the API:

- `# Examples` for representative usage.
- `# Errors` when a function returns `Result` or a trait method may return an error.
- `# Panics` when a function can panic for reasons callers need to understand.
- `# Safety` for unsafe functions, unsafe traits, or other APIs with caller obligations needed to avoid undefined behavior.
- `# Abort` when a function can abort or otherwise terminate the process.

Do not add every section mechanically. `# Errors`, `# Panics`, `# Safety`, and `# Abort` are required only when the behavior exists. Avoid padding tiny obvious items with boilerplate, but keep public library APIs useful when read in rustdoc without surrounding source context.

Keep `# Safety` narrow. It is for undefined-behavior-relevant obligations, not a generic warning section for risky product or business behavior.

Do not create parameter tables for ordinary Rust functions. Prefer prose that explains how parameters are used in the operation, especially when the relationship between parameters matters.

## Mark `pub use` Items with `#[doc(inline)]` (M-DOC-INLINE)

Use `#[doc(inline)]` on explicit `pub use` re-exports of crate-local items when the re-export is intended to feel like part of the current public module. This helps rustdoc present the re-exported item alongside its public siblings instead of hiding it in an opaque re-export block.

Prefer explicit re-exports first:

```rust
#[doc(inline)]
pub use inner::{Client, Config};
```

Do not use `#[doc(inline)]` to justify public glob re-exports. The attribute changes documentation presentation only; it does not make `pub use inner::*` reviewable or stable. Follow the public re-export guidance before deciding how to present the item in rustdoc.

Do not inline `std` or third-party re-exports by default. Leaving external items as visible re-exports helps readers understand provenance and dependency boundaries.

Use this attribute when the re-exported path is the public home readers should browse. Avoid it for compatibility aliases, transitional exports, or surfaces where the original module path is the clearer documentation location.
