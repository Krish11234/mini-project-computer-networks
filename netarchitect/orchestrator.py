"""NetArchitect design pipeline orchestrator."""

from __future__ import annotations

from pathlib import Path

from netarchitect.engines.config_generator import (
    build_device_configs_from_design,
    generate_device_config,
    generate_full_config,
)
from netarchitect.engines.media_engine import decide_all_media
from netarchitect.engines.routing_engine import decide_routing
from netarchitect.engines.vlsm_engine import allocate_vlsm
from netarchitect.models import NetworkDesign, Rationale, ScenarioInput


def run_design(scenario: ScenarioInput) -> NetworkDesign:
    """Execute the full NetArchitect design pipeline for a given scenario."""
    rationales: list[Rationale] = []

    media_decisions, media_rationales, optical_budgets = decide_all_media(
        scenario.links
    )
    rationales.extend(media_rationales)

    vlsm_result, vlsm_rationales = allocate_vlsm(scenario)
    rationales.extend(vlsm_rationales)

    routing_decision, routing_rationale = decide_routing(scenario)
    rationales.append(routing_rationale)

    design = NetworkDesign(
        scenario_name=scenario.scenario_name,
        scale=scenario.scale,
        media_decisions=media_decisions,
        optical_budgets=optical_budgets,
        vlsm_result=vlsm_result,
        routing_decision=routing_decision,
        rationales=rationales,
    )

    device_configs = build_device_configs_from_design(design)
    design.device_configs = device_configs

    return design



def export_config(design: NetworkDesign, output_path: str | Path) -> Path:
    """
    Generate the merged Cisco IOS config and write it to disk.
    Creates parent directories if they don't exist.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cfg_text = generate_full_config(design)
    path.write_text(cfg_text, encoding="utf-8")
    return path


def export_rationale_report(design: NetworkDesign, output_path: str | Path) -> Path:
    """
    Write a human-readable architectural rationale report to a Markdown file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        f"# Architectural Rationale Report — {design.scenario_name}",
        "",
        f"**Scale:** {design.scale.value}",
        "",
    ]

    # VLSM summary
    if design.vlsm_result:
        lines.append("## VLSM Allocation Summary")
        lines.append("")
        lines.append(f"Root Network: `{design.vlsm_result.root_network}`")
        lines.append(f"Total Requested Hosts: {design.vlsm_result.total_requested_hosts:,}")
        lines.append(f"Overall Efficiency: {design.vlsm_result.overall_efficiency_pct}%")
        lines.append("")
        lines.append("| Subnet | CIDR | Hosts | Capacity | Efficiency | Wildcard |")
        lines.append("|--------|------|------:|--------:|-----------:|----------|")
        for a in design.vlsm_result.allocations:
            lines.append(
                f"| {a.name} | {a.cidr_notation} | {a.required_hosts} | "
                f"{a.usable_host_capacity} | {a.efficiency_pct}% | "
                f"{a.wildcard_mask} |"
            )
        lines.append("")

    # Routing
    if design.routing_decision:
        lines.append("## Routing Protocol Decision")
        lines.append("")
        lines.append(f"**Selected:** {design.routing_decision.protocol.value}")
        lines.append("")
        lines.append(design.routing_decision.rationale)
        lines.append("")

    # Media decisions
    if design.media_decisions:
        lines.append("## Physical Media Decisions")
        lines.append("")
        lines.append("| Link | Distance | Medium | Transceiver | Standard |")
        lines.append("|------|--------:|--------|-------------|----------|")
        for m in design.media_decisions:
            lines.append(
                f"| {m.source_node} ↔ {m.destination_node} | {m.distance_m}m | "
                f"{m.recommended_medium.value} | {m.transceiver.value} | "
                f"{m.ieee_standard} |"
            )
        lines.append("")

    # Optical budgets
    if design.optical_budgets:
        lines.append("## Optical Link Budgets")
        lines.append("")
        lines.append("| Link | Distance | Total Loss | Margin | Viable |")
        lines.append("|------|--------:|-----------:|-------:|--------|")
        for b in design.optical_budgets:
            status = "✅ Yes" if b.is_viable else "❌ No"
            lines.append(
                f"| {b.link_id} | {b.distance_km} km | {b.total_loss_dB} dB | "
                f"{b.link_margin_dB} dB | {status} |"
            )
        lines.append("")

    # All rationales
    lines.append("## Detailed Engineering Rationales")
    lines.append("")
    for i, r in enumerate(design.rationales, 1):
        lines.append(f"### {i}. {r.decision_summary}")
        lines.append(f"**Category:** {r.decision_category}")
        if r.rfc_ieee_citations:
            lines.append(f"**Citations:** {', '.join(r.rfc_ieee_citations)}")
        lines.append("")
        lines.append(r.detail)
        lines.append("")

    content = "\n".join(lines)
    path.write_text(content, encoding="utf-8")
    return path
