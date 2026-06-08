# Unsafe Code Guidelines

Sources:

- [Microsoft Pragmatic Rust Guidelines - Safety Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/safety/index.html)
- [Rust API Guidelines - Documentation](https://rust-lang.github.io/api-guidelines/documentation.html)

This reference includes only:

- [Unsafe Needs Reason, Should be Avoided (`M-UNSAFE`)](https://microsoft.github.io/rust-guidelines/guidelines/safety/index.html#M-UNSAFE)
- [All Code Must be Sound (`M-UNSOUND`)](https://microsoft.github.io/rust-guidelines/guidelines/safety/index.html#M-UNSOUND)
- [Unsafe Implies Undefined Behavior (`M-UNSAFE-IMPLIES-UB`)](https://microsoft.github.io/rust-guidelines/guidelines/safety/index.html#M-UNSAFE-IMPLIES-UB)
- [Unsafe functions document safety invariants (`C-SAFETY`)](https://rust-lang.github.io/api-guidelines/documentation.html#c-safety)

## Unsafe Needs Reason, Should be Avoided (M-UNSAFE)

Use `unsafe` only when there is a concrete reason that safe Rust cannot satisfy:

- A novel sound abstraction, such as a smart pointer, allocator, or other low-level wrapper.
- A measured performance need after benchmarking.
- FFI, platform, or kernel calls.

Do not use ad-hoc `unsafe` as a shortcut inside otherwise unrelated code. In particular, do not use `unsafe` to make enum casts shorter with `transmute`, bypass `Send` or `Sync` requirements, or evade lifetime rules.

Every unsafe block, unsafe function, unsafe trait, and unsafe impl must have plain-text safety reasoning close to the code. The reasoning should explain:

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

## All Code Must be Sound (M-UNSOUND)

Unsound code is never acceptable. A safe-looking API is unsound if any call pattern available to safe Rust can cause undefined behavior, even if the problematic call looks unusual or unlikely.

Keep the terms distinct:

- `unsafe` code can be sound when its invariants are correct and enforced.
- Safe code can be dangerous in ordinary product terms, such as deleting data, without being `unsafe` in Rust's technical sense.
- Safe code is unsound when it can trigger undefined behavior without requiring the caller to enter an `unsafe` boundary.

If a safe abstraction cannot enforce the invariants needed to avoid undefined behavior, do not expose that operation as safe. Use an `unsafe fn`, unsafe trait, or other explicit unsafe boundary and document the caller obligations in a `# Safety` section.

Soundness boundaries are module boundaries. Safe functions inside a module may rely on invariants established by other code in the same module, but the module's public safe surface must preserve those invariants for all safe callers.

Tests, fuzzing, Miri, and code review are supporting evidence, not replacements for a soundness argument. Review unsafe abstractions by identifying the exact invariants, who can violate them, and how the module prevents safe callers from causing undefined behavior.

## Unsafe Implies Undefined Behavior (M-UNSAFE-IMPLIES-UB)

Use the `unsafe` marker only when misuse can cause undefined behavior. It is for UB-relevant caller or implementor obligations, not for APIs that are dangerous only in product, business, security-policy, or operational terms.

Mark a function `unsafe fn` only when the caller must uphold memory, lifetime, aliasing, threading, initialization, FFI, or other soundness invariants to avoid undefined behavior. Mark a trait `unsafe trait` only when implementors must uphold invariants that unsafe code may rely on.

Do not mark an API `unsafe` merely to warn that it can delete data, consume money, bypass authorization, leak secrets, block forever, corrupt business state, or perform another dangerous non-UB action. Keep those APIs safe in Rust's technical sense and express the risk with ordinary API design tools:

- Precise names that make the operation explicit.
- Strong input types, capability tokens, permission checks, or confirmation gates.
- `Result`-based error handling for expected failure modes.
- Documentation of domain risks and required authorization.
- Runtime validation, audit logging, or feature gating when appropriate.

This rule complements soundness guidance: if a safe API cannot enforce a UB-relevant invariant, move that obligation to an explicit unsafe boundary and document it in a `# Safety` section. If misuse cannot cause undefined behavior, do not use `unsafe` as a warning label; doing so dilutes the meaning of `unsafe` and creates warning fatigue.
