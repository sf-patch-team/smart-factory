"""FS1~FS6: 외부 네트워크 없이 수집·검증·원자적 게시를 시험한다."""
import gzip
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from http.client import IncompleteRead
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import sync_vulnerability_feeds as feeds


def kev_payload(count=5, released="2026-10-23T00:00:00Z"):
    entries = []
    for number in range(count):
        entries.append({
            "cveID": f"CVE-2026-{1000 + number}", "vendorProject": "Test",
            "product": "Test product", "vulnerabilityName": "Test issue",
            "dateAdded": "2026-10-20", "shortDescription": "Fixture only",
            "requiredAction": "Apply update", "dueDate": "2026-11-01",
        })
    return json.dumps({"vulnerabilities": entries, "count": count,
                       "dateReleased": released, "catalogVersion": "2026.10.23"}).encode()


def epss_payload(count=5, score_date="2026-10-23"):
    lines = [f"#model_version:v2025.03.14,score_date:{score_date}T00:00:00+0000",
             "cve,epss,percentile"]
    lines.extend(f"CVE-2026-{1000 + number},0.42,0.95" for number in range(count))
    return gzip.compress(("\n".join(lines) + "\n").encode(), mtime=0)


class Response(io.BytesIO):
    def __init__(self, body, length=None):
        super().__init__(body)
        self.headers = {"Content-Length": str(len(body) if length is None else length),
                        "ETag": '"fixture-v1"', "Last-Modified": "Fri, 23 Oct 2026 00:00:00 GMT"}


class FeedSyncTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.bodies = {"kev": kev_payload(), "epss": epss_payload()}
        self.requests = []
        self.failures = {}
        self.network = patch.object(feeds, "urlopen", side_effect=self.respond).start()
        self.addCleanup(patch.stopall)
        patch.object(feeds.time, "sleep").start()

    def respond(self, request, timeout):
        self.requests.append(request)
        name = "epss" if "epss" in request.full_url else "kev"
        failure = self.failures.get(name)
        if isinstance(failure, int):
            raise HTTPError(request.full_url, failure, "Fixture response", {}, None)
        body = self.bodies[name]
        return Response(body, len(body) + 10 if failure == "truncated" else None)

    def run_sync(self, intervals=None):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return feeds.sync_once(self.root, intervals)

    def state(self):
        return json.loads((self.root / "current.json").read_text(encoding="utf-8"))

    def assert_original_preserved(self, original, name):
        self.assertEqual(self.state()[name], original[name])
        for information in original.values():
            path = self.root / information["file"]
            self.assertEqual(feeds.digest(path), information["sha256"])

    def test_fs1_valid_feeds_preserve_original_and_metadata(self):
        self.assertEqual(self.run_sync(), 0)
        state = self.state()
        self.assertEqual(set(state), {"kev", "epss"})
        for name, information in state.items():
            self.assertEqual(information["count"], 5)
            self.assertEqual((self.root / information["file"]).read_bytes(), self.bodies[name])
            self.assertEqual(feeds.digest(self.root / information["file"]), information["sha256"])
        self.assertEqual(state["epss"]["source_date"], "2026-10-23")
        self.assertEqual(state["epss"]["version"], "v2025.03.14")
        self.assertFalse(list(self.root.glob("*.pending")))

    def test_fs2_identical_content_does_not_create_new_versions(self):
        self.assertEqual(self.run_sync(), 0)
        original = self.state()
        self.assertEqual(self.run_sync(), 0)
        for name in original:
            self.assertEqual(self.state()[name]["file"], original[name]["file"])
            self.assertEqual(len(list((self.root / name).iterdir())), 1)
        for request in self.requests[2:]:
            self.assertEqual(request.get_header("If-none-match"), '"fixture-v1"')
            self.assertIn("Oct 2026", request.get_header("If-modified-since"))

    def test_fs2_not_modified_reuses_verified_original(self):
        self.assertEqual(self.run_sync(), 0)
        original = self.state()
        self.failures = {"kev": 304, "epss": 304}
        self.assertEqual(self.run_sync(), 0)
        for name in original:
            self.assertEqual(self.state()[name]["sha256"], original[name]["sha256"])
            self.assertEqual(self.state()[name]["fetched_at"], original[name]["fetched_at"])
        self.assertFalse(list(self.root.glob("*.pending")))

    def test_fs2_missing_cache_drops_conditional_headers(self):
        self.assertEqual(self.run_sync(), 0)
        (self.root / self.state()["kev"]["file"]).unlink()
        self.requests.clear()
        self.assertEqual(self.run_sync(), 0)
        self.assertIsNone(self.requests[0].get_header("If-none-match"))
        self.assertTrue((self.root / self.state()["kev"]["file"]).is_file())

    def test_fs2_corrupt_cached_file_cannot_accept_304(self):
        self.assertEqual(self.run_sync(), 0)
        original = self.state()
        (self.root / original["kev"]["file"]).write_bytes(b"corrupted")
        self.requests.clear()
        self.failures = {"kev": 304, "epss": 304}
        self.assertEqual(self.run_sync(), 1)
        self.assertEqual(self.state()["kev"], original["kev"])
        self.assertIsNone(self.requests[0].get_header("If-none-match"))

    def test_fs3_kev_falls_back_without_leaking_endpoint_validators(self):
        self.assertEqual(self.run_sync(), 0)
        original_responder = self.respond

        def fallback_response(request, timeout):
            if "www.cisa.gov" in request.full_url:
                raise HTTPError(request.full_url, 403, "Fixture denial", {}, None)
            return original_responder(request, timeout)

        self.requests.clear()
        self.network.side_effect = fallback_response
        self.assertEqual(self.run_sync(), 0)
        self.assertIn("raw.githubusercontent.com", self.state()["kev"]["url"])
        self.assertIsNone(self.requests[0].get_header("If-none-match"))

    def test_fs3_incomplete_read_retries_and_isolates_source(self):
        self.assertEqual(self.run_sync(), 0)
        original = self.state()
        original_responder = self.respond
        kev_attempts = []

        def interrupted_response(request, timeout):
            if "epss" not in request.full_url:
                kev_attempts.append(request.full_url)
                raise IncompleteRead(b"partial fixture", 30)
            return original_responder(request, timeout)

        self.network.side_effect = interrupted_response
        self.bodies["epss"] = epss_payload(score_date="2026-10-24")
        self.assertEqual(self.run_sync(), 1)
        self.assertEqual(len(kev_attempts), 6)
        self.assert_original_preserved(original, "kev")
        self.assertEqual(self.state()["epss"]["source_date"], "2026-10-24")

    def test_fs3_extra_csv_columns_rejected_and_metadata_spaces_accepted(self):
        self.assertEqual(self.run_sync(), 0)
        original = self.state()
        text = gzip.decompress(self.bodies["epss"]).decode()
        self.bodies["epss"] = gzip.compress(text.replace(",0.42,0.95", ",0.42,0.95,extra").encode())
        self.assertEqual(self.run_sync(), 1)
        self.assert_original_preserved(original, "epss")
        spaced = text.replace("#model_version:", "# model_version: ").replace(
            ",score_date:", ", score_date: ")
        self.bodies["epss"] = gzip.compress(spaced.encode())
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual(self.state()["epss"]["version"], "v2025.03.14")

    def test_fs3_http_invalid_and_truncated_keep_manifest(self):
        self.assertEqual(self.run_sync(), 0)
        original = self.state()
        original_bytes = (self.root / "current.json").read_bytes()
        for failure in (503, "invalid", "truncated"):
            with self.subTest(failure=failure):
                self.bodies = {"kev": kev_payload(), "epss": epss_payload()}
                self.failures = {"kev": failure, "epss": failure}
                if failure == "invalid":
                    self.bodies = {"kev": b'{"count": 1}', "epss": b"not gzip"}
                self.assertEqual(self.run_sync(), 2)
                self.assertEqual((self.root / "current.json").read_bytes(), original_bytes)
                self.assert_original_preserved(original, "kev")
                self.assertFalse(list(self.root.glob("*.pending")))

    def test_fs3_failing_kev_does_not_block_epss_publication(self):
        self.assertEqual(self.run_sync(), 0)
        original = self.state()
        self.failures["kev"] = 503
        self.bodies["epss"] = epss_payload(score_date="2026-10-24")
        self.assertEqual(self.run_sync(), 1)
        self.assert_original_preserved(original, "kev")
        self.assertEqual(self.state()["epss"]["source_date"], "2026-10-24")
        self.assertNotEqual(self.state()["epss"]["sha256"], original["epss"]["sha256"])

    def test_fs3_invalid_deflate_keeps_epss_and_allows_kev_update(self):
        self.assertEqual(self.run_sync(), 0)
        original = self.state()
        self.bodies["epss"] = b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\x07" + b"\x00" * 8
        self.bodies["kev"] = kev_payload(released="2026-10-24T00:00:00Z")
        self.assertEqual(self.run_sync(), 1)
        self.assert_original_preserved(original, "epss")
        self.assertEqual(self.state()["kev"]["source_date"], "2026-10-24T00:00:00+00:00")
        self.assertNotEqual(self.state()["kev"]["sha256"], original["kev"]["sha256"])
        self.assertFalse(list(self.root.glob("*.pending")))

    def test_fs4_older_feeds_and_excessive_drop_are_rejected(self):
        self.assertEqual(self.run_sync(), 0)
        original = self.state()
        candidates = [(kev_payload(released="2026-10-22T00:00:00Z"),
                       epss_payload(score_date="2026-10-22")),
                      (kev_payload(count=3), epss_payload(count=3))]
        for kev, epss in candidates:
            with self.subTest(candidate=len(kev)):
                self.bodies = {"kev": kev, "epss": epss}
                self.assertEqual(self.run_sync(), 2)
                self.assertEqual(self.state(), original)
        self.bodies = {"kev": kev_payload(count=4), "epss": epss_payload(count=4)}
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual(self.state()["kev"]["count"], 4)
        self.assertEqual(self.state()["epss"]["count"], 4)

    def test_fs5_other_process_cannot_acquire_held_os_lock(self):
        command = ("import sys; from pathlib import Path; "
                   "from scripts.sync_vulnerability_feeds import exclusive; "
                   "context = exclusive(Path(sys.argv[1])); context.__enter__()")
        with feeds.exclusive(self.root):
            blocked = subprocess.run([sys.executable, "-c", command, str(self.root)],
                                     cwd=feeds.BASE, capture_output=True, timeout=15)
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn(b"Error", blocked.stderr)
        released = subprocess.run([sys.executable, "-c", command, str(self.root)],
                                  cwd=feeds.BASE, capture_output=True, timeout=15)
        self.assertEqual(released.returncode, 0, released.stderr.decode(errors="replace"))

    def test_fs6_independent_intervals_skip_fresh_epss(self):
        self.assertEqual(self.run_sync(), 0)
        state = self.state()
        checked = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        for information in state.values():
            information["checked_at"] = checked
        feeds.save_json(self.root / "current.json", state)
        self.requests.clear()
        self.assertEqual(self.run_sync({"kev": 900, "epss": 86400}), 0)
        self.assertEqual(len(self.requests), 1)
        self.assertNotIn("epss", self.requests[0].full_url)
        self.assertEqual(self.state()["epss"], state["epss"])


if __name__ == "__main__":
    unittest.main()
