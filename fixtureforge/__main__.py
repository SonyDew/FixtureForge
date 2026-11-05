import argparse
import json
import sys
from .core import SchemaError, generate

def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate deterministic JSON fixtures from a limited JSON Schema subset.")
    parser.add_argument("schema", help="JSON Schema file, or - for stdin")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--count", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        if args.schema == "-":
            schema = json.load(sys.stdin)
        else:
            with open(args.schema, encoding="utf-8") as source:
                schema = json.load(source)
        values = generate(schema, args.seed, args.count)
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaError, OverflowError, ValueError) as exc:
        message = "invalid input or unsupported schema"
        print("fixtureforge: " + message, file=sys.stderr)
        return 2
    print(json.dumps(values, ensure_ascii=False, indent=2, allow_nan=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
