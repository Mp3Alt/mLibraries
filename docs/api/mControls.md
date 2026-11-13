# mControls

mControls builds native TruWorlds controls with one owner, consistent theme tokens
and explicit callbacks. It has no reactive state dependency. Use mWidgets when
configuration should follow readable values.

Install these Module assets in Creator's Asset Browser:

| Source | Asset path |
| --- | --- |
| `packages/mCleanup/src/mCleanup.trs` | `mLibraries/mCleanup` |
| `packages/mBind/src/mBind.trs` | `mLibraries/mBind` |
| `packages/mControls/src/mControls.trs` | `mLibraries/mControls` |

Import paths identify script assets, separately from the instance tree. Run UI
code in a client script under a ScreenUI in `game.UICanvas`.

```trs
local mBind = import("/mLibraries/mBind")
local mControls = import("/mLibraries/mControls")
local owner = mBind.Scope()
local screen = owner.New("ScreenUI", { Parent = game.UICanvas })
local ui = mControls.New({ Parent = screen })
owner.Add(ui.Destroy)

local window = ui.Window({ Text = "Settings", Position = new Vector2(80, 90) })
local column = ui.Column({
    Parent = window.Content, AnchorRight = 1, AnchorBottom = 1,
    Size = new Vector2(), MinSize = new Vector2(), Padding = new Vector2(12, 12)
})
ui.Toggle({
    Parent = column.Content, Text = "Music", Value = true,
    MinSize = new Vector2(0, 36),
    OnChanged = func(enabled): print("Music: " + enabled)
})
# When the screen is no longer needed: owner.Destroy()
```

## Kit and ownership

`New({Parent, Theme?, AutoStep?})` returns a kit. Parent is borrowed. Destroying
the kit releases every component, connection and active animation it owns.

| Member | Contract |
| --- | --- |
| `Scope` | Owned mBind scope. Add related cleanup here. |
| `Parent` | Default native parent for new components. |
| `Theme` | Copied snapshot. Use SetTheme to apply changes. |
| `SetTheme(overrides)` | Validate and replace the kit palette. Component overrides remain. |
| `Step(delta)` | Advance visual motion with finite, nonnegative seconds. |
| `GetCount()` | Number of live component registrations. |
| `GetActiveCount()` | Number of active visual animations. |
| `GetOverlayCount()` | Number of open dropdowns requiring placement updates. |
| `IsDestroyed()`, `Destroy()` | Inspect or idempotently dispose the kit. |

Every constructor takes one configuration table and returns `Root`, `Scope`,
`Destroy()`, `IsDestroyed()`, `SetVisible(boolean)`, `SetDisabled(boolean)`,
`GetDisabled()`, `SetTheme(overrides)` and `GetTheme()`. Setters reject use after
disposal. Value getters return the last stored value. A handle's Scope owns its
native tree and event connections. Destroying Root directly also disposes its
component when the native Destroyed signal is delivered. That signal is
asynchronous; use handle.Destroy for immediate scope teardown.

Common configuration is `Parent`, `Name`, `Position`, `Size`, `MinSize`, `Pivot`,
`AnchorLeft`, `AnchorRight`, `AnchorTop`, `AnchorBottom`, `FlexRatio`,
`FitContents`, `ZIndex`, `Visible`, `Disabled` and `Theme`. Theme colors and option
arrays are copied. Other caller configuration is read as configuration, so do
not mutate it to control a live component. Use its setters instead.

Inside native layouts, Size and Position do not control placement. Use MinSize,
FlexRatio and FitContents. For a container that fills its parent, set spanning
anchors, Size to `new Vector2()` and MinSize to `new Vector2()`.

## Components

| Constructor | Additional configuration and handle members |
| --- | --- |
| `Panel` | `ClipsChildren`; `Content = Root`. |
| `Text` | `Text`, `TextAlignment`, `WrapText`; `SetText(text)`. |
| `Button` | `Text`, `OnPressed()`; `SetText(text)`, guarded `Activate()`. |
| `IconButton` | Required `ImageId`; `OnPressed()`; `Icon` is the native tint panel. Uses caller artwork, with no font symbol fallback. |
| `Input` | `Value`, `Placeholder`, `MaxLength` (default 1024), `BlurOnSubmit`, `SelectAllOnFocus`, `OnChanged(text)`, `OnSubmitted(text)`; `GetValue`, silent `SetValue`, `SetPlaceholder`. |
| `Checkbox`, `Toggle`, `Switch` | Boolean `Value`, `Text`, `OnChanged(boolean)`; `GetValue`, silent `SetValue`, `SetText`, guarded `Activate`. Switch aliases Toggle. |
| `Slider` | `Min` (0), `Max` (1), `Step` (0), `Value`, `OnChanged(number)`; `GetValue`, silent `SetValue`. |
| `Dropdown` | `Options`, optional `Value`, `Placeholder`, `OnChanged(text)`; `GetValue`, silent `SetValue`, `SetOpen`, `GetOpen`, `Popup`, owned `Portal` ScreenUI, guarded `Activate`. |
| `Progress` | Slider range/value configuration; silent `SetValue`, `GetValue`; no user interaction. |
| `Separator` | A one-pixel line unless Size or MinSize overrides it. |
| `Scroll` | `ScrollX`, `ScrollY`; `Content = Root`, a native UIScrollPanel. Disabling prevents scrolling. |
| `Row`, `Column` | `Spacing`, `Padding`, `MainAlign`, `CrossAlign`; `Content = Root`, a native layout. |
| `Window` | `Text`, `Modal`, `Draggable`, `OnClosed()`; `Content`, `SetText`, guarded `Close`. Close hides the window. |

SetValue never calls OnChanged. Input stores the native Text readback after a
programmatic write, including MaxLength normalization, and suppresses that
write's TextChanged echo. Slider clamps to the range and rounds to the nearest
Step from Min. A zero Step is continuous. An increment too small to represent
the step count leaves the finite clamped value unchanged. Stored values keep their precision;
format a separate label when displaying them. Dropdown supports up to 256
unique strings. Its value is a choice string or nil to clear the selection.

Silent range writes preserve an active gesture, so a controlled slider can
reconcile a declined value and continue accepting later movement in the same drag.

User callbacks are synchronous application work and must not yield. Callback
errors are not silently swallowed by the controls. They do not send remotes,
validate server permissions or grant authority. A server must independently
validate any game action requested by client UI.

## Theme

`Theme(overrides?)` returns a new validated table. Unknown tokens fail, catching
misspellings. Each color is copied into a new Color4.

| Tokens | Accepted values |
| --- | --- |
| `Background`, `Surface`, `Raised`, `Accent`, `Text`, `Muted`, `Border`, `Disabled` | Color4 colors. |
| `Radius` | 0 to 64 pixels, default 7. |
| `Spacing`, `Padding` | 0 to 128 pixels, defaults 8 and 12. |
| `Height` | 16 to 200 pixels, default 36. |
| `TextSize` | 4 to 80 pixels, default 15. |
| `BorderWidth` | 0 to 8 pixels, default 1. |
| `AnimationSpeed` | 0 to 60, default 20. Zero applies visual values immediately. |

SetTheme restyles existing controls. Height, Radius and other tokens used when
constructing geometry do not perform a full responsive layout rebuild. Give
components explicit layout sizes when changing dimensions. The default typeface
is the native OpenSans, with OpenSansBold for window titles.

## Input, motion and limits

Buttons use native Pressed, cancellation and tint behavior. Disabled and hidden
controls refuse semantic activation. A slider changes only on a completed click
or an active native drag. A cancelled drag restores its starting value; disabling
or hiding a control cancels further local drag updates. Window drag cancellation
restores the captured position.

Keyboard shortcuts apply to the currently hovered control only when no text
field owns keyboard focus: Enter/Space activate buttons and booleans, arrows
adjust sliders or dropdown choices, Home/End reach slider bounds, and Escape
closes a dropdown. This is hover keyboard support, not a complete Tab navigation
or screen reader accessibility system. Keyboard focus for native text inputs
stays with TruWorlds.

Pointer coordinates convert through ScreenUI.ViewportToLocal, including native
ScreenUI scaling. Slider/window dragging and dropdown placement reject rotated or scaled UIObject
ancestors because AbsolutePosition excludes those transforms. Other native
input/layout limitations still apply. Each dropdown owns a portal ScreenUI above
its source screen's DisplayOrder, so later layout siblings and ancestor scroll
clips do not cover the popup. The portal copies source screen scaling, positions
from native layout, flips or shrinks to available viewport space, and closes when
its trigger is hidden, clipped or removed. Placement updates share the kit driver
while open. The borrowed source screen's stacking behavior is unchanged. Native
core interfaces retain their protected priority.

Toggle and range visuals use exponential interpolation. With AutoStep enabled,
one frame connection is created while motion or an open dropdown needs updates,
then disconnected when neither remains. AutoStep=false leaves both to Step. Idle Step performs no
component scan. Reentrant Step calls throw rather than advancing the same list
twice. This is an implementation contract, not a measured speed or memory claim.

mControls targets native TruScript APIs and does not promise Roblox source
compatibility. See [the specification](../../tests/mControls.spec.trs) for pure
and real-client contracts.
