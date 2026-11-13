# mReactive

mReactive combines owned native UI construction, local reactive state, keyed rows and motion. It depends on [mBind](mBind.md), [mState](mState.md) and [mSpring](mSpring.md). Its API is written for TruScript. Dependencies are explicit rather than inferred from reads.

```truscript
local mReactive = import("/mLibraries/mReactive")
local ui = mReactive.Scope()
local screen = ui.New("ScreenUI", { Parent = game.UICanvas })
local count = ui.Value(0)
local text = ui.Computed([count], expr(values): "Count: " + values[0])
local label = ui.New("UITextPanel", {
    Text = mReactive.Bind(text),
    Parent = screen
})
count.Set(3)
# ui.Destroy() when the screen closes.
```

All methods use dot calls. Keep callbacks synchronous. A scope owns what it creates, including state, subscriptions, native roots, row scopes and motion. External sources and parents are borrowed.

## Scope and state

| Call | Contract |
| --- | --- |
| `mReactive.Scope(options)` | Creates an owner. `AutoStep` defaults to true; `{ AutoStep = false }` disables its frame subscription. Unknown options throw. |
| `mReactive.Bind(source, map)` | Returns an mBind property descriptor. `map` is optional. Use it inside `New` property tables. |
| `mReactive.Batch(work)` | Delegates to mState.Batch and returns its caught failures. It coalesces accepted writes; it is not rollback or cross-task isolation. |
| `ui.Value(initial)` | Returns an owned writable mState handle. Nil, false and zero are valid. |
| `ui.Computed(dependencies, compute)` | Returns an owned read-only mState.Derived handle. The explicit dependency array stays fixed. `compute(values)` receives values in dependency order. |
| `ui.Observe(source, apply)` | Applies the current value immediately, then observes future changes. Returns a removable watch handle with `GetError()`. |
| `ui.Child()` | Returns a full mReactive scope owned by this one. Destroying the child removes its parent registration. |
| `ui.Destroy()` | Closes the owner and returns cleanup failures. Repeated calls return an empty array. |
| `ui.IsDestroyed()` | Reports whether the local owner is closed. |
| `ui.GetCount()` | Counts active direct ownership registrations in the local scope. It is not the number of native descendants. |

`New`, `Bind`, `Watch`, `On`, `Add` and `Own` on a scope delegate to mBind. In particular, `ui.Bind(instance, property, source, map)` creates a binding, while `mReactive.Bind(source, map)` creates a descriptor. See [mBind's class, property, event and ownership contracts](mBind.md).

Values, computed results and motion outputs retain their original mState identities, so they can be dependencies of another Computed. Their `Destroy()` and `RequestDestroy()` methods also release ownership registrations. Explicit Destroy retains mState's computation guard. Owner teardown uses RequestDestroy, which immediately closes the handle and queues graph cleanup if another computation is running. Destroying a dependency cascades through mState's dependent graph. Other scope-owned registrations are released when explicitly destroyed or when their scope closes.

Computed inherits mState's limits: 1 to 64 distinct live dependencies, depth at most 64, borrowed values and native equality. Computations must be pure. Creating a Computed or motion inside an active mState notification is rejected by mState's graph-construction guard. Create stable graphs during setup. For lists, the queued reconciliation described below supplies a safe render phase outside the source notification.

## Keyed rows

```truscript
local items = ui.Value([{ Id = 7, Name = "Mp3" }])
local rows = ui.For(container, items, expr(item, index): item.Id,
    func(row, item, index, key):
        local text = row.Computed([item, index], expr(values): values[1] + ": " + values[0].Name)
        return row.New("UITextPanel", { Text = mReactive.Bind(text) })
)

items.Set([{ Id = 7, Name = "Updated" }, { Id = 8, Name = "New" }])
# Automatic scopes reconcile on the next frame.
# A manual scope reconciles with ui.Step(0).
```

`ui.For(parent, source, key, render)` reads an array source. `key(item, index)` must return a unique string or finite number; zero and the empty string are valid keys. Indices are zero based. The renderer receives `(rowScope, itemState, indexState, key)` and must return a distinct, unparented native root. Create row resources through rowScope. The list owns the returned root as well.

Initial rendering happens before For returns. Later source notifications enqueue the list once. Repeated writes before the next Step coalesce to the latest array. Reconciliation runs before motion during the next automatic frame or explicit `ui.Step(delta)`. This phase lets new row renderers safely create Computed and motion values without changing mState's notification semantics.

Retained keys keep the same root, row scope and item/index handles. Their item and index states update in one mState batch. Only new keys call the renderer; removed keys destroy their complete row scope. Native sibling order follows the array through MoveAfter. Use a dedicated parent for rows, optionally with a native layout child. Do not reparent or reorder owned roots from elsewhere.

All keys are checked before touching retained rows. New row scopes are staged before parenting or updating existing states. A duplicate key or failed renderer destroys every staged row and preserves the previous committed list. Native parenting failures also destroy staged rows and attempt to restore the surviving sibling order. External destruction or reparenting during reconciliation can prevent that restoration. Keep arrays and row objects stable while callbacks run; replace source arrays to publish changes.

Staged and committed row scopes are visible to teardown throughout reconciliation. If a native task closes the list while rendering or parenting is in progress, newly acquired roots are released instead of being republished into a closed list.

After native parenting commits, item/index updates and removed-row cleanup cannot be rolled back. An observer or removed-row cleanup failure is reported while the committed keys remain in place. Additional cleanup failures, including staged rollback errors after a primary rendering failure, are retained for the owning scope's Destroy result. This distinction is intentional: a callback may already have changed external state. A later valid update or Refresh can retry work.

| List method | Contract |
| --- | --- |
| `rows.GetCount()` | Number of committed rows. |
| `rows.GetRoot(key)` | Retained native root, or nil when absent. |
| `rows.GetError()` | Most recent reconciliation failure, cleared after a successful reconciliation. |
| `rows.Refresh()` | Reconciles immediately from source.Get; throws on failure. Call outside state notifications and other reconciliation callbacks. |
| `rows.Destroy()` / `Disconnect()` | Cancels pending work, disconnects the source and destroys every row. Idempotent. |
| `rows.IsDestroyed()` | Reports list disposal. |

A failed scheduled reconciliation appears in `ui.Step`'s failure array and the list's GetError. It waits for another source change or an explicit Refresh; it does not retry a broken renderer every frame. A renderer or key callback must not change or destroy its owning list, yield, or mutate the source it is currently rendering.

## Motion

```truscript
local target = ui.Value(0)
local eased = ui.Tween(target, 0.2, "QuadOut")
local spring = ui.Spring(target, { Frequency = 4, Damping = 1 })
target.Set(100)
# Both are readable sources for mReactive.Bind or ui.Computed.
```

`ui.Spring(source, options)` uses mSpring's numeric solver and configuration. `ui.Tween(source, duration, easing)` interpolates over finite seconds from 0 through 60. Supported easings are `Linear` (default), `QuadIn`, `QuadOut`, `QuadInOut` and `CubicOut`.

Both return owned read-only mState handles with Get, Observe, Destroy and IsDestroyed. They also expose `GetError()` for the latest invalid source target or step failure. `IsResting()` is false when a new target is waiting to be applied; otherwise it reports whether the spring is resting or the tween is complete. It throws after disposal. A value keeps its initial type: number, Vector2 or Vector3. All components must be finite. Vector targets are copied by component when received, so later mutation of a borrowed vector does not change a pending target.

Targets apply at the next Step. Several targets before a Step coalesce. A spring keeps velocity when retargeted. A tween retargets from its current interpolated position and starts a full new duration. A zero-duration tween reaches its endpoint on the next Step, including Step(0). Completed motion does not publish unchanged values each frame. Invalid targets keep the last valid target and record an error; a later valid target clears it.

Spring Step(0) does not advance or snap. A positive step also processes a new
target already inside both spring tolerances, so it snaps to that target rather
than leaving the previous output in place.

`ui.Step(delta)` first reconciles queued lists, then advances motion in one mState batch. Delta must be finite seconds from 0 through 60. It returns caught failures while continuing independent motion. Reentrant or overlapping Step calls throw busy; disposal closes ownership immediately and skips later publication where possible. Already executing callbacks cannot be interrupted. All work must be synchronous; no background worker is created per value or row.

Child scopes and row scopes share their root scope's scheduler. Calling Step on any live member advances the whole scope family, so call it once per frame. A scope family with AutoStep=true lazily owns at most one FrameStepped subscription, first created when it needs a list or motion. It stays until the root scope closes. Idle callbacks return without walking rows. Automatic callbacks skip a tick if another Step owns the gate, and cap an unusually large frame delta at 60 seconds. This is UI motion, not a fixed-time physics clock.

Motion outputs also provide `SetPaused(boolean)` and `IsPaused()`. Paused motion keeps its current value, velocity and tween time. Target changes wait until it resumes. Pausing does not mean the motion has reached its target. This lets hidden retained controls freeze without creating a separate frame driver.

`ui.GetMotionCount()`, `GetPendingListCount()`, `GetFrameConnectionCount()` and `GetError()` inspect the shared scheduler. A manual idle Step validates delta and returns an empty array without a state batch or list snapshots. These are behavior contracts, not a claim about device frame rate, memory use or the engine's collector.

## Verification

The development suite exports `Run()` for deterministic state and motion contracts, `RunNative()` for native keyed roots and row teardown, and `RunConcurrent()` for the real automatic frame driver. Native compilation and runtime outcomes are recorded by the project verification run. No Luau compatibility, mobile performance or universal scheduler interleaving guarantee is claimed.
