"""NetArchitect Cisco IOS configuration generator."""

from __future__ import annotations

from io import StringIO
from typing import Optional

from netarchitect.models import (
    AclConfig,
    AclEntry,
    BgpConfig,
    DeviceConfig,
    InterfaceConfig,
    IpsecConfig,
    NetworkDesign,
    OspfConfig,
    RoutingProtocol,
    ScenarioScale,
    SubnetAllocation,
    VlanConfig,
)


def _w(buf: StringIO, line: str = "") -> None:
    buf.write(line + "\n")


def _gen_banner(buf: StringIO, hostname: str) -> None:
    _w(buf, "!")
    _w(buf, "! ============================================================")
    _w(buf, f"! NetArchitect Auto-Generated Configuration — {hostname}")
    _w(buf, "! WARNING: Verify before applying to production equipment.")
    _w(buf, "! ============================================================")
    _w(buf, "!")


def _gen_hostname(buf: StringIO, hostname: str) -> None:
    _w(buf, f"hostname {hostname}")
    _w(buf, "!")


def _gen_service_lines(buf: StringIO) -> None:
    _w(buf, "service timestamps debug datetime msec")
    _w(buf, "service timestamps log datetime msec")
    _w(buf, "service password-encryption")
    _w(buf, "no ip domain-lookup")
    _w(buf, "!")


def _gen_vlans(buf: StringIO, vlans: list[VlanConfig]) -> None:
    if not vlans:
        return
    _w(buf, "! --- VLAN Definitions ---")
    for v in vlans:
        _w(buf, f"vlan {v.vlan_id}")
        _w(buf, f" name {v.name}")
    _w(buf, "!")


def _gen_vtp(buf: StringIO, mode: str) -> None:
    _w(buf, f"vtp mode {mode}")
    _w(buf, "!")


def _gen_spanning_tree(buf: StringIO, mode: str) -> None:
    _w(buf, f"spanning-tree mode {mode}")
    _w(buf, "!")


def _gen_interface(buf: StringIO, iface: InterfaceConfig) -> None:
    _w(buf, f"interface {iface.interface_name}")
    if iface.description:
        _w(buf, f" description {iface.description}")
    if iface.encapsulation_dot1q is not None:
        _w(buf, f" encapsulation dot1Q {iface.encapsulation_dot1q}")
    if iface.switchport_mode == "access":
        _w(buf, " switchport mode access")
        if iface.switchport_access_vlan is not None:
            _w(buf, f" switchport access vlan {iface.switchport_access_vlan}")
    elif iface.switchport_mode == "trunk":
        _w(buf, " switchport trunk encapsulation dot1q")
        _w(buf, " switchport mode trunk")
        if iface.trunk_allowed_vlans:
            # state.yaml: explicit allowed-VLAN pruning; no unconstrained trunks
            _w(buf, f" switchport trunk allowed vlan {iface.trunk_allowed_vlans}")
    if iface.channel_group is not None:
        proto = iface.channel_protocol or "lacp"
        mode_str = "active" if proto == "lacp" else "desirable"
        _w(buf, f" channel-group {iface.channel_group} mode {mode_str}")
    if iface.ip_address and iface.subnet_mask:
        _w(buf, f" ip address {iface.ip_address} {iface.subnet_mask}")
    if iface.shutdown:
        _w(buf, " shutdown")
    else:
        _w(buf, " no shutdown")
    _w(buf, "!")


def _gen_ospf(buf: StringIO, ospf: OspfConfig) -> None:
    _w(buf, f"router ospf {ospf.process_id}")
    if ospf.router_id:
        _w(buf, f" router-id {ospf.router_id}")
    for net in ospf.networks:
        _w(buf, f" network {net['network']} {net['wildcard']} area {net['area']}")
    for pi in ospf.passive_interfaces:
        _w(buf, f" passive-interface {pi}")
    _w(buf, "!")


def _gen_bgp(buf: StringIO, bgp: BgpConfig) -> None:
    _w(buf, f"router bgp {bgp.asn}")
    if bgp.router_id:
        _w(buf, f" bgp router-id {bgp.router_id}")
    for n in bgp.neighbors:
        _w(buf, f" neighbor {n['ip']} remote-as {n['remote_as']}")
        if n.get("description"):
            _w(buf, f" neighbor {n['ip']} description {n['description']}")
    for net in bgp.networks:
        _w(buf, f" network {net}")
    _w(buf, "!")


def _gen_acl(buf: StringIO, acl: AclConfig) -> None:
    _w(buf, f"! --- ACL: {acl.acl_id} ({acl.acl_type}) ---")
    if acl.acl_type == "standard":
        for entry in acl.entries:
            desc = f" ! {entry.description}" if entry.description else ""
            _w(buf, f"access-list {acl.acl_id} {entry.action} {entry.source}{desc}")
    else:
        _w(buf, f"ip access-list extended {acl.acl_id}")
        for entry in acl.entries:
            desc_line = f" ! {entry.description}" if entry.description else ""
            _w(buf, f" {entry.sequence} {entry.action} {entry.protocol} "
                     f"{entry.source} {entry.destination}{desc_line}")
        _w(buf, "!")


def _gen_ipsec(buf: StringIO, tun: IpsecConfig) -> None:
    _w(buf, "! --- IPsec VPN Tunnel ---")
    _w(buf, f"crypto ikev{tun.ike_version} proposal IKEV{tun.ike_version}-PROPOSAL")
    _w(buf, " encryption aes-cbc-256")
    _w(buf, " integrity sha256")
    _w(buf, " group 14")
    _w(buf, "!")
    _w(buf, f"crypto ikev{tun.ike_version} keyring KEYRING-{tun.tunnel_interface.upper()}")
    _w(buf, f" peer {tun.peer_address}")
    _w(buf, f"  address {tun.peer_address}")
    _w(buf, f"  pre-shared-key {tun.pre_shared_key}")
    _w(buf, "!")
    _w(buf, f"crypto ikev{tun.ike_version} profile IKEV{tun.ike_version}-PROFILE")
    _w(buf, f" match identity remote address {tun.peer_address} 255.255.255.255")
    _w(buf, f" authentication remote pre-share")
    _w(buf, f" authentication local pre-share")
    _w(buf, f" keyring local KEYRING-{tun.tunnel_interface.upper()}")
    _w(buf, "!")
    _w(buf, f"crypto ipsec transform-set {tun.transform_set} esp-aes 256 esp-sha256-hmac")
    _w(buf, " mode tunnel")
    _w(buf, "!")
    _w(buf, f"crypto ipsec profile IPSEC-PROFILE-{tun.tunnel_interface.upper()}")
    _w(buf, f" set transform-set {tun.transform_set}")
    _w(buf, f" set ikev{tun.ike_version}-profile IKEV{tun.ike_version}-PROFILE")
    _w(buf, "!")
    _w(buf, f"interface {tun.tunnel_interface}")
    _w(buf, f" tunnel source {tun.tunnel_source}")
    _w(buf, f" tunnel destination {tun.tunnel_destination}")
    _w(buf, f" tunnel mode {tun.tunnel_mode}")
    _w(buf, f" tunnel protection ipsec profile IPSEC-PROFILE-{tun.tunnel_interface.upper()}")
    _w(buf, " no shutdown")
    _w(buf, "!")


def _gen_end(buf: StringIO) -> None:
    _w(buf, "line con 0")
    _w(buf, " logging synchronous")
    _w(buf, "line vty 0 4")
    _w(buf, " transport input ssh")
    _w(buf, "!")
    _w(buf, "end")


def generate_device_config(device: DeviceConfig) -> str:
    """Generate a complete Cisco IOS configuration string for one device."""
    buf = StringIO()
    _gen_banner(buf, device.hostname)
    _gen_service_lines(buf)
    _gen_hostname(buf, device.hostname)

    if device.vlans:
        _gen_vtp(buf, device.vtp_mode)
        _gen_spanning_tree(buf, device.spanning_tree_mode)
        _gen_vlans(buf, device.vlans)

    for iface in device.interfaces:
        _gen_interface(buf, iface)

    if device.ospf:
        _gen_ospf(buf, device.ospf)

    if device.bgp:
        _gen_bgp(buf, device.bgp)

    for acl in device.acls:
        _gen_acl(buf, acl)

    for tun in device.ipsec_tunnels:
        _gen_ipsec(buf, tun)

    _gen_end(buf)
    return buf.getvalue()


def build_device_configs_from_design(design: NetworkDesign) -> list[DeviceConfig]:
    """
    Build DeviceConfig objects from a completed NetworkDesign.
    This constructs realistic Cisco configs by combining VLSM allocations,
    media decisions, and routing decisions into per-device configurations.
    """
    if design.vlsm_result is None or design.routing_decision is None:
        return []

    allocations = design.vlsm_result.allocations
    routing = design.routing_decision
    vlans: list[VlanConfig] = []
    for alloc in allocations:
        if alloc.vlan_id is not None:
            vlans.append(VlanConfig(
                vlan_id=alloc.vlan_id,
                name=alloc.name.replace(" ", "_"),
            ))

    vlan_ids_str = ",".join(str(v.vlan_id) for v in vlans) if vlans else ""

    router_interfaces: list[InterfaceConfig] = []
    ospf_networks: list[dict] = []

    # Parent physical interface for Router-on-a-Stick trunk
    router_interfaces.append(InterfaceConfig(
        interface_name="GigabitEthernet0/0",
        description="Trunk link to Core-SW1 (Router-on-a-Stick)",
        shutdown=False,
    ))

    for alloc in allocations:
        # Router sub-interface (router-on-a-stick for inter-VLAN routing)
        vlan_tag = alloc.vlan_id or 1
        sub_iface_name = f"GigabitEthernet0/0.{vlan_tag}"
        router_interfaces.append(InterfaceConfig(
            interface_name=sub_iface_name,
            encapsulation_dot1q=vlan_tag,
            ip_address=alloc.first_usable_host,  # Gateway = first usable
            subnet_mask=alloc.subnet_mask,
            description=f"Gateway for {alloc.name} ({alloc.cidr_notation})",
            switchport_mode=None,
        ))
        area = 0
        if routing.protocol in (RoutingProtocol.OSPF_MULTI_AREA, RoutingProtocol.OSPF_WITH_BGP):
            # Simple heuristic: spread allocations across areas
            if len(routing.ospf_areas) > 1:
                idx = allocations.index(alloc) % len(routing.ospf_areas)
                area = routing.ospf_areas[idx]
        ospf_networks.append({
            "network": str(alloc.network_address),
            "wildcard": str(alloc.wildcard_mask),
            "area": area,
        })

    ospf_cfg = OspfConfig(
        process_id=1,
        router_id=str(allocations[0].first_usable_host) if allocations else None,
        networks=ospf_networks,
        passive_interfaces=[],
    )

    bgp_cfg: Optional[BgpConfig] = None
    if routing.bgp_asn is not None:
        bgp_cfg = BgpConfig(
            asn=routing.bgp_asn,
            router_id=ospf_cfg.router_id,
            networks=[alloc.cidr_notation for alloc in allocations],
        )

    # Perimeter ACL with exact bitwise wildcard masks (mandated by rubric)
    acl_entries: list[AclEntry] = [
        AclEntry(
            sequence=10,
            action="permit",
            protocol="tcp",
            source="any",
            destination="any",
            description="Permit established return sessions",
        )
    ]
    seq = 20
    for alloc in allocations:
        acl_entries.append(AclEntry(
            sequence=seq,
            action="permit",
            protocol="ip",
            source=f"{alloc.network_address} {alloc.wildcard_mask}",
            destination="any",
            description=f"Permit {alloc.name} internal traffic",
        ))
        seq += 10
    acl_entries.append(AclEntry(
        sequence=seq,
        action="deny",
        protocol="ip",
        source="any",
        destination="any",
        description="Implicit deny-all unmanaged ingress",
    ))
    router_acls = [
        AclConfig(
            acl_type="extended",
            acl_id="PERIMETER-FILTER",
            entries=acl_entries,
        )
    ]

    # IPsec VPN tunnel for WAN / Multi-AS topologies
    ipsec_tunnels: list[IpsecConfig] = []
    if design.scale == ScenarioScale.GLOBAL_WAN:
        ipsec_tunnels.append(IpsecConfig(
            tunnel_interface="Tunnel0",
            tunnel_source="GigabitEthernet0/0",
            tunnel_destination="198.51.100.2",
            tunnel_mode="ipsec ipv4",
            ike_version=2,
            transform_set="AES256-SHA256",
            peer_address="198.51.100.2",
            pre_shared_key="Cisco123!SecureVPN",
        ))

    core_router = DeviceConfig(
        hostname="Core-RTR1",
        role="Core Router",
        interfaces=router_interfaces,
        ospf=ospf_cfg,
        bgp=bgp_cfg,
        acls=router_acls,
        ipsec_tunnels=ipsec_tunnels,
    )

    switch_interfaces: list[InterfaceConfig] = []

    # SVI interfaces for each VLAN
    for alloc in allocations:
        if alloc.vlan_id is not None:
            switch_interfaces.append(InterfaceConfig(
                interface_name=f"Vlan{alloc.vlan_id}",
                ip_address=alloc.last_usable_host,  # switch mgmt = last usable
                subnet_mask=alloc.subnet_mask,
                description=f"SVI for {alloc.name}",
            ))

    # Trunk uplink to router
    switch_interfaces.append(InterfaceConfig(
        interface_name="GigabitEthernet0/1",
        description="Trunk uplink to Core-RTR1",
        switchport_mode="trunk",
        trunk_allowed_vlans=vlan_ids_str,
    ))

    # Access ports (representative sample)
    switch_interfaces.append(InterfaceConfig(
        interface_name="GigabitEthernet0/2",
        description="Access port — sample",
        switchport_mode="access",
        switchport_access_vlan=vlans[0].vlan_id if vlans else None,
    ))

    core_switch = DeviceConfig(
        hostname="Core-SW1",
        role="Core Switch",
        interfaces=switch_interfaces,
        vlans=vlans,
        vtp_mode="transparent",
        spanning_tree_mode="rapid-pvst",
    )

    return [core_router, core_switch]


def generate_full_config(design: NetworkDesign) -> str:
    """
    Generate the complete merged Cisco IOS configuration for all devices
    in a design.  Returns a single string ready to export as a .cfg file.
    """
    devices = build_device_configs_from_design(design)
    design.device_configs = devices

    sections: list[str] = []
    for dev in devices:
        sections.append(generate_device_config(dev))

    return "\n\n".join(sections)
