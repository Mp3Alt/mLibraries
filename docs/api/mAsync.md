# mAsync

Original cooperative task helpers for mLibraries. This initial API wraps native scheduling; it does not implement Promise chains, forced coroutine cancellation, retries, or timeouts. Runtime verification is recorded separately from this API contract.

```truscript
local mAsync = import("/mLibraries/mAsync")
local tasks = mAsync.New(nil)

local onReady = func(token, payload):
    token.Checkpoint()
    print(payload.Message)
    return true

local job = tasks.Delay(2, onReady, { Message = "ready" })

job.Cancel()
local outcome = job.GetOutcome()
```

## Construction and scheduling

`mAsync.New(runtime)` returns an independent helper instance. Pass `nil` for the native adapter. Importing the module and constructing an instance start no background work.

| Method | Behavior |
| --- | --- |
| `Run(work, payload)` | Schedules `work(token, payload)` using the adapter's Spawn function. |
| `Defer(work, payload)` | Schedules a task that calls Wait(0) before starting work. |
| `Delay(seconds, work, payload)` | Schedules a task that calls Wait(seconds) before starting work. Seconds must be a finite, nonnegative number; numeric strings are rejected. |

Each method returns a Job. Work returns one value and may yield in a native script. Its result can be `nil`, `false`, or zero. A missing work function is rejected before scheduling; other non-callable values fail when invoked. No callback-start ordering is promised for Run: an injected dispatcher may start it immediately. Defer guarantees a wait boundary, not an exact frame or a deadline. Native waits can resume late.

## Jobs and cancellation

`job.GetOutcome()` returns a fresh record containing `Status`, `Value`, `Error`, and `CancellationRequested`. Status is `Pending`, `Running`, `Succeeded`, `Failed`, or `Cancelled`. Use the status to interpret Value and Error; either can legitimately be `nil`. Snapshot fields are independent, while referenced result/error objects remain the original values.

`job.Cancel()` returns true for the first accepted request and false for repeated requests or a settled job.

Outcome records are published together and captured once before reading their fields. Accepted cancellation publishes the request flag for running work; rejected late requests do not alter a completed record. Dispatch checks the cancellation claim before starting work, and captures the work/payload record once before releasing its control reference.

The lifecycle claim code follows the installed guide's single-statement completion model and uses simple local counters. Native stress previously exposed a repeated-read failure in mSignal despite that guide's broader wording. Stable captures avoid repeated mutable-slot reads, but the bounded tests do not certify every VM boundary or prove that an arbitrary expression is a transaction. User callbacks are not atomic.

- A pending request immediately settles as Cancelled and releases the queued work and payload references. Its callback will not run. A coroutine already inside Wait remains suspended until the native scheduler resumes it; this API cannot remove that shell from the engine.
- Once work is Running, cancellation sets the request flag. `token.IsCancellationRequested()` reads it, and `token.Checkpoint()` stops work by throwing a private per-job sentinel. The runner catches that sentinel and settles as Cancelled.
- Work that ignores the request, or catches the checkpoint sentinel itself and returns, can still succeed. A different thrown value settles as Failed even if cancellation was requested. Side effects already performed remain performed.
- An adapter Wait failure that arrives after pending cancellation cannot replace the terminal Cancelled outcome.

Work/payload control references are cleared at dispatch and settlement. A running callback necessarily retains its active arguments. Completed jobs retain their Value or Error for callers; release the Job when those results are no longer needed. Cancellation cannot force a native HTTP request, data operation, or arbitrary waiting callback to abort. Host script teardown is outside this contract and does not guarantee that suspended `finally` blocks run.

## Runtime adapter and tests

An injected runtime supplies two plain functions, called with dot syntax:

- `Spawn(task)`: accept and run the zero-argument task exactly once, immediately or later, or throw before accepting it.
- `Wait(seconds)`: suspend for the requested duration in production, or simulate that boundary in a deterministic test. Its return value is ignored.

Construction checks that both fields exist. TruScript lacks a general runtime type query, so callability errors surface when a field is invoked. A synchronous Spawn failure before dispatch becomes a Failed job. Wait and work errors are captured as their original thrown values, including `nil`.

The deterministic specification injects a queued dispatcher and a Wait hook. It checks state transitions, cancellation, falsy results, arbitrary thrown values, scheduling failures, immediate dispatch, and duplicate dispatch protection. It does not measure native timing or prove teardown behavior. Native Spawn/Wait tests require a playtest script: Creator's atomic `run_truscript` forbids waiting and background work.

The separate `RunConcurrent()` specification requires Play. It runs two bounded workloads with 128 native-backed jobs each: competing requests against held work, then completion readers and cancellation contenders against already running work. It observes native runner exit, matching terminal values, accepted-request flags and retained tokens after rejected late requests. Deterministic Wait hooks cannot force the VM's automatic yield between arbitrary statements, and these stress workloads sample schedules rather than certifying every race or VM boundary. Record the tested engine version with the results.
