# Native UI libraries

Use mBind, mReactive, mControls and mWidgets to build native TruWorlds UI. They
handle different layers so you can use a control kit on its own or add reactive
state where it helps.

| Library | Purpose | Direct dependencies |
| --- | --- | --- |
| [mBind](api/mBind.md) | Native instances, events and property bindings | mCleanup |
| [mReactive](api/mReactive.md) | Scoped state, keyed lists, springs and tweens | mBind, mState, mSpring |
| [mControls](api/mControls.md) | Themed buttons, inputs, toggles, sliders and layouts | mBind |
| [mWidgets](api/mWidgets.md) | Reactive components | mReactive, mControls |

## Install

Create Module assets at the paths below and leave them unattached. Install their
dependencies from the [main source map](../mLibraries.json) too.

| Asset path | Source |
| --- | --- |
| `mLibraries/mBind` | [mBind.trs](../packages/mBind/src/mBind.trs) |
| `mLibraries/mReactive` | [mReactive.trs](../packages/mReactive/src/mReactive.trs) |
| `mLibraries/mControls` | [mControls.trs](../packages/mControls/src/mControls.trs) |
| `mLibraries/mWidgets` | [mWidgets.trs](../packages/mWidgets/src/mWidgets.trs) |

Visible UI belongs in a Client script. mBind uses explicit native factories and
property/event adapters. It does not promise arbitrary reflection or Roblox
source compatibility.

## A reactive toggle

```truscript
local mBind = import("/mLibraries/mBind")
local mWidgets = import("/mLibraries/mWidgets")
local lifetime = mBind.Scope()
local screen = lifetime.New("ScreenUI", { Parent = game.UICanvas })
local ui = mWidgets.New({ Parent = screen })
lifetime.Add(ui.Destroy)
local music = ui.Scope.Value(true)

ui.Toggle({
    Text = "Music",
    Value = music,
    Position = new Vector2(24, 80),
    OnChanged = func(enabled): music.Set(enabled)
})
# When this menu closes: lifetime.Destroy()
```

Readable values provide `Get()` and `Observe(callback)`. They can drive text,
visibility, values and theme without being writable. `OnChanged` is a user
request; the application decides whether to commit the value. Computed values
remain readonly, and imperative mControls setters are silent to avoid feedback
loops.

## Ownership and stepping

Keep a scope or kit for each feature lifetime and destroy it when the feature
closes. Child resources, subscriptions and owned motion retire with their owner.
Do not keep using a handle after destruction.

Automatic scopes share their frame driver within a scope family. Passing
`AutoStep = false` leaves time under the caller's control through `Step(delta)`.
Do not manually step an owner that is already being stepped automatically.

Keyed lists retain a row's native root and scope while its key exists. Use unique,
stable keys. Removed rows retire through their row owner.

## Gallery and tests

The optional [client gallery](../examples/mUiGallery.client.trs) shows controls,
theme changes, reactive state and retained rows. Run it separately from native
fixtures, then detach it when finished.

See [testing](testing.md) for contract suites and real-client tests. Check actual
pointer input, viewport sizes and physical devices separately. Repeated ownership
counts can detect retained UI, but they do not measure every managed object or
prove a performance improvement.

The [architecture note](architecture/ui-libraries.md) describes the shared
interfaces and teardown behavior in more detail.
