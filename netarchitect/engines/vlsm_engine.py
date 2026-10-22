"""NetArchitect Bitwise VLSM Subnet Engine."""

from __future__ import annotations

import math
from ipaddress import IPv4Address, IPv4Network

from netarchitect.exceptions import SubnetExhaustionError, SubnetOverlapError
from netarchitect.models import (
    Rationale,
    ScenarioInput,
    SubnetAllocation,
    SubnetRequirement,
    VLSMResult,
)



def _hosts_to_prefix(required_hosts: int) -> int:
    """
    Compute the CIDR prefix length for a block that can accommodate
    `required_hosts` *usable* addresses (i.e. excluding network and
    broadcast).

    Formula:  block_size = 2^n  where n is the smallest integer such
              that 2^n - 2 >= required_hosts.
    Returns:  prefix = 32 - n
    """
    # Need at least required_hosts + 2 total addresses
    n = math.ceil(math.log2(required_hosts + 2))
    # Minimum /30 for any subnet (2 usable hosts)
    n = max(n, 2)
    return 32 - n


def _int_to_ipv4(val: int) -> IPv4Address:
    """Convert a 32-bit integer to an IPv4Address."""
    return IPv4Address(val)


def _ipv4_to_int(addr: IPv4Address) -> int:
    """Convert an IPv4Address to a 32-bit integer."""
    return int(addr)


def _compute_subnet_mask(prefix: int) -> IPv4Address:
    """Compute the dotted-decimal subnet mask from a CIDR prefix."""
    mask_int = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    return _int_to_ipv4(mask_int)


def _compute_wildcard_mask(prefix: int) -> IPv4Address:
    """
    Compute the inverted wildcard mask for ACL matching.
    Wildcard = bitwise NOT of subnet mask (lower 32 bits).
    """
    mask_int = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    wildcard_int = mask_int ^ 0xFFFFFFFF
    return _int_to_ipv4(wildcard_int)


def _check_overlap(
    new_net: IPv4Network, existing: list[IPv4Network]
) -> None:
    """Raise SubnetOverlapError if the new network overlaps any existing one."""
    for ex in existing:
        if new_net.overlaps(ex):
            raise SubnetOverlapError(str(new_net), str(ex))


def allocate_vlsm(scenario: ScenarioInput) -> tuple[VLSMResult, list[Rationale]]:
    """
    Run the full VLSM allocation algorithm on a scenario.

    Returns:
        VLSMResult with all SubnetAllocations
        list[Rationale] with per-subnet explainability entries
    """
    root = scenario.root_network
    root_int = _ipv4_to_int(root.network_address)
    root_prefix = root.prefixlen
    total_addresses = 2 ** (32 - root_prefix)
    # Usable = total - 2 (for the root's own network/broadcast), but for
    # VLSM we care about the raw address space we can carve subnets from.
    available_space = total_addresses
    sorted_reqs: list[SubnetRequirement] = sorted(
        scenario.subnet_requirements, key=lambda r: r.required_hosts, reverse=True
    )
    total_demanded = 0
    for req in sorted_reqs:
        block_bits = math.ceil(math.log2(req.required_hosts + 2))
        block_bits = max(block_bits, 2)
        total_demanded += 2 ** block_bits

    if total_demanded > available_space:
        raise SubnetExhaustionError(
            root_prefix=str(root),
            available_hosts=available_space - 2,
            requested_hosts=total_demanded,
        )
    current_address_int = root_int
    allocations: list[SubnetAllocation] = []
    allocated_networks: list[IPv4Network] = []
    rationales: list[Rationale] = []

    for req in sorted_reqs:
        prefix = _hosts_to_prefix(req.required_hosts)
        block_size = 2 ** (32 - prefix)

        # Align to block boundary (network address must be divisible by block_size)
        if current_address_int % block_size != 0:
            current_address_int += block_size - (current_address_int % block_size)

        # Boundary check: ensure we haven't exceeded root address space
        if current_address_int + block_size > root_int + total_addresses:
            raise SubnetExhaustionError(
                root_prefix=str(root),
                available_hosts=total_addresses - 2,
                requested_hosts=total_demanded,
            )

        network_addr = _int_to_ipv4(current_address_int)
        broadcast_addr = _int_to_ipv4(current_address_int + block_size - 1)
        first_host = _int_to_ipv4(current_address_int + 1)
        last_host = _int_to_ipv4(current_address_int + block_size - 2)
        subnet_mask = _compute_subnet_mask(prefix)
        wildcard_mask = _compute_wildcard_mask(prefix)
        usable_capacity = block_size - 2
        wastage = usable_capacity - req.required_hosts
        efficiency = round((req.required_hosts / usable_capacity) * 100, 2) if usable_capacity > 0 else 0.0

        new_network = IPv4Network(f"{network_addr}/{prefix}", strict=True)

        # Zero-overlap verification
        _check_overlap(new_network, allocated_networks)
        allocated_networks.append(new_network)

        allocation = SubnetAllocation(
            name=req.name,
            vlan_id=req.vlan_id,
            required_hosts=req.required_hosts,
            network_address=network_addr,
            cidr_prefix=prefix,
            subnet_mask=subnet_mask,
            wildcard_mask=wildcard_mask,
            first_usable_host=first_host,
            last_usable_host=last_host,
            broadcast_address=broadcast_addr,
            usable_host_capacity=usable_capacity,
            wastage=wastage,
            efficiency_pct=efficiency,
        )
        allocations.append(allocation)

        # Per-subnet rationale
        rationales.append(Rationale(
            decision_category="VLSM Allocation",
            decision_summary=f"{req.name}: {new_network}",
            mathematical_justification=(
                f"Required {req.required_hosts} hosts → "
                f"ceil(log₂({req.required_hosts}+2)) = {math.ceil(math.log2(req.required_hosts + 2))} → "
                f"block size 2^{32 - prefix} = {block_size} addresses → "
                f"/{prefix} (usable: {usable_capacity}, wastage: {wastage}, "
                f"efficiency: {efficiency}%)"
            ),
            rfc_ieee_citations=["RFC 1918 (Private Addressing)", "RFC 950 (Subnetting)"],
            detail=(
                f"Allocated {new_network} for '{req.name}' "
                f"(VLAN {req.vlan_id or 'N/A'}). "
                f"Network: {network_addr}, Mask: {subnet_mask}, "
                f"Wildcard: {wildcard_mask}, "
                f"Hosts: {first_host}–{last_host}, "
                f"Broadcast: {broadcast_addr}. "
                f"Efficiency: {efficiency}%."
            ),
        ))

        current_address_int += block_size
    total_requested = sum(a.required_hosts for a in allocations)
    total_usable = sum(a.usable_host_capacity for a in allocations)
    overall_eff = round((total_requested / total_usable) * 100, 2) if total_usable > 0 else 0.0

    vlsm_result = VLSMResult(
        root_network=str(root),
        total_requested_hosts=total_requested,
        total_available_hosts=total_addresses - 2,
        allocations=allocations,
        overall_efficiency_pct=overall_eff,
        rationale=(
            f"VLSM allocation from root {root}: "
            f"{len(allocations)} subnets carved, "
            f"{total_requested:,} hosts requested across "
            f"{total_usable:,} usable addresses "
            f"(overall efficiency {overall_eff}%). "
            f"All subnets sorted descending by host count to minimise "
            f"fragmentation. Zero overlapping blocks verified via "
            f"bitwise boundary checks."
        ),
    )

    return vlsm_result, rationales
