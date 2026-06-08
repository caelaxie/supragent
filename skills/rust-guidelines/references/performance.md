# Performance Guidelines

Sources:

- [PingCAP Rust Style Guide - Performance](https://pingcap.github.io/style-guide/rust/performance.html)
- [Rust Standard Library - `Vec`](https://doc.rust-lang.org/std/vec/struct.Vec.html)
- [Rust Standard Library - `String`](https://doc.rust-lang.org/std/string/struct.String.html)
- [Rust Standard Library - `Rc`](https://doc.rust-lang.org/std/rc/struct.Rc.html)
- [Rust Standard Library - `Arc`](https://doc.rust-lang.org/std/sync/struct.Arc.html)
- [Rust Standard Library - `RefCell`](https://doc.rust-lang.org/std/cell/struct.RefCell.html)
- [Rust Standard Library - `Mutex`](https://doc.rust-lang.org/std/sync/struct.Mutex.html)

This reference includes only:

- Benchmark-first optimization.
- Avoiding unnecessary allocation and copying.
- Visible expensive behavior.
- Wrapper and synchronization cost decisions.
- Concurrency design for performance-sensitive code.

## Source Precedence

Use standard library documentation as the higher-authority source for concrete type behavior. Treat the PingCAP guide as practical style guidance where it aligns with measured behavior and local API policy.

When this file overlaps with `unsafe-code.md`, `functions.md`, `expressions.md`, `simple-abstractions.md`, `send-types.md`, or `statics.md`, use those focused references for the detailed rule.

## Measure Before Optimizing

Prefer simple, clear code until there is a concrete performance reason to optimize. Use profiling, benchmarks, production telemetry, or a well-scoped performance requirement to justify non-obvious changes.

When optimizing:

- Identify the bottleneck before changing code.
- Keep the benchmark, profile, or rationale near the change when practical.
- Compare the optimized version against the simple version.
- Avoid changing public API shape for performance unless the cost is measurable and the new surface is easier to use correctly.

Performance-driven `unsafe` needs a measured benefit and a soundness argument. Follow `unsafe-code.md` before adding unsafe code or calling unchecked APIs.

## Allocation and Copying

Avoid unnecessary allocation, cloning, and intermediate collections in hot paths. Prefer borrowing, iterators, and direct transformation when they keep ownership and control flow clear.

Do not collect into `Vec`, allocate `String`, clone large values, or box values only to satisfy a local implementation shape. If the allocation is part of the operation's contract, make that cost visible through the function name, argument type, return type, or documentation.

Use capacity-aware construction when growth is predictable:

- Use `Vec::with_capacity` or `String::with_capacity` when the final size is known or cheaply estimated.
- Use `push` and `push_str` for repeated string assembly in hot paths.
- Keep `format!` for non-hot paths or when formatting clarity matters more than avoiding intermediate allocation.

Empty `Vec` and `String` values are cheap enough that avoiding them is usually not a useful optimization. Focus on repeated growth, large buffers, copies, and intermediate allocations instead.

## Iteration and Indexing

Use iterators, `enumerate`, windows, chunks, and direct element references for ordinary collection traversal. This usually makes traversal intent clearer and avoids manual indexing mistakes.

Do not claim iterator use is automatically faster. Index-based loops can be appropriate when the index itself is the algorithm, when multiple collections are traversed in lockstep, or when profiling shows a benefit.

Avoid forcing iteration with an unused `collect`. Use a `for` loop or `for_each` when the result is intentionally discarded. Follow `expressions.md` for the readability tradeoff between iterator adapters and loops.

## Visible Costs

Do not hide code that may allocate, block, sleep, perform I/O, lock, spawn work, or otherwise have surprising latency. The cost should be clear from the API surface or documentation.

Examples:

- A conversion named `as_*` should not allocate.
- A method that performs I/O should use a name such as `read`, `write`, `load`, `save`, `open`, or `connect`.
- A function that may block on a lock or external service should document that behavior when callers need to plan around latency.

For public APIs, follow `functions.md` and `documentation.md` so expensive behavior is visible in signatures and rustdoc.

## Ownership and Synchronization

Choose ownership and synchronization wrappers for the actual sharing model:

- Use `Rc` for single-threaded shared ownership.
- Use `Arc` when shared ownership must cross threads or async boundaries that require `Send` or `Sync`.
- Use `RefCell` for single-threaded interior mutability when runtime borrow checks are acceptable.
- Use `Mutex` or another synchronization primitive when mutation must be coordinated across threads or tasks.

Do not expose `Arc`, `Rc`, `Box`, `Mutex`, or `RefCell` in public APIs only because the implementation uses them. Hide implementation wrappers behind crate-owned types unless the wrapper is central to the API or a measured performance reason justifies exposing it.

`Arc` and `Mutex` are not automatically wrong in single-threaded-looking code: runtime requirements, public `Send` compatibility, shared service handles, or future cross-thread use can justify them. Treat `!Send` and single-thread-only APIs as deliberate compatibility choices; see `send-types.md`.

Avoid global mutable state for performance unless duplicate instances cannot affect correctness and the optimization is isolated. Follow `statics.md` for static and thread-local state.

## Concurrency and Blocking

Consider concurrency during design for performance-sensitive systems. Lock contention, blocking I/O, sleeping threads, and unnecessary synchronization can dominate runtime cost.

Prefer designs that:

- Keep locks out of hot loops where practical.
- Keep critical sections small.
- Avoid holding locks across `.await`, blocking I/O, callbacks, or user code.
- Separate pure computation from I/O so it can be tested, batched, parallelized, or scheduled independently.
- Use bounded queues, backpressure, or batching when throughput matters.

Do not add concurrency by default. Single-threaded code can be faster, simpler, and easier to reason about when the workload is small, latency-sensitive, or dominated by sequential dependencies.

## Complexity and Input Size

Consider algorithmic complexity, but weigh it against expected input size and real workload shape. A simple linear scan can beat a more complex data structure for small inputs; a better asymptotic algorithm matters when the input can grow.

Document assumptions when performance depends on them, such as small bounded input, rare slow paths, amortized allocation, or expected cache size.
