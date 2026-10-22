"""NetArchitect Layer 3 Routing Protocol Decision Engine."""

from __future__ import annotations

from netarchitect.models import (
    Rationale,
    RoutingDecision,
    RoutingProtocol,
    ScenarioInput,
)

_SINGLE_AREA_SUBNET_THRESHOLD = 50


def decide_routing(scenario: ScenarioInput) -> tuple[RoutingDecision, Rationale]:
    """
    Evaluate the scenario parameters and select the appropriate routing
    protocol(s).  Returns (RoutingDecision, Rationale).
    """
    num_subnets = len(scenario.subnet_requirements)
    is_multi_site = scenario.num_sites > 1
    is_multi_as = scenario.is_multi_as
    is_cloud = scenario.cloud_vpc_connected

    if is_multi_as or is_cloud:
        protocol = RoutingProtocol.OSPF_WITH_BGP
        areas = list(range(scenario.num_sites))  # Area 0 backbone + area per site
        if 0 not in areas:
            areas.insert(0, 0)
        bgp_asn = 65001  # Private ASN default
        rfc_refs = ["RFC 2328 (OSPFv2)", "RFC 4271 (BGP-4)", "RFC 6996 (Private ASNs)"]
        rationale_text = (
            f"Network spans {'multiple Autonomous Systems' if is_multi_as else 'cloud VPC peering'} "
            f"across {scenario.num_sites} sites with {num_subnets} subnets. "
            f"Selected Multi-Area OSPF for internal routing domain isolation, "
            f"failure containment, and route summarisation at ABR boundaries "
            f"(RFC 2328). eBGP (RFC 4271) is additionally required for "
            f"{'inter-AS path selection' if is_multi_as else 'Cloud VPC route exchange'} "
            f"with policy-based path manipulation and route filtering at ASBR. "
            f"Private ASN {bgp_asn} assigned per RFC 6996."
        )
    elif num_subnets >= _SINGLE_AREA_SUBNET_THRESHOLD or (is_multi_site and num_subnets > 20):
        # Large single-AS → Multi-Area OSPF
        protocol = RoutingProtocol.OSPF_MULTI_AREA
        areas = list(range(scenario.num_sites))
        if 0 not in areas:
            areas.insert(0, 0)
        bgp_asn = None
        rfc_refs = ["RFC 2328 (OSPFv2)"]
        rationale_text = (
            f"Single Autonomous System with {num_subnets} subnets across "
            f"{scenario.num_sites} sites. Subnet count {'exceeds' if num_subnets >= _SINGLE_AREA_SUBNET_THRESHOLD else 'approaches'} "
            f"the {_SINGLE_AREA_SUBNET_THRESHOLD}-subnet threshold for single-area OSPF. "
            f"Selected Multi-Area OSPFv2 (RFC 2328) with Area 0 backbone and "
            f"one area per site to contain SPF flooding, reduce LSDB size at "
            f"each ABR, and enable inter-area route summarisation. Dijkstra "
            f"SPF runs independently within each area, limiting convergence "
            f"blast radius."
        )
    else:
        # Simple single-AS → Single-Area OSPF
        protocol = RoutingProtocol.OSPF_SINGLE_AREA
        areas = [0]
        bgp_asn = None
        rfc_refs = ["RFC 2328 (OSPFv2)"]
        rationale_text = (
            f"Single Autonomous System with {num_subnets} subnets "
            f"({'single site' if scenario.num_sites == 1 else f'{scenario.num_sites} sites'}) — "
            f"well below the {_SINGLE_AREA_SUBNET_THRESHOLD}-subnet multi-area threshold. "
            f"Selected Single-Area OSPFv2 Area 0 (RFC 2328) for link-state "
            f"fast convergence via Dijkstra SPF, loop-free shortest-path "
            f"forwarding, and zero external routing protocol overhead. "
            f"All interfaces participate in Area 0 with a flat LSDB."
        )

    decision = RoutingDecision(
        protocol=protocol,
        ospf_areas=areas,
        bgp_asn=bgp_asn,
        rationale=rationale_text,
        rfc_references=rfc_refs,
    )

    rationale = Rationale(
        decision_category="Layer 3 Routing Protocol",
        decision_summary=f"{protocol.value} selected",
        physical_justification=(
            f"{scenario.num_sites} sites, {num_subnets} subnets, "
            f"multi-AS={is_multi_as}, cloud={is_cloud}"
        ),
        rfc_ieee_citations=rfc_refs,
        detail=rationale_text,
    )

    return decision, rationale
