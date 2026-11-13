# Using mSpring

Create a spring for a value you own, retarget it when that target changes, and pass an explicit elapsed time to Step. Apply the returned value to your UI or game object in the same owning task.

~~~truscript
local mSpring = import("/mLibraries/mSpring")
local spring = mSpring.New(new Vector2(), { Frequency = 3, Damping = 0.8 })
spring.SetTarget(new Vector2(120, 40))

# From your existing update callback, using its elapsed seconds:
local position = spring.Step(1 / 60)
~~~

The example's fixed time is illustrative. Use measured elapsed time from the update loop you already own. mSpring does not create another loop or manage that connection for you.

A higher frequency responds more quickly. Damping below one can overshoot; one approaches without oscillating; above one moves more slowly without oscillation. Zero damping keeps oscillating. These descriptions concern the mathematical model, not a performance guarantee.

Impulse changes velocity rather than the target. Snap finishes at the current target immediately. Reset starts again at a supplied value and also moves the target there. A spring initially has zero velocity and its target equals its initial value.

Keep one owner for updates. A concurrent mutation throws a busy error; it is not retried automatically. Invalid input or overflow leaves the last published state intact. Keep input vectors stable while a call reads them.

The [API reference](api/mSpring.md) defines bounds, tolerances and numeric limits. Native vectors use their host component precision. No native buffer, easing/tween alias, background scheduler or engine instance is created.

The specification checks numeric references, supported types and rejected inputs. See [testing](testing.md) and the [verification record](verification/libraries-0.12.2.md) for the recorded scope. Numeric contracts do not establish visual, frame-loop, physical-device or concurrent-mutation behavior.
