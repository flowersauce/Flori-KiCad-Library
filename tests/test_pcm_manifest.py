"""验证收集文件和变更判定使用相同规则，以及 Git 差异中的删除和重命名。"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from pcm_manifest import (
    MANIFEST_PATH, affects_package, changed_paths, collect_files,
    load_manifest, matches_path, should_build,
)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest = {
            "schema_version": 1,
            "metadata": "pcm/metadata.json",
            "files": [
                {"source": "resources/datasheets/**/*", "suffixes": [".pdf"]},
                {"source": "pcm/install.md", "target": "resources/install.md"},
                {"source": "docs/provenance.json", "target": "resources/provenance.json",
                 "json_remove": ["backup"]},
            ],
            "build_inputs": ["tools/build.py"],
        }
        self.write("resources/datasheets/root.PDF", b"root")
        self.write("resources/datasheets/vendor/中文 资料.pdf", b"nested")
        self.write("resources/datasheets/vendor/README.md", b"ignored")
        self.write("pcm/install.md", b"install")
        self.write("docs/provenance.json", b'{"backup":"tmp/old", "origin":"upstream"}')
        self.write(MANIFEST_PATH, json.dumps(self.manifest).encode())

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def test_collection_and_trigger_agree(self):
        manifest = load_manifest(self.root)
        payload = collect_files(self.root, manifest)
        self.assertEqual(set(payload), {
            "resources/datasheets/root.PDF", "resources/datasheets/vendor/中文 资料.pdf",
            "resources/install.md", "resources/provenance.json",
        })
        self.assertEqual(json.loads(payload["resources/provenance.json"]), {"origin": "upstream"})
        for path in ("resources/datasheets/root.PDF", "resources/datasheets/vendor/中文 资料.pdf",
                     "pcm/install.md", "docs/provenance.json", "pcm/metadata.json",
                     "tools/build.py", MANIFEST_PATH):
            self.assertTrue(affects_package(manifest, path), path)
        self.assertFalse(affects_package(manifest, "resources/datasheets/vendor/README.md"))
        self.assertFalse(affects_package(manifest, "README.md"))

    def test_new_input_requires_only_one_entry(self):
        self.write("resources/extra/document.txt", b"new input")
        self.assertFalse(affects_package(self.manifest, "resources/extra/document.txt"))
        self.manifest["files"].append({"source": "resources/extra/*.txt"})
        self.assertEqual(collect_files(self.root, self.manifest)["resources/extra/document.txt"], b"new input")
        self.assertTrue(affects_package(self.manifest, "resources/extra/document.txt"))

    def test_pattern_directory_boundaries(self):
        self.assertTrue(matches_path("a/b/file.pdf", "a/**/*.pdf"))
        self.assertTrue(matches_path("a/file.pdf", "a/**/*.pdf"))
        self.assertFalse(matches_path("a/b/file.pdf", "a/*.pdf"))
        self.assertFalse(matches_path("other/a/file.pdf", "a/**/*.pdf"))

    def test_deleted_input_still_triggers(self):
        (self.root / "pcm/install.md").unlink()
        self.assertTrue(affects_package(self.manifest, "pcm/install.md"))
        with self.assertRaises(FileNotFoundError):
            collect_files(self.root, self.manifest)

    def test_collision_and_path_escape_are_rejected(self):
        self.manifest["files"].append({"source": "pcm/install.md", "target": "resources/install.md"})
        with self.assertRaises(ValueError):
            collect_files(self.root, self.manifest)
        self.manifest["files"] = [{"source": "../outside.txt"}]
        self.write(MANIFEST_PATH, json.dumps(self.manifest).encode())
        with self.assertRaises(ValueError):
            load_manifest(self.root)

    def test_rename_keeps_old_and_new_paths(self):
        def git(*arguments):
            return subprocess.check_output(["git", *arguments], cwd=self.root).decode().strip()

        git("init", "-q")
        git("add", ".")
        git("-c", "user.name=PCM test", "-c", "user.email=pcm@example.invalid", "commit", "-qm", "before")
        before = git("rev-parse", "HEAD")
        (self.root / "pcm/install.md").rename(self.root / "renamed.md")
        git("add", "-A")
        git("-c", "user.name=PCM test", "-c", "user.email=pcm@example.invalid", "commit", "-qm", "after")
        paths = changed_paths(self.root, before, "HEAD")
        self.assertEqual(set(paths), {"pcm/install.md", "renamed.md"})
        self.assertTrue(any(affects_package(self.manifest, path) for path in paths))

    def test_missing_baseline_builds_conservatively(self):
        with patch("pcm_manifest.changed_paths", side_effect=subprocess.CalledProcessError(1, "git")):
            self.assertTrue(should_build(self.root, self.manifest, "push", {"before": "abc", "after": "def"}))
        self.assertTrue(should_build(self.root, self.manifest, "push", {"before": "0" * 40, "after": "def"}))
        self.assertTrue(should_build(self.root, self.manifest, "pull_request", {}))
        self.assertTrue(should_build(self.root, self.manifest, "workflow_dispatch", {}))

    def test_docs_only_skip_and_mixed_changes_build(self):
        event = {"before": "abc", "after": "def"}
        with patch("pcm_manifest.changed_paths", return_value=["README.md", "docs/guide.md"]):
            self.assertFalse(should_build(self.root, self.manifest, "push", event))
        with patch("pcm_manifest.changed_paths", return_value=["README.md", "pcm/install.md"]):
            self.assertTrue(should_build(self.root, self.manifest, "push", event))

    def test_payload_contains_only_current_libraries(self):
        from build_pcm import package_payload

        self.write("symbols/Flori_Test.kicad_sym", b'(kicad_symbol_lib (version 20241209))')
        self.write("footprints/Flori_Test.pretty/Test.kicad_mod", b'(footprint "Test")')
        self.manifest["files"] = [
            {"source": "symbols/Flori_*.kicad_sym"},
            {"source": "footprints/Flori_*.pretty/*.kicad_mod"},
        ]
        self.write(MANIFEST_PATH, json.dumps(self.manifest).encode())
        self.assertEqual(set(package_payload(self.root, "example.flori")), {
            "symbols/Flori_Test.kicad_sym", "footprints/Flori_Test.pretty/Test.kicad_mod",
        })


if __name__ == "__main__":
    unittest.main()
