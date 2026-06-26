from __future__ import annotations

import argparse
from pathlib import Path

from qedsoft.models import ProjectConfig
from qedsoft.orchestrator import QEDSoft


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qedsoft",
        description="QEDSoft: natural-language to formal RTL verification artifacts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="Generate and verify SVA/Lean artifacts.")
    verify.add_argument("--spec", required=True, type=Path, help="Natural-language chip spec.")
    verify.add_argument("--rtl", type=Path, help="Optional RTL/SystemVerilog source.")
    verify.add_argument("--out", type=Path, default=Path("runs/qedsoft"), help="Output directory.")
    verify.add_argument("--top", help="Override top module name.")
    verify.add_argument("--clock", help="Override clock signal.")
    verify.add_argument("--reset", help="Override reset signal.")
    verify.add_argument("--reset-active-high", action="store_true", help="Treat reset as active high.")
    verify.add_argument("--no-external-tools", action="store_true", help="Skip Lean/EDA tool subprocesses.")
    verify.add_argument("--repair-rounds", type=int, default=2, help="Max structured repair rounds.")
    verify.add_argument("--memory", type=Path, help="Optional feedback-memory JSON path.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify":
        config = ProjectConfig(
            top_module=args.top,
            clock=args.clock,
            reset=args.reset,
            reset_active_low=False if args.reset_active_high else None,
            use_external_tools=not args.no_external_tools,
            max_repair_rounds=args.repair_rounds,
            memory_path=args.memory,
        )
        result = QEDSoft(config).run_from_paths(args.spec, args.rtl, args.out)
        print(f"QEDSoft output: {result.output_dir}")
        print(f"Success: {result.success}")
        print(f"Report: {result.output_dir / 'qedsoft_report.md'}")
        return 0 if result.success else 2

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
