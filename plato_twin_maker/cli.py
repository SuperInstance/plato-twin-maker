"""
CLI entry point for plato-twin-maker.
"""

import sys
from plato_twin_maker.plat_twin_maker import main

def main():
    """Wrapper that calls the plat_twin_maker main function."""
    from plato_twin_maker.plat_twin_maker import PlatoTwinMaker
    import argparse, os, hashlib

    parser = argparse.ArgumentParser(
        description='plato-twin-maker: Create PLATO-twin of any repository'
    )
    parser.add_argument('--repo', required=True, help='URL or local path of repository')
    parser.add_argument('--plato', default='http://localhost:8847', help='PLATO room server URL')
    parser.add_argument('--room-prefix', default='twin', help='Room name prefix')
    parser.add_argument('--local-clone', help='Override clone path')
    parser.add_argument('--dry-run', action='store_true', help='Analyze only, do not submit to PLATO')
    parser.add_argument('--verbose', '-v', action='store_true')

    args = parser.parse_args()

    print(f"[ptwin] Starting twin creation for {args.repo}")

    try:
        maker = PlatoTwinMaker(
            repo_url=args.repo,
            plato_url=args.plato,
            local_clone_path=args.local_clone,
            room_prefix=args.room_prefix,
        )

        twin = maker.make()
        print(f"[ptwin] Twin created: {twin.modules} modules, {len(twin.tiles)} tiles")
        print(f"[ptwin] Room: {twin.room_name}")

        if not args.dry_run:
            test_result = maker.run_tests()
            print(f"[ptwin] Tests: {'PASS' if test_result['tests_passed'] else 'FAIL'}")
            if args.verbose and test_result.get('test_output'):
                print(test_result['test_output'][:500])

        manifest_path = f"/tmp/twin-manifest-{twin.repo_hash}.json"
        import json
        with open(manifest_path, 'w') as f:
            json.dump(twin.__dict__, f, indent=2, default=str)
        print(f"[ptwin] Manifest saved to {manifest_path}")

    except Exception as e:
        print(f"[ptwin] Error: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())