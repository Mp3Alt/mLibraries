# mState

mState supplies local observable values, fixed derived dependencies and synchronous batches. It depends on [mSignal](mSignal.md) and [mCleanup](mCleanup.md). It does not replicate data, watch table contents or infer dependencies from property reads.

```truscript
local mState = import("/mLibraries/mState")
local count = mState.New(0)
local doubled = mState.Derived([count], expr(values): values[0] * 2)
local connection = doubled.Observe(expr(value): print(value))
local failures = count.Set(3)
count.Destroy()
```

Methods use dot calls. Values are borrowed references and use native equality; there is no deep copy or custom equality function.

## Constructors and batching

| Call | Contract |
| --- | --- |
| `mState.New(initial)` | Returns an observable writable value. Nil, false and zero are valid values. |
| `mState.Derived(dependencies, compute)` | Copies an array of 1-64 distinct live mState handles. Runs `compute(values)` initially and returns a read-only derived value. |
| `mState.Batch(work)` | Runs synchronous work, then drains accepted writes when the outer module-context batch ends. Returns caught failures from the drain it owns. |

Dependencies stay fixed. They must be original library handles, not copied handle tables or arbitrary Get/Observe adapters. A dependency must already exist, so the supported construction API cannot add a cycle. Derived depth is capped at 64. Changing the caller's dependency array does not change the graph.

Each computation receives a fresh array of dependency values in declared order. Objects inside it remain borrowed references. Computations must be pure and must not yield. New values, subscriptions, writes, ordinary Destroy calls and batches are rejected while computation is active. RequestDestroy is the explicit exception for owned teardown: it closes immediately and queues graph cleanup until computation finishes. A later compute failure keeps that node's last successful result; a subsequent dependency change can retry it. Initial computation or invalid construction throws. Graph construction during an active notification drain also throws busy.

## Value methods

| Call | Contract |
| --- | --- |
| `value.Get()` | Returns the currently committed value. Throws after disposal is requested. |
| `value.Set(next)` | Queues a writable-value assignment and synchronously drains when it can own the pump. Returns caught failures; derived values reject direct writes. |
| `value.Observe(handler, owner)` | Subscribes to future changes and returns a connection with `Disconnect()` and `IsConnected()`. `owner` may be omitted or nil. |
| `value.IsDestroyed()` | Returns whether disposal has been requested. |
| `value.Destroy()` | Requests permanent disposal, cancels pending delivery and returns failures from any drain it owns. Repeated calls return an empty array. |
| `value.RequestDestroy()` | Closes immediately like Destroy, but also accepts teardown while a computation is active. Graph unlinking waits for the owning drain; the requesting call then returns an empty failure array. |

Observe does not call the handler initially. It passes the new value as one payload and invokes handlers in registration order. An optional cleanup owner adopts the returned connection through `AddConnection`. If adoption throws, the new connection is disconnected before the failure is rethrown. The cleanup owner owns the binding, not the source value.

Use handles as returned; replacing their methods or inspecting/modifying their internal entries is outside the contract. Their identity metadata is local implementation state, not a permission or remote-validation mechanism.

## Commit and notification order

Outside a batch or active notification drain, Set commits before returning. Inside either scope, writes stay queued. Get therefore returns the previous committed value until the outer batch or current dispatch finishes. A reentrant Set does not recursively fire observers.

The pump commits queued writes in order, settles dirty derived nodes from lower to higher dependency depth, then delivers public notifications. Before the first public notification of a settled wave, dependent values have recomputed. Different values notify in first-change queue order; handlers for one value run in subscription order.

Several queued assignments to one value coalesce to its final value. Returning to the last emitted value produces no public change. A finite reentrant observer write starts another settlement wave after the current dispatch. Every observer in that dispatch receives its original payload. Arbitrary concurrent Get calls are not a transactional snapshot of the whole graph.

Batch is not rollback. Writes accepted before a callback failure still commit. Nested batches defer their drain to the outer module-context batch. The batch depth and queue belong to this module context, so another native task can join an active batch. Work must not wait, spawn asynchronous batch work or treat Batch as an isolated cross-task transaction.

## Errors and lifetime

Set and Batch return arrays containing original caught observer, later computation and batch-work failures. One failed observer does not stop later observers. A call made inside an existing batch/drain usually returns an empty array because another call owns completion and failure reporting. With overlapping native tasks, those arrays are not per-request error correlations. Inspect the result of the call that completes the drain.

Misuse throws: disposed access, a write to a derived value, invalid dependencies, missing callbacks, impure computation or busy graph construction. Derived construction can also own a drain; a failure in that drain throws and disposes its new value. It reports the initial construction failure first if construction and queued work both fail.

Destroy marks the value disposed immediately, so observers that have not passed their disposal check are skipped. An in-progress callback cannot be interrupted or rolled back. Cleanup itself joins the queue when a batch/drain is active. During cleanup, destruction cascades to all dependent derived values, disconnects their observers and unlinks them from surviving parents. Destroying a derived value does not destroy its parents. There is no final change notification on destruction.

Use RequestDestroy in resource owners that can close from a different native task
while computation is active. It cannot wait for that computation or report the
later drain's failures to the requesting task. Get and Set reject the closed value
immediately. If a dependency is closed during initial graph construction, that
construction fails and unwinds. This method is for lifecycle teardown, not a way
to make impure computed functions into ordinary state writers.

Observers and batch work must finish synchronously. Finite feedback is supported; an unbounded observer feedback loop is the caller's error. A forcibly stopped host is outside guaranteed teardown, as it is for mCleanup. No garbage-collection or allocation benchmark is claimed.

## Verification

The specification covers values, batching, dependency settlement, failure
reporting and owned teardown during computation. Its concurrent methods require
a real Client script in Play. See [testing](../testing.md) and the
[verification record](../verification/libraries-0.12.2.md) for the recorded scope.
Bounded workloads do not prove every scheduler interleaving or a performance gain.
