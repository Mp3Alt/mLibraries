# mLibraries: Getting started with mSignal, mCleanup, and mAsync

[GitHub repository](https://github.com/Mp3Alt/mLibraries) | [Download 0.1.0-dev](https://github.com/Mp3Alt/mLibraries/releases/download/v0.1.0-dev/mLibraries-0.1.0-dev.zip)

I've put together **mLibraries**, a small set of TruScript modules for custom events, cleanup, and background tasks in TruWorlds.

Each module works on its own. You can use one without installing the others. The `m` prefix stands for Mp3.

This is version **0.1.0-dev**, tested with TruWorlds Creator **2026.43.7** and released under the MIT license.

| Module | What it does |
| --- | --- |
| mSignal | Custom events whose callbacks run in connection order. |
| mCleanup | Disconnects connections, destroys instances, and runs cleanup functions. |
| mAsync | Runs or delays tasks and lets them respond to cancellation. |

## Installation

Download the source package and create a folder named **mLibraries** in Creator's **Asset Browser**. Inside it, create three scripts and set each script's type to **Module**:

| Asset Browser path | Copy the source from |
| --- | --- |
| `mLibraries/mSignal` | `packages/mSignal/src/mSignal.trs` |
| `mLibraries/mCleanup` | `packages/mCleanup/src/mCleanup.trs` |
| `mLibraries/mAsync` | `packages/mAsync/src/mAsync.trs` |

Use the names exactly as shown. The source files have a `.trs` extension; the import paths below do not.

These paths belong to the Asset Browser, not the world's instance tree. Leave the Module scripts unattached and load them from another script with `import`:

```text
local mSignal = import("/mLibraries/mSignal")
local mCleanup = import("/mLibraries/mCleanup")
local mAsync = import("/mLibraries/mAsync")
```

The leading `/` makes the path absolute, so moving the script that imports them won't change which module it finds. Methods use dot syntax, such as `owner.Destroy()`.

To run the examples, create a **Server** script, attach it to a Folder inside **World**, and start a local playtest. The modules also work in Client scripts. Run the async examples during Play because the editor's one-shot commands cannot start background tasks or wait.

## mSignal: custom events

Use mSignal for notifications such as a changed score, a selected item, or a component finishing its work.

```text
local mSignal = import("/mLibraries/mSignal")
local scoreChanged = mSignal.New()

local connection = scoreChanged.Connect(func(update):
    print(update.Name + " has " + update.Score + " points")
)

local failures = scoreChanged.Fire({ Name = "Mp3", Score = 10 })
for problem in failures:
    warn(tostring(problem))

connection.Disconnect()
scoreChanged.Destroy()
```

`Connect` returns a connection you can disconnect separately. `Once` listens for the next fire only. `DisconnectAll` removes the current listeners so you can reuse the signal. `Destroy` closes it permanently.

Each fire sends one payload. Use a table for several values, as in the example. `nil`, `false`, and `0` are valid payloads too.

Callbacks run in connection order, in the task that called `Fire`. A callback that waits delays the rest of that fire, so keep handlers short. New listeners added by a callback join later fires. A one-shot listener is disconnected before its callback starts, including when that callback fires the signal again.

If a callback throws, `Fire` collects the error and continues with the other eligible listeners. It returns those errors in an array. Check the array, as shown above, because mSignal doesn't log them for you.

Signals stay local. Use TruWorlds' remote APIs to send messages between the server and players.

## mCleanup: keep teardown in one place

When a menu closes or a character component is removed, its connections and temporary objects need to go with it. Register that work with mCleanup, then clean it up with one call.

This example owns a signal and its connection:

```text
local mSignal = import("/mLibraries/mSignal")
local mCleanup = import("/mLibraries/mCleanup")

local owner = mCleanup.New()
local changed = mSignal.New()

owner.Add(changed.Destroy)

local connection = changed.Connect(func(value):
    print("Changed to " + value)
)
owner.AddConnection(connection)

local fireErrors = changed.Fire(42)
for problem in fireErrors:
    warn(tostring(problem))

local cleanupErrors = owner.Destroy()
for problem in cleanupErrors:
    warn(tostring(problem))
```

Cleanup runs in reverse registration order. This example disconnects the connection before destroying the signal. Register dependencies first and the things using them afterwards.

There are three registration methods:

- `Add(callback)` registers a function with no arguments.
- `AddConnection(connection)` calls its `Disconnect()` method during cleanup.
- `AddInstance(instance)` calls its `Destroy()` method during cleanup.

Use `Clean()` when the owner is resetting and will be reused. Use `Destroy()` when its lifetime ends. Repeated destruction is safe, and adding new work to a destroyed owner throws.

If a cleanup callback throws, the remaining callbacks still run. `Clean` and `Destroy` return the caught errors. Keep cleanup callbacks synchronous. They should not wait for other work to finish.

## mAsync: delayed and background work

mAsync gives each task a job handle so you can check whether it finished, failed, or was cancelled. Pass `nil` to `New` to use TruWorlds' native scheduler:

```text
local mAsync = import("/mLibraries/mAsync")
local tasks = mAsync.New(nil)

local announce = func(token, message):
    token.Checkpoint()
    print(message)
    return true

local job = tasks.Delay(1, announce, "Ready")

wait(1.1)
local result = job.GetOutcome()
print(result.Status)
```

`Delay` waits before starting the work. Waits can resume late, so this example may print `Pending` or `Running` instead of `Succeeded`. Waiting 1.1 seconds doesn't guarantee that the job has finished.

The scheduling methods are:

| Method | Behavior |
| --- | --- |
| `Run(work, payload)` | Schedules background work. |
| `Defer(work, payload)` | Yields once before starting work. |
| `Delay(seconds, work, payload)` | Waits before starting work. Seconds must be a finite, nonnegative number. |

Work receives `(token, payload)` and can return one result. `GetOutcome()` returns a record containing `Status`, `Value`, `Error`, and `CancellationRequested`.

The statuses are `Pending`, `Running`, `Succeeded`, `Failed`, and `Cancelled`. Check `Status` before reading the result. A successful job can return `0`, `false`, or `nil`.

### Cancellation

Cancel delayed work before it starts:

```text
local mAsync = import("/mLibraries/mAsync")
local tasks = mAsync.New(nil)

local announce = func(token, message):
    print(message)

local job = tasks.Delay(5, announce, "This was scheduled")
job.Cancel()
print(job.GetOutcome().Status)
```

If cancellation is accepted while the job is pending, its callback won't run. If the underlying coroutine is already waiting, it still has to wake up before it can exit.

Running work needs to cooperate. Put checkpoints where it is safe to stop:

```text
local mAsync = import("/mLibraries/mAsync")
local tasks = mAsync.New(nil)

local worker = func(token, interval):
    for step in range(20):
        token.Checkpoint()
        print("Step " + step)
        wait(interval)
    return "finished"

local job = tasks.Run(worker, 0.05)
wait(0.1)
job.Cancel()
```

`Checkpoint` stops cancelled work by throwing a private value that the job runner handles. Keep it outside catch blocks that would swallow that value. Work that ignores cancellation can still finish successfully. Anything it already changed stays changed.

### Reading a result

When a job has completed, inspect its outcome like this:

```text
local result = job.GetOutcome()

if result.Status == "Succeeded":
    print(result.Value)
elif result.Status == "Failed":
    warn(tostring(result.Error))
elif result.Status == "Cancelled":
    print("Cancelled")
else:
    print("Still working")
```

Use that snippet with a `job` from one of the earlier examples. It checks the current state without waiting for the job to finish.

## Current limitations

- mSignal runs callbacks synchronously and has no `Wait()` method. A slow or yielding handler delays its caller. A callback already claimed by another task may still run after disconnection.
- mCleanup only cleans up what you register. It doesn't find forgotten resources or deduplicate registrations. Adding work while cleanup is running is rejected.
- Cancellation in mAsync is cooperative. It cannot forcibly kill a callback or abort an arbitrary HTTP or data request.
- Cleanup is not guaranteed if the host forcibly stops a script. That includes suspended `finally` blocks.
- This release has no Promise chains, `all`/`race`, retries, timeouts, or `Await` method.
- These modules don't replicate their state or save it to persistent storage.

## Testing

The release passed the following on both a local server and client:

| Suite | Passed | Failed |
| --- | ---: | ---: |
| Contract tests | 52 | 0 |
| Native scheduling and integration checks | 9 | 0 |
| Concurrency checks | 4 | 0 |

The concurrency checks cover overlapping one-shot fires, repeated disconnects, registration during destruction, and overlapping cleanup operations. The tests and instructions are included in the download.

These results are from Creator 2026.43.7 on one desktop test environment. They don't cover every possible schedule or device. I haven't published comparative speed or long-running memory benchmarks yet.

## Feedback for the TruWorlds developers

A few requests came out of working on these modules:

**Optional type checking.** I'd like to describe callback parameters and table shapes in code. A cleanup connection needs `Disconnect()`, for example, and a job needs `Cancel()` and `GetOutcome()`. The compiler and API-name checks already catch problems with native calls. Checking our own module APIs could catch a missing method or wrong callback argument before the script runs.

**Classes, records, and interfaces.** The installed 2026.43.7 guide documents tables and closures for user-defined objects, with no script-level class declaration or inheritance. That's how these modules are built. A class or record definition could cut down the factory code and give the editor information about constructors, methods, and fields. Interfaces could describe things like a connection without requiring inheritance.

**Callback validation and member lookup.** A supported callable check would let a library reject a bad callback when it is registered. Safe member lookup could support generic cleanup adapters too. I used separate `AddConnection` and `AddInstance` methods so the code doesn't have to guess which method a resource needs. The existing [instance member access discussion](https://devboard.truworlds.com/t/truscript-allow-arbitrary-member-access-on-instances/104) covers part of this.

**Scheduling and cancellation.** Native cancellable timers and a documented defer boundary would let libraries do more with less wrapper code. mAsync currently uses `spawn` and `wait`. It can stop a pending callback from running, but it can't remove a coroutine that is already asleep. More examples of when tasks can interleave would also be valuable. The disconnect stress test caught a repeated-read problem that I fixed by capturing a stable listener entry.

**Library installation and updates.** I'd like a standard bundle format that keeps module paths, script types, versions, and dependencies intact. This release needs a source map and manual installation steps. A supported file-based workflow would make it simpler to review changes and update an installed library.

**Testing tools and documentation.** I used local server and client playtests to check these modules. A test runner that covers both and exports results would save time on repeated checks. The website and installed docs also need to agree on behavior. For example, the installed docs say `error()` logs and continues in attached scripts, while the [public globals reference](https://create.truworlds.com/docs/globals) says it stops execution. A version note would make that difference clearer.

## Feedback and updates

If you try these, let me know what worked, what was awkward, and what you'd use next. For bugs, please include your Creator version, a small reproduction, and the result you expected.

I'll keep this topic updated as the modules develop. The source is MIT licensed; include the license when distributing copies or substantial portions.
