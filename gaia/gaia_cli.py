"""
gaia/gaia_cli.py — Command-Line Interface for GAIA Supervisor & Aria Lab
Allows monitoring, triggering curiosity sessions, rolling back snapshots, and testing guardrails.
"""

import sys
import os
import json
import argparse
import time

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Ensure project root on sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gaia.gaia_supervisor import supervisor
from gaia.gaia_safety import audit_code_safety
from gaia.gaia_voice import gaia_speak
from gaia.gaia_bus import bus
from gaia.gaia_healer import SANDBOX_DIR


def cmd_status():
    print("\n" + "=" * 60)
    print("👩‍🏫 GAIA: Big Sister & AI Supervisor Status")
    print("=" * 60)
    status = supervisor.get_status()
    print(f"Status:             {'SUPERVISING' if status['is_supervising'] else 'WATCHING / IDLE'}")
    print(f"Sandbox Location:   {status['sandbox_dir']}")
    print(f"Total Snapshots:    {status['total_snapshots']}")
    print(f"Latest Snapshot:    {status['latest_snapshot']}")
    print("\n📋 Recent Events:")
    for ev in status["recent_events"][-6:]:
        print(f"  [{ev['timestamp']}] {ev['sender']} ({ev['type']}): {ev['message']}")
    print("=" * 60 + "\n")


def cmd_curiosity(topic: str = None):
    print(f"\n🚀 Launching Aria's Autonomous Curiosity Session under GAIA's Supervision...")
    success, msg = supervisor.run_curiosity_cycle(custom_topic=topic)
    print(f"\nResult: {'SUCCESS ✅' if success else 'FAILED ❌'}")
    print(f"Details: {msg}\n")


def cmd_rollback():
    print("\n⏪ Rolling back Aria's sandbox to the latest stable snapshot...")
    success, msg = supervisor.rollback_latest()
    print(f"Result: {msg}\n")


def cmd_test_safety():
    print("\n🛡️ Testing GAIA Security Guardrail with dangerous code...")
    unsafe_code = """
import os
# Deliberately malicious attempt outside sandbox
os.system("rmdir /s /q C:\\Windows")
with open("C:/Users/Aviral/.env", "r") as f:
    keys = f.read()
"""
    report = audit_code_safety(unsafe_code, SANDBOX_DIR)
    print(f"Is Safe: {report.is_safe}")
    print(f"Violations Caught ({len(report.violations)}):")
    for v in report.violations:
        print(f"  ❌ {v}")
    print(f"\nGAIA's Sisterly Advice:\n{report.advice}\n")
    if not report.is_safe:
        print("✅ SUCCESS: GAIA successfully intercepted and neutralized the security hazard!")


def cmd_test_heal():
    print("\n🩺 Testing GAIA's Auto-Healing Engine...")
    broken_code = """
import time

def register_tool():
    # Deliberate syntax / runtime error (undefined variable)
    result = undefined_variable_name + 10
    return "test_tool", lambda q: result

if __name__ == "__main__":
    register_tool()
"""
    success, msg = supervisor.supervise_code_deployment("tools/broken_test.py", broken_code, idea_desc="Testing self-repair")
    print(f"Result: {msg}\n")


def cmd_learning():
    print("\n" + "=" * 60)
    print("📚 Mutual Sister Learning Ledger (Aria & GAIA)")
    print("=" * 60)
    learning_file = os.path.join(SANDBOX_DIR, "sister_learning.json")
    if os.path.exists(learning_file):
        try:
            with open(learning_file, "r", encoding="utf-8") as f:
                records = json.load(f)
            if records:
                for idx, r in enumerate(records[-8:], 1):
                    solver_tag = "👧 ARIA (Self-Healed)" if r["solver"] == "ARIA" else "👩‍🏫 GAIA (Assisted)"
                    print(f"\n{idx}. [{r['timestamp']}] Solved by: {solver_tag}")
                    print(f"   Script:  {r['script']}")
                    print(f"   Error:   {r['error_summary']}")
                    print(f"   Lesson:  {r['lesson']}")
            else:
                print("No learning records yet. Aria and GAIA are ready to experiment!")
        except Exception as e:
            print(f"Error reading learning ledger: {e}")
    else:
        print("No learning ledger found yet.")
    print("=" * 60 + "\n")


def cmd_diff():
    print("\n" + "=" * 60)
    print("🔍 Aria Evolution Diff: C:\\MyAgent\\agent.py vs E:\\MyAgent\\aria_evolved.py")
    print("=" * 60)
    diff_info = supervisor.get_diff()
    print(f"Status: {diff_info['summary']}\n")
    if diff_info["has_changes"]:
        print("Diff Preview:")
        print(diff_info["diff_text"][:3000])
        if len(diff_info["diff_text"]) > 3000:
            print("\n... (diff truncated for display, full log in E:\\MyAgent\\ARIA_CHANGELOG.md)")
    print("=" * 60 + "\n")


def cmd_promote():
    print("\n🚀 Promoting Aria's evolved code from E: drive into C:\\MyAgent\\agent.py...")
    success, msg = supervisor.promote_to_c()
    print(f"Result: {msg}\n")


def cmd_reset():
    print("\n🔄 Resetting E:\\MyAgent\\aria_evolved.py to match pristine C:\\MyAgent\\agent.py...")
    success, msg = supervisor.reset_e_from_c()
    print(f"Result: {msg}\n")


def cmd_vault_status():
    print("\n" + "=" * 60)
    print("☁️ GAIA Google Cloud Storage (GCS) Auto-Vault Telemetry")
    print("=" * 60)
    from gaia.gaia_vault import vault
    st = vault.get_status()
    print(f"Bucket Name:            gs://{st['bucket_name']}/")
    print(f"GCS Connected:          {'✅ ACTIVE' if st['cloud_available'] else '❌ OFFLINE'}")
    print(f"Cloud Snapshots Stored: {st['cloud_snapshots_count']}")
    print(f"Local Snapshots on E:   {st['local_snapshots_count']}")
    print(f"Free Disk on E: Drive:  {st['local_e_free_gb']} GB")
    print("=" * 60 + "\n")


def cmd_vault_sync():
    print("\n☁️ Syncing all local snapshots & learning ledger to Google Cloud Storage...")
    from gaia.gaia_vault import vault
    res = vault.sync_vault(retention_hours=24)
    print(f"Bucket:                 gs://{res['bucket']}/")
    print(f"Uploaded Snapshots:     {res['uploaded_snapshots']}")
    print(f"Purged Local Stale (>24h): {res['purged_local']} snapshots")
    print(f"Freed Local Space:      {round(res['freed_bytes'] / 1024, 2)} KB")
    print(f"Total Cloud Snapshots:  {res['total_cloud_snapshots']}\n")


def main():
    parser = argparse.ArgumentParser(description="GAIA Supervisor & Aria Lab CLI")
    parser.add_argument("--status", action="store_true", help="Show live status of GAIA and Aria's lab")
    parser.add_argument("--curiosity", type=str, nargs="?", const="", help="Run autonomous curiosity session (optional topic)")
    parser.add_argument("--rollback", action="store_true", help="Roll back sandbox to previous stable snapshot")
    parser.add_argument("--test-safety", action="store_true", help="Test GAIA's AST security guardrail")
    parser.add_argument("--test-heal", action="store_true", help="Test GAIA's auto-healing on broken code")
    parser.add_argument("--learning", action="store_true", help="View lessons learned mutually by Aria and GAIA")
    parser.add_argument("--diff", action="store_true", help="Show diff between C:\\MyAgent\\agent.py and E:\\MyAgent\\aria_evolved.py")
    parser.add_argument("--promote", action="store_true", help="Promote approved evolved code from E: drive to C:\\MyAgent\\agent.py")
    parser.add_argument("--reset", action="store_true", help="Reset E:\\MyAgent\\aria_evolved.py to match pristine C: baseline")
    parser.add_argument("--vault-status", action="store_true", help="Show Google Cloud Storage Vault status and storage savings")
    parser.add_argument("--vault-sync", action="store_true", help="Upload local snapshots to GCS and purge stale local files")

    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.curiosity is not None:
        cmd_curiosity(args.curiosity if args.curiosity else None)
    elif args.rollback:
        cmd_rollback()
    elif args.test_safety:
        cmd_test_safety()
    elif args.test_heal:
        cmd_test_heal()
    elif args.learning:
        cmd_learning()
    elif args.diff:
        cmd_diff()
    elif args.promote:
        cmd_promote()
    elif args.reset:
        cmd_reset()
    elif args.vault_status:
        cmd_vault_status()
    elif args.vault_sync:
        cmd_vault_sync()
    else:
        cmd_status()


if __name__ == "__main__":
    main()
