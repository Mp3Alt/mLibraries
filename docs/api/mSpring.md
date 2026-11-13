# mSpring

mSpring advances a damped spring only when you call Step. It supports a number, Vector2 or Vector3 and keeps that type for the spring's lifetime. It creates no tasks, frame connections, tweens or engine instances.

~~~truscript
local spring = import("/mLibraries/mSpring").New(0, { Frequency = 4, Damping = 1 })
spring.SetTarget(10)
local value = spring.Step(1 / 60)
~~~

| Method | Contract |
| --- | --- |
| New(initial, options) | Returns a spring. Pass nil for default options. |
| SetTarget(value) | Changes the target without advancing time or replacing velocity. |
| Step(dt) | Advances by finite seconds from 0 through 60 and returns the current value. Zero leaves it unchanged. |
| Impulse(deltaVelocity) | Adds velocity in units per second. |
| Snap() | Sets value to target and velocity to zero. |
| Reset(value) | Sets value and target to value, with zero velocity. |
| GetValue(), GetVelocity(), GetTarget() | Return the current typed value. Vector results are fresh host values. |
| IsResting() | True when every position-error and velocity component meets its tolerance. |

Use dot calls. Setters return nil. Invalid configuration, wrong types, nonfinite values, out-of-range time and computed overflow throw static messages before state publication. Concurrent mutations are rejected as busy instead of queued; getters capture one published state. This is not forced cancellation or a general VM transaction guarantee.

Only these options are accepted:

| Option | Default | Bounds |
| --- | ---: | --- |
| Frequency | 4 | 0.001 through 60 cycles per second |
| Damping | 1 | 0 through 4; zero oscillates without decay, one is critical damping |
| PositionTolerance | 0.0001 | 0 through 1,000,000, in value units |
| VelocityTolerance | 0.0001 | 0 through 1,000,000, in units per second |

Options are copied. Finite inputs must have the original spring type; numeric strings, booleans, forged vector tables and mixed vector dimensions are rejected. Vector validation calls a trusted native Dot method, not a method supplied by the input. Components are copied and calculated separately.

Step uses the closed-form solution of y'' + 2*damping*omega*y' + omega^2*y = 0, where y is value minus target and omega is 2*pi*Frequency. Underdamped, critical and overdamped cases are handled separately. Small-angle series avoid cancellation near critical damping; stable negative roots avoid exponential overflow in the overdamped case. The method is subject to floating-point and host-vector precision.

After a positive step, meeting both tolerances snaps exactly to target with zero velocity. This uses component-wise absolute error, not Euclidean vector length. Set both tolerances to zero when measuring unsnapped numerical behavior. A new target does not itself snap or advance.

The 60-second dt limit is a library input bound, not an engine timing limit. No elapsed time is silently dropped or clamped. Retarget between steps when the target changes. Moving the target during one step is outside this model.

The specification includes independent fixed scalar references generated with SciPy 1.18.1 matrix exponentials, including both sides of critical damping, undamped motion and a large overdamped step. See [SciPy expm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html). This is numeric/API coverage, not a frame-loop, device or concurrency benchmark. See [testing](../testing.md) and the [verification record](../verification/libraries-0.12.2.md); no frame-rate, allocation or speed claim is made.
