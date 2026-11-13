# mWidgets

mWidgets is the reactive component layer over mControls and mReactive. A readable
value can drive text, a control value, visibility, disabled state or theme.
The caller explicitly decides whether an input request changes application state.

Install Module assets at these Asset Browser paths:

| Source | Asset path |
| --- | --- |
| `packages/mSignal/src/mSignal.trs` | `mLibraries/mSignal` |
| `packages/mCleanup/src/mCleanup.trs` | `mLibraries/mCleanup` |
| `packages/mState/src/mState.trs` | `mLibraries/mState` |
| `packages/mSpring/src/mSpring.trs` | `mLibraries/mSpring` |
| `packages/mBind/src/mBind.trs` | `mLibraries/mBind` |
| `packages/mReactive/src/mReactive.trs` | `mLibraries/mReactive` |
| `packages/mControls/src/mControls.trs` | `mLibraries/mControls` |
| `packages/mWidgets/src/mWidgets.trs` | `mLibraries/mWidgets` |

Use a client script. Script asset paths and native instance parents are separate.

```trs
local mBind = import("/mLibraries/mBind")
local mWidgets = import("/mLibraries/mWidgets")
local owner = mBind.Scope()
local screen = owner.New("ScreenUI", { Parent = game.UICanvas })
local ui = mWidgets.New({ Parent = screen })
owner.Add(ui.Destroy)
local music = ui.Scope.Value(false)
local caption = ui.Scope.Computed([music], func(values):
    if values[0]: return "Music on"
    return "Music off"
)
ui.Toggle({
    Text = caption, Value = music, Position = new Vector2(24, 90),
    OnChanged = music.Set
})
# Later: owner.Destroy()
```

## Reactive configuration

`New({Parent, Theme?, AutoStep?})` returns a kit. Theme can be a literal override
table or a readable source of override tables. Parent is borrowed.

Every mControls constructor is available: Panel, Text, Button, IconButton,
Input, Checkbox, Toggle, Switch, Slider, Dropdown, Progress, Separator, Scroll,
Row, Column and Window. Native layout options, theme tokens and control behavior
follow [mControls](mControls.md).

These fields accept either literal configuration or a readable source:

| Field | Supported component behavior |
| --- | --- |
| `Text` | Components with SetText: labels, buttons, booleans and window titles. |
| `Value` | Input, Checkbox, Toggle/Switch, Slider, Dropdown and Progress. |
| `Visible`, `Disabled` | All component handles. |
| `Theme` | All components, or the entire kit through New. |
| `Placeholder` | Input. |

A readable source supplies `Get()` and future-only `Observe(callback)`, returning
a connection with Disconnect(). mState and mReactive values satisfy this contract.
Use IsSource(value) for protocol detection; it does not certify arbitrary user
implementations. mReactive owns initial application and subscription. False, zero,
empty strings and nil values are not replaced by truthy defaults. Unsupported
readable fields fail construction and release the partial native tree.

State updates apply through the component's setters. A binding failure retains
the last successfully applied native state. `handle.GetBindingError(field)`
reports that binding's latest error, or nil after a subsequent successful update.
Initial failures throw and dispose partial subscriptions and native resources.

## Input requests and one writer

For a readable Value, OnChanged is a request. Use an explicit callback to commit
it to application state. mWidgets never calls Set on an arbitrary source. A computed
or readonly source is valid.

```trs
local amount = ui.Scope.Value(0.5)
ui.Slider({
    Value = amount, Min = 0, Max = 1, Step = 0.01,
    OnChanged = func(requested):
        if requested <= 0.8: amount.Set(requested)
})
```

After OnChanged returns, the control rereads its source and reconciles the visual
value. If the application declines a request, its previous value remains. The
same reconciliation runs after a throwing callback. If work must be asynchronous,
commit the desired pending state synchronously and perform that work separately.
User callbacks must not yield. A controlled Window similarly rereads its Visible
source after OnClosed, so the caller decides whether closing is accepted.

Programmatic SetValue stays silent for literal, uncontrolled values. Calling
SetValue on a source-controlled Value throws. Corresponding SetText, SetVisible,
SetDisabled, SetPlaceholder and SetTheme setters also refuse to replace their
source's ownership. Use the source's application-owned writer instead. Avoid
direct writes through Root or Control while a reactive binding owns that value.

Dropdown Options are copied literal arrays, not reactive collections. Use
mReactive.For for retained keyed collections of components instead of recreating a
list of controls whenever one item changes.

## Lifetimes and stepping

The kit exposes `Scope` (a full mReactive scope), `Parent`, a copied `Theme`
snapshot, `Step(delta)`, `SetTheme(overrides)`, `GetCount()`, `IsDestroyed()` and
idempotent `Destroy()`. Kit SetTheme is available for a literal initial theme;
a source-controlled kit theme must be changed through that source.

Each component forwards mControls members and adds its reactive `Scope`, native
`Root`, underlying `Control`, and GetBindingError. Destroy releases subscriptions
and the underlying control. External native Root destruction also disposes the
reactive scope when the asynchronous Destroyed signal arrives. Prefer the handle's
Destroy method for immediate teardown.

Default AutoStep uses one frame connection per mWidgets kit to advance its mReactive
scope family and mControls motion. Its idle callback only checks work counts.
Both inner layers run with AutoStep=false, avoiding duplicate drivers. The public
kit Scope therefore expects the kit's driver or Step for motions and queued keyed
lists. With AutoStep=false, call ui.Step(delta) once per desired update. Destroy
disconnects the driver. No background polling task or remote is created.

The kit follows native TruScript ownership and readable-value contracts. It does
not add language typechecking or remove native UI constraints. The contracts in
`tests/mWidgets.spec.trs` cover its API; the optional
`examples/mUiGallery.client.trs` demonstrates native inputs, palette changes,
motion and retained keyed rows together.
