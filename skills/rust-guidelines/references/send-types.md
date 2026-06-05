# Send Type Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Libraries / Interoperability Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/libs/interop/index.html)

This reference includes only:

- [Types are `Send` (`M-TYPES-SEND`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/interop/index.html#M-TYPES-SEND)

## Types are `Send` (M-TYPES-SEND)

Public types should generally be `Send` so they work with Tokio and runtime abstractions.

The official Rust API Guidelines discuss `Send` and `Sync` together. This reference focuses on `Send` because async runtimes commonly require sendable futures, but shared public handles and references should also be checked for `Sync` where callers may use them across threads.

Apply this especially to futures:

- Explicit `Future` types should be asserted as `Send`.
- Futures returned implicitly from `async fn` and async methods should be `Send`.
- Validate the main async entry points even when testing every method would be noisy.

Example assertion for an explicit future:

```rust
const fn assert_send<T: Send>() {}
const _: () = assert_send::<MyFuture>();
```

Example assertion for an async entry point:

```rust
fn assert_send<T: Send>(_: T) {}

_ = assert_send(run_job());
```

Most regular public types should also be `Send`, because holding a non-`Send` value such as `Rc` across an `.await` can make the entire future `!Send`. Interior-mutability types also need care: for example, `RefCell<T>` can be `Send` when `T: Send`, but it is not `Sync`.

Treat `!Send` as a deliberate compatibility exception. It can be acceptable for values that are only used instantaneously and have no reason to be held across `.await` boundaries, but document the intent and keep the API surface clear.
