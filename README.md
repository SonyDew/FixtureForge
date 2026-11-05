# FixtureForge

**SonyDev GitHub Marathon — Day 10 (November 5, 2026). Status: In Development.**

FixtureForge generates deterministic JSON fixtures from a restricted JSON Schema subset. It uses the Python standard library, does not access the network, and does not modify input files.

## Run

```sh
python -m pip install .
fixtureforge examples/user.schema.json --seed 42 --count 3
python -m fixtureforge examples/user.schema.json --seed 42 --count 3
python -m unittest discover -s tests -v
```

The CLI writes a JSON array, even for one fixture. Pass `-` as the schema path to read standard input. Exit status is 0 for success and 2 for invalid input.

## Supported schema subset

Every schema object must declare one type: `object`, `array`, `string`, `integer`, `number`, `boolean`, or `null`. Supported keywords: `properties`, `required`, `additionalProperties: false`, `items`, `enum`, `const`, `minimum`, `maximum`, `minLength`, `maxLength`, `minItems`, and `maxItems`, where applicable. Unknown keywords are rejected. Numeric bounds are inclusive. Optional object properties may be omitted.

This is not a general JSON Schema implementation. It does not support `$ref`, `pattern`, `format`, `oneOf`, type arrays, or semantic constraints. Strings use lowercase ASCII letters and digits. Arrays without `items` can only be generated when empty. Schema depth is limited to 32, fixture count to 1,000, and string and array length bounds to 1,000. Seeds are reproducible within the implementation; cross-language output compatibility is not guaranteed.

## Development report — morning, November 5, 2026

The initial implementation includes deterministic per-index random streams, schema checks, CLI, examples, and standard-library tests. A local prototype passed 12 tests on Linux with Python 3.13, and an offline wheel build succeeded. The published GitHub version has not yet been independently executed as a checkout; full regression testing and boundary review remain for the evening.
