# Native UI library architecture

mBind, mReactive, mControls and mWidgets use native TruScript APIs. The layers
separate resource ownership, state, controls and composition without requiring
one large framework.

## Layers

- mBind owns native instances, event connections and property bindings.
- mReactive adds scoped mState values, explicit computed dependencies, retained keyed
  lists and stepped or automatically driven spring/tween values over mBind.
- mControls supplies native controls, layout and a shared theme through mBind.
- mWidgets composes reactive, themed components using mReactive and mControls.

Native Creator 2026.43.7 rejected `panel["Name"]` with `Cannot index UIPanel`.
mBind therefore uses reviewed factories and explicit property/event adapters.
It does not evaluate source strings or promise arbitrary native reflection.

## Shared interfaces

mBind exports `Scope()`, `Value(source, map?)`, and factory/property introspection.
A source supplies `Get()` and `Observe(callback)` returning a connection with
`Disconnect()`. mState and mReactive values satisfy this protocol. Observe is a
future-change subscription; mBind performs the initial application separately.

A binding scope supplies:

- `New(className, properties?)`: create an owned native instance. Parent is set last.
  Property values can use `mBind.Value(source, map)`. Reserved `Events` and
  `Children` entries wire handlers and parent ordered children. Unknown names fail.
- `Bind(instance, propertyName, source, map?)`: immediate, owned one-way binding.
- `Watch(source, apply)`: owned initial application and future observations.
- `On(instance, eventName, callback)`: owned native connection through a known adapter.
- `Add(cleanup)`, `Own(instance)`, `Child()`, `Destroy()`, `IsDestroyed()`, `GetCount()`.
  Resource handles use idempotent `Destroy()`/`Disconnect()` and release registrations.

Bindings have one writer per instance/property, disconnect on disposal, retain the
last successful property after a failed update and expose their latest error.
Initial construction failure releases its partial resources. Destruction does not
interrupt an already executing user callback. Supplied callbacks must not yield.

mReactive exports `Scope(options?)`, `Bind(source, map?)`, and `Batch(work)`.
Its scope extends the binding interface with `Value(initial)`,
`Computed(dependencies, compute)`, `Observe(source, callback)`,
`For(parent, source, key, render)`, `Spring(source, options?)`,
`Tween(source, duration, easing?)`, and `Step(delta)`.
Computed uses mState's fixed explicit dependency contract. A list renderer receives
`(rowScope, itemState, indexState, key)` and returns its native root. Keys must be
unique; existing keys retain roots and scopes. Removed rows are destroyed.
Motion supports numbers, Vector2 and Vector3; `AutoStep=false` allows deterministic
stepping. A live automatic scope owns at most one frame subscription.

mControls exports `New({Parent, Theme?, AutoStep?})` and `Theme(overrides?)`.
Its kit owns a binding Scope and exposes `Scope`, `Parent`, `Theme`, `Step`, `Destroy`
and native constructors taking one config table. Every component handle supplies
`Root` and `Destroy`; value controls also supply `GetValue` and silent `SetValue`.
Callbacks describe user changes. The application owns any network or gameplay action.

mWidgets exports `New({Parent, Theme?, AutoStep?})` with matching component names.
It accepts readable sources for text, values, visibility, disabled state and theme,
and owns the subscriptions through mReactive. Explicit `OnChanged` callbacks own
two-way state changes; a readonly source is never silently treated as writable.

## Verification

Use deterministic contracts for value and ownership behavior, then real Client
fixtures for native instances, input, scheduler overlap, keyed identity, motion
and teardown. The [testing guide](../testing.md) lists the included fixtures.

Record source revisions and Creator versions with results. Native input checks,
physical-device coverage and performance measurements answer different questions;
a passing resource-count test does not establish heap size or FPS.
