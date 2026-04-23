"""Public entrypoint for writing the current reproduction audit artifact."""

from __future__ import annotations

import argparse

from agentconductor.application.reproduction import write_reproduction_audit_entrypoint


def main() -> None:
    """CLI entrypoint for the current paper-reproduction audit."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the output reproduction-audit JSON artifact.",
    )
    args = parser.parse_args()

    audit = write_reproduction_audit_entrypoint(args.output)
    print(
        "agentconductor-repro:",
        f"claim={audit.overall_claim.value}",
        f"exact_ready={str(audit.exact_reproduction_ready).lower()}",
        f"blocking_gaps={len(audit.blocking_gap_ids)}",
    )
