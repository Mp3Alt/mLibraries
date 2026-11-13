# Using mState

mState keeps local application values and their derived results together. Use it for a selected item, local settings or a calculated display value. Server/client replication and game authority remain the application's responsibility.

## Install

Create these **Module** scripts in Creator's Asset Browser. Copy in their source and leave them unattached. Asset paths omit `.trs` and are separate from the instance tree.

| Asset Browser path | Source |
| --- | --- |
| `mLibraries/mSignal` | [mSignal.trs](../packages/mSignal/src/mSignal.trs) |
| `mLibraries/mCleanup` | [mCleanup.trs](../packages/mCleanup/src/mCleanup.trs) |
| `mLibraries/mState` | [mState.trs](../packages/mState/src/mState.trs) |

The module has no native instances, timers or network calls. Use it from the script context that owns the state.

## Derive a value

```truscript
local mState = import("/mLibraries/mState")
local price = mState.New(10)
local quantity = mState.New(1)
local total = mState.Derived([price, quantity], expr(values): values[0] * values[1])

local connection = total.Observe(expr(value): print("total: " + value))
local failures = mState.Batch(func():
    price.Set(12)
    quantity.Set(3)
)
```

After Batch returns, total is 36 and its observer has received one change. Inspect `failures` for callback or computation failures. Derived dependencies are explicit and copied; the computation receives their values in the same order. Keep it pure and synchronous.

Set inside Batch or an observer queues its assignment. A Get in that scope reads the previous committed value. Outside those scopes, Set commits and settles dependent values before it returns. This deferred behavior is deliberate: it avoids recursively dispatching a second change inside a first observer.

## Own a binding

Observe subscribes to future changes. To initialize a view, subscribe first and then apply its current value:

```truscript
local mCleanup = import("/mLibraries/mCleanup")
local owner = mCleanup.New()
local update = func(value):
    print("display: " + value)

total.Observe(update, owner)
update(total.Get())
```

Replace the print with your view update. Destroying owner disconnects the binding while leaving total and its parents alive. If an owner rejects the connection during adoption, Observe disconnects it and throws. There is no implicit UI-property binding or automatic native-resource ownership.

When the feature ends, destroy the values it owns:

```truscript
owner.Destroy()
price.Destroy()
quantity.Destroy()
```

Destroying price cascades to total; quantity stays independent until explicitly destroyed. If only a derived value is no longer needed, destroy it directly to remove its parent subscriptions without destroying those parents. A destroyed value cannot be revived.

## Boundaries

Values use native equality. Editing a field inside the same table or array does not create an observable change. Pass a replacement value when the application needs a new notification; mState neither copies object contents nor creates deep proxies.

Batch is synchronous and has no rollback. If work throws, already accepted writes still commit and the failure is returned. Nested work shares the module-context batch, including writes from another native task while that batch is active. Do not yield in work, observers or computation, and do not use Batch as an asynchronous transaction.

The graph has 1-64 distinct dependencies per derived value and at most 64 derived levels. Handles must be actual returned mState values, used without cloning or internal modification. No SetDependencies operation exists. During active notification dispatch, creating a new Derived graph can fail busy; arrange the graph during feature setup.

Later computation failures retain the last successful derived result. Observer failures are isolated, so later listeners still run. Read the [API reference](api/mState.md) for queued writes, returned failure arrays, disposal and concurrency scope.

## Tests

Install [mState.spec.trs](../tests/mState.spec.trs) as Module asset `mLibraries/tests/mStateSpec`, plus the existing `mLibraries/mTestKit` helper. Its pure entry point is:

```truscript
return import("/mLibraries/tests/mStateSpec").Run()
```

The suite has 34 contracts. The common mNativeSmoke fixture automatically calls its two yielding RunConcurrent cases. Separate [mStateNativeClient.trs](../tests/mStateNativeClient.trs) is an optional alternative Client entry for the same workload. Do not attach both in one context, and leave the optional fixture unattached outside isolated local tests. Do not call the yielding entry through an atomic editor command.

The deterministic and concurrent specifications check state settlement and overlapping lifetimes separately. See [testing](testing.md) and the [verification record](verification/libraries-0.12.2.md) for the recorded scope. These tests do not establish performance, every scheduler interleaving or automatic replication.
