"""NetArchitect interactive terminal interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure Windows terminal handles UTF-8 emojis and special characters cleanly
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich import box

from netarchitect.orchestrator import run_design, export_config, export_rationale_report
from netarchitect.presets import list_presets, load_preset
from netarchitect.models import ScenarioInput, NetworkDesign

app = typer.Typer(
    name="netarchitect",
    help="NetArchitect: Algorithmic Network Planning & Self-Explaining Architecture Engine",
    add_completion=False,
)
console = Console()

EXPORTS_DIR = Path("exports")


def _print_header() -> None:
    console.print(Panel.fit(
        "[bold cyan]NetArchitect[/bold cyan]  🏗️\n"
        "[dim]Algorithmic Network Planning & Self-Explaining Architecture Engine[/dim]\n"
        "[dim]CIC-307 Computer Networks Mini-Project[/dim]",
        border_style="bright_blue",
        padding=(1, 4),
    ))
    console.print()


def _print_vlsm_table(design: NetworkDesign) -> None:
    if design.vlsm_result is None:
        return
    table = Table(
        title="📊  VLSM Subnet Allocations",
        box=box.ROUNDED,
        title_style="bold green",
        header_style="bold white on dark_green",
        show_lines=True,
    )
    table.add_column("Subnet Name", style="cyan", no_wrap=True)
    table.add_column("VLAN", justify="center")
    table.add_column("CIDR", style="yellow")
    table.add_column("Mask", style="dim")
    table.add_column("Wildcard", style="magenta")
    table.add_column("Gateway", style="green")
    table.add_column("Broadcast", style="red")
    table.add_column("Hosts", justify="right")
    table.add_column("Capacity", justify="right")
    table.add_column("Efficiency", justify="right")

    for a in design.vlsm_result.allocations:
        eff_style = "green" if a.efficiency_pct > 75 else ("yellow" if a.efficiency_pct > 50 else "red")
        table.add_row(
            a.name,
            str(a.vlan_id or "—"),
            a.cidr_notation,
            str(a.subnet_mask),
            str(a.wildcard_mask),
            str(a.first_usable_host),
            str(a.broadcast_address),
            str(a.required_hosts),
            str(a.usable_host_capacity),
            f"[{eff_style}]{a.efficiency_pct}%[/{eff_style}]",
        )
    console.print(table)
    console.print(
        f"  [bold]Overall efficiency:[/bold] {design.vlsm_result.overall_efficiency_pct}%  "
        f"| Root: [cyan]{design.vlsm_result.root_network}[/cyan]"
    )
    console.print()


def _print_media_table(design: NetworkDesign) -> None:
    if not design.media_decisions:
        return
    table = Table(
        title="🔌  Physical Media Decisions",
        box=box.ROUNDED,
        title_style="bold blue",
        header_style="bold white on dark_blue",
        show_lines=True,
    )
    table.add_column("Link", style="cyan", no_wrap=True)
    table.add_column("Distance", justify="right")
    table.add_column("Medium", style="yellow")
    table.add_column("Transceiver", style="magenta")
    table.add_column("Max Reach", justify="right")
    table.add_column("Standard", style="dim")

    for m in design.media_decisions:
        table.add_row(
            f"{m.source_node} ↔ {m.destination_node}",
            f"{m.distance_m:,.0f} m",
            m.recommended_medium.value,
            m.transceiver.value,
            f"{m.max_reach_m:,.0f} m",
            m.ieee_standard,
        )
    console.print(table)
    console.print()


def _print_optical_budgets(design: NetworkDesign) -> None:
    if not design.optical_budgets:
        return
    table = Table(
        title="🔬  Optical Link Budgets",
        box=box.ROUNDED,
        title_style="bold magenta",
        header_style="bold white on purple4",
        show_lines=True,
    )
    table.add_column("Link", style="cyan")
    table.add_column("Distance", justify="right")
    table.add_column("Total Loss", justify="right")
    table.add_column("Margin", justify="right")
    table.add_column("Viable", justify="center")

    for b in design.optical_budgets:
        viable = "[green]✅ Yes[/green]" if b.is_viable else "[red]❌ No[/red]"
        margin_style = "green" if b.link_margin_dB > 3 else ("yellow" if b.link_margin_dB > 0 else "red")
        table.add_row(
            b.link_id,
            f"{b.distance_km:,.2f} km",
            f"{b.total_loss_dB:.2f} dB",
            f"[{margin_style}]{b.link_margin_dB:.2f} dB[/{margin_style}]",
            viable,
        )
    console.print(table)
    console.print()


def _print_routing(design: NetworkDesign) -> None:
    if design.routing_decision is None:
        return
    rd = design.routing_decision
    console.print(Panel(
        f"[bold]{rd.protocol.value}[/bold]\n\n"
        f"OSPF Areas: {rd.ospf_areas}\n"
        f"BGP ASN: {rd.bgp_asn or 'N/A'}\n\n"
        f"[dim]{rd.rationale}[/dim]\n\n"
        f"[bold]References:[/bold] {', '.join(rd.rfc_references)}",
        title="🌐  Routing Protocol Decision",
        border_style="bright_green",
    ))
    console.print()


@app.command("run")
def cmd_run(
    preset: str = typer.Option(None, "--preset", "-p", help="Preset name (campus_lan, metro_man, global_wan)"),
    custom_file: str = typer.Option(None, "--file", "-f", help="Path to custom scenario JSON file"),
    export_dir: str = typer.Option("exports", "--export-dir", "-o", help="Output directory for exports"),
) -> None:
    """Run the NetArchitect design pipeline on a preset or custom scenario."""
    _print_header()

    # ── Load scenario ─────────────────────────────────────────────────────
    if custom_file:
        console.print(f"[bold]Loading custom scenario from:[/bold] {custom_file}")
        with open(custom_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        scenario = ScenarioInput(**data)
    elif preset:
        console.print(f"[bold]Loading preset:[/bold] [cyan]{preset}[/cyan]")
        scenario = load_preset(preset)
    else:
        # Interactive selection
        available = list_presets()
        console.print("[bold]Available presets:[/bold]")
        for i, name in enumerate(available, 1):
            console.print(f"  [cyan]{i}.[/cyan] {name}")
        choice = Prompt.ask(
            "Select a preset number or enter a custom JSON path",
            default="1",
        )
        if choice.isdigit() and 1 <= int(choice) <= len(available):
            preset = available[int(choice) - 1]
            scenario = load_preset(preset)
        else:
            with open(choice, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            scenario = ScenarioInput(**data)

    console.print(f"  [dim]Scenario:[/dim] {scenario.scenario_name}")
    console.print(f"  [dim]Scale:[/dim] {scenario.scale.value}")
    console.print(f"  [dim]Root:[/dim] {scenario.root_network}")
    console.print(f"  [dim]Subnets:[/dim] {len(scenario.subnet_requirements)}")
    console.print(f"  [dim]Links:[/dim] {len(scenario.links)}")
    console.print()

    with console.status("[bold green]Running NetArchitect design pipeline…[/bold green]"):
        design = run_design(scenario)

    _print_vlsm_table(design)
    _print_media_table(design)
    _print_optical_budgets(design)
    _print_routing(design)

    out = Path(export_dir)
    safe_name = scenario.scenario_name.lower().replace(" ", "_").replace("–", "").replace("—", "")[:40]

    cfg_path = export_config(design, out / f"{safe_name}.cfg")
    console.print(f"[bold green]✅  Cisco config exported:[/bold green] {cfg_path}")

    report_path = export_rationale_report(design, out / f"{safe_name}_rationale.md")
    console.print(f"[bold green]✅  Rationale report exported:[/bold green] {report_path}")

    console.print()
    console.print("[bold cyan]Pipeline complete.[/bold cyan] 🎉")


@app.command("list-presets")
def cmd_list_presets() -> None:
    """List all available preset scenarios."""
    _print_header()
    presets = list_presets()
    for name in presets:
        console.print(f"  • [cyan]{name}[/cyan]")


@app.command("validate")
def cmd_validate(
    file: str = typer.Argument(..., help="Path to a scenario JSON file to validate"),
) -> None:
    """Validate a custom scenario JSON file against the Pydantic schema."""
    _print_header()
    try:
        with open(file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        scenario = ScenarioInput(**data)
        console.print(f"[bold green]✅  Valid scenario:[/bold green] {scenario.scenario_name}")
        console.print(f"  Subnets: {len(scenario.subnet_requirements)}, Links: {len(scenario.links)}")
    except Exception as e:
        console.print(f"[bold red]❌  Validation failed:[/bold red] {e}")
        raise typer.Exit(code=1)


def main() -> None:
    """Entry point for `python -m netarchitect.cli`."""
    app()


if __name__ == "__main__":
    main()
