"""Count-scoped binding snapshots preserve and recheck file identities."""

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forex_demo_lab.trendline import data


class CountBindingTests(unittest.TestCase):
    def test_binding_maps_are_defensive_and_refresh_at_scope_exit(self):
        reads = []

        @data.cached_bindings
        def record():
            reads.append("read")
            return {"source": "value"}

        with data.replay_bindings():
            record().clear()
            with data.replay_bindings():
                self.assertEqual({"source": "value"}, record())
            self.assertEqual(["read"], reads)
        self.assertEqual(["read", "read"], reads)
        record()
        self.assertEqual(["read", "read", "read"], reads)

    def test_changed_file_rejects_the_count_and_next_scope_uses_fresh_bytes(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.write_bytes(b"first")

            @data.cached_bindings
            def record():
                return {"source": hashlib.sha256(source.read_bytes()).hexdigest()}

            with self.assertRaisesRegex(ValueError, "source bindings changed"):
                with data.replay_bindings():
                    before = record()
                    source.write_bytes(b"changed")
                    self.assertEqual(before, record())
            with data.replay_bindings():
                self.assertNotEqual(before, record())
