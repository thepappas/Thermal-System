import hashlib
import importlib.util
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "package_release.py"
spec = importlib.util.spec_from_file_location("package_release", SCRIPT)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleasePackageTests(unittest.TestCase):
    def test_semver_tags(self):
        for tag in ("v1.2.3", "v0.0.0", "v1.2.3-rc.1", "v1.2.3+build.01"):
            self.assertTrue(release.valid_tag(tag), tag)
        for tag in ("1.2.3", "v01.2.3", "v1.2", "v1.2.3-01", "v1.2.3/", "v1.2.3\n"):
            self.assertFalse(release.valid_tag(tag), tag)

    def test_bundle_contains_only_committed_files_and_valid_checksum(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            def git(*args):
                return subprocess.check_output(
                    ["git", "-C", str(root), *args], text=True
                ).strip()

            git("init", "-q")
            git("config", "user.email", "test@example.invalid")
            git("config", "user.name", "Test")
            (root / "README.md").write_text("committed\n")
            git("add", "README.md")
            git("commit", "-qm", "Initial")
            commit = git("rev-parse", "HEAD")
            (root / "README.md").write_text("uncommitted\n")
            (root / "secrets.yaml").write_text("private\n")
            output = root / "dist"
            subprocess.run(
                ["python3", str(SCRIPT), "v1.2.3-rc.1", commit, str(output)],
                cwd=root,
                check=True,
            )
            bundle = output / "thermal-system-v1.2.3-rc.1.tar.gz"
            data = bundle.read_bytes()
            self.assertEqual(
                (output / "SHA256SUMS").read_text(),
                f"{hashlib.sha256(data).hexdigest()}  {bundle.name}\n",
            )
            with tarfile.open(bundle) as archive:
                files = [member for member in archive.getmembers() if member.isfile()]
                self.assertEqual([member.name for member in files], [
                    "thermal-system-v1.2.3-rc.1/README.md"
                ])
                self.assertEqual(archive.extractfile(files[0]).read(), b"committed\n")
            subprocess.run(
                ["python3", str(SCRIPT), "v1.2.3-rc.1", commit, str(output)],
                cwd=root,
                check=True,
            )
            self.assertEqual(bundle.read_bytes(), data)
            for tag, revision in (("v1.2", commit), ("v1.2.3", commit[:8])):
                result = subprocess.run(
                    ["python3", str(SCRIPT), tag, revision, str(root / "invalid")],
                    cwd=root,
                    capture_output=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((root / "invalid").exists())


if __name__ == "__main__":
    unittest.main()
