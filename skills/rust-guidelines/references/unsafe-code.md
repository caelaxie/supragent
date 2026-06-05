# Unsafe Code Guidelines

Sources:

- [Microsoft Pragmatic Rust Guidelines - Safety Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/safety/index.html)
- [Rust API Guidelines - Documentation](https://rust-lang.github.io/api-guidelines/documentation.html)

This reference includes only:

- [Unsafe Needs Reason, Should be Avoided (`M-UNSAFE`)](https://microsoft.github.io/rust-guidelines/guidelines/safety/index.html#M-UNSAFE)
- [Unsafe functions document safety invariants (`C-SAFETY`)](https://rust-lang.github.io/api-guidelines/documentation.html#c-safety)

## Unsafe Needs Reason, Should be Avoided (M-UNSAFE)

Use `unsafe` only when there is a concrete reason that safe Rust cannot satisfy:

- A novel sound abstraction, such as a smart pointer, allocator, or other low-level wrapper.
- A measured performance need after benchmarking.
- FFI, platform, or kernel calls.

Do not use ad-hoc `unsafe` as a shortcut inside otherwise unrelated code. In particular, do not use `unsafe` to make enum casts shorter with `transmute`, bypass `Send` or `Sync` requirements, or evade lifetime rules.

Every unsafe block, unsafe function, and unsafe impl must have plain-text safety reasoning close to the code. The reasoning should explain:

- Which invariants must hold.
- Who is responsible for upholding them.
- Why the unsafe operation is sound under those invariants.
- What tests, assertions, or construction boundaries keep the invariant true.

Public `unsafe fn` APIs must document caller obligations in a `# Safety` section. If the function can be safe for callers only under specific preconditions, those preconditions belong in that section, not only in code review notes.

For novel abstractions:

- Verify there is no established safe or better-tested alternative.
- Keep the abstraction minimal and testable.
- Design for adversarial safe code, including panicking closures and surprising `Deref`, `Clone`, or `Drop` implementations.
- Run Miri where practical, especially for pointer, aliasing, initialization, or drop-order invariants.

For performance-driven unsafe:

- Benchmark first and keep the benchmark result or rationale near the change.
- Prefer safe code unless the unsafe version gives a meaningful measured benefit.
- Apply the same safety reasoning to `_unchecked` helpers and calls to existing unsafe APIs.
- Run Miri where practical.

For FFI and platform calls:

- Prefer established interop libraries or generated bindings when they can avoid hand-written unsafe code.
- Document which call patterns are valid and which ownership, lifetime, threading, and nullability assumptions the foreign API requires.
- Keep unsafe boundaries small and wrap them in safe Rust only when the wrapper can enforce the required invariants.
