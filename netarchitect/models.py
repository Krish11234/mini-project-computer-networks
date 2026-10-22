"""NetArchitect Pydantic data models and schemas."""

from __future__ import annotations

import math
from enum import Enum
from ipaddress import IPv4Address, IPv4Network
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MediaType(str, Enum):
    """Physical layer media types (state.yaml → layer_1_physical_media)."""
    CAT6A = "Cat6a"           # 10GBASE-T, ≤ 100 m, IEEE 802.3an
    OM4_MMF = "OM4_MMF"       # 10GBASE-SR, ≤ 400 m, IEEE 802.3ae
    OS2_SMF = "OS2_SMF"       # 10GBASE-LR/ER, > 400 m


class TransceiverType(str, Enum):
    """Optical / electrical transceiver modules."""
    RJ45_10GBASET = "RJ-45 (10GBASE-T)"
    SFP_10GBASESR = "SFP+ 10GBASE-SR (850nm VCSEL)"
    SFP_10GBASELR = "SFP+ 10GBASE-LR (1310nm Laser)"
    SFP_10GBASEER = "SFP+ 10GBASE-ER (1550nm Laser)"


class RoutingProtocol(str, Enum):
    """Layer 3 routing protocol choices (state.yaml → layer_3_routing_protocols)."""
    OSPF_SINGLE_AREA = "Single-Area OSPFv2 (Area 0)"
    OSPF_MULTI_AREA = "Multi-Area OSPFv2"
    EBGP = "eBGP (RFC 4271)"
    OSPF_WITH_BGP = "Multi-Area OSPF + eBGP Redistribution"


class ScenarioScale(str, Enum):
    """High-level deployment scale identifiers."""
    CAMPUS_LAN = "Campus LAN"
    METRO_MAN = "Metro MAN"
    GLOBAL_WAN = "Global WAN"
    CUSTOM = "Custom"


class DeviceRole(str, Enum):
    """Cisco device roles in the topology."""
    CORE_ROUTER = "Core Router"
    DISTRIBUTION_ROUTER = "Distribution Router"
    ACCESS_SWITCH = "Access Switch"
    DISTRIBUTION_SWITCH = "Distribution Switch"
    CORE_SWITCH = "Core Switch"
    FIREWALL = "Firewall"
    WAN_EDGE_ROUTER = "WAN Edge Router"


class LinkInput(BaseModel):
    """A single physical link between two nodes in the topology."""
    link_id: str = Field(..., description="Unique identifier for this link")
    source_node: str
    destination_node: str
    distance_m: float = Field(..., gt=0, description="Cable run distance in metres")
    forced_medium: Optional[MediaType] = Field(
        None,
        description="If set, the user is forcing a specific medium; "
                    "engine will validate or raise PhysicalDistanceViolationError",
    )


class SubnetRequirement(BaseModel):
    """A single subnet requirement (department / VLAN / service)."""
    name: str = Field(..., description="e.g. 'Engineering VLAN', 'VoIP', 'CCTV'")
    required_hosts: int = Field(..., gt=0, description="Number of usable host addresses needed")
    vlan_id: Optional[int] = Field(None, ge=1, le=4094, description="802.1Q VLAN ID")
    description: Optional[str] = None


class ScenarioInput(BaseModel):
    """
    Complete user-supplied (or preset-loaded) scenario describing the
    network to be designed.
    """
    scenario_name: str
    scale: ScenarioScale
    root_network: IPv4Network
    subnet_requirements: list[SubnetRequirement] = Field(
        ..., min_length=1, description="At least one subnet is required"
    )
    links: list[LinkInput] = Field(
        default_factory=list, description="Physical link inventory"
    )
    num_sites: int = Field(1, ge=1, description="Number of physical sites / buildings")
    is_multi_as: bool = Field(
        False,
        description="True if the network spans multiple Autonomous Systems",
    )
    cloud_vpc_connected: bool = Field(
        False,
        description="True if AWS/Azure/GCP VPC peering is required",
    )

    @field_validator("subnet_requirements")
    @classmethod
    def _check_unique_names(cls, v: list[SubnetRequirement]) -> list[SubnetRequirement]:
        names = [s.name for s in v]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate subnet requirement names are not allowed")
        return v


class MediaDecision(BaseModel):
    """Result of the L1 media selection engine for a single link."""
    link_id: str
    source_node: str
    destination_node: str
    distance_m: float
    recommended_medium: MediaType
    transceiver: TransceiverType
    max_reach_m: float = Field(
        ..., description="Maximum reach of the selected medium at 10 Gbps"
    )
    ieee_standard: str
    rationale: str = Field(
        ..., description="Engineering rationale with IEEE / physical justification"
    )


class OpticalBudget(BaseModel):
    """Optical link-budget calculation for fiber links."""
    link_id: str
    tx_power_dBm: float
    rx_sensitivity_dBm: float
    fiber_attenuation_dB_per_km: float
    connector_loss_dB: float = Field(default=0.5, description="Per connector pair")
    splice_loss_dB: float = Field(default=0.1, description="Per fusion splice")
    num_connectors: int = Field(default=2)
    num_splices: int = Field(default=0)
    distance_km: float
    total_loss_dB: float = Field(0.0, description="Computed total path loss")
    link_margin_dB: float = Field(0.0, description="Power budget margin (must be > 0)")
    is_viable: bool = Field(True, description="True if link margin > 0")

    def compute(self) -> "OpticalBudget":
        """Compute total loss and margin."""
        fiber_loss = self.fiber_attenuation_dB_per_km * self.distance_km
        conn_loss = self.connector_loss_dB * self.num_connectors
        spl_loss = self.splice_loss_dB * self.num_splices
        self.total_loss_dB = round(fiber_loss + conn_loss + spl_loss, 2)
        self.link_margin_dB = round(
            self.tx_power_dBm - self.rx_sensitivity_dBm - self.total_loss_dB, 2
        )
        self.is_viable = self.link_margin_dB > 0
        return self


class SubnetAllocation(BaseModel):
    """
    A single VLSM-allocated subnet with all attributes mandated by
    state.yaml → layer_3_subnetting_vlsm → subnet_attributes.
    """
    name: str
    vlan_id: Optional[int] = None
    required_hosts: int
    network_address: IPv4Address
    cidr_prefix: int = Field(..., ge=0, le=32)
    subnet_mask: IPv4Address
    wildcard_mask: IPv4Address = Field(
        ..., description="Inverted wildcard mask for ACL matching"
    )
    first_usable_host: IPv4Address
    last_usable_host: IPv4Address
    broadcast_address: IPv4Address
    usable_host_capacity: int
    wastage: int = Field(
        ..., description="usable_host_capacity - required_hosts"
    )
    efficiency_pct: float = Field(
        ..., description="(required_hosts / usable_host_capacity) * 100"
    )

    @property
    def cidr_notation(self) -> str:
        return f"{self.network_address}/{self.cidr_prefix}"


class VLSMResult(BaseModel):
    """Aggregate output of the VLSM engine."""
    root_network: str
    total_requested_hosts: int
    total_available_hosts: int
    allocations: list[SubnetAllocation]
    overall_efficiency_pct: float
    rationale: str


class RoutingDecision(BaseModel):
    """Result of the L3 routing protocol selection engine."""
    protocol: RoutingProtocol
    ospf_areas: list[int] = Field(
        default_factory=lambda: [0],
        description="OSPF area IDs; [0] for single-area",
    )
    bgp_asn: Optional[int] = Field(None, description="BGP Autonomous System Number")
    rationale: str = Field(
        ..., description="Engineering rationale with RFC citations"
    )
    rfc_references: list[str] = Field(default_factory=list)


class InterfaceConfig(BaseModel):
    """Configuration for a single Cisco IOS interface."""
    interface_name: str = Field(..., description="e.g. GigabitEthernet0/1, Vlan10")
    ip_address: Optional[IPv4Address] = None
    subnet_mask: Optional[IPv4Address] = None
    description: Optional[str] = None
    shutdown: bool = False
    switchport_mode: Optional[str] = Field(
        None, description="'access' or 'trunk'"
    )
    switchport_access_vlan: Optional[int] = None
    trunk_allowed_vlans: Optional[str] = Field(
        None,
        description="Explicit VLAN list for trunk pruning (state.yaml: no unconstrained trunks)",
    )
    channel_group: Optional[int] = None
    channel_protocol: Optional[str] = Field(None, description="'lacp' or 'pagp'")
    encapsulation_dot1q: Optional[int] = Field(
        None, description="802.1Q VLAN ID for router subinterface encapsulation"
    )


class VlanConfig(BaseModel):
    """802.1Q VLAN definition."""
    vlan_id: int = Field(..., ge=1, le=4094)
    name: str


class OspfConfig(BaseModel):
    """OSPF process configuration block."""
    process_id: int = Field(1, ge=1)
    router_id: Optional[str] = None
    networks: list[dict] = Field(
        default_factory=list,
        description="List of {'network': ..., 'wildcard': ..., 'area': ...}",
    )
    passive_interfaces: list[str] = Field(default_factory=list)


class BgpConfig(BaseModel):
    """BGP process configuration block."""
    asn: int
    router_id: Optional[str] = None
    neighbors: list[dict] = Field(
        default_factory=list,
        description="List of {'ip': ..., 'remote_as': ..., 'description': ...}",
    )
    networks: list[str] = Field(default_factory=list)


class AclEntry(BaseModel):
    """A single ACL entry (ACE)."""
    sequence: int
    action: str = Field(..., description="'permit' or 'deny'")
    protocol: str = Field(default="ip")
    source: str = Field(..., description="Source address with wildcard or 'any'")
    destination: str = Field(..., description="Destination address with wildcard or 'any'")
    description: Optional[str] = None


class AclConfig(BaseModel):
    """Standard or Extended Access Control List."""
    acl_type: str = Field(..., description="'standard' or 'extended'")
    acl_id: str = Field(..., description="ACL number or name")
    entries: list[AclEntry]


class IpsecConfig(BaseModel):
    """IPsec VPN tunnel configuration."""
    tunnel_interface: str
    tunnel_source: str
    tunnel_destination: str
    tunnel_mode: str = Field(default="ipsec ipv4", description="VTI mode")
    ike_version: int = Field(default=2)
    transform_set: str = Field(default="AES256-SHA256")
    peer_address: str
    pre_shared_key: str = Field(default="CHANGE_ME_IMMEDIATELY")


class DeviceConfig(BaseModel):
    """Complete Cisco IOS configuration for a single device."""
    hostname: str
    role: DeviceRole
    interfaces: list[InterfaceConfig] = Field(default_factory=list)
    vlans: list[VlanConfig] = Field(default_factory=list)
    vtp_mode: str = Field(
        default="transparent",
        description="VTP mode – always 'transparent' or 'off' per state.yaml",
    )
    spanning_tree_mode: str = Field(
        default="rapid-pvst",
        description="Rapid-PVST+ per state.yaml L2 rules",
    )
    ospf: Optional[OspfConfig] = None
    bgp: Optional[BgpConfig] = None
    acls: list[AclConfig] = Field(default_factory=list)
    ipsec_tunnels: list[IpsecConfig] = Field(default_factory=list)
    raw_banner: Optional[str] = None


class Rationale(BaseModel):
    """
    An individual engineering rationale produced by the Explainability Engine.
    Every media, subnet, or routing decision must generate one of these
    (state.yaml → explainability_engine → mandate).
    """
    decision_category: str = Field(
        ..., description="e.g. 'Layer 1 Media', 'VLSM Allocation', 'Routing Protocol'"
    )
    decision_summary: str
    physical_justification: Optional[str] = None
    mathematical_justification: Optional[str] = None
    rfc_ieee_citations: list[str] = Field(default_factory=list)
    detail: str = Field(..., description="Full narrative rationale")


class NetworkDesign(BaseModel):
    """
    The complete output of the NetArchitect engine for a single scenario.
    Bundles all decisions, allocations, device configs, and rationales.
    """
    scenario_name: str
    scale: ScenarioScale
    media_decisions: list[MediaDecision] = Field(default_factory=list)
    optical_budgets: list[OpticalBudget] = Field(default_factory=list)
    vlsm_result: Optional[VLSMResult] = None
    routing_decision: Optional[RoutingDecision] = None
    device_configs: list[DeviceConfig] = Field(default_factory=list)
    rationales: list[Rationale] = Field(default_factory=list)
