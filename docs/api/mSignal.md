# mSignal

`mSignal` creates synchronous events with one payload per fire. Use a table or array when the event carries several values. Each signal owns its listeners; each connection can stop listening independently.

```truscript
local mSignal = import("/mLibraries/mSignal")
local discovered = mSignal.New()

local connection = discovered.Connect(func(payload):
    print(payload.Name)
)

local errors = discovered.Fire({ Name = "Observatory" })
connection.Disconnect()
discovered.Destroy()
```

## API

| Call | Result |
| --- | --- |
| `mSignal.New()` | A fresh signal. |
| `signal.Connect(handler)` | A connection for a callable receiving one payload. |
| `signal.Once(handler)` | A connection removed before its first callback begins. |
| `signal.Fire(payload)` | An array of caught callback failures, in dispatch order. |
| `signal.DisconnectAll()` | Disconnects every current listener. The signal remains reusable. |
| `signal.Destroy()` | Permanently closes the signal and disconnects all listeners. |
| `signal.GetListenerCount()` | The number of connected listeners. |
| `signal.IsDestroyed()` | Whether the signal has been destroyed. |
| `connection.Disconnect()` | Stops future calls; safe to repeat. |
| `connection.IsConnected()` | Whether this connection can still receive a callback. |

Use dot calls. The returned functions already capture their owner. A handler must be callable; `nil` is rejected at registration, and other non-callable values fail when dispatched.

## Dispatch contract

- Callbacks begin in connection order and run in the calling task. A yielding callback delays the remaining callbacks and the return from `Fire`. Prefer callbacks that do not yield.
- Membership is captured when a fire begins. Listeners connected during a callback do not join that fire. A nested fire is a new fire and sees the connections present when it begins.
- A listener disconnected before its dispatch is claimed is skipped, including after `DisconnectAll` or `Destroy` inside another callback. A callback already claimed by another task may still run after disconnection; disconnection cannot retract work already claimed.
- `Once` disconnects before invoking the callback. Nested fires and callback failures cannot make that connection run twice.
- Nested fires execute depth first. A nested fire returns its own error array; its caller is responsible for inspecting that result.
- `nil`, `false` and `0` are valid payloads. Arrays, tables and objects pass by reference; the library does not clone or freeze them.
- A catchable callback failure is appended to the returned error array and the next eligible listener still runs. The original thrown value is preserved. Inspect the array; failures are not logged or rethrown automatically.

Destroy and disconnect are idempotent. Firing after destruction returns an empty array. Connecting or registering a one-shot listener after destruction throws. A callback already running is allowed to finish.

One-shot calls and disconnection share a local claim ticket. Dispatch captures the immutable owner/handler entry once, so a concurrent disconnect cannot turn a later read of that entry into `nil`. An overlapping `DisconnectAll` may return while the first bulk drain is still running; it does not start another drain of the same batch. Connections created during that operation fall before or after its list detachment. `Destroy` also drains a newer list if it overlaps a bulk operation.

Disconnect removes the record from the signal and clears its callback and owner references. A fire already in progress retains its snapshot until it returns. The module does not schedule background tasks or create engine instances. `Wait`, async dispatch and thread cancellation are outside this API.

## Verification scope

The accompanying `Run()` tests exercise ordering, listener mutation, nested fires, error isolation, payload identity and lifecycle behavior. A separate `RunConcurrent()` entry point starts native-script stress tasks; it yields and cannot run in `run_truscript`. Stress testing samples scheduler interleavings rather than proving every possible schedule. Runtime results and the installed engine version belong in the project's test evidence. No performance or memory benchmark is claimed by this API.

Creator 2026.43.7 concurrent-disconnect testing exposed a `nil` owner read when an earlier implementation checked and reread the mutable entry in one expression. This implementation uses a stable local entry instead. The language guide's statement-completion wording must not be treated as proof that repeated mutable reads are safe under concurrency; that observation is limited to the tested engine and failure.
