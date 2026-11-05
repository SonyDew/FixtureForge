import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from fixtureforge import SchemaError, generate

class FixtureTests(unittest.TestCase):
    def test_deterministic(self):
        schema = {"type": "array", "items": {"type": "integer", "minimum": 2, "maximum": 5}, "minItems": 3, "maxItems": 3}
        self.assertEqual(generate(schema, 5, 4), generate(schema, 5, 4))
        self.assertEqual(generate(schema, 5, 1), generate(schema, 5, 4)[:1])
    def test_seeds_differ(self):
        schema = {"type": "string", "minLength": 20, "maxLength": 20}
        self.assertNotEqual(generate(schema, 1), generate(schema, 2))
    def test_required(self):
        schema = {"type": "object", "required": ["id"], "properties": {"id": {"type": "integer", "minimum": 1, "maximum": 1}}}
        self.assertEqual(generate(schema), [{"id": 1}])
    def test_enum(self):
        schema = {"type": "string", "enum": ["red", "blue"]}
        self.assertTrue(all(x in ("red", "blue") for x in generate(schema, 1, 30)))
    def test_const(self):
        self.assertEqual(generate({"type": "null", "const": None}), [None])
    def test_unknown_keyword(self):
        with self.assertRaises(SchemaError):
            generate({"type": "string", "pattern": "x"})
    def test_bad_range(self):
        with self.assertRaises(SchemaError):
            generate({"type": "integer", "minimum": 2, "maximum": 1})
    def test_missing_required_property(self):
        with self.assertRaises(SchemaError):
            generate({"type": "object", "required": ["x"]})
    def test_invalid_enum(self):
        with self.assertRaises(SchemaError):
            generate({"type": "integer", "enum": ["no"]})
    def test_count(self):
        for count in (0, 1001, 1.5, True):
            with self.subTest(count=count), self.assertRaises(SchemaError):
                generate({"type": "null"}, count=count)
    def test_cli_does_not_modify_schema(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "schema.json"
            original = '{"type":"boolean"}'
            path.write_text(original)
            result = subprocess.run([sys.executable, "-m", "fixtureforge", str(path), "--count", "3"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)), 3)
            self.assertEqual(path.read_text(), original)
    def test_cli_rejects_unsupported(self):
        result = subprocess.run([sys.executable, "-m", "fixtureforge", "-"], input='{"type":"string","format":"email"}', capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("email", result.stderr)


    def test_array_without_items_is_empty(self):
        self.assertEqual(generate({"type": "array"}, seed=3, count=50), [[]] * 50)

    def test_nonempty_array_without_items_rejected(self):
        with self.assertRaises(SchemaError):
            generate({"type": "array", "minItems": 1})

    def test_wide_number_range_stays_finite(self):
        schema = {"type": "number", "minimum": -1e308, "maximum": 1e308}
        import math
        values = generate(schema, seed=17, count=100)
        self.assertTrue(all(math.isfinite(value) and -1e308 <= value <= 1e308 for value in values))

    def test_nested_invalid_schema_rejected(self):
        with self.assertRaises(SchemaError):
            generate({"type": "object", "properties": {"nested": {"type": "string", "pattern": "x"}}})

    def test_input_is_not_mutated(self):
        schema = {"type": "object", "required": ["x"], "properties": {"x": {"type": "array", "items": {"type": "boolean"}}}}
        before = json.dumps(schema, sort_keys=True)
        generate(schema, seed=1, count=5)
        self.assertEqual(json.dumps(schema, sort_keys=True), before)

    def test_cli_invalid_json_does_not_echo_input(self):
        secret = "private_value_123"
        result = subprocess.run([sys.executable, "-m", "fixtureforge", "-"], input='{"type":"string","const":"' + secret, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(secret, result.stderr)
        self.assertFalse(result.stdout)

if __name__ == "__main__":
    unittest.main()
