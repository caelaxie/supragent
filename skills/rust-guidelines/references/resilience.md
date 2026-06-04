# Resilience Guidelines

Source: [Microsoft Pragmatic Rust Guidelines - Libraries / Resilience Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/libs/resilience/index.html)

This reference includes only:

- [I/O and System Calls Are Mockable (`M-MOCKABLE-SYSCALLS`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/resilience/index.html#M-MOCKABLE-SYSCALLS)
- [Test Utilities are Feature Gated (`M-TEST-UTIL`)](https://microsoft.github.io/rust-guidelines/guidelines/libs/resilience/index.html#M-TEST-UTIL)

## I/O and System Calls Are Mockable (M-MOCKABLE-SYSCALLS)

Make user-facing types that perform I/O, system calls, or other environment-dependent effects testable by routing those effects through a mockable core.

This applies to file and network access, clocks, entropy, hardware-dependent behavior, environment-dependent state, and other fragile or non-deterministic operations.

Avoid:

- Ad-hoc I/O inside business logic, such as directly reading a hard-coded file path.
- Public constructors that hide non-mockable I/O or system-call dependencies.
- Creating a private runtime or I/O core that callers cannot replace or control in tests.

Prefer one of these shapes:

- Accept an injected runtime, I/O handle, clock, random source, or service handle that is already mockable.
- Provide inherent mocking support, usually as `new_mocked() -> (Self, MockCtrl)`, with the library instance first and the mock controller second.
- For runtime-aware libraries, extend the runtime abstraction with a mock variant instead of inventing a second dispatch path.

Keep mocking support behind the same test-only feature gate used for other test utilities.

## Test Utilities are Feature Gated (M-TEST-UTIL)

Guard test-only behavior behind an explicit feature flag so production builds cannot accidentally bypass safety checks.

Use one clearly named feature when practical, preferably `test-util`. Gate functionality such as:

- Mocking hooks and controllers.
- Sensitive data inspection helpers.
- Safety-check overrides.
- Fake data generators.

Example:

```rust
impl HttpClient {
    pub fn get() {
        // Production behavior.
    }

    #[cfg(feature = "test-util")]
    pub fn bypass_certificate_checks() {
        // Test-only behavior.
    }
}
```
