"""
Generation status tracker for ilhmp hillshade pipeline.

Writes status JSON to local dist/status/ or S3 (s3://exaggeratedrelief/status/).

Usage:
    tracker = StatusTracker("exaggeratedrelief", run_id="12345678")
    tracker.init("cook-dark-9x-z10-16", county="cook", theme="dark", ...)
    tracker.update(status="running", phase="generate_tiles", percent=40)
    tracker.complete(outputs={"pmtiles_url": "...", "mbtiles_size_mb": 42})
    tracker.fail(phase="render_hillshade", error="OOM killed")
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Valid state constants ──────────────────────────────────────────────────

STATUSES = {
    "queued", "validating", "provisioning", "running",
    "uploading", "complete", "failed", "cancelled",
}

PHASES = {
    "validate_request", "estimate_job", "provision_worker",
    "download_dem", "build_mosaic", "render_hillshade",
    "generate_tiles", "package_pmtiles", "package_mbtiles",
    "upload_artifacts", "update_catalog", "cleanup", "published",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _zoom_list(zoom_str: str) -> list:
    """Parse '10-16' → [10,11,12,13,14,15,16]."""
    try:
        lo, hi = zoom_str.split("-")
        return list(range(int(lo), int(hi) + 1))
    except Exception:
        return []


# ── Low-level S3/local I/O ─────────────────────────────────────────────────

class _Store:
    """Unified local/S3 write backend, mirroring Cache pattern."""

    def __init__(self, bucket: Optional[str]):
        if bucket:
            self._mode = "s3"
            self._bucket = bucket.rstrip("/")
        else:
            self._mode = "local"
            self._local = Path("dist/status")
            self._local.mkdir(parents=True, exist_ok=True)

    def _s3_uri(self, key: str) -> str:
        return f"s3://{self._bucket}/{key}"

    def put(self, key: str, obj: dict) -> bool:
        """Write dict as JSON to key."""
        data = json.dumps(obj, indent=2)
        if self._mode == "s3":
            result = subprocess.run(
                ["aws", "s3", "cp", "-", self._s3_uri(key),
                 "--content-type", "application/json",
                 "--cache-control", "no-cache"],
                input=data, text=True, capture_output=True,
            )
            if result.returncode != 0:
                print(f"⚠️  S3 status write failed ({key}): {result.stderr.strip()}",
                      file=sys.stderr)
                return False
            return True
        else:
            path = self._local / key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data)
            return True

    def get(self, key: str) -> Optional[dict]:
        """Read JSON from key, return None if missing."""
        if self._mode == "s3":
            result = subprocess.run(
                ["aws", "s3", "cp", self._s3_uri(key), "-"],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                return None
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return None
        else:
            path = self._local / key
            if not path.exists():
                return None
            try:
                return json.loads(path.read_text())
            except json.JSONDecodeError:
                return None

    def list_keys(self, prefix: str) -> list:
        """List keys under prefix."""
        if self._mode == "s3":
            result = subprocess.run(
                ["aws", "s3", "ls", f"{self._s3_uri(prefix)}/"],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                return []
            keys = []
            for line in result.stdout.splitlines():
                parts = line.split()
                if parts:
                    keys.append(f"{prefix}/{parts[-1]}")
            return keys
        else:
            base = self._local / prefix
            if not base.exists():
                return []
            return [str(p.relative_to(self._local)) for p in base.glob("*.json")]


# ── Public API ────────────────────────────────────────────────────────────

class StatusTracker:
    """Stateful job tracker for a single GitHub Actions run."""

    def __init__(self, bucket: Optional[str] = None, run_id: Optional[str] = None):
        """
        Args:
            bucket: S3 bucket name (e.g. "exaggeratedrelief"), or None for local.
                    Also reads S3_BUCKET env var as fallback.
            run_id: GitHub run_id (string). Written into status for traceability.
        """
        resolved_bucket = bucket or os.environ.get("S3_BUCKET") or os.environ.get("STATUS_BUCKET")
        self._store = _Store(resolved_bucket)
        self._run_id = run_id or os.environ.get("GITHUB_RUN_ID", "local")
        self._job_id: Optional[str] = None

        # Restore job_id from env if we're in a later step of the same workflow
        if "JOB_ID" in os.environ:
            self._job_id = os.environ["JOB_ID"]

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def init(
        self,
        job_id: str,
        county: str,
        theme: str,
        dem: str = "dtm",
        zoom: str = "10-16",
        exaggeration: str = "auto",
        github_run_url: Optional[str] = None,
    ) -> dict:
        """Create a new job status record and return it."""
        self._job_id = job_id
        now = _now_iso()
        status = {
            "job_id": job_id,
            "county": county,
            "theme": theme,
            "dem": dem,
            "exaggeration": exaggeration,
            "zoom": zoom,
            "zooms_requested": _zoom_list(zoom),
            "zooms_completed": [],
            "status": "queued",
            "phase": "validate_request",
            "percent": 0,
            "started_at": now,
            "updated_at": now,
            "message": "Job queued",
            "github_run_url": github_run_url or self._default_run_url(),
            "outputs": {},
            "error": None,
            "next_action": None,
        }
        self._store.put(f"status/jobs/{job_id}.json", status)
        self._write_job_id_to_env(job_id)
        self.update_index()
        return status

    def update(
        self,
        status: str,
        phase: str,
        percent: int,
        message: Optional[str] = None,
        **extra,
    ) -> dict:
        """Update an existing job. Merges extra fields into the record."""
        record = self._load() or {}
        record.update({
            "status": status,
            "phase": phase,
            "percent": percent,
            "updated_at": _now_iso(),
        })
        if message is not None:
            record["message"] = message
        record.update(extra)
        self._store.put(f"status/jobs/{self._job_id}.json", record)
        self.update_index()
        return record

    def fail(
        self,
        phase: str,
        error: str,
        next_action: Optional[str] = None,
        percent: Optional[int] = None,
    ) -> dict:
        """Mark job as failed."""
        record = self._load() or {}
        if percent is not None:
            record["percent"] = percent
        record.update({
            "status": "failed",
            "phase": phase,
            "updated_at": _now_iso(),
            "error": error,
            "next_action": next_action,
        })
        self._store.put(f"status/jobs/{self._job_id}.json", record)
        self.update_index()
        return record

    def complete(self, outputs: dict) -> dict:
        """Mark job as complete with output metadata."""
        record = self._load() or {}
        record.update({
            "status": "complete",
            "phase": "published",
            "percent": 100,
            "updated_at": _now_iso(),
            "outputs": outputs,
            "error": None,
        })
        self._store.put(f"status/jobs/{self._job_id}.json", record)
        self.update_index()
        return record

    # ── Index ──────────────────────────────────────────────────────────────

    def update_index(self) -> dict:
        """Rebuild status/index.json from all jobs/*.json."""
        keys = self._store.list_keys("status/jobs")
        jobs = []
        for key in sorted(keys):
            record = self._store.get(key)
            if not record:
                continue
            jobs.append({
                "job_id": record.get("job_id", ""),
                "county": record.get("county", ""),
                "theme": record.get("theme", ""),
                "status": record.get("status", ""),
                "phase": record.get("phase", ""),
                "percent": record.get("percent", 0),
                "updated_at": record.get("updated_at", ""),
                "status_url": f"/status/jobs/{record.get('job_id', '')}.json",
            })

        # Sort: running first, then by updated_at desc
        def sort_key(j):
            priority = {"running": 0, "provisioning": 1, "uploading": 2,
                        "queued": 3, "validating": 4, "failed": 5,
                        "complete": 6, "cancelled": 7}.get(j["status"], 9)
            return (priority, j.get("updated_at", ""))

        jobs.sort(key=sort_key)

        index = {"updated_at": _now_iso(), "jobs": jobs}
        self._store.put("status/index.json", index)
        return index

    # ── GitHub summary ────────────────────────────────────────────────────

    def write_github_summary(self, record: Optional[dict] = None) -> None:
        """Write a markdown summary to $GITHUB_STEP_SUMMARY."""
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if not summary_path:
            return
        if record is None:
            record = self._load() or {}

        status = record.get("status", "unknown")
        county = record.get("county", "?")
        theme = record.get("theme", "?")
        exag = record.get("exaggeration", "?")
        zoom = record.get("zoom", "?")
        phase = record.get("phase", "?")
        percent = record.get("percent", 0)
        outputs = record.get("outputs") or {}
        error = record.get("error")
        gh_url = record.get("github_run_url", "")

        status_emoji = {
            "complete": "✅", "failed": "❌", "running": "🔄",
            "uploading": "📤", "provisioning": "🔧",
        }.get(status, "⏳")

        lines = [
            f"## {status_emoji} Hillshade Generation — {county}",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| County | `{county}` |",
            f"| Theme | `{theme}` |",
            f"| Exaggeration | `{exag}x` |",
            f"| Zoom | `{zoom}` |",
            f"| Status | **{status}** |",
            f"| Phase | `{phase}` |",
            f"| Progress | {percent}% |",
        ]

        if outputs:
            lines += ["", "### Outputs", ""]
            for k, v in outputs.items():
                lines.append(f"- **{k}**: `{v}`")

        if error:
            lines += ["", f"### ❌ Error", "", f"```", error, "```"]

        if gh_url:
            lines += ["", f"[View full run]({gh_url})"]

        with open(summary_path, "a") as f:
            f.write("\n".join(lines) + "\n")

    # ── Helpers ───────────────────────────────────────────────────────────

    def _load(self) -> Optional[dict]:
        if not self._job_id:
            return None
        return self._store.get(f"status/jobs/{self._job_id}.json")

    def _default_run_url(self) -> str:
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        run_id = self._run_id
        if repo and run_id:
            return f"https://github.com/{repo}/actions/runs/{run_id}"
        return ""

    @staticmethod
    def _write_job_id_to_env(job_id: str) -> None:
        """Persist JOB_ID to $GITHUB_ENV so later steps can pick it up."""
        gh_env = os.environ.get("GITHUB_ENV")
        if gh_env:
            with open(gh_env, "a") as f:
                f.write(f"JOB_ID={job_id}\n")


# ── Module-level convenience wrappers (backwards compat) ─────────────────

def _default_tracker() -> StatusTracker:
    return StatusTracker()


def init_job_status(job_id, county, theme, dem, zoom, exaggeration, github_run_url) -> dict:
    return _default_tracker().init(job_id, county=county, theme=theme, dem=dem,
                                   zoom=zoom, exaggeration=exaggeration,
                                   github_run_url=github_run_url)


def update_job_status(job_id, status, phase, percent, message=None, **extra):
    t = StatusTracker()
    t._job_id = job_id
    return t.update(status=status, phase=phase, percent=percent, message=message, **extra)


def fail_job_status(job_id, phase, error, next_action=None, percent=None):
    t = StatusTracker()
    t._job_id = job_id
    return t.fail(phase=phase, error=error, next_action=next_action, percent=percent)


def complete_job_status(job_id, outputs: dict):
    t = StatusTracker()
    t._job_id = job_id
    return t.complete(outputs=outputs)


def update_status_index():
    return _default_tracker().update_index()


def write_github_summary(status: dict):
    _default_tracker().write_github_summary(record=status)
