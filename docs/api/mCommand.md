# mCommand

mCommand parses bounded command text and dispatches registered handlers after authorization. It has no engine, networking, player lookup or storage dependency.

```truscript
local mCommand = import("/mLibraries/mCommand")
local commands = mCommand.New()

local double = func(context, args):
    return args.amount * 2

local registered = commands.Register({
    Name = "double",
    Aliases = ["twice"],
    Description = "Double a number",
    Arguments = [{ Name = "amount", Type = "number" }],
    Run = double
})

# Local example only. A server framework must supply its own trusted policy.
local context = { Authorize = expr(description): true }
local result = commands.Execute(context, "twice 0")
if result.Ok:
    print(result.Value)
else:
    print(result.Code, result.Message)
```

## API

Registry methods return `{ Ok = true, Value = ... }` or `{ Ok = false, Code = ..., Message = ... }`. Check `Ok`; a successful handler can return `nil`, `false` or zero. Caught authorization and handler exceptions produce fixed messages, without raw errors or stack traces.

| Call | Successful Value |
| --- | --- |
| `mCommand.New()` | A new registry. This constructor returns the registry directly. |
| `commands.Register(definition)` | A description of the registered command. |
| `commands.Parse(text)` | `{ Name = normalized_name, Tokens = [...] }`, with argument strings only in Tokens. Parsing does not require registration. |
| `commands.Execute(context, text)` | The handler's one return value. |
| `commands.Describe()` | Command descriptions in registration order. |

A definition has `Name`, optional `Aliases`, optional `Description`, optional `Arguments`, and `Run(context, args)`. Unknown definition fields are rejected. Aliases and Arguments must be arrays; omitted values become empty arrays. Each argument has only `Name` and `Type`. All arguments are required.

Names and argument names start with an ASCII letter, followed by ASCII letters, digits, `_` or `-`, up to 32 characters. They are normalized to lowercase. Canonical names and aliases share one namespace; duplicates, including case variants within a definition, are rejected.

Argument types are exactly `string`, `number` and `boolean`. Handlers receive a fresh table keyed by normalized argument name. Number tokens use signed decimal or exponent notation and must convert to a finite number; hexadecimal, grouping separators, NaN and infinity are rejected. Boolean tokens accept ASCII `true` or `false`, ignoring case. Strings remain text, including empty quoted strings.

Registration copies aliases, argument definitions and description metadata. Register, Parse and Describe return fresh records and arrays. Authorization receives its own copied description with no Run function. Mutating those values cannot change the registry. Handler functions, trusted context and arbitrary handler results retain ordinary reference-value behavior; results are not retained by the registry or deep-cloned.

## Text format and limits

- Input is limited to 512 characters as reported by native `string.length`, with at most 16 total tokens: the command and up to 15 arguments.
- ASCII spaces and tabs separate tokens. Double quotes surround a whole token and preserve whitespace; `""` is an empty token. A closing quote must be followed by whitespace or the end of the input.
- Inside quotes, `\"` becomes a quote and `\\` becomes one backslash. Other escapes are rejected. Quotes and backslashes inside an unquoted token are rejected.
- Semicolons, line breaks and other control characters except separator tabs are rejected, including inside quotes. Unquoted `&` and `|` are rejected. Quoted `&` and `|` are ordinary data.
- Prefixes belong to the caller. Supply `help`, rather than `/help`, `:help` or `;help`. The parser has no expression evaluation, command chaining or script execution.
- A registry holds at most 64 commands. A command has at most eight aliases, 15 argument definitions and a 160-character description.

## Authorization and failures

Execute parses the text, finds the registered command, then calls `context.Authorize(description)`. Only literal `true` permits dispatch. A missing policy denies access; an exception or non-callable policy returns AuthorizationFailed. Authorization happens before argument conversion and handler invocation. No custom argument resolver is part of this API.

The context must be constructed by trusted server code when used for privileged commands. Never accept a context or authorization decision from a client. mCommand does not authenticate actors, impose rate limits, define roles or protect a server by itself. A command that yields before changing privileged state must recheck current permissions through its host framework immediately before the change.

Invalid definitions and inputs return structured failures rather than partial registration. A non-nil handler is retained without invoking it during registration; a non-callable handler becomes CommandFailed only if authorized dispatch reaches it. Handlers can log private diagnostics before throwing; raw caught exceptions are intentionally omitted from public results.

Failure codes are `InvalidDefinition`, `RegistrationBusy`, `RegistryFull`, `DuplicateName`, `InvalidInput`, `EmptyInput`, `InvalidSyntax`, `TooManyTokens`, `UnknownCommand`, `Unauthorized`, `AuthorizationFailed`, `ArgumentCount`, `InvalidArgument` and `CommandFailed`.

Register commands during trusted startup. Overlapping registration is rejected with RegistrationBusy; it does not wait or retry. Published command records are private and are never edited in place. The registry has no removal or Destroy method; release it when its owner ends. This contract does not make user policies or handlers atomic.

The specification's `Run()` covers parser boundaries, quoting, hostile text as data, malformed records, copied metadata, collisions, limits, authorization order, typed conversion and generic failures. Its separate `RunConcurrent()` requires a native playtest script. It exercises competing registrations with alias observation and yielding authorization while metadata and registration activity overlap. These bounded workloads sample interleavings. Runtime verification is recorded separately; the module makes no performance or security-certification claim.
