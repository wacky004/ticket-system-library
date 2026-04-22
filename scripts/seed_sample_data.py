"""Seed sample tickets for local testing/demo use."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta

from app.db.database import create_ticket, initialize_database


def build_samples(count: int) -> list[dict[str, str]]:
    statuses = ["Open", "In Progress", "Waiting on Client", "Resolved"]
    priorities = ["Low", "Medium", "High", "Urgent"]
    categories = ["Technical", "Account", "Billing", "Operations"]
    samples: list[dict[str, str]] = []

    for idx in range(1, count + 1):
        follow_up = (datetime.now() + timedelta(days=idx % 10)).strftime("%Y-%m-%d")
        samples.append(
            {
                "title": f"Seed Ticket {idx}",
                "client_name": f"Client {((idx - 1) % 5) + 1}",
                "va_name": f"VA {((idx - 1) % 4) + 1}",
                "category": categories[(idx - 1) % len(categories)],
                "priority": priorities[(idx - 1) % len(priorities)],
                "status": statuses[(idx - 1) % len(statuses)],
                "assigned_to": f"Tech {((idx - 1) % 3) + 1}",
                "source": "Seed Script",
                "description": f"Auto-seeded ticket #{idx}.",
                "follow_up_date": follow_up,
                "tags_text": "seed,example",
            }
        )
    return samples


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed sample tickets.")
    parser.add_argument("--count", type=int, default=12, help="Number of sample tickets to add")
    args = parser.parse_args()

    initialize_database()
    samples = build_samples(max(1, args.count))
    for sample in samples:
        create_ticket(sample)

    print(f"Seeded {len(samples)} sample tickets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
