# Using mTopbar

mTopbar gives client features a shared row of buttons beside the built-in controls. Its button and dock motion follow the script behavior recovered from Creator 2026.43.7. Icons can toggle a panel, show a numeric badge or open a small dropdown. Badges, dropdowns and overflow are library features rather than copies of native toolbar features.

## Install

Create these **Module** scripts in Creator's Asset Browser and copy in their source. Leave them unattached. Asset paths omit `.trs` and are separate from the instance tree.

| Asset Browser path | Source |
| --- | --- |
| `mLibraries/mSignal` | [mSignal.trs](../packages/mSignal/src/mSignal.trs) |
| `mLibraries/mCleanup` | [mCleanup.trs](../packages/mCleanup/src/mCleanup.trs) |
| `mLibraries/mTopbar` | [mTopbar.trs](../packages/mTopbar/src/mTopbar.trs) |

Call mTopbar from a **Client** entry script attached to your feature's runtime instance. Importing a module asset and attaching a Client script are separate steps.

## Add a button

This example adds an Inventory button to the shared default row. Use a short fallback label for the 48-unit button. `Tooltip` supplies its full name in the overflow list; hovering does not open a tooltip. Use the selection events to show or hide your inventory panel.

```truscript
local mTopbar = import("/mLibraries/mTopbar")
local icon = mTopbar.GetDefault().Add({
    Name = "Inventory",
    Label = "I",
    Tooltip = "Open inventory",
    Group = "panels"
})

icon.Selected.Connect(func(selected):
    print("inventory opened")
)
icon.Deselected.Connect(func(deselected):
    print("inventory closed")
)
```

Use a unique name for each feature. Calls to `GetDefault()` share one bar; they do not create another row each time. The default bar destroys itself when its last icon is removed. A later feature can request the default bar again.

Only overlapping first construction can make `GetDefault()` yield while another caller creates the bar. Use attached Client scripts. Add/Dock registration contention throws, so callers that intentionally overlap those operations may retry.

Icons in the same nonempty group select exclusively. Selecting the next icon deselects the previous one first. Set `Toggle = false` for an action button rather than a persistent selection. Hiding or disabling an icon also deselects it. Selection itself adds no stroke or background change. A feature can change its image from a selection callback, as the native backpack does.

## Give the feature ownership

Destroy the icon when the feature ends:

```truscript
icon.Destroy()
```

If the feature already has an mCleanup owner, register the icon's destroy function when creating it:

```truscript
owner.Add(icon.Destroy)
```

The feature owns its icon, not the whole shared bar. Calling `bar.Destroy()` would also remove other features' icons. Keep the feature's own native connections and panel resources under its cleanup owner as well. Stop and restart Play after editing attached scripts; hot replacement is not a guaranteed cleanup path.

## Images and menus

Set `Image` to a valid uploaded TruWorlds image asset ID. A PNG disk path is not an asset ID. `ImageSize` defaults to 28 and accepts 8-40; `icon.SetImageSize(size)` changes it later. The image is centered, and an empty `Image` shows the fallback label instead.

Set `ImageSize` to suit the padding in your uploaded image. The feature that adds
an icon owns that handle and should destroy it when the feature closes.

An icon can also have a flat dropdown of up to 16 items:

```truscript
local actions = mTopbar.GetDefault().Add({
    Name = "QuickActions",
    Label = "A",
    Tooltip = "Quick actions"
})
actions.SetMenu([
    {
        Text = "Print status",
        Run = func():
            print("status requested")
    }
])
```

Choosing an enabled row closes the dropdown, deselects the icon and runs its client handler with the icon handle. Definitions are copied, and `GetState().MenuCount` reports the number of menu items. Pass an empty array to clear a menu. A menu handler does not acquire server permissions.

Opening another menu closes and deselects the previous menu owner. Disabled rows are visibly dim and cannot run. The popup's dismiss surface leaves the button row available, so a different icon can be selected directly.

Changing a badge, fallback label or image size repaints that icon without running layout or rebuilding an open menu's rows. Selection stays intact. Placement and visibility changes still update layout.

## Positioning and limits

The default insets are left **168**, right **218** and top **8**. The right margin reserves a 200-unit player list, its 10-unit edge margin and an 8-unit gap. These are application-chosen margins beside the native controls; no supported API was found that reports the native toolbar's occupied rectangle. Use `bar.SetInsets(left, right, top)` when a project's layout needs different margins. A separate bar can be created with `mTopbar.New(...)`; its `AutoDestroy` option defaults to false.

When no 48-unit button fits between the reserved margins, the row moves below the native row. If there are more visible icons than available slots, a `More` button opens a scrolling overflow list. Choosing an overflow entry activates the same icon. The feature still owns and destroys that one handle.

Standalone buttons are 48 x 48 with an 8-unit gap between controls. Their visual panel uses radius 15, `new Color4(0.6, 0.6, 0.6)` and the public `UIPanelStyle.FrostedGlass` style. Dock backgrounds and dropdown panels use the same glass construction. Glass blends with the scene, so the constructor color is not its final on-screen RGB value.

## Button motion

The hit area stays fixed while the visual panel and its contents animate. A standalone button targets scale **1.12** on hover, **0.92** while held inside and **1** outside. These transitions use **0.2-second Back Out** tweens. Disabling clears the held state and targets scale 1 with transparency 0.5.

Leaving while holding returns toward scale 1. Reentering before releasing returns toward the held scale. Releasing inside returns toward the hover scale; releasing or cancelling outside returns toward 1. Right and middle mouse buttons do not start the held animation. Reenabling an icon that is still hovered returns toward its hover scale.

Each handled pointer transition replaces the current tween with a full-duration transition from the current values. Changing an image, label, badge or selection does not restart that motion. Programmatic activation and key bindings do not simulate a pointer press. There is no custom hover or selected outline.

## Dock two buttons

Use a dock when two controls should sit together without the usual gap:

```truscript
local bar = mTopbar.GetDefault()
local inventory = bar.Add({ Name = "InventoryPair", Label = "I", Tooltip = "Inventory" })
local shop = bar.Add({ Name = "ShopPair", Label = "S", Tooltip = "Shop" })
local dock = bar.Dock(inventory, shop)
```

The pair shares a **96 x 48** glass background. Each fixed hit area is **44 x 48**, with a 4-unit inset at either end. Both icons must belong to this bar, share a side and be free of another dock. The first icon supplies the pair's layout order. Each icon keeps its activation, selection and menu.

The clear item visuals target scale **1.15** on hover and **0.9** while held, with held transparency **0.25**. These transitions use **0.2-second Cubic Out** tweens. The shared background stays at scale 1. A separate **52 x 52** glass highlight follows the latest hovered cell once per frame, so crossing between the two cells within one frame slides it without an intervening fade.

The highlight starts hidden at scale 0.7. Entering targets transparency 0 with a 0.15-second Linear Out fade and scale 1 with a 0.2-second Back Out tween. Leaving fades it out in 0.075 seconds and scales it back to 0.7 in 0.2 seconds. Crossing cells slides it in 0.2 seconds with Cubic Out and pulses its scale to 1.1, then back to 1, over two 0.15-second Back Out tweens.

Hiding either icon leaves a **52 x 48** single-item dock. Its background and icon visual independently use the standalone hover and press motion around the same center; the fixed hit area does not scale. The two-item highlight is hidden on this path. Hiding both items or the whole bar clears dock motion and hover state. Destroying one icon undocks the survivor.

Call `dock.Destroy()` to separate the icons without deleting them and restore their individual glass surfaces. Undock before calling either icon's `SetSide`, which throws while docked. The feature remains responsible for destroying its icons when it ends.

## Verification and limits

The motion targets, event handling and timing target the installed
**Creator 2026.43.7** HUD. See [testing](testing.md) and the
[verification record](verification/libraries-0.12.2.md) for the local scope.

Matching script values does not prove every intermediate rendered pixel, pointer scheduling, touch behavior or behavior on later versions. Glass rendering remains the engine's responsibility. Numeric badges and dropdowns are custom additions. Native MenuUI uses small notification dots, and it removes or rebuilds core items rather than disabling an individual dock cell. The library's disabled dock behavior is an extension of the shared button rules.

This is not a stable extension of protected core UI or a promise of compatibility with another platform's topbar libraries. It does not hide native controls or change server authorization. Application permissions must still be checked on the server.

One bar accepts at most 64 icons. Names and labels are limited to 64 characters, `Tooltip` metadata to 128, image IDs to 256, and badges to integers from 0 to 9,999. See the [API reference](api/mTopbar.md) for options and methods.

For a new project or engine version, repeat layout, physical input and feature-lifetime checks. Physical devices, keyboard/gamepad paths, long sessions and fresh concurrent first construction of the default bar need their own verification. Script-level matching is not a performance measurement or a promise of identical behavior on every device.
