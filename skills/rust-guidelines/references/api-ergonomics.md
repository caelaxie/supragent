# API Ergonomics Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Libraries / UX Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html)

This reference includes only:

- [Accept `impl AsRef<>` Where Feasible (`M-IMPL-ASREF`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-IMPL-ASREF)
- [Accept `impl RangeBounds<>` Where Feasible (`M-IMPL-RANGEBOUNDS`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-IMPL-RANGEBOUNDS)
- [Accept `impl 'IO'` Where Feasible (`M-IMPL-IO`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-IMPL-IO)
- [Essential Functionality Should be Inherent (`M-ESSENTIAL-FN-INHERENT`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/ux/index.html#M-ESSENTIAL-FN-INHERENT)

## Accept `impl AsRef<>` Where Feasible (M-IMPL-ASREF)

Use `impl AsRef<T>` in function parameters when callers have several natural input shapes and the function only needs a borrowed view.

Common examples:

- Accept `impl AsRef<str>` instead of forcing `&str` or `String`.
- Accept `impl AsRef<Path>` instead of forcing `&Path` or `PathBuf`.
- Accept `impl AsRef<[u8]>` instead of forcing `&[u8]` or `Vec<u8>`.

Use this mainly on function and method parameters. Do not infect stored public types with generic `T: AsRef<_>` fields unless there is a measured reason and the generic is not user-visible API clutter. Prefer owned storage such as `String`, `PathBuf`, or `Vec<u8>` inside structs when the value must be retained.

If the function must take ownership and the call is high-frequency or high-volume, evaluate whether accepting an owned type is more honest about allocation and performance than accepting `AsRef` and cloning internally.

## Accept `impl RangeBounds<>` Where Feasible (M-IMPL-RANGEBOUNDS)

Use standard range types and traits for numeric ranges. Avoid hand-rolled parameter pairs such as `(low, high)` or `low, high`, which are easy to mix up and make inclusivity unclear.

When a function can work with any range shape, accept `impl RangeBounds<T>` rather than a single concrete `Range<T>`. This lets callers use natural Rust syntax such as:

- `start..end`
- `start..`
- `..end`
- `..`

Accept a concrete range type only when the API truly requires that specific bound form.

## Accept `impl 'IO'` Where Feasible (M-IMPL-IO)

Keep one-shot parsing and initialization logic independent from concrete I/O sources. Accept the standard I/O trait the operation actually needs rather than forcing a concrete type such as `File`.

Use synchronous traits such as `std::io::Read`, `std::io::BufRead`, and `std::io::Write` for synchronous APIs. This keeps functions usable with files, streams, stdin, in-memory byte slices, and test buffers.

For async APIs that should work across runtimes, prefer runtime-neutral traits such as `futures::io::AsyncRead` or `futures::io::AsyncWrite`. If a type performs runtime-specific continuous I/O, make the runtime dependency explicit elsewhere instead of hiding it behind a misleading generic I/O parameter.

Default to sans-I/O business logic when the I/O is only needed to supply or receive bytes. This avoids multiplying parsers by transport type and makes tests simpler.

## Essential Functionality Should be Inherent (M-ESSENTIAL-FN-INHERENT)

Expose a type's core functionality as inherent methods. Trait implementations can provide interoperability, extension points, or shared abstractions, but they should forward to inherent methods rather than hiding essential operations behind a trait import.

This keeps the API discoverable from the type itself:

- Users can find core methods through ordinary completion on `Type`.
- Documentation for the type shows the essential operations directly.
- Trait imports remain optional for generic code instead of mandatory for basic use.

When both an inherent method and a trait method exist, make the trait implementation call the inherent method. Avoid duplicating behavior or making the trait path the only implementation.
