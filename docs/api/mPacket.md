# mPacket

mPacket validates a fixed record schema and converts rows to a flat native array. It creates no remotes, connections or background work. It does not implement a native binary buffer.

```truscript
local mPacket = import("/mLibraries/mPacket")
local inventory = mPacket.New({
    Id = 7,
    Fields = [
        { Name = "ItemId", Type = "integer", Min = 0, Max = 65535 },
        { Name = "Quantity", Type = "integer", Min = 0, Max = 255 }
    ]
})

local encoded = inventory.Encode([
    { ItemId = 7, Quantity = 2 },
    { ItemId = 9, Quantity = 1 }
])
if encoded.Ok:
    local decoded = inventory.Decode(encoded.Value)
    if decoded.Ok:
        print(decoded.Value[0].ItemId)
```

The encoded value in this example is `[7, 1, 2, 7, 2, 9, 1]`: schema ID, version, row count, then each row's fields in schema order.

## API

Methods use dot calls. `New` returns a codec directly. `Encode` and `Decode` return `{ Ok = true, Value = ... }` or `{ Ok = false, Code = ..., Message = ... }`. Failed results do not expose partial output or raw caught exceptions. `Describe` returns a schema directly, without an `Ok` wrapper.

| Call | Result |
| --- | --- |
| `mPacket.New(config)` | A codec with a private compiled schema. Invalid schemas throw the fixed string `Invalid mPacket schema.` |
| `codec.Encode(records)` | A fresh flat native array after validating every row. |
| `codec.Decode(packet)` | A fresh array of canonical record tables after validating the header, shape and values. |
| `codec.Describe()` | A fresh `{ Id, Version, MaxRecords, MaxTextLength, Fields }` description, including defaults and copied field definitions. |

## Schema configuration

Only these configuration keys are accepted:

| Key | Rules |
| --- | --- |
| `Id` | Required integer from 1 through 65,535. |
| `Version` | Integer from 1 through 255; defaults to 1. |
| `MaxRecords` | Integer from 1 through 64; defaults to 64. An encoded batch may contain zero rows. |
| `MaxTextLength` | Integer from 0 through 4,096; defaults to 1,024. Limits the sum of string character counts across the whole packet. |
| `Fields` | Required array of 1 through 8 field definitions, in wire order. |

Field names are case-sensitive and unique within the schema. Each starts with an ASCII letter, followed by ASCII letters, digits or `_`, with a maximum length of 32 characters. Names are preserved rather than normalized.

| `Type` | Required field keys | Accepted values |
| --- | --- | --- |
| `integer` | `Name`, `Type`, `Min`, `Max` | Finite whole numbers within the inclusive bounds. Both bounds must also be finite whole numbers, with `Min <= Max`. |
| `number` | `Name`, `Type`, `Min`, `Max` | Finite numbers within the inclusive finite bounds, with `Min <= Max`. |
| `boolean` | `Name`, `Type` | Literal `true` or `false`. |
| `string` | `Name`, `Type`, `MaxLength` | Strings with at most `MaxLength` characters. The limit is an integer from 1 through 256. Empty strings are allowed. |

Unknown configuration or field-definition keys are rejected. `Min` and `Max` are required for numeric fields, and are not allowed on boolean or string fields. `MaxLength` belongs only to strings. A zero total text budget permits empty strings but rejects nonempty string content.

Numeric ranges are logical validation rules. Choosing an integer range of 0..255 does not make the engine transmit that value as one physical byte. No quantization or numeric coercion is performed. Strict whole-number checks do not rely on TruScript's tolerant numeric equality.

## Packet format and validation

The wire value is an ordinary native array:

```text
[Id, Version, record_count, row0_field0, row0_field1, ..., row1_field0, ...]
```

Its exact length is `3 + record_count * field_count`, at most 515 elements. Header values must be whole numbers and obey their bounds before the ID and version are matched. Missing values, trailing values, nested values, wrong types and out-of-range fields fail. Rows supplied to Encode must contain exactly the declared fields; missing and extra keys fail.

Schema ID and version are compatibility checks. They are not secrets, identities or authorization. Two independently constructed codecs should use a consistent definition of the ID, version, field order, types and bounds. The header carries no field names or schema hash, so reusing an ID/version for a different field order can reinterpret otherwise valid values. Changing a field or its order requires an explicit compatibility decision, normally a new version or ID; the codec does not migrate old packets.

`MaxTextLength` and string `MaxLength` use native character counts. They are not UTF-8 byte counts or engine-wire budgets. The engine's own message limits still apply when the array is sent through a remote.

Failure codes are `InvalidRecords`, `InvalidRecord`, `InvalidValue`, `TextLimit`, `InvalidPacket` and `SchemaMismatch`. Check `Ok` before reading `Value`; do not infer success from the truthiness of a field value.

## Ownership and integration

New copies the schema into private compiled data. Later changes to the original config or a Describe result do not edit that schema. Encode and Decode return fresh containers containing the allowed primitive values; the codec does not retain a history of caller packets or records.

Keep config, records and packets stable while the relevant call reads them. Copying the schema does not establish an atomic snapshot of concurrently changing caller-owned data. A successful decode establishes the declared structure and ranges, not the truth of a client's request.

Use an engine-created remote and the engine-supplied sender. Authenticate and charge a server-owned request budget before Decode, then enforce game rules before acting. The [native remote guide](../mPacket.md) shows the ordering. mPacket itself supplies no permissions, rate limiting, routing, retries or arbitrary-object serialization.

## Performance scope

mPacket uses flat native arrays, not a binary buffer. Its checks and copying
add work; a smaller number of array fields does not establish smaller wire
payloads or lower memory use. Benchmark the actual public API and the native
transport with the records your game sends.

The included specification checks valid schemas and packets, malformed values,
bounds and copied output. Native fixtures exercise concurrency and remote
integration separately. See [testing](../testing.md) and the
[verification record](../verification/libraries-0.12.2.md) for scope.
