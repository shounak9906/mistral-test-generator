#!/usr/bin/env python3
"""
CLI for the Spec→Test Generator project.
Allows running generation and test execution directly from the command line.

Usage examples:
    python cli.py generate under_test.py "n/a"
    python cli.py run
"""

import argparse
import os
import json
from pathlib import Path
from main import generate_and_save_bundle, _run_enabled, run_bundle_tests, BundleRequest

def main():
    parser = argparse.ArgumentParser(
        description="Spec→Test Generator CLI (using FastAPI backend logic)"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ------------- generate -------------
    gen_parser = subparsers.add_parser("generate", help="Generate and save tests")
    gen_parser.add_argument("code_path", type=str, help="Path to Python module (e.g. under_test.py)")
    # Optional spec flag instead of positional argument
    gen_parser.add_argument(
        "--spec", "-s",
        type=str,
        default="n/a",
        help="Description of what the function does",
    )
    gen_parser.add_argument("--cleanup", action="store_true", help="Cleanup old tests (per-symbol mode)")

    # ------------- run -------------
    run_parser = subparsers.add_parser("run", help="Run generated tests via pytest")
    run_parser.add_argument("--enable", action="store_true", help="Force enable run mode (sets ENABLE_RUN=1)")

    args = parser.parse_args()

    if args.command == "generate":
        code = Path(args.code_path).read_text()

        req = BundleRequest(
            code=code,
            spec=args.spec,
            module_path=args.code_path,
            tests_mode="per_symbol" if args.cleanup else "single",
            cleanup_old=args.cleanup
        )

        result = generate_and_save_bundle(req)
        print("✅ Generated tests:")
        print(json.dumps(result.model_dump(), indent=2))


    elif args.command == "run":
        if args.enable:
            os.environ["ENABLE_RUN"] = "1"

        if not _run_enabled():
            print("❌ Run mode disabled. Use '--enable' to override.")
            return

        exit_code, out = run_bundle_tests()
        print("✅ Pytest output:\n")
        print(out)
        print(f"Exit code: {exit_code}")

if __name__ == "__main__":
    main()
