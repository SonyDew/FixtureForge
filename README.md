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

## Development report — afternoon, November 5, 2026

Reviewed the published generator, CLI, tests, and package metadata. Corrected two edge cases: arrays without an `items` schema now generate empty arrays rather than failing randomly, and wide floating-point ranges use weighted interpolation to avoid overflow in `maximum - minimum`. Added six regression tests covering these cases, nested unsupported keywords, unchanged input schemas, and CLI error output.

The numeric interpolation was checked separately with 100 generated values between -1e308 and 1e308 on the available Python runtime. The full repository test suite and installed CLI were not executed in this review because a working local checkout was unavailable. The six new tests are committed but not yet verified by a full test run. Status remains In Development.

Known limitations: this tool implements only the documented schema subset; it is not a JSON Schema validator. Large or deeply nested output can consume substantial memory, and seed reproducibility is tied to this implementation. Before marking the MVP complete, run `python -m unittest discover -s tests -v` and test the installed command from a clean environment.
