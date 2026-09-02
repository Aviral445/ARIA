"""
gaia/gaia_vault.py — Google Cloud Storage (GCS) Auto-Vault & Local Disk Pruner
Archives Aria & GAIA snapshots, diffs, and learning ledgers to Google Cloud Storage
and purges local snapshot bloat from E:\\MyAgent to permanently preserve disk space.
"""

import os
import sys
import time
import json
import shutil
from typing import Dict, Any, List, Tuple, Optional

# Core paths
from core.paths import ARIA_EVOLVED_DIR, ROOT_DIR
from gaia.gaia_bus import bus

# Default GCS Configuration
VAULT_BUCKET_NAME = os.environ.get("GAIA_VAULT_BUCKET", "aria-gaia-vault-0421124464")
LOCAL_SNAPSHOTS_DIR = os.path.join(ARIA_EVOLVED_DIR, "snapshots")
LOCAL_DIFFS_DIR = os.path.join(ARIA_EVOLVED_DIR, "diffs")
LOCAL_LEARNING_FILE = os.path.join(ARIA_EVOLVED_DIR, "sister_learning.json")


class GaiaVault:
    def __init__(self, bucket_name: str = VAULT_BUCKET_NAME):
        self.bucket_name = bucket_name
        self._client = None
        self._bucket = None

    def _get_bucket(self):
        """Lazy-load GCS client and bucket."""
        if self._bucket is None:
            try:
                from google.cloud import storage
                self._client = storage.Client()
                self._bucket = self._client.bucket(self.bucket_name)
            except Exception as e:
                print(f"[GAIA Vault] GCS Init Warning: {e}")
                return None
        return self._bucket

    def is_available(self) -> bool:
        """Returns True if GCS bucket is accessible."""
        b = self._get_bucket()
        if b is None:
            return False
        try:
            return b.exists()
        except Exception:
            return False

    # ── 1. CLOUD UPLOAD OPERATIONS ───────────────────────────────────────────
    def upload_snapshot(self, snapshot_id: str) -> Tuple[bool, str]:
        """
        Uploads an entire snapshot directory to GCS:
        gs://<bucket>/snapshots/<snapshot_id>/...
        """
        b = self._get_bucket()
        if not b:
            return False, "Google Cloud Storage client not available."

        snap_path = os.path.join(LOCAL_SNAPSHOTS_DIR, snapshot_id)
        if not os.path.exists(snap_path):
            return False, f"Local snapshot '{snapshot_id}' does not exist."

        uploaded_files = []
        try:
            for root, dirs, files in os.walk(snap_path):
                dirs[:] = [d for d in dirs if d not in ["platform-tools", "__pycache__", ".git"]]
                for f in files:
                    if f.endswith(".pyc") or f.endswith(".exe") or f.endswith(".dll"):
                        continue
                    local_file = os.path.join(root, f)
                    rel_path = os.path.relpath(local_file, snap_path).replace("\\", "/")
                    blob_name = f"snapshots/{snapshot_id}/{rel_path}"
                    blob = b.blob(blob_name)
                    blob.upload_from_filename(local_file)
                    uploaded_files.append(blob_name)

            msg = f"Uploaded {len(uploaded_files)} files for snapshot '{snapshot_id}' to GCS vault (gs://{self.bucket_name}/snapshots/{snapshot_id}/)."
            bus.emit("GAIA", "VAULT_UPLOAD", msg, {"snapshot_id": snapshot_id, "files_count": len(uploaded_files)})
            return True, msg
        except Exception as e:
            err_msg = f"Failed to upload snapshot '{snapshot_id}' to GCS: {e}"
            bus.emit("GAIA", "VAULT_ERROR", err_msg, {"snapshot_id": snapshot_id})
            return False, err_msg

    def upload_learning_ledger(self) -> Tuple[bool, str]:
        """Uploads sister_learning.json to GCS."""
        b = self._get_bucket()
        if not b or not os.path.exists(LOCAL_LEARNING_FILE):
            return False, "Ledger or GCS unavailable."
        try:
            blob = b.blob("learning/sister_learning.json")
            blob.upload_from_filename(LOCAL_LEARNING_FILE)
            return True, f"Backed up sister learning ledger to gs://{self.bucket_name}/learning/sister_learning.json"
        except Exception as e:
            return False, f"Failed to upload learning ledger: {e}"

    # ── 2. CLOUD RESTORE / DOWNLOAD OPERATIONS ───────────────────────────────
    def download_snapshot(self, snapshot_id: str) -> Tuple[bool, str]:
        """
        Downloads a snapshot from GCS into local E:\\MyAgent\\snapshots\\<snapshot_id>\\.
        Used when rolling back to a snapshot that was purged from local disk.
        """
        b = self._get_bucket()
        if not b:
            return False, "Google Cloud Storage client not available."

        target_dir = os.path.join(LOCAL_SNAPSHOTS_DIR, snapshot_id)
        os.makedirs(target_dir, exist_ok=True)

        prefix = f"snapshots/{snapshot_id}/"
        try:
            blobs = list(b.list_blobs(prefix=prefix))
            if not blobs:
                return False, f"No remote snapshot '{snapshot_id}' found in GCS bucket."

            for blob in blobs:
                rel_path = blob.name[len(prefix):]
                if not rel_path:
                    continue
                dest_file = os.path.join(target_dir, rel_path.replace("/", os.sep))
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                blob.download_to_filename(dest_file)

            msg = f"Restored snapshot '{snapshot_id}' from GCS vault ({len(blobs)} files)."
            bus.emit("GAIA", "VAULT_RESTORE", msg, {"snapshot_id": snapshot_id})
            return True, msg
        except Exception as e:
            return False, f"Failed to restore snapshot '{snapshot_id}' from GCS: {e}"

    def list_cloud_snapshots(self) -> List[str]:
        """Lists all snapshot IDs archived in GCS."""
        b = self._get_bucket()
        if not b:
            return []
        try:
            blobs = b.list_blobs(prefix="snapshots/")
            snap_ids = set()
            for blob in blobs:
                parts = blob.name.split("/")
                if len(parts) >= 2 and parts[1]:
                    snap_ids.add(parts[1])
            return sorted(list(snap_ids), reverse=True)
        except Exception:
            return []

    # ── 3. LOCAL DISK PRUNING (FREE LOCAL DRIVE SPACE) ────────────────────────
    def purge_local_snapshots(self, retention_hours: int = 24) -> Tuple[int, int]:
        """
        Scans local E:\\MyAgent\\snapshots\\, checks that each snapshot exists in GCS,
        and deletes local copies older than retention_hours.
        Returns: (purged_count, freed_bytes)
        """
        if not os.path.exists(LOCAL_SNAPSHOTS_DIR):
            return 0, 0

        b = self._get_bucket()
        if not b:
            return 0, 0

        cutoff_sec = time.time() - (retention_hours * 3600)
        purged_count = 0
        freed_bytes = 0

        cloud_snaps = set(self.list_cloud_snapshots())

        for snap_id in os.listdir(LOCAL_SNAPSHOTS_DIR):
            snap_path = os.path.join(LOCAL_SNAPSHOTS_DIR, snap_id)
            if not os.path.isdir(snap_path):
                continue

            meta_file = os.path.join(snap_path, "meta.json")
            snap_time = 0
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        snap_time = meta.get("timestamp", 0)
                except Exception:
                    pass

            if snap_time == 0:
                snap_time = os.path.getmtime(snap_path)

            # If snapshot is older than retention_hours
            if snap_time < cutoff_sec:
                # 1. Ensure it's in GCS first!
                if snap_id not in cloud_snaps:
                    ok, _ = self.upload_snapshot(snap_id)
                    if not ok:
                        continue  # Do not delete locally if upload fails!

                # 2. Calculate size to report space freed
                snap_size = sum(
                    os.path.getsize(os.path.join(r, f))
                    for r, _, files in os.walk(snap_path)
                    for f in files
                )

                # 3. Safely delete local copy
                try:
                    shutil.rmtree(snap_path)
                    purged_count += 1
                    freed_bytes += snap_size
                except Exception as e:
                    print(f"[GAIA Vault] Failed to purge {snap_id}: {e}")

        if purged_count > 0:
            freed_kb = round(freed_bytes / 1024, 2)
            msg = f"🧹 Local Disk Pruner: Purged {purged_count} local snapshots (> {retention_hours}h old) from E: drive. Freed {freed_kb} KB. (All safely backed up in GCS)."
            bus.emit("GAIA", "VAULT_PURGE", msg, {"purged_count": purged_count, "freed_bytes": freed_bytes})

        return purged_count, freed_bytes

    # ── 4. SYNC EVERYTHING ───────────────────────────────────────────────────
    def sync_vault(self, retention_hours: int = 24) -> Dict[str, Any]:
        """
        Comprehensive sync:
        1. Backs up any local snapshots not yet in GCS.
        2. Backs up learning ledger.
        3. Purges stale local snapshots older than retention_hours.
        """
        cloud_snaps = set(self.list_cloud_snapshots())
        uploaded_now = 0

        if os.path.exists(LOCAL_SNAPSHOTS_DIR):
            for snap_id in os.listdir(LOCAL_SNAPSHOTS_DIR):
                if snap_id not in cloud_snaps:
                    ok, _ = self.upload_snapshot(snap_id)
                    if ok:
                        uploaded_now += 1

        self.upload_learning_ledger()
        purged, freed = self.purge_local_snapshots(retention_hours=retention_hours)

        return {
            "bucket": self.bucket_name,
            "uploaded_snapshots": uploaded_now,
            "purged_local": purged,
            "freed_bytes": freed,
            "total_cloud_snapshots": len(self.list_cloud_snapshots())
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns high-level telemetry on Vault & local drive."""
        try:
            free_e_gb = round(shutil.disk_usage(ARIA_EVOLVED_DIR).free / (1024 ** 3), 2)
        except Exception:
            free_e_gb = 0.0

        cloud_snaps = self.list_cloud_snapshots()
        local_count = 0
        if os.path.exists(LOCAL_SNAPSHOTS_DIR):
            local_count = len([d for d in os.listdir(LOCAL_SNAPSHOTS_DIR) if os.path.isdir(os.path.join(LOCAL_SNAPSHOTS_DIR, d))])

        return {
            "bucket_name": self.bucket_name,
            "cloud_available": self.is_available(),
            "cloud_snapshots_count": len(cloud_snaps),
            "local_snapshots_count": local_count,
            "local_e_free_gb": free_e_gb
        }


# Global Singleton
vault = GaiaVault()
