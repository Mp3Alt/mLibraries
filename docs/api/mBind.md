# mBind

mBind creates native UI, connects events and binds properties to readable values.
A scope owns everything it creates. Destroy it when the menu closes.

Install `packages/mBind/src/mBind.trs` as a **Module** at `mLibraries/mBind` in
Creator's Asset Browser. Install `mCleanup` at `mLibraries/mCleanup` too. Import
paths refer to script assets, independently of the instance tree.

```trs
local mBind = import("/mLibraries/mBind")
local mState = import("/mLibraries/mState")
local ui = mBind.Scope()
local count = mState.New(0)
ui.Add(expr(): count.Destroy())

local screen = ui.New("ScreenUI", { Parent = game.UICanvas })
local button = ui.New("UIButton", {
    Text = mBind.Value(count, expr(value): "Count: " + value),
    Size = new Vector2(180, 40),
    Position = new Vector2(24, 80),
    Parent = screen,
    Events = { Pressed = func(): count.Set(count.Get() + 1) }
})
# Later: ui.Destroy()
```

This example also needs mState and its dependencies. It runs in a client script.
Nothing in mBind sends remote requests or grants administration permissions.

## Scope

| Method | Contract |
| --- | --- |
| `New(className, properties?)` | Returns an owned native instance. Applies Parent last. |
| `Bind(instance, property, source, map?)` | Applies the current value, then observes future changes. |
| `Watch(source, apply)` | Calls apply immediately and after changes, reading the current source value. |
| `On(instance, event, callback)` | Connects a known native event without changing its arguments. |
| `Own(instance)` | Adopts an instance for destruction. Does not reparent it. |
| `Add(callback)` | Registers a teardown callback. |
| `Child()` | Creates an independently disposable child scope. |
| `Destroy()` | Closes immediately and runs teardown in reverse order. Returns caught failures. |
| `GetCount()` | Number of active direct registrations, including child scopes. |
| `IsDestroyed()` | Whether the scope is closed. |

Add, Own, On, Bind and Watch return removable handles with idempotent `Destroy()`,
`Disconnect()` and `IsDestroyed()`. Destroying a child removes its parent's
registration. Repeatedly replacing components therefore does not retain their old
cleanup slots. A scope's Destroy call cannot stop a callback already running.

Bind and Watch additionally expose `GetError()` and `Refresh()`. A later apply or
mapping failure leaves the previous successful property value and records the
error. A successful update clears it. An initial failure throws and releases the
subscription. Dispose a native target to release its bindings when its Destroyed
signal runs, or dispose its owning scope for immediate teardown.

Only one active binding may write a given native instance/property. Dispose that
binding before replacing it. Concurrent writer admissions can be rejected as busy;
they never create a second writer. Release requests drain under the same gate.

## Construction

Properties use explicit native adapters. Unknown names and properties belonging to
another class throw. `mBind.Value(source, map?)` marks a property as reactive.
`Events` maps event names to callbacks. `Children` supplies ordered native children.
Successful construction adopts those children through native parent ownership.
Failed construction restores their previous parents before releasing its new root.
Callback side effects are outside that rollback.

Factories support ScreenUI, UIPanel, UITextPanel, UIButton, UITextInput, UICircle,
UIScrollPanel, UIBackgroundImage, UIHorizontalLayout, UIVerticalLayout and
UIGridLayout. `GetClasses()`, `GetProperties()` and `GetEvents()` return independent
arrays of supported names. Native methods and readonly properties are not bindable.

## Readable values and limits

A source supplies `Get()` and `Observe(callback)`. Observe subscribes to future
changes and returns a connection with `Disconnect()`. mState and mReactive values
already meet this contract. Subscribe happens before the first read so a change
during subscription is not lost. Reentrant changes settle on the latest current
value; intermediate values may be coalesced.

Callbacks, mapping functions and teardown callbacks must finish without yielding.
Unbounded feedback is an application error. Native notifications run in separate
tasks; disposal prevents new work but cannot interrupt user code already executing.
The library uses fixed adapters because Creator 2026.43.7 rejects string indexing
on native UI objects. It does not use reflection, source evaluation or automatic
dependency discovery. Native UI is local presentation; server validation remains
the application's responsibility.
