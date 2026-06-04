# Structured Logging Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Universal Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html)

This reference includes only:

- [Use Structured Logging with Message Templates (`M-LOG-STRUCTURED`)](https://microsoft.github.io/rust-guidelines/guidelines/universal/index.html#M-LOG-STRUCTURED)

## Use Structured Logging with Message Templates (M-LOG-STRUCTURED)

Prefer structured logging events with named fields over preformatted strings. Keep values as fields so subscribers and log backends can filter, group, and render them without losing structure.

Guidelines:

- Emit events with stable names, preferably hierarchical dot notation such as `file.open.success`.
- Include named properties for values operators will search or filter on.
- Avoid eager string formatting before logging; pass values as fields and let the logging backend render them.
- Follow OpenTelemetry semantic conventions for common fields when they fit.
- Redact sensitive data before it enters an event field or message.

Example with `tracing`:

```rust
tracing::event!(
    name: "file.write.success",
    tracing::Level::INFO,
    file.path = %path.display(),
    file.size = bytes_written,
    "wrote {{file.size}} bytes to {{file.path}}",
);
```

Use message-template placeholders such as `{{file.path}}` in the message text when the backend supports delayed rendering. Keep the structured fields authoritative; the message should make the event readable, not be the only place important data exists.
