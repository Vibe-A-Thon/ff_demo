#!/usr/bin/env python3
"""Fraud Forge AMC CLI - Command-line interface for AMC operations.

Usage:
    python -m app.cli.amc_cli validate <file.amc>
    python -m app.cli.amc_cli inspect <file.amc>
    python -m app.cli.amc_cli diff <old.amc> <new.amc>
    python -m app.cli.amc_cli export --team <team_id> [--output <dir>]
    python -m app.cli.amc_cli generate-demo --team <team_id> [--version <semver>]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

# Rich console for pretty output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.capsules.amc.amc_service import (
    validate_amc_bytes,
    diff_amc_bytes,
    export_amc,
)
from app.services.capsules.amc.demo_amc_generator import (
    generate_demo_amc,
    save_demo_amc,
)


def print_success(msg: str):
    """Print success message."""
    if RICH_AVAILABLE:
        Console().print(f"[green]✓[/green] {msg}")
    else:
        print(f"✓ {msg}")


def print_error(msg: str):
    """Print error message."""
    if RICH_AVAILABLE:
        Console().print(f"[red]✗[/red] {msg}")
    else:
        print(f"✗ {msg}")


def print_warning(msg: str):
    """Print warning message."""
    if RICH_AVAILABLE:
        Console().print(f"[yellow]![/yellow] {msg}")
    else:
        print(f"! {msg}")


def cmd_validate(args):
    """Validate an AMC file."""
    filepath = Path(args.file)
    if not filepath.exists():
        print_error(f"File not found: {filepath}")
        return 1

    payload = filepath.read_bytes()
    result = validate_amc_bytes(payload)

    if RICH_AVAILABLE:
        console = Console()
        
        # Create results table
        table = Table(title=f"AMC Validation: {filepath.name}", box=box.ROUNDED)
        table.add_column("Check", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Details")

        checks = [
            ("Structure", result.get("structure"), "ZIP format and required files"),
            ("Schemas", result.get("schemas"), "manifest and agent profile schemas"),
            ("Integrity", result.get("integrity"), "SHA-256 hash verification"),
            ("Safety", result.get("policy"), "PII and prohibited content scan"),
            ("Compatibility", result.get("compatibility"), "Runtime version compatibility"),
        ]

        for name, passed, details in checks:
            status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
            table.add_row(name, status, details)

        console.print(table)

        if result.get("valid"):
            console.print(Panel("[green bold]AMC VALIDATED SUCCESSFULLY[/green bold]", expand=False))
        else:
            console.print(Panel(f"[red bold]VALIDATION FAILED[/red bold]\n{', '.join(result.get('errors', []))}", expand=False))
    else:
        print(f"\n=== AMC Validation: {filepath.name} ===\n")
        print(f"Structure: {'PASS' if result.get('structure') else 'FAIL'}")
        print(f"Schemas: {'PASS' if result.get('schemas') else 'FAIL'}")
        print(f"Integrity: {'PASS' if result.get('integrity') else 'FAIL'}")
        print(f"Safety: {'PASS' if result.get('policy') else 'FAIL'}")
        print(f"Compatibility: {'PASS' if result.get('compatibility') else 'FAIL'}")
        print()
        if result.get("valid"):
            print_success("AMC validated successfully")
        else:
            print_error(f"Validation failed: {', '.join(result.get('errors', []))}")

    return 0 if result.get("valid") else 1


def cmd_inspect(args):
    """Inspect an AMC file and display its contents."""
    filepath = Path(args.file)
    if not filepath.exists():
        print_error(f"File not found: {filepath}")
        return 1

    import zipfile
    import io

    payload = filepath.read_bytes()
    
    try:
        zf = zipfile.ZipFile(io.BytesIO(payload), "r")
    except zipfile.BadZipFile:
        print_error("Invalid ZIP archive")
        return 1

    # Read manifest
    manifest = None
    try:
        manifest_data = zf.read("manifest.json")
        manifest = json.loads(manifest_data)
    except (KeyError, json.JSONDecodeError):
        print_error("Could not read manifest.json")
        return 1

    if RICH_AVAILABLE:
        console = Console()
        
        # Basic info panel
        info = f"""
[bold]Team:[/bold] {manifest.get('team_name', 'Unknown')} ({manifest.get('team_id', 'Unknown')})
[bold]Version:[/bold] {manifest.get('team_version', '0.0.0')}
[bold]Created:[/bold] {manifest.get('created_at', 'Unknown')}
[bold]AMC Version:[/bold] {manifest.get('amc_version', '1.0')}
"""
        console.print(Panel(info, title="AMC Package Info", expand=False))

        # Export scope
        scope = manifest.get("export_scope", {})
        console.print("\n[bold]Export Scope:[/bold]")
        console.print(f"  Memory layers: {', '.join(scope.get('include_memory_layers', []))}")
        console.print(f"  Include logs: {scope.get('include_logs', 'none')}")
        console.print(f"  Include models: {scope.get('include_models', False)}")
        console.print(f"  Include battle refs: {scope.get('include_battle_refs', False)}")

        # Agents table
        agents = manifest.get("agents", [])
        if agents:
            table = Table(title="Agents", box=box.ROUNDED)
            table.add_column("Agent ID", style="cyan")
            table.add_column("Role")
            table.add_column("Version")
            
            for agent in agents:
                table.add_row(
                    agent.get("agent_id", "Unknown"),
                    agent.get("role", "Unknown"),
                    agent.get("agent_version", "0.0.0"),
                )
            console.print(table)

        # File tree
        tree = Tree(f"[bold]{filepath.name}[/bold]")
        for name in sorted(zf.namelist()):
            parts = name.split("/")
            current = tree
            for part in parts:
                if part:
                    # Find or create child
                    found = None
                    for child in current._children:
                        if child.label == part:
                            found = child
                            break
                    if found:
                        current = found
                    else:
                        current = current.add(part)
        
        console.print("\n")
        console.print(tree)
    else:
        print(f"\n=== AMC Package Info ===")
        print(f"Team: {manifest.get('team_name', 'Unknown')} ({manifest.get('team_id', 'Unknown')})")
        print(f"Version: {manifest.get('team_version', '0.0.0')}")
        print(f"Created: {manifest.get('created_at', 'Unknown')}")
        print(f"\n=== Agents ===")
        for agent in manifest.get("agents", []):
            print(f"  - {agent.get('agent_id')}: {agent.get('role')} v{agent.get('agent_version')}")
        print(f"\n=== Files ===")
        for name in sorted(zf.namelist()):
            print(f"  {name}")

    zf.close()
    return 0


def cmd_diff(args):
    """Compare two AMC files."""
    old_path = Path(args.old_file)
    new_path = Path(args.new_file)
    
    if not old_path.exists():
        print_error(f"Old file not found: {old_path}")
        return 1
    if not new_path.exists():
        print_error(f"New file not found: {new_path}")
        return 1

    old_payload = old_path.read_bytes()
    new_payload = new_path.read_bytes()

    result = diff_amc_bytes(old_payload, new_payload)

    if RICH_AVAILABLE:
        console = Console()
        
        console.print(Panel(f"[bold]Comparing:[/bold] {old_path.name} → {new_path.name}", expand=False))
        
        # Manifest changes
        manifest_diff = result.get("manifest", {})
        if manifest_diff.get("team_version_old") != manifest_diff.get("team_version_new"):
            console.print(f"\n[bold]Version:[/bold] {manifest_diff.get('team_version_old')} → {manifest_diff.get('team_version_new')}")
        
        # Agent counts
        agent_diff = result.get("agents", {})
        console.print(f"\n[bold]Agents:[/bold] {agent_diff.get('old_count', 0)} → {agent_diff.get('new_count', 0)}")
        
        if agent_diff.get("added"):
            console.print(f"  [green]+ Added: {', '.join(agent_diff['added'])}[/green]")
        if agent_diff.get("removed"):
            console.print(f"  [red]- Removed: {', '.join(agent_diff['removed'])}[/red]")
        
        # Memory changes
        memory_diff = result.get("memory", {})
        console.print("\n[bold]Memory Changes:[/bold]")
        console.print(f"  Semantic: {memory_diff.get('semantic_delta', 0):+d}")
        console.print(f"  Episodic: {memory_diff.get('episodic_delta', 0):+d}")
        console.print(f"  Procedural: {memory_diff.get('procedural_delta', 0):+d}")
        
        # Summary
        console.print(Panel(result.get("summary", "No summary available"), title="Summary", expand=False))
    else:
        print(f"\n=== Diff: {old_path.name} → {new_path.name} ===")
        print(json.dumps(result, indent=2))

    return 0


def cmd_export(args):
    """Export an AMC file for a team."""
    print_warning("Export requires a running database. Use the API or web interface for production exports.")
    print(f"Would export team '{args.team}' to '{args.output or './output'}'")
    return 0


def cmd_generate_demo(args):
    """Generate a demo AMC file."""
    path = save_demo_amc(
        output_path=args.output or "./demo_amc",
        team_id=args.team,
        team_version=args.version,
    )
    print_success(f"Generated demo AMC: {path}")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ff-amc",
        description="Fraud Forge AMC CLI - Manage Agent Memory Capsules",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate an AMC file")
    p_validate.add_argument("file", help="Path to .amc file")
    p_validate.set_defaults(func=cmd_validate)

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect an AMC file")
    p_inspect.add_argument("file", help="Path to .amc file")
    p_inspect.set_defaults(func=cmd_inspect)

    # diff
    p_diff = subparsers.add_parser("diff", help="Compare two AMC files")
    p_diff.add_argument("old_file", help="Path to old .amc file")
    p_diff.add_argument("new_file", help="Path to new .amc file")
    p_diff.set_defaults(func=cmd_diff)

    # export
    p_export = subparsers.add_parser("export", help="Export an AMC file")
    p_export.add_argument("--team", "-t", required=True, help="Team ID to export")
    p_export.add_argument("--output", "-o", help="Output directory")
    p_export.set_defaults(func=cmd_export)

    # generate-demo
    p_demo = subparsers.add_parser("generate-demo", help="Generate a demo AMC file")
    p_demo.add_argument("--team", "-t", default="blue", help="Team ID (default: blue)")
    p_demo.add_argument("--version", "-v", default="1.2.0", help="Version (default: 1.2.0)")
    p_demo.add_argument("--output", "-o", help="Output directory")
    p_demo.set_defaults(func=cmd_generate_demo)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
