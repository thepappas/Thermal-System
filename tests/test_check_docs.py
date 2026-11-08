import contextlib
import importlib.util
import io
import pathlib
import tempfile
import unittest

path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "check_docs.py"
spec = importlib.util.spec_from_file_location("check_docs", path)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class DocumentationTest(unittest.TestCase):
    def test_links_and_fences(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            checker.ROOT = root
            doc = root / "README.md"
            (root / "target.md").write_text("# Target\n", encoding="utf-8")
            doc.write_text("# Test\n\n[ok](target.md)\n\n```\n[ignored](missing)\n```\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(checker.main(), 0)
            doc.write_text("# Test\n\n[bad](missing.md)\n\n```\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(checker.main(), 1)


if __name__ == "__main__":
    unittest.main()
