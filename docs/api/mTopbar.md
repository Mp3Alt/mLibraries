# mTopbar

mTopbar creates a client-side row of buttons using ordinary TruWorlds UI. It depends on [mSignal](mSignal.md) and [mCleanup](mCleanup.md). The buttons are styled to sit beside the native controls; they are not inserted into the protected core toolbar.

Button and dock geometry and motion target **Creator 2026.43.7**. Recheck
layout and actual input on another engine build. See [testing](../testing.md)
and the [verification record](../verification/libraries-0.12.2.md) for scope.

Numeric badges, dropdown menus, overflow and selection groups are library features. This API does not promise full TopbarPlus compatibility or provide a platform extension API.

## Create a bar

```truscript
local mTopbar = import("/mLibraries/mTopbar")
local bar = mTopbar.New({
    Name = "MyTopbar",
    LeftInset = 168,
    RightInset = 218,
    TopInset = 8,
    AutoDestroy = false
})
```

Call from a Client script. Methods use dot calls.

| Call | Behavior |
| --- | --- |
| `mTopbar.New(config)` | Creates a bar with its own UI and lifetime. Config is optional. `Name` defaults to `"mTopbar"` and accepts up to 64 characters. Insets default to left 168, right 218 and top 8; `AutoDestroy` defaults to false. |
| `mTopbar.GetDefault()` | Lazily creates or returns the shared default bar. It uses `AutoDestroy = true` and destroys itself when its last icon is removed. A contending first construction can yield; ordinary access returns the live bar. |
| `bar.Add(definition)` | Adds an icon and returns its handle. At most 64 icons belong to one bar. Overlapping registration throws; callers may retry. |
| `bar.Dock(first, second)` | Joins two icons into one adjacent pair and returns a dock handle. Overlapping Add/Dock registration throws; callers may retry. |
| `bar.SetVisible(visible)` | Shows or hides the bar. Hiding also deselects its icons. |
| `bar.SetInsets(left, right, top)` | Sets the three reserved margins. Each must be finite and between 0 and 4,096. |
| `bar.GetCount()` | Returns the number of registered icons. |
| `bar.IsDestroyed()` | Returns whether the bar has been destroyed. |
| `bar.Destroy()` | Destroys the bar and its icons. |

Use `GetDefault()` across features that should share one row. Creating a separate bar for each feature gives each an independent layout, which can overlap. An icon name must be unique within its bar.

The installed 43.7 guide, `guide/where-code-runs` under Module scripts and import, documents that a module runs once and its importers share the returned value. The module-local default therefore serves features on that client; it is not a networked bar shared between players.

Default construction uses a double-checked claim. Only a first call that overlaps construction waits with `wait(0)` until the claim is released. Call it from an attached Client script, not an atomic editor runner that cannot wait. Contention during the very first construction has not been forced in the recorded native checks.

## Add an icon

```truscript
local icon = bar.Add({
    Name = "Inventory",
    Label = "I",
    Tooltip = "Open inventory",
    Toggle = true,
    Group = "panels"
})
```

| Field | Default | Contract |
| --- | --- | --- |
| `Name` | Required | Unique, nonempty name, at most 64 characters |
| `Image` | `""` | Image asset ID, at most 256 characters |
| `ImageSize` | `28` | Centered image size from 8 to 40 |
| `Label` | `""` | Fallback button text, at most 64 characters; use one or two letters |
| `Tooltip` | `""` | Overflow label metadata, at most 128 characters; no hover popup |
| `Badge` | `0` | Integer from 0 to 9,999 |
| `Order` | `0` | Finite number from -1,000,000 to 1,000,000 |
| `Side` | `"Left"` | `"Left"` or `"Right"` |
| `Toggle` | `true` | Whether activation toggles selection |
| `Group` | `""` | Up to 64 characters; nonempty groups make selection exclusive within the bar |
| `Enabled` | `true` | Whether the icon accepts activation |
| `Visible` | `true` | Whether the icon is shown |
| `Key` | `nil` | Optional key binding |

Numeric ranges describe API input limits, not engine networking or rendering budgets. Image values are asset IDs rather than local PNG paths.

The image is centered in the button. The fallback label shows when `Image` is empty, not alongside the image. Badge zero is hidden; values above 99 display as `99+`. `Tooltip` supplies the overflow row's text, falling back to `Name` when empty. It does not create a tooltip on hover.

## Icon methods

| Call | Behavior |
| --- | --- |
| `icon.SetImage(image)` | Changes the image ID. |
| `icon.SetImageSize(size)` | Changes the centered image size, from 8 to 40. |
| `icon.SetLabel(label)` | Changes the label. |
| `icon.SetTooltip(tooltip)` | Changes the overflow label metadata. |
| `icon.SetBadge(badge)` | Changes the badge value. |
| `icon.SetOrder(order)` | Changes the layout order. |
| `icon.SetSide(side)` | Moves the icon to the left or right side. Throws while docked; undock first. |
| `icon.SetEnabled(enabled)` | Enables or disables activation. Disabling also deselects it. |
| `icon.SetVisible(visible)` | Shows or hides the icon. Hiding also deselects it. |
| `icon.SetSelected(selected)` | Changes logical selection and returns whether it changed. It adds no selected outline or background. |
| `icon.BindKey(key)` | Changes the key binding; `nil` clears it. |
| `icon.Activate()` | Attempts activation and returns whether it was accepted. |
| `icon.IsSelected()` | Returns the current selection state. |
| `icon.IsDestroyed()` | Returns whether the icon has been destroyed. |
| `icon.GetState()` | Returns a copied state record. Editing it does not change the icon. |
| `icon.Destroy()` | Removes and destroys this icon. |

Setter inputs retain the corresponding definition limits. Limit violations and mutation of a destroyed icon or bar throw. Repeated `Destroy()` is harmless; the status getters remain available after destruction.

Order and ImageSize retain exact accepted numeric values. Their setters do not
use the runtime's tolerant numeric equality to discard small changes.

`SetBadge`, `SetLabel` and `SetImageSize` repaint the icon without running layout. They preserve an open menu's existing rows and selection. Content or selection updates do not restart an unchanged pointer animation. Changes that affect placement or visibility still run layout.

`GetState()` includes `Name`, `Image`, `ImageSize`, `Label`, `Tooltip`, `Badge`, `Order`, `Side`, `Enabled`, `Visible`, `Selected`, `Toggle`, `Group`, `Key`, `MenuCount` and `Destroyed`. It does not expose the native button or menu handlers.

Selecting an icon in a nonempty group updates the group state before callbacks and sends the old selection's `Deselected` notification before the new selection's `Selected` notification. Listeners may change that state again. Programmatic selection does not send `Activated`.

Selection does not change the button's surface or glyph automatically. A feature can call `SetImage` from its selection callbacks, as the native backpack switches between its normal and filled glyphs. Programmatic activation and key bindings do not simulate hover or a held pointer.

`Activated`, `Selected` and `Deselected` are mSignal signals. Each sends the icon handle as its one payload. Accepted activation changes toggle/menu selection before sending `Activated`. With `Toggle = false` and no menu, activation sends `Activated` without changing selection. Hidden or disabled icons, or a hidden bar, reject activation. Observe selection signals to show and hide a feature panel; observe activation for button actions. Destroying an icon ends its owned UI and subscriptions without sending a final `Deselected` notification.

Key bindings are checked only while no native text field has focus. The first registered visible, enabled match wins within a bar. Keys are not consumed, so another feature or native control may also handle them.

## Dropdown menus

`icon.SetMenu(items)` supplies up to 16 flat menu items. Each item has `Text` (up to 64 characters), optional `Image` (up to 256 characters) and `Disabled` (false by default), and a `Run` function. The library copies the definitions. Replacing a menu deselects its icon and closes its dropdown; an empty array clears the menu. It does not provide nested menus or arbitrary UI content slots. Choosing an enabled item closes the dropdown, deselects the icon and invokes `Run(icon)`. Catchable handler failures are logged as warnings.

Replacing one icon's menu preserves an unrelated open menu, including a menu
selected by a Deselected listener during that replacement.

```truscript
icon.SetMenu([
    {
        Text = "Print status",
        Run = func():
            print("status requested")
    }
])
```

Menu handlers are trusted client code. Any resulting server action still requires the game's normal remote validation and permissions.

One popup is open per bar. Opening a different menu deselects the old menu owner, including across different groups; unrelated nonmenu selection is retained unless group rules deselect it. Disabled menu rows dim their text/image and cannot run. Menu rows animate their clear visual using the standalone button's scale and transparency rules. The outside-dismiss surface starts below the button row, leaving that row available for direct switching. Dropdown layout is a library addition, not a recovered native toolbar menu.

## Dock two icons

`bar.Dock(first, second)` requires two distinct, live icons from that bar, on the same side and not already docked. The pair shares a **96 x 48** glass background. Its fixed **44 x 48** hit areas sit at x4 and x48, giving centers x26 and x70 and a 4-unit outer inset. Their visuals are clear and use `UIPanelStyle.None` over the shared surface. Each icon keeps its activation, selection, menu and pointer state. Layout uses the first icon's order and their shared side.

| Call | Behavior |
| --- | --- |
| `dock.Destroy()` | Undocks the pair without destroying either icon. |
| `dock.IsDestroyed()` | Returns whether the dock has ended. |

Hiding one icon leaves a **52 x 48** single-item dock. The fixed hit area and glass background share a center, while the background and clear icon visual animate independently. This path uses standalone motion and has no hover highlight. Restoring the second icon returns to the 96-unit pair. Hiding the bar or removing the dock from the visible row cancels its motion and clears hover/highlight state.

Undocking restores each surviving button's standalone geometry and glass style. Destroying either icon also undocks the surviving one. To change an icon's side, destroy its dock first. A dock is a layout relationship, not a replacement icon or a new permission context.

Icon, dock and bar destruction each claim their cleanup once, including parallel
calls. Bar closure detaches its current registrations before draining them;
another task already cleaning an icon does not make that drain wait or repeat
its cleanup. Disposal releases owned references while in-flight internal work
uses captured native targets rather than rereading cleared slots.

## Pointer motion

The fixed button root captures input; its visual and contents animate around their center. The root does not scale with them.

| Path | Hover scale | Held inside scale | Held transparency | Duration and easing |
| --- | --- | --- | --- | --- |
| Standalone | 1.12 | 0.92 | 0 | 0.2 seconds, Back Out |
| Single-item dock | 1.12 | 0.92 | 0 | 0.2 seconds, Back Out; visual and background animate separately |
| Two-item dock | 1.15 | 0.9 | 0.25 | 0.2 seconds, Cubic Out; shared background remains at scale 1 |

Idle targets scale 1 and transparency 0. Disabled buttons target scale 1 and transparency 0.5 with their current path's easing. Disabling clears the held state and retains whether the pointer is inside. Reenabling while still inside therefore targets the hover scale. Native MenuUI removes or rebuilds core items instead of disabling a dock cell; the library's disabled dock behavior extends the shared button rules.

Pointer enter and exit refresh the animation. Only an enabled left mouse down starts the held state. Left mouse up or cancellation clears it, including outside the button; a parent change also clears it. Leaving while held targets idle without forgetting the press, so reentering before release targets the held scale. Releasing inside targets hover; releasing outside targets idle.

Each input refresh cancels the previous tween and starts a full-duration replacement from the current property values, even when the target is unchanged. Content repainting skips that restart when the target is unchanged. Completed callbacks affect only the tween still owned by their slot. Hiding and destroying controls cancel owned motion.

### Two-item highlight

A separate **52 x 52** glass highlight sits behind the pair. It starts hidden at scale 0.7 and transparency 1. The latest hovered cell is reconciled once per frame. An unchanged hovered identity does nothing, and crossing cells within one frame does not force an intervening hide.

| Transition | Position | Transparency | Scale |
| --- | --- | --- | --- |
| None to item | Place immediately at its center | To 0 in 0.15 seconds, Linear Out | To 1 in 0.2 seconds, Back Out |
| Item to none | Keep the current position | To 1 in 0.075 seconds, Linear Out | To 0.7 in 0.2 seconds, Back Out |
| Item A to B | To B's center in 0.2 seconds, Cubic Out | Unchanged | To 1.1 in 0.15 seconds, then to 1 in 0.15 seconds, both Back Out |

Fade, slide and scale use separate replacing tween slots. A fade completion hides the highlight only if no item is shown, and a pulse settles only if that item is still shown. Pressing a cell changes its visual, not the shared background or highlight. Changing the visible dock count resets the highlight and cancels the old motion.

## Layout and overflow

The default right inset of 218 reserves the historical 200-unit player-list width, a 10-unit edge margin and an 8-unit gap. The left inset reserves the built-in left controls. These are configurable layout choices, not live measurements of core UI.

Standalone buttons are 48 x 48, with an 8-unit gap between controls and radius 15. Dock geometry is described above. When no 48-unit slot fits between the reserved margins, the row moves down 56 units and uses 8-unit side margins; its default fallback top is 64. When more visible icons exist than fit, a `More` button opens a scrolling overflow list. Docked pairs enter overflow together. An overflow row activates the existing icon handle rather than creating another icon or bypassing its enabled state. `GetCount()` still includes overflow and hidden icons. Popups are clamped to the space left of the current right reservation.

Standalone visuals, dock backgrounds, dock highlights and dropdown panels use `new Color4(0.6, 0.6, 0.6)`, `UIPanelStyle.FrostedGlass` and radius 15. The button/dock construction values came from the embedded runtime HUD payload in Creator 2026.43.7 and use public UI APIs. They describe the constructor, not a flat rendered RGB value; glass appearance depends on the scene behind it.

There is no separate hover or selected outline. Edges drawn by FrostedGlass belong to the engine renderer. Numeric badges are custom 24 x 20 labels; native MenuUI uses small notification dots instead.

## Platform boundaries

mTopbar owns ordinary `ScreenUI` resources under `game.UICanvas`. Its insets reserve space chosen by the application; they are not a live measurement of the built-in toolbar. `ScreenUI.Priority` is reserved for core UI, and `DisplayOrder` cannot make game UI cover it. Device safe areas do not describe the occupied native toolbar region on desktop.

The native behavior target is the installed Creator 2026.43.7 script implementation. Matching its construction values, transitions and event rules does not establish identical intermediate pixels, native pointer scheduling, mobile touch routing or behavior on other versions. The engine still renders the public glass material. mTopbar does not call private core-script APIs, hide built-in controls or grant server authority. Programmatic contracts and manual input checks have separate scopes. See [testing](../testing.md) for recorded runs and remaining acceptance checks.
