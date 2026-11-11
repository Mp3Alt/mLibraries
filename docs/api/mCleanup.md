# mCleanup

`mCleanup` owns synchronous teardown work. Register a callback, connection or instance when creating it, then call `Clean` when the owner resets or `Destroy` when the owner ends permanently.

```truscript
local mCleanup = import("/mLibraries/mCleanup")
local owner = mCleanup.New()

owner.Add(func():
    print("owner closed")
)

# owner.AddConnection(connection)
# owner.AddInstance(instance)

local errors = owner.Destroy()
```

## API

| Call | Result |
| --- | --- |
| `mCleanup.New()` | A fresh cleanup owner. |
| `owner.Add(callback)` | Registers a callable with no arguments; returns it. |
| `owner.AddConnection(connection)` | Registers `connection.Disconnect()`; returns the connection. |
| `owner.AddInstance(instance)` | Registers `instance.Destroy()`; returns the instance. |
| `owner.Clean()` | Drains current work in reverse registration order; returns caught failures. The owner remains reusable. |
| `owner.Destroy()` | Closes the owner before draining current work; returns caught failures. |
| `owner.GetCount()` | The number of queued registrations, excluding a batch already draining. |
| `owner.IsDestroyed()` | Whether registration is permanently closed. |

Use dot calls. Each returned function already captures its owner. The explicit adapters avoid guessing a resource's type or teardown method. A connection must provide a callable `Disconnect`; an instance must provide a callable `Destroy`. Adapter method failures are collected during cleanup. `nil` registration is rejected immediately.

## Ownership and error contract

- Each registration is invoked at most once by this owner. Register a resource once; the library does not deduplicate registrations.
- Teardown runs last in, first out. Register dependencies before the resources that depend on them.
- `Clean` detaches the batch before invoking its callbacks and removes each callback from the batch before calling it.
- Catchable failures are appended to the returned array in execution order. Remaining callbacks still run. The original thrown values are preserved; inspect the result because the library does not log or rethrow them automatically.
- Reentrant or overlapping `Clean` returns an empty array. A callback may call `Destroy`: this closes registration, leaves the active batch running and returns an empty array to that nested call. The outer call receives any failures from the active batch. An overlapping call does not wait for work claimed by the first caller.
- `Add`, `AddConnection` and `AddInstance` throw while cleanup is in progress or after destruction. Arrange resource creation outside teardown callbacks.
- `Clean` is reusable. Repeated `Destroy` calls return an empty array and cannot repeat work. `Clean` after destruction also returns an empty array once the active batch has finished.

The cleanup gate separates batch ownership from callback execution and is reset in `finally`. Its registration guards and native array operations are implementation details, not a general guarantee that a TruScript expression forms a critical section. Validate scheduling behavior using the separate native-script suite in the target engine version.

Callbacks must finish synchronously and should not yield. The library does not cancel threads, await async work or interrupt a callback already running. A host forcibly stopping a script is outside its cleanup guarantees. Ordinary callback errors release the cleaning guard through `finally`, allowing reuse after `Clean`.

## Verification scope

`Run()` tests cover reverse order, reuse, adapter calls, error isolation, reentrancy, rejected registrations and permanent destruction. A separate `RunConcurrent()` entry point uses native-script tasks to stress overlapping registration, cleaning and destruction; it yields and cannot run in `run_truscript`. Stress tests sample schedules rather than proving all interleavings. Live engine connection and instance adapters should also be exercised in the target Creator version. No performance benchmark is claimed.
