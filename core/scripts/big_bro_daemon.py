"""
scripts/big_bro_daemon.py — Standalone Headless Daemon for Big Bro Antigravity
Allows Big Bro Antigravity to monitor Aria's mailbox, review pending tools, and provide guidance
completely headlessly without needing the Antigravity IDE open.
"""

import os
import sys
import time
import argparse
from datetime import datetime

# Set up project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.big_bro_bridge import BigBroBridge, TokenBudgetGuard


def process_mailbox_once(bridge: BigBroBridge, verbose: bool = True) -> int:
    """Processes all pending messages in the Big Bro mailbox."""
    pending = bridge.get_pending_messages()
    if not pending:
        if verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Big Bro Mailbox is clear. No pending questions from Aria.")
        return 0

    processed_count = 0
    for msg in pending:
        msg_id = msg.get("id")
        topic = msg.get("topic", "")
        code = msg.get("code_snippet", "")
        sender = msg.get("sender", "Aria")

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📬 Reviewing request from {sender}: {topic}")

        # Check with Big Bro engine
        response = bridge.ask(topic=topic, code_or_path=code)
        bridge.resolve_message(msg_id, response)
        processed_count += 1
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Advice delivered:\n{response}\n")

    return processed_count


def run_daemon(poll_interval: int = 10):
    """Runs the headless background monitoring loop."""
    print(f"==================================================")
    print(f"  🚀 Big Bro Antigravity Standalone Daemon Started")
    print(f"  Watching Aria's mailbox every {poll_interval}s")
    print(f"  Headless mode active (No IDE required!)")
    print(f"==================================================\n")

    bridge = BigBroBridge()
    guard = TokenBudgetGuard()

    try:
        while True:
            budget_state = guard.load_state()
            # Process pending items
            process_mailbox_once(bridge, verbose=False)
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\n👋 Big Bro Daemon stopped safely.")


def main():
    parser = argparse.ArgumentParser(description="Big Bro Antigravity Standalone Headless Daemon")
    parser.add_argument("--once", action="store_true", help="Process pending requests once and exit immediately")
    parser.add_argument("--daemon", action="store_true", help="Run as continuous background monitoring loop")
    parser.add_argument("--interval", type=int, default=10, help="Polling interval in seconds (default: 10)")
    parser.add_argument("--status", action="store_true", help="Check current mailbox and token budget status")

    args = parser.parse_args()
    bridge = BigBroBridge()
    guard = TokenBudgetGuard()

    if args.status:
        state = guard.load_state()
        pending = bridge.get_pending_messages()
        print(f"\n--- Big Bro Status ---")
        print(f"Daily Tokens Used: {state.get('tokens_used', 0)} / {guard.daily_limit}")
        print(f"Requests Today:    {state.get('requests_today', 0)} / {guard.max_requests}")
        print(f"Pending Messages:  {len(pending)}")
        for p in pending:
            print(f"  • [{p.get('id')}] {p.get('sender')}: {p.get('topic')}")
        return

    if args.once:
        process_mailbox_once(bridge, verbose=True)
    elif args.daemon:
        run_daemon(poll_interval=args.interval)
    else:
        # Default to checking once
        process_mailbox_once(bridge, verbose=True)


if __name__ == "__main__":
    main()
