import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tavryn import Runtime, TavrynError, parse  # noqa: E402


class TavrynTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "inbox").mkdir()
        (self.root / "drafts").mkdir()
        (self.root / "inbox" / "message.txt").write_text("hello", encoding="utf-8")

    def runtime(self, source, read=None, write=None, audit=None):
        return Runtime(parse(source), self.root,
                       {"read": read or [], "write": write or []}, audit)

    def test_allowed_read_and_write(self):
        source = '''needs read "inbox/*.txt"
needs write "drafts/*.txt"
let content = read("inbox/message.txt")
write("drafts/reply.txt", "Reply: " + content)
say(2 + 3)
'''
        runtime = self.runtime(source, ["inbox/*.txt"], ["drafts/*.txt"])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            runtime.run()
        self.assertEqual(output.getvalue(), "5\n")
        self.assertEqual((self.root / "drafts" / "reply.txt").read_text(), "Reply: hello")
        self.assertEqual([event["decision"] for event in runtime.events], ["allow", "allow"])

    def test_source_declaration_does_not_grant_access(self):
        runtime = self.runtime('needs write "drafts/*.txt"\nwrite("drafts/x.txt", "x")')
        with self.assertRaisesRegex(TavrynError, "not granted by host"):
            runtime.run()
        self.assertFalse((self.root / "drafts" / "x.txt").exists())
        self.assertEqual(runtime.events[0]["decision"], "deny")

    def test_host_grant_does_not_expand_source_declaration(self):
        runtime = self.runtime('needs read "inbox/*.txt"\nlet p = "drafts/x.txt"\nlet x = read(p)',
                               read=["drafts/*.txt"])
        with self.assertRaisesRegex(TavrynError, "not declared"):
            runtime.run()

    def test_missing_declaration_is_a_static_error(self):
        with self.assertRaisesRegex(TavrynError, "needs read"):
            parse('let x = read("inbox/message.txt")')

    def test_parent_escape_is_denied(self):
        runtime = self.runtime('needs read "inbox/*.txt"\nlet x = read("../secret.txt")',
                               read=["inbox/*.txt"])
        with self.assertRaisesRegex(TavrynError, "invalid relative path"):
            runtime.run()
        self.assertEqual(runtime.events[0]["reason"], "invalid path")

    def test_symlink_is_denied(self):
        (self.root / "inbox" / "link.txt").symlink_to(self.root / "inbox" / "message.txt")
        runtime = self.runtime('needs read "inbox/*.txt"\nlet x = read("inbox/link.txt")',
                               read=["inbox/*.txt"])
        with self.assertRaisesRegex(TavrynError, "symbolic links"):
            runtime.run()

    def test_audit_omits_file_content(self):
        audit = self.root / "audit.jsonl"
        runtime = self.runtime('needs read "inbox/*.txt"\nlet x = read("inbox/message.txt")',
                               read=["inbox/*.txt"], audit=audit)
        runtime.run()
        events = [json.loads(line) for line in audit.read_text().splitlines()]
        self.assertEqual(events[0]["decision"], "allow")
        self.assertNotIn("hello", audit.read_text())

    def test_bad_type_for_addition(self):
        runtime = self.runtime('say("x" + 1)')
        with self.assertRaisesRegex(TavrynError, "two strings or two integers"):
            runtime.run()


if __name__ == "__main__":
    unittest.main()
