# Architectural Rationale Report — Metro MAN – FinTech HQ + 2 Branch Sites

**Scale:** Metro MAN

## VLSM Allocation Summary

Root Network: `172.16.0.0/18`
Total Requested Hosts: 450
Overall Efficiency: 68.81%

| Subnet | CIDR | Hosts | Capacity | Efficiency | Wildcard |
|--------|------|------:|--------:|-----------:|----------|
| HQ Trading Floor | 172.16.0.0/25 | 100 | 126 | 79.37% | 0.0.0.127 |
| HQ Back Office | 172.16.0.128/25 | 80 | 126 | 63.49% | 0.0.0.127 |
| VoIP All Sites | 172.16.1.0/25 | 70 | 126 | 55.56% | 0.0.0.127 |
| Branch-1 Operations | 172.16.1.128/26 | 60 | 62 | 96.77% | 0.0.0.63 |
| Branch-2 Operations | 172.16.1.192/26 | 50 | 62 | 80.65% | 0.0.0.63 |
| HQ Server/Colo | 172.16.2.0/26 | 40 | 62 | 64.52% | 0.0.0.63 |
| Branch-1 Guest | 172.16.2.64/27 | 20 | 30 | 66.67% | 0.0.0.31 |
| Branch-2 Guest | 172.16.2.96/27 | 15 | 30 | 50.0% | 0.0.0.31 |
| Management VLAN | 172.16.2.128/27 | 15 | 30 | 50.0% | 0.0.0.31 |

## Routing Protocol Decision

**Selected:** Single-Area OSPFv2 (Area 0)

Single Autonomous System with 9 subnets (3 sites) — well below the 50-subnet multi-area threshold. Selected Single-Area OSPFv2 Area 0 (RFC 2328) for link-state fast convergence via Dijkstra SPF, loop-free shortest-path forwarding, and zero external routing protocol overhead. All interfaces participate in Area 0 with a flat LSDB.

## Physical Media Decisions

| Link | Distance | Medium | Transceiver | Standard |
|------|--------:|--------|-------------|----------|
| HQ-Core-RTR ↔ HQ-Dist-SW1 | 15.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| HQ-Dist-SW1 ↔ HQ-Acc-SW1 | 30.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| HQ-Dist-SW1 ↔ HQ-Acc-SW2 | 45.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| HQ-Core-RTR ↔ BR1-Edge-RTR | 15000.0m | OS2_SMF | SFP+ 10GBASE-ER (1550nm Laser) | IEEE 802.3ae (10GBASE-ER, 1550 nm) |
| HQ-Core-RTR ↔ BR2-Edge-RTR | 35000.0m | OS2_SMF | SFP+ 10GBASE-ER (1550nm Laser) | IEEE 802.3ae (10GBASE-ER, 1550 nm) |
| BR1-Edge-RTR ↔ BR1-Acc-SW1 | 20.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| BR2-Edge-RTR ↔ BR2-Acc-SW1 | 25.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |

## Optical Link Budgets

| Link | Distance | Total Loss | Margin | Viable |
|------|--------:|-----------:|-------:|--------|
| M4-HQ-Core-to-Branch1 | 15.0 km | 4.9 dB | 9.9 dB | ✅ Yes |
| M5-HQ-Core-to-Branch2 | 35.0 km | 10.3 dB | 4.5 dB | ✅ Yes |

## Detailed Engineering Rationales

### 1. HQ-Core-RTR ↔ HQ-Dist-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 15.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 2. HQ-Dist-SW1 ↔ HQ-Acc-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 30.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 3. HQ-Dist-SW1 ↔ HQ-Acc-SW2: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 45.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 4. HQ-Core-RTR ↔ BR1-Edge-RTR: OS2_SMF
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3ae (10GBASE-ER, 1550 nm)

Link distance 15000.0m exceeds the 400m OM4 MMF limit (10GBASE-SR). Selected OS2 9/125 µm single-mode fibre with SFP+ 10GBASE-ER (1550nm Laser) transceiver (IEEE 802.3ae (10GBASE-ER, 1550 nm)), max reach 40000m. Single-mode fibre eliminates modal dispersion, and the optical link budget must be verified to ensure adequate receive power margin at this distance.

### 5. HQ-Core-RTR ↔ BR2-Edge-RTR: OS2_SMF
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3ae (10GBASE-ER, 1550 nm)

Link distance 35000.0m exceeds the 400m OM4 MMF limit (10GBASE-SR). Selected OS2 9/125 µm single-mode fibre with SFP+ 10GBASE-ER (1550nm Laser) transceiver (IEEE 802.3ae (10GBASE-ER, 1550 nm)), max reach 40000m. Single-mode fibre eliminates modal dispersion, and the optical link budget must be verified to ensure adequate receive power margin at this distance.

### 6. BR1-Edge-RTR ↔ BR1-Acc-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 20.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 7. BR2-Edge-RTR ↔ BR2-Acc-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 25.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 8. HQ Trading Floor: 172.16.0.0/25
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 172.16.0.0/25 for 'HQ Trading Floor' (VLAN 10). Network: 172.16.0.0, Mask: 255.255.255.128, Wildcard: 0.0.0.127, Hosts: 172.16.0.1–172.16.0.126, Broadcast: 172.16.0.127. Efficiency: 79.37%.

### 9. HQ Back Office: 172.16.0.128/25
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 172.16.0.128/25 for 'HQ Back Office' (VLAN 20). Network: 172.16.0.128, Mask: 255.255.255.128, Wildcard: 0.0.0.127, Hosts: 172.16.0.129–172.16.0.254, Broadcast: 172.16.0.255. Efficiency: 63.49%.

### 10. VoIP All Sites: 172.16.1.0/25
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 172.16.1.0/25 for 'VoIP All Sites' (VLAN 60). Network: 172.16.1.0, Mask: 255.255.255.128, Wildcard: 0.0.0.127, Hosts: 172.16.1.1–172.16.1.126, Broadcast: 172.16.1.127. Efficiency: 55.56%.

### 11. Branch-1 Operations: 172.16.1.128/26
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 172.16.1.128/26 for 'Branch-1 Operations' (VLAN 40). Network: 172.16.1.128, Mask: 255.255.255.192, Wildcard: 0.0.0.63, Hosts: 172.16.1.129–172.16.1.190, Broadcast: 172.16.1.191. Efficiency: 96.77%.

### 12. Branch-2 Operations: 172.16.1.192/26
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 172.16.1.192/26 for 'Branch-2 Operations' (VLAN 50). Network: 172.16.1.192, Mask: 255.255.255.192, Wildcard: 0.0.0.63, Hosts: 172.16.1.193–172.16.1.254, Broadcast: 172.16.1.255. Efficiency: 80.65%.

### 13. HQ Server/Colo: 172.16.2.0/26
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 172.16.2.0/26 for 'HQ Server/Colo' (VLAN 30). Network: 172.16.2.0, Mask: 255.255.255.192, Wildcard: 0.0.0.63, Hosts: 172.16.2.1–172.16.2.62, Broadcast: 172.16.2.63. Efficiency: 64.52%.

### 14. Branch-1 Guest: 172.16.2.64/27
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 172.16.2.64/27 for 'Branch-1 Guest' (VLAN 41). Network: 172.16.2.64, Mask: 255.255.255.224, Wildcard: 0.0.0.31, Hosts: 172.16.2.65–172.16.2.94, Broadcast: 172.16.2.95. Efficiency: 66.67%.

### 15. Branch-2 Guest: 172.16.2.96/27
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 172.16.2.96/27 for 'Branch-2 Guest' (VLAN 51). Network: 172.16.2.96, Mask: 255.255.255.224, Wildcard: 0.0.0.31, Hosts: 172.16.2.97–172.16.2.126, Broadcast: 172.16.2.127. Efficiency: 50.0%.

### 16. Management VLAN: 172.16.2.128/27
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 172.16.2.128/27 for 'Management VLAN' (VLAN 99). Network: 172.16.2.128, Mask: 255.255.255.224, Wildcard: 0.0.0.31, Hosts: 172.16.2.129–172.16.2.158, Broadcast: 172.16.2.159. Efficiency: 50.0%.

### 17. Single-Area OSPFv2 (Area 0) selected
**Category:** Layer 3 Routing Protocol
**Citations:** RFC 2328 (OSPFv2)

Single Autonomous System with 9 subnets (3 sites) — well below the 50-subnet multi-area threshold. Selected Single-Area OSPFv2 Area 0 (RFC 2328) for link-state fast convergence via Dijkstra SPF, loop-free shortest-path forwarding, and zero external routing protocol overhead. All interfaces participate in Area 0 with a flat LSDB.
