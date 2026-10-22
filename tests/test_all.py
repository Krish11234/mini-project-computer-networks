"""NetArchitect comprehensive test suite."""

from __future__ import annotations

import math
from ipaddress import IPv4Address, IPv4Network

import pytest

from netarchitect.exceptions import (
    PhysicalDistanceViolationError,
    SubnetExhaustionError,
    SubnetOverlapError,
)
from netarchitect.models import (
    LinkInput,
    MediaType,
    ScenarioInput,
    SubnetRequirement,
)
from netarchitect.engines.media_engine import decide_media, decide_all_media
from netarchitect.engines.vlsm_engine import allocate_vlsm, _compute_wildcard_mask, _compute_subnet_mask
from netarchitect.engines.routing_engine import decide_routing
from netarchitect.engines.config_generator import generate_device_config, build_device_configs_from_design
from netarchitect.orchestrator import run_design
from netarchitect.presets import list_presets, load_preset


class TestMediaEngine:
    """Tests for L1 media selection and boundary enforcement."""

    def test_cat6a_within_100m(self):
        link = LinkInput(link_id="T1", source_node="A", destination_node="B", distance_m=50)
        dec, rat, budget = decide_media(link)
        assert dec.recommended_medium == MediaType.CAT6A
        assert budget is None  # No optical budget for copper

    def test_cat6a_at_boundary_100m(self):
        link = LinkInput(link_id="T2", source_node="A", destination_node="B", distance_m=100)
        dec, rat, budget = decide_media(link)
        assert dec.recommended_medium == MediaType.CAT6A

    def test_om4_mmf_at_101m(self):
        link = LinkInput(link_id="T3", source_node="A", destination_node="B", distance_m=101)
        dec, rat, budget = decide_media(link)
        assert dec.recommended_medium == MediaType.OM4_MMF
        assert budget is not None

    def test_om4_mmf_at_boundary_400m(self):
        link = LinkInput(link_id="T4", source_node="A", destination_node="B", distance_m=400)
        dec, rat, budget = decide_media(link)
        assert dec.recommended_medium == MediaType.OM4_MMF

    def test_os2_smf_at_401m(self):
        link = LinkInput(link_id="T5", source_node="A", destination_node="B", distance_m=401)
        dec, rat, budget = decide_media(link)
        assert dec.recommended_medium == MediaType.OS2_SMF

    def test_os2_smf_long_haul(self):
        link = LinkInput(link_id="T6", source_node="A", destination_node="B", distance_m=15000)
        dec, rat, budget = decide_media(link)
        assert dec.recommended_medium == MediaType.OS2_SMF
        assert budget is not None
        assert budget.distance_km == 15.0

    def test_forced_copper_over_100m_raises_error(self):
        """state.yaml: boundary_violation → PhysicalDistanceViolationError."""
        link = LinkInput(
            link_id="T7", source_node="A", destination_node="B",
            distance_m=150, forced_medium=MediaType.CAT6A,
        )
        with pytest.raises(PhysicalDistanceViolationError) as exc_info:
            decide_media(link)
        assert "IEEE 802.3an" in str(exc_info.value)

    def test_forced_mmf_over_400m_raises_error(self):
        link = LinkInput(
            link_id="T8", source_node="A", destination_node="B",
            distance_m=500, forced_medium=MediaType.OM4_MMF,
        )
        with pytest.raises(PhysicalDistanceViolationError):
            decide_media(link)

    def test_optical_budget_viability(self):
        link = LinkInput(link_id="T9", source_node="A", destination_node="B", distance_m=200)
        dec, rat, budget = decide_media(link)
        assert budget is not None
        assert budget.is_viable  # 200m should be well within OM4 budget

    def test_rationale_contains_ieee_citation(self):
        link = LinkInput(link_id="T10", source_node="X", destination_node="Y", distance_m=75)
        dec, rat, budget = decide_media(link)
        assert "IEEE" in rat.detail
        assert len(rat.rfc_ieee_citations) > 0

def _make_scenario(subnets: list[SubnetRequirement], root: str = "10.0.0.0/16") -> ScenarioInput:
    return ScenarioInput(
        scenario_name="Test",
        scale="Campus LAN",
        root_network=IPv4Network(root),
        subnet_requirements=subnets,
    )


class TestVLSMEngine:
    """Tests for the bitwise VLSM allocation engine."""

    def test_basic_allocation(self):
        reqs = [
            SubnetRequirement(name="A", required_hosts=100),
            SubnetRequirement(name="B", required_hosts=50),
        ]
        scenario = _make_scenario(reqs)
        result, rationales = allocate_vlsm(scenario)
        assert len(result.allocations) == 2

    def test_descending_sort_order(self):
        """state.yaml: Host requirements sorted DESCENDING before allocation."""
        reqs = [
            SubnetRequirement(name="Small", required_hosts=10),
            SubnetRequirement(name="Large", required_hosts=500),
            SubnetRequirement(name="Medium", required_hosts=100),
        ]
        scenario = _make_scenario(reqs)
        result, _ = allocate_vlsm(scenario)
        # Allocations should be sorted: Large (500), Medium (100), Small (10)
        assert result.allocations[0].name == "Large"
        assert result.allocations[1].name == "Medium"
        assert result.allocations[2].name == "Small"

    def test_zero_address_overlap(self):
        """state.yaml: Zero tolerance for overlapping address blocks."""
        reqs = [
            SubnetRequirement(name=f"Net{i}", required_hosts=30)
            for i in range(10)
        ]
        scenario = _make_scenario(reqs)
        result, _ = allocate_vlsm(scenario)

        networks = [
            IPv4Network(f"{a.network_address}/{a.cidr_prefix}")
            for a in result.allocations
        ]
        # No pair of networks should overlap
        for i, n1 in enumerate(networks):
            for n2 in networks[i+1:]:
                assert not n1.overlaps(n2), f"Overlap: {n1} ↔ {n2}"

    def test_subnet_attributes_complete(self):
        """state.yaml: Every subnet must output all required attributes."""
        reqs = [SubnetRequirement(name="Test", required_hosts=60, vlan_id=10)]
        scenario = _make_scenario(reqs)
        result, _ = allocate_vlsm(scenario)

        alloc = result.allocations[0]
        assert alloc.network_address is not None
        assert alloc.cidr_prefix > 0
        assert alloc.subnet_mask is not None
        assert alloc.wildcard_mask is not None
        assert alloc.first_usable_host is not None
        assert alloc.last_usable_host is not None
        assert alloc.broadcast_address is not None
        assert alloc.usable_host_capacity >= alloc.required_hosts
        assert 0 <= alloc.efficiency_pct <= 100

    def test_broadcast_and_gateway_addresses(self):
        reqs = [SubnetRequirement(name="Net1", required_hosts=100)]
        scenario = _make_scenario(reqs, root="192.168.0.0/24")
        result, _ = allocate_vlsm(scenario)
        alloc = result.allocations[0]

        # For a /25 block starting at 192.168.0.0:
        net = IPv4Network(f"{alloc.network_address}/{alloc.cidr_prefix}")
        assert alloc.first_usable_host == net.network_address + 1
        assert alloc.broadcast_address == net.broadcast_address
        assert alloc.last_usable_host == net.broadcast_address - 1

    def test_subnet_exhaustion_error(self):
        """state.yaml: Raise SubnetExhaustionError when capacity exceeded."""
        reqs = [SubnetRequirement(name="Huge", required_hosts=300)]
        scenario = _make_scenario(reqs, root="10.0.0.0/24")  # Only 254 usable
        with pytest.raises(SubnetExhaustionError):
            allocate_vlsm(scenario)

    def test_efficiency_calculation(self):
        reqs = [SubnetRequirement(name="Exact", required_hosts=126)]
        scenario = _make_scenario(reqs)
        result, _ = allocate_vlsm(scenario)
        alloc = result.allocations[0]
        expected_eff = round((126 / alloc.usable_host_capacity) * 100, 2)
        assert alloc.efficiency_pct == expected_eff

class TestWildcardMask:
    """Tests for inverted wildcard mask calculations on arbitrary prefixes."""

    @pytest.mark.parametrize("prefix,expected_wildcard", [
        (8,  "0.255.255.255"),
        (16, "0.0.255.255"),
        (24, "0.0.0.255"),
        (25, "0.0.0.127"),
        (26, "0.0.0.63"),
        (27, "0.0.0.31"),
        (28, "0.0.0.15"),
        (29, "0.0.0.7"),
        (30, "0.0.0.3"),
        (32, "0.0.0.0"),
        (20, "0.0.15.255"),
        (18, "0.0.63.255"),
        (13, "0.7.255.255"),
    ])
    def test_wildcard_mask(self, prefix: int, expected_wildcard: str):
        wc = _compute_wildcard_mask(prefix)
        assert str(wc) == expected_wildcard

    @pytest.mark.parametrize("prefix,expected_mask", [
        (24, "255.255.255.0"),
        (25, "255.255.255.128"),
        (26, "255.255.255.192"),
        (27, "255.255.255.224"),
        (16, "255.255.0.0"),
        (8,  "255.0.0.0"),
    ])
    def test_subnet_mask(self, prefix: int, expected_mask: str):
        sm = _compute_subnet_mask(prefix)
        assert str(sm) == expected_mask

    def test_mask_wildcard_complement(self):
        """Mask + Wildcard should bitwise-OR to 0xFFFFFFFF."""
        for prefix in range(1, 33):
            mask = int(_compute_subnet_mask(prefix))
            wc = int(_compute_wildcard_mask(prefix))
            assert mask | wc == 0xFFFFFFFF
            assert mask & wc == 0

class TestRoutingEngine:
    """Tests for routing protocol decision thresholds."""

    def test_single_area_ospf_small_network(self):
        reqs = [SubnetRequirement(name=f"N{i}", required_hosts=10) for i in range(5)]
        scenario = _make_scenario(reqs)
        scenario.num_sites = 1
        decision, _ = decide_routing(scenario)
        assert decision.protocol.value == "Single-Area OSPFv2 (Area 0)"
        assert decision.ospf_areas == [0]

    def test_multi_area_ospf_many_subnets(self):
        reqs = [SubnetRequirement(name=f"N{i}", required_hosts=5) for i in range(55)]
        scenario = _make_scenario(reqs)
        scenario.num_sites = 3
        decision, _ = decide_routing(scenario)
        assert "Multi-Area" in decision.protocol.value

    def test_bgp_for_multi_as(self):
        reqs = [SubnetRequirement(name="N1", required_hosts=10)]
        scenario = _make_scenario(reqs)
        scenario.is_multi_as = True
        decision, _ = decide_routing(scenario)
        assert "BGP" in decision.protocol.value
        assert decision.bgp_asn is not None

    def test_bgp_for_cloud_vpc(self):
        reqs = [SubnetRequirement(name="N1", required_hosts=10)]
        scenario = _make_scenario(reqs)
        scenario.cloud_vpc_connected = True
        decision, _ = decide_routing(scenario)
        assert "BGP" in decision.protocol.value

    def test_rationale_contains_rfc(self):
        reqs = [SubnetRequirement(name="N1", required_hosts=10)]
        scenario = _make_scenario(reqs)
        _, rationale = decide_routing(scenario)
        assert any("RFC" in c for c in rationale.rfc_ieee_citations)

class TestPresetIntegration:
    """Full pipeline tests for each preset profile."""

    @pytest.mark.parametrize("preset_name", ["campus_lan", "metro_man", "global_wan"])
    def test_preset_loads(self, preset_name):
        scenario = load_preset(preset_name)
        assert scenario.scenario_name
        assert len(scenario.subnet_requirements) > 0

    @pytest.mark.parametrize("preset_name", ["campus_lan", "metro_man", "global_wan"])
    def test_full_pipeline(self, preset_name):
        scenario = load_preset(preset_name)
        design = run_design(scenario)

        # VLSM completed
        assert design.vlsm_result is not None
        assert len(design.vlsm_result.allocations) == len(scenario.subnet_requirements)

        # No overlapping subnets
        networks = [
            IPv4Network(f"{a.network_address}/{a.cidr_prefix}")
            for a in design.vlsm_result.allocations
        ]
        for i, n1 in enumerate(networks):
            for n2 in networks[i+1:]:
                assert not n1.overlaps(n2)

        # Routing decided
        assert design.routing_decision is not None

        # Media decided for all links
        assert len(design.media_decisions) == len(scenario.links)

        # Device configs generated
        assert len(design.device_configs) >= 1

        # Rationales generated
        assert len(design.rationales) > 0

    def test_campus_lan_uses_ospf_single_area(self):
        scenario = load_preset("campus_lan")
        design = run_design(scenario)
        assert "OSPF" in design.routing_decision.protocol.value

    def test_global_wan_uses_bgp(self):
        scenario = load_preset("global_wan")
        design = run_design(scenario)
        assert "BGP" in design.routing_decision.protocol.value
        assert design.routing_decision.bgp_asn is not None

    def test_campus_lan_has_copper_and_fiber(self):
        """Campus LAN should have both Cat6a and OM4 links."""
        scenario = load_preset("campus_lan")
        design = run_design(scenario)
        media_types = {m.recommended_medium for m in design.media_decisions}
        assert MediaType.CAT6A in media_types
        assert MediaType.OM4_MMF in media_types

    def test_metro_man_has_smf_links(self):
        """Metro MAN has 15–35 km links → must use OS2 SMF."""
        scenario = load_preset("metro_man")
        design = run_design(scenario)
        smf_links = [m for m in design.media_decisions if m.recommended_medium == MediaType.OS2_SMF]
        assert len(smf_links) >= 2

    @pytest.mark.parametrize("preset_name", ["campus_lan", "metro_man", "global_wan"])
    def test_config_is_valid_cisco_syntax(self, preset_name):
        """Verify generated config contains key Cisco IOS commands."""
        from netarchitect.engines.config_generator import generate_full_config
        scenario = load_preset(preset_name)
        design = run_design(scenario)
        cfg = generate_full_config(design)

        assert "hostname" in cfg
        assert "interface" in cfg
        assert "router ospf" in cfg or "router bgp" in cfg
        assert "no shutdown" in cfg


    def test_forced_os2_smf_short_link(self):
        """Forcing OS2 SMF on short link must not throw KeyError and must use SMF transceiver."""
        link = LinkInput(
            link_id="FORCED-SMF-50M",
            source_node="SW1",
            destination_node="SW2",
            distance_m=50,
            forced_medium=MediaType.OS2_SMF,
        )
        dec, rat, budget = decide_media(link)
        assert dec.recommended_medium == MediaType.OS2_SMF
        assert "10GBASE-LR" in dec.transceiver.value
        assert budget is not None
        assert budget.is_viable
        assert budget.link_margin_dB > 0

    def test_router_subinterface_encapsulation_dot1q(self):
        """Router-on-a-Stick subinterfaces must have encapsulation dot1Q <vlan> before IP address."""
        from netarchitect.engines.config_generator import generate_full_config
        scenario = load_preset("campus_lan")
        design = run_design(scenario)
        cfg = generate_full_config(design)
        assert "encapsulation dot1Q 10" in cfg
        assert "interface GigabitEthernet0/0.10" in cfg
        assert "interface GigabitEthernet0/0" in cfg

    def test_perimeter_acl_generated_with_wildcards(self):
        """Router must contain extended ACL with inverted wildcard masks matching allocations."""
        from netarchitect.engines.config_generator import generate_full_config
        scenario = load_preset("campus_lan")
        design = run_design(scenario)
        cfg = generate_full_config(design)
        assert "ip access-list extended PERIMETER-FILTER" in cfg
        # Wildcard mask for the first subnet must appear in the ACL
        first_alloc = design.vlsm_result.allocations[0]
        assert str(first_alloc.wildcard_mask) in cfg

    def test_global_wan_ipsec_vpn_tunnel(self):
        """Global WAN configuration must include IPsec VTI and IKEv2 configuration."""
        from netarchitect.engines.config_generator import generate_full_config
        scenario = load_preset("global_wan")
        design = run_design(scenario)
        cfg = generate_full_config(design)
        assert "crypto ikev2 proposal" in cfg
        assert "crypto ipsec profile" in cfg
        assert "interface Tunnel0" in cfg

class TestPresets:
    def test_list_presets(self):
        presets = list_presets()
        assert "campus_lan" in presets
        assert "metro_man" in presets
        assert "global_wan" in presets

    def test_invalid_preset_raises(self):
        with pytest.raises(FileNotFoundError):
            load_preset("nonexistent_scenario")
