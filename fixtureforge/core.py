"""Generate deterministic JSON fixtures from a supported schema subset."""
import hashlib
import json
import math
import random

class SchemaError(ValueError):
    pass

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)

def validate(schema, depth=0):
    if depth > 32 or not isinstance(schema, dict):
        raise SchemaError("invalid schema object or nesting depth")
    kind = schema.get("type")
    allowed = {
        "object": {"properties", "required", "additionalProperties"},
        "array": {"items", "minItems", "maxItems"},
        "string": {"minLength", "maxLength"},
        "integer": {"minimum", "maximum"},
        "number": {"minimum", "maximum"},
        "boolean": set(),
        "null": set(),
    }
    if not isinstance(kind, str) or kind not in allowed:
        raise SchemaError("unsupported or missing type")
    unknown = set(schema) - allowed[kind] - {"type", "enum", "const"}
    if unknown:
        raise SchemaError("unsupported schema keywords")
    if "properties" in schema:
        if not isinstance(schema["properties"], dict):
            raise SchemaError("properties must be an object")
        for name, child in schema["properties"].items():
            if not isinstance(name, str):
                raise SchemaError("property names must be strings")
            validate(child, depth + 1)
    if "required" in schema:
        required = schema["required"]
        if (not isinstance(required, list) or
            any(not isinstance(x, str) for x in required) or
            len(required) != len(set(required)) or
            any(x not in schema.get("properties", {}) for x in required)):
            raise SchemaError("required must list unique declared properties")
    if "additionalProperties" in schema and schema["additionalProperties"] is not False:
        raise SchemaError("only additionalProperties: false is supported")
    if "items" in schema:
        validate(schema["items"], depth + 1)
    for lo, hi in (("minItems", "maxItems"), ("minLength", "maxLength")):
        for key in (lo, hi):
            if key in schema and (type(schema[key]) is not int or not 0 <= schema[key] <= 1000):
                raise SchemaError(key + " must be an integer from 0 to 1000")
        if schema.get(lo, 0) > schema.get(hi, 1000):
            raise SchemaError(lo + " exceeds " + hi)
    for key in ("minimum", "maximum"):
        if key in schema:
            value = schema[key]
            if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
                raise SchemaError(key + " must be finite")
            if kind == "number" and type(value) is int and abs(value) > 10**308:
                raise SchemaError(key + " is outside supported floating-point range")
    if "minimum" in schema and "maximum" in schema and schema["minimum"] > schema["maximum"]:
        raise SchemaError("minimum exceeds maximum")
    if kind == "integer" and math.ceil(schema.get("minimum", 0)) > math.floor(schema.get("maximum", 100)):
        raise SchemaError("integer range is empty")
    if kind == "array" and "items" not in schema and schema.get("minItems", 0) > 0:
        raise SchemaError("nonempty array requires items")
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        raise SchemaError("enum must be a nonempty array")
    try:
        candidates = schema.get("enum", []) + ([schema["const"]] if "const" in schema else [])
        for item in candidates:
            canonical(item)
            if not matches(item, schema):
                raise SchemaError("enum or const violates schema")
        if "const" in schema and "enum" in schema and canonical(schema["const"]) not in {canonical(x) for x in schema["enum"]}:
            raise SchemaError("const is not in enum")
    except (TypeError, ValueError, OverflowError) as exc:
        if isinstance(exc, SchemaError):
            raise
        raise SchemaError("enum or const must contain JSON values") from None

def matches(value, schema):
    kind = schema["type"]
    if kind == "null": ok = value is None
    elif kind == "boolean": ok = type(value) is bool
    elif kind == "integer": ok = type(value) is int
    elif kind == "number": ok = type(value) in (int, float) and math.isfinite(value)
    elif kind == "string": ok = isinstance(value, str)
    elif kind == "array": ok = isinstance(value, list)
    else: ok = isinstance(value, dict)
    if not ok:
        return False
    if kind in ("integer", "number"):
        if value < schema.get("minimum", float("-inf")) or value > schema.get("maximum", float("inf")):
            return False
    if kind == "string" and not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 1000):
        return False
    if kind == "array":
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 1000):
            return False
        if "items" not in schema and value:
            return False
        if "items" in schema and any(not matches(x, schema["items"]) for x in value):
            return False
    if kind == "object":
        props = schema.get("properties", {})
        if any(x not in value for x in schema.get("required", [])):
            return False
        if schema.get("additionalProperties") is False and any(x not in props for x in value):
            return False
        if any(not matches(v, props[k]) for k, v in value.items() if k in props):
            return False
    return True

def make(schema, rng):
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return rng.choice(schema["enum"])
    kind = schema["type"]
    if kind == "null": return None
    if kind == "boolean": return bool(rng.getrandbits(1))
    if kind == "integer":
        return rng.randint(math.ceil(schema.get("minimum", 0)), math.floor(schema.get("maximum", 100)))
    if kind == "number":
        lo, hi = schema.get("minimum", 0), schema.get("maximum", 100)
        if lo > hi: raise SchemaError("number range is empty")
        if lo == hi:
            return lo
        weight = rng.random()
        result = (1.0 - weight) * lo + weight * hi
        return min(hi, max(lo, result))
    if kind == "string":
        low, high = schema.get("minLength", 0), schema.get("maxLength", 16)
        n = rng.randint(low, max(low, min(high, 32)))
        alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
        return "".join(rng.choice(alphabet) for _ in range(n))
    if kind == "array":
        if "items" not in schema:
            return []
        low, high = schema.get("minItems", 0), schema.get("maxItems", 3)
        n = rng.randint(low, max(low, min(high, 10)))
        if n and "items" not in schema:
            raise SchemaError("nonempty array requires items")
        return [make(schema["items"], rng) for _ in range(n)]
    return {name: make(child, rng) for name, child in sorted(schema.get("properties", {}).items())
            if name in schema.get("required", []) or rng.getrandbits(1)}

def generate(schema, seed=0, count=1):
    validate(schema)
    if type(seed) is not int or type(count) is not int or not 1 <= count <= 1000:
        raise SchemaError("seed must be an integer; count must be 1 to 1000")
    results = []
    for index in range(count):
        digest = hashlib.sha256(f"{seed}:{index}".encode()).digest()
        value = make(schema, random.Random(int.from_bytes(digest, "big")))
        if not matches(value, schema):
            raise SchemaError("generated value violates schema")
        results.append(value)
    return results
