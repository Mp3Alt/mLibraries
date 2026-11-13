# Changelog

## 0.12.2-dev

Added 15 libraries alongside mSignal, mCleanup and mAsync:

- mCommand for command parsing, typed arguments, aliases and permissions.
- mPacket for schema-based encoding and validation using flat native arrays.
- mNet for client/server events, requests, replies and server pushes.
- mState for values, computations, observers and batched updates.
- mPlayer for player and character lifetimes.
- mData for profiles, leases, migrations and autosaving.
- mStore for atomic shared records and explicit fresh reads.
- mBan for validated ban records, expiry and protected removal.
- mMessaging for polled message topics with retained history.
- mSpring for number, Vector2 and Vector3 springs.
- mTopbar for buttons, docks, menus, badges, keybinds and overflow.
- mBind, mReactive, mControls and mWidgets for native UI.

Fixes and changes:

- Fixed mAsync cancellation reporting and stable outcome/execution reads.
- Fixed stale character setup after overlapping player lifecycle changes.
- Fixed shared-store success after a validator closes its handle.
- Fixed reactive springs retaining an old target near their resting point.
- Preserved small control values and guarded slider quantization overflow.
- Added deferred graph cleanup for owned state closed during computation.
- Reworked topbar hover, press, dock geometry and shared-highlight motion.
- Preserved menu rows during label, badge and image-size updates.
- Fixed popup replacement and concurrent icon, dock and bar cleanup.
- Simplified command lowercase handling while retaining input checks.

Added API references, installation guides, usage examples and a native UI gallery.
Expanded contract, concurrency, lifecycle, storage and remote-load tests. Native
styling and runtime observations remain specific to the tested Creator version;
see [testing](docs/testing.md) for the method and limits.

## 0.1.0-dev

First development release, November 11, 2026.

- mSignal: synchronous events, one-shot listeners and explicit disconnection.
- mCleanup: callback, connection and instance cleanup in reverse registration order.
- mAsync: background jobs, delays, outcomes and cooperative cancellation.
- API references, installation guide, usage comments and test suites.

Validated with Creator 2026.43.7. See the [original verification record](docs/verification/2026-11-11.md)
for that release's tested workloads and limits.
