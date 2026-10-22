# Architectural Rationale Report — Campus LAN – 3-Building University Network

**Scale:** Campus LAN

## VLSM Allocation Summary

Root Network: `10.10.0.0/16`
Total Requested Hosts: 1,480
Overall Efficiency: 75.36%

| Subnet | CIDR | Hosts | Capacity | Efficiency | Wildcard |
|--------|------|------:|--------:|-----------:|----------|
| Building-A Engineering | 10.10.0.0/23 | 350 | 510 | 68.63% | 0.0.1.255 |
| Building-B Labs | 10.10.2.0/24 | 250 | 254 | 98.43% | 0.0.0.255 |
| Building-C Library | 10.10.3.0/24 | 200 | 254 | 78.74% | 0.0.0.255 |
| VoIP Network | 10.10.4.0/24 | 180 | 254 | 70.87% | 0.0.0.255 |
| Wireless APs | 10.10.5.0/24 | 150 | 254 | 59.06% | 0.0.0.255 |
| Building-A Admin | 10.10.6.0/25 | 120 | 126 | 95.24% | 0.0.0.127 |
| CCTV / Security | 10.10.6.128/25 | 100 | 126 | 79.37% | 0.0.0.127 |
| Building-B Faculty | 10.10.7.0/25 | 80 | 126 | 63.49% | 0.0.0.127 |
| Server Farm | 10.10.7.128/27 | 30 | 30 | 100.0% | 0.0.0.31 |
| Management VLAN | 10.10.7.160/27 | 20 | 30 | 66.67% | 0.0.0.31 |

## Routing Protocol Decision

**Selected:** Single-Area OSPFv2 (Area 0)

Single Autonomous System with 10 subnets (3 sites) — well below the 50-subnet multi-area threshold. Selected Single-Area OSPFv2 Area 0 (RFC 2328) for link-state fast convergence via Dijkstra SPF, loop-free shortest-path forwarding, and zero external routing protocol overhead. All interfaces participate in Area 0 with a flat LSDB.

## Physical Media Decisions

| Link | Distance | Medium | Transceiver | Standard |
|------|--------:|--------|-------------|----------|
| Core-SW1 ↔ Dist-SW-A | 250.0m | OM4_MMF | SFP+ 10GBASE-SR (850nm VCSEL) | IEEE 802.3ae (10GBASE-SR, 850 nm VCSEL) |
| Core-SW1 ↔ Dist-SW-B | 300.0m | OM4_MMF | SFP+ 10GBASE-SR (850nm VCSEL) | IEEE 802.3ae (10GBASE-SR, 850 nm VCSEL) |
| Core-SW1 ↔ Dist-SW-C | 180.0m | OM4_MMF | SFP+ 10GBASE-SR (850nm VCSEL) | IEEE 802.3ae (10GBASE-SR, 850 nm VCSEL) |
| Dist-SW-A ↔ Acc-SW-A1 | 45.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| Dist-SW-A ↔ Acc-SW-A2 | 60.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| Dist-SW-B ↔ Acc-SW-B1 | 55.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| Dist-SW-B ↔ Acc-SW-B2 | 70.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| Dist-SW-C ↔ Acc-SW-C1 | 40.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| Dist-SW-C ↔ Acc-SW-C2 | 50.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| Core-SW1 ↔ Core-RTR1 | 10.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |

## Optical Link Budgets

| Link | Distance | Total Loss | Margin | Viable |
|------|--------:|-----------:|-------:|--------|
| L1-CoreSW-to-DistA | 0.25 km | 1.88 dB | 8.22 dB | ✅ Yes |
| L2-CoreSW-to-DistB | 0.3 km | 2.05 dB | 8.05 dB | ✅ Yes |
| L3-CoreSW-to-DistC | 0.18 km | 1.63 dB | 8.47 dB | ✅ Yes |

## Detailed Engineering Rationales

### 1. Core-SW1 ↔ Dist-SW-A: OM4_MMF
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3ae (10GBASE-SR, 850 nm VCSEL)

Link distance 250.0m exceeds the 100m Cat6a copper limit (IEEE 802.3an) but is within the 400.0m reach of OM4 50/125 µm multimode fibre with SFP+ 10GBASE-SR (850nm VCSEL) transceiver (IEEE 802.3ae (10GBASE-SR, 850 nm VCSEL)). OM4 provides an effective modal bandwidth of 4700 MHz·km at 850 nm, sufficient for 10 Gbps at this distance.

### 2. Core-SW1 ↔ Dist-SW-B: OM4_MMF
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3ae (10GBASE-SR, 850 nm VCSEL)

Link distance 300.0m exceeds the 100m Cat6a copper limit (IEEE 802.3an) but is within the 400.0m reach of OM4 50/125 µm multimode fibre with SFP+ 10GBASE-SR (850nm VCSEL) transceiver (IEEE 802.3ae (10GBASE-SR, 850 nm VCSEL)). OM4 provides an effective modal bandwidth of 4700 MHz·km at 850 nm, sufficient for 10 Gbps at this distance.

### 3. Core-SW1 ↔ Dist-SW-C: OM4_MMF
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3ae (10GBASE-SR, 850 nm VCSEL)

Link distance 180.0m exceeds the 100m Cat6a copper limit (IEEE 802.3an) but is within the 400.0m reach of OM4 50/125 µm multimode fibre with SFP+ 10GBASE-SR (850nm VCSEL) transceiver (IEEE 802.3ae (10GBASE-SR, 850 nm VCSEL)). OM4 provides an effective modal bandwidth of 4700 MHz·km at 850 nm, sufficient for 10 Gbps at this distance.

### 4. Dist-SW-A ↔ Acc-SW-A1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 45.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 5. Dist-SW-A ↔ Acc-SW-A2: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 60.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 6. Dist-SW-B ↔ Acc-SW-B1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 55.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 7. Dist-SW-B ↔ Acc-SW-B2: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 70.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 8. Dist-SW-C ↔ Acc-SW-C1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 40.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 9. Dist-SW-C ↔ Acc-SW-C2: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 50.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 10. Core-SW1 ↔ Core-RTR1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 10.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 11. Building-A Engineering: 10.10.0.0/23
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 10.10.0.0/23 for 'Building-A Engineering' (VLAN 10). Network: 10.10.0.0, Mask: 255.255.254.0, Wildcard: 0.0.1.255, Hosts: 10.10.0.1–10.10.1.254, Broadcast: 10.10.1.255. Efficiency: 68.63%.

### 12. Building-B Labs: 10.10.2.0/24
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 10.10.2.0/24 for 'Building-B Labs' (VLAN 30). Network: 10.10.2.0, Mask: 255.255.255.0, Wildcard: 0.0.0.255, Hosts: 10.10.2.1–10.10.2.254, Broadcast: 10.10.2.255. Efficiency: 98.43%.

### 13. Building-C Library: 10.10.3.0/24
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 10.10.3.0/24 for 'Building-C Library' (VLAN 50). Network: 10.10.3.0, Mask: 255.255.255.0, Wildcard: 0.0.0.255, Hosts: 10.10.3.1–10.10.3.254, Broadcast: 10.10.3.255. Efficiency: 78.74%.

### 14. VoIP Network: 10.10.4.0/24
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 10.10.4.0/24 for 'VoIP Network' (VLAN 60). Network: 10.10.4.0, Mask: 255.255.255.0, Wildcard: 0.0.0.255, Hosts: 10.10.4.1–10.10.4.254, Broadcast: 10.10.4.255. Efficiency: 70.87%.

### 15. Wireless APs: 10.10.5.0/24
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 10.10.5.0/24 for 'Wireless APs' (VLAN 80). Network: 10.10.5.0, Mask: 255.255.255.0, Wildcard: 0.0.0.255, Hosts: 10.10.5.1–10.10.5.254, Broadcast: 10.10.5.255. Efficiency: 59.06%.

### 16. Building-A Admin: 10.10.6.0/25
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 10.10.6.0/25 for 'Building-A Admin' (VLAN 20). Network: 10.10.6.0, Mask: 255.255.255.128, Wildcard: 0.0.0.127, Hosts: 10.10.6.1–10.10.6.126, Broadcast: 10.10.6.127. Efficiency: 95.24%.

### 17. CCTV / Security: 10.10.6.128/25
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 10.10.6.128/25 for 'CCTV / Security' (VLAN 70). Network: 10.10.6.128, Mask: 255.255.255.128, Wildcard: 0.0.0.127, Hosts: 10.10.6.129–10.10.6.254, Broadcast: 10.10.6.255. Efficiency: 79.37%.

### 18. Building-B Faculty: 10.10.7.0/25
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 10.10.7.0/25 for 'Building-B Faculty' (VLAN 40). Network: 10.10.7.0, Mask: 255.255.255.128, Wildcard: 0.0.0.127, Hosts: 10.10.7.1–10.10.7.126, Broadcast: 10.10.7.127. Efficiency: 63.49%.

### 19. Server Farm: 10.10.7.128/27
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 10.10.7.128/27 for 'Server Farm' (VLAN 90). Network: 10.10.7.128, Mask: 255.255.255.224, Wildcard: 0.0.0.31, Hosts: 10.10.7.129–10.10.7.158, Broadcast: 10.10.7.159. Efficiency: 100.0%.

### 20. Management VLAN: 10.10.7.160/27
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 10.10.7.160/27 for 'Management VLAN' (VLAN 99). Network: 10.10.7.160, Mask: 255.255.255.224, Wildcard: 0.0.0.31, Hosts: 10.10.7.161–10.10.7.190, Broadcast: 10.10.7.191. Efficiency: 66.67%.

### 21. Single-Area OSPFv2 (Area 0) selected
**Category:** Layer 3 Routing Protocol
**Citations:** RFC 2328 (OSPFv2)

Single Autonomous System with 10 subnets (3 sites) — well below the 50-subnet multi-area threshold. Selected Single-Area OSPFv2 Area 0 (RFC 2328) for link-state fast convergence via Dijkstra SPF, loop-free shortest-path forwarding, and zero external routing protocol overhead. All interfaces participate in Area 0 with a flat LSDB.
