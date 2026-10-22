# Architectural Rationale Report — Global WAN – 4-City Enterprise + Cloud VPC

**Scale:** Global WAN

## VLSM Allocation Summary

Root Network: `192.168.0.0/16`
Total Requested Hosts: 1,950
Overall Efficiency: 82.07%

| Subnet | CIDR | Hosts | Capacity | Efficiency | Wildcard |
|--------|------|------:|--------:|-----------:|----------|
| Singapore-IoT Scanners | 192.168.0.0/23 | 500 | 510 | 98.04% | 0.0.1.255 |
| AWS VPC Workloads | 192.168.2.0/24 | 250 | 254 | 98.43% | 0.0.0.255 |
| London-DC Servers | 192.168.3.0/24 | 200 | 254 | 78.74% | 0.0.0.255 |
| Azure VNet Workloads | 192.168.4.0/24 | 200 | 254 | 78.74% | 0.0.0.255 |
| NewYork-DC Servers | 192.168.5.0/24 | 180 | 254 | 70.87% | 0.0.0.255 |
| London-Office Users | 192.168.6.0/24 | 150 | 254 | 59.06% | 0.0.0.255 |
| NewYork-Office Users | 192.168.7.0/25 | 120 | 126 | 95.24% | 0.0.0.127 |
| Tokyo-DC Servers | 192.168.7.128/25 | 100 | 126 | 79.37% | 0.0.0.127 |
| Tokyo-Office Users | 192.168.8.0/25 | 80 | 126 | 63.49% | 0.0.0.127 |
| Global VoIP | 192.168.8.128/25 | 80 | 126 | 63.49% | 0.0.0.127 |
| Singapore-Office Users | 192.168.9.0/26 | 60 | 62 | 96.77% | 0.0.0.63 |
| Management VLAN | 192.168.9.64/27 | 30 | 30 | 100.0% | 0.0.0.31 |

## Routing Protocol Decision

**Selected:** Multi-Area OSPF + eBGP Redistribution

Network spans multiple Autonomous Systems across 4 sites with 12 subnets. Selected Multi-Area OSPF for internal routing domain isolation, failure containment, and route summarisation at ABR boundaries (RFC 2328). eBGP (RFC 4271) is additionally required for inter-AS path selection with policy-based path manipulation and route filtering at ASBR. Private ASN 65001 assigned per RFC 6996.

## Physical Media Decisions

| Link | Distance | Medium | Transceiver | Standard |
|------|--------:|--------|-------------|----------|
| LON-Core-RTR ↔ LON-Dist-SW1 | 50.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| LON-Dist-SW1 ↔ LON-Acc-SW1 | 35.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| NYC-Core-RTR ↔ NYC-Dist-SW1 | 40.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| NYC-Dist-SW1 ↔ NYC-Acc-SW1 | 30.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| TKY-Core-RTR ↔ TKY-Dist-SW1 | 55.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| TKY-Dist-SW1 ↔ TKY-Acc-SW1 | 25.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| SGP-Core-RTR ↔ SGP-Dist-SW1 | 45.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| SGP-Dist-SW1 ↔ SGP-Acc-SW1 | 20.0m | Cat6a | RJ-45 (10GBASE-T) | IEEE 802.3an (10GBASE-T) |
| LON-Core-RTR ↔ NYC-Core-RTR | 5570000.0m | OS2_SMF | SFP+ 10GBASE-ER (1550nm Laser) | IEEE 802.3ae (10GBASE-ER, 1550 nm) |
| NYC-Core-RTR ↔ TKY-Core-RTR | 10850000.0m | OS2_SMF | SFP+ 10GBASE-ER (1550nm Laser) | IEEE 802.3ae (10GBASE-ER, 1550 nm) |
| TKY-Core-RTR ↔ SGP-Core-RTR | 5300000.0m | OS2_SMF | SFP+ 10GBASE-ER (1550nm Laser) | IEEE 802.3ae (10GBASE-ER, 1550 nm) |
| LON-Core-RTR ↔ AWS-TGW | 1000.0m | OS2_SMF | SFP+ 10GBASE-LR (1310nm Laser) | IEEE 802.3ae (10GBASE-LR, 1310 nm) |
| NYC-Core-RTR ↔ Azure-ER-GW | 1500.0m | OS2_SMF | SFP+ 10GBASE-LR (1310nm Laser) | IEEE 802.3ae (10GBASE-LR, 1310 nm) |

## Optical Link Budgets

| Link | Distance | Total Loss | Margin | Viable |
|------|--------:|-----------:|-------:|--------|
| W9-LON-to-NYC-WAN | 5570.0 km | 1504.8 dB | -1490.0 dB | ❌ No |
| W10-NYC-to-TKY-WAN | 10850.0 km | 2930.4 dB | -2915.6 dB | ❌ No |
| W11-TKY-to-SGP-WAN | 5300.0 km | 1431.9 dB | -1417.1 dB | ❌ No |
| W12-LON-to-AWS-VPC | 1.0 km | 1.35 dB | 12.55 dB | ✅ Yes |
| W13-NYC-to-Azure-VNet | 1.5 km | 1.52 dB | 12.38 dB | ✅ Yes |

## Detailed Engineering Rationales

### 1. LON-Core-RTR ↔ LON-Dist-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 50.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 2. LON-Dist-SW1 ↔ LON-Acc-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 35.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 3. NYC-Core-RTR ↔ NYC-Dist-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 40.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 4. NYC-Dist-SW1 ↔ NYC-Acc-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 30.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 5. TKY-Core-RTR ↔ TKY-Dist-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 55.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 6. TKY-Dist-SW1 ↔ TKY-Acc-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 25.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 7. SGP-Core-RTR ↔ SGP-Dist-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 45.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 8. SGP-Dist-SW1 ↔ SGP-Acc-SW1: Cat6a
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3an (10GBASE-T)

Link distance 20.0m is within the 100.0m channel reach of Cat6a twisted-pair copper (IEEE 802.3an (10GBASE-T)). Cat6a provides 500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, and enables cost-effective PoE/PoE+ power delivery. No optical transceivers are required, minimising per-port cost.

### 9. LON-Core-RTR ↔ NYC-Core-RTR: OS2_SMF
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3ae (10GBASE-ER, 1550 nm)

Link distance 5570000.0m exceeds the 400m OM4 MMF limit (10GBASE-SR). Selected OS2 9/125 µm single-mode fibre with SFP+ 10GBASE-ER (1550nm Laser) transceiver (IEEE 802.3ae (10GBASE-ER, 1550 nm)), max reach 40000m. Single-mode fibre eliminates modal dispersion, and the optical link budget must be verified to ensure adequate receive power margin at this distance.

### 10. NYC-Core-RTR ↔ TKY-Core-RTR: OS2_SMF
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3ae (10GBASE-ER, 1550 nm)

Link distance 10850000.0m exceeds the 400m OM4 MMF limit (10GBASE-SR). Selected OS2 9/125 µm single-mode fibre with SFP+ 10GBASE-ER (1550nm Laser) transceiver (IEEE 802.3ae (10GBASE-ER, 1550 nm)), max reach 40000m. Single-mode fibre eliminates modal dispersion, and the optical link budget must be verified to ensure adequate receive power margin at this distance.

### 11. TKY-Core-RTR ↔ SGP-Core-RTR: OS2_SMF
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3ae (10GBASE-ER, 1550 nm)

Link distance 5300000.0m exceeds the 400m OM4 MMF limit (10GBASE-SR). Selected OS2 9/125 µm single-mode fibre with SFP+ 10GBASE-ER (1550nm Laser) transceiver (IEEE 802.3ae (10GBASE-ER, 1550 nm)), max reach 40000m. Single-mode fibre eliminates modal dispersion, and the optical link budget must be verified to ensure adequate receive power margin at this distance.

### 12. LON-Core-RTR ↔ AWS-TGW: OS2_SMF
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3ae (10GBASE-LR, 1310 nm)

Link distance 1000.0m exceeds the 400m OM4 MMF limit (10GBASE-SR). Selected OS2 9/125 µm single-mode fibre with SFP+ 10GBASE-LR (1310nm Laser) transceiver (IEEE 802.3ae (10GBASE-LR, 1310 nm)), max reach 10000m. Single-mode fibre eliminates modal dispersion, and the optical link budget must be verified to ensure adequate receive power margin at this distance.

### 13. NYC-Core-RTR ↔ Azure-ER-GW: OS2_SMF
**Category:** Layer 1 Physical Media
**Citations:** IEEE 802.3ae (10GBASE-LR, 1310 nm)

Link distance 1500.0m exceeds the 400m OM4 MMF limit (10GBASE-SR). Selected OS2 9/125 µm single-mode fibre with SFP+ 10GBASE-LR (1310nm Laser) transceiver (IEEE 802.3ae (10GBASE-LR, 1310 nm)), max reach 10000m. Single-mode fibre eliminates modal dispersion, and the optical link budget must be verified to ensure adequate receive power margin at this distance.

### 14. Singapore-IoT Scanners: 192.168.0.0/23
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.0.0/23 for 'Singapore-IoT Scanners' (VLAN 40). Network: 192.168.0.0, Mask: 255.255.254.0, Wildcard: 0.0.1.255, Hosts: 192.168.0.1–192.168.1.254, Broadcast: 192.168.1.255. Efficiency: 98.04%.

### 15. AWS VPC Workloads: 192.168.2.0/24
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.2.0/24 for 'AWS VPC Workloads' (VLAN 100). Network: 192.168.2.0, Mask: 255.255.255.0, Wildcard: 0.0.0.255, Hosts: 192.168.2.1–192.168.2.254, Broadcast: 192.168.2.255. Efficiency: 98.43%.

### 16. London-DC Servers: 192.168.3.0/24
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.3.0/24 for 'London-DC Servers' (VLAN 10). Network: 192.168.3.0, Mask: 255.255.255.0, Wildcard: 0.0.0.255, Hosts: 192.168.3.1–192.168.3.254, Broadcast: 192.168.3.255. Efficiency: 78.74%.

### 17. Azure VNet Workloads: 192.168.4.0/24
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.4.0/24 for 'Azure VNet Workloads' (VLAN 101). Network: 192.168.4.0, Mask: 255.255.255.0, Wildcard: 0.0.0.255, Hosts: 192.168.4.1–192.168.4.254, Broadcast: 192.168.4.255. Efficiency: 78.74%.

### 18. NewYork-DC Servers: 192.168.5.0/24
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.5.0/24 for 'NewYork-DC Servers' (VLAN 20). Network: 192.168.5.0, Mask: 255.255.255.0, Wildcard: 0.0.0.255, Hosts: 192.168.5.1–192.168.5.254, Broadcast: 192.168.5.255. Efficiency: 70.87%.

### 19. London-Office Users: 192.168.6.0/24
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.6.0/24 for 'London-Office Users' (VLAN 11). Network: 192.168.6.0, Mask: 255.255.255.0, Wildcard: 0.0.0.255, Hosts: 192.168.6.1–192.168.6.254, Broadcast: 192.168.6.255. Efficiency: 59.06%.

### 20. NewYork-Office Users: 192.168.7.0/25
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.7.0/25 for 'NewYork-Office Users' (VLAN 21). Network: 192.168.7.0, Mask: 255.255.255.128, Wildcard: 0.0.0.127, Hosts: 192.168.7.1–192.168.7.126, Broadcast: 192.168.7.127. Efficiency: 95.24%.

### 21. Tokyo-DC Servers: 192.168.7.128/25
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.7.128/25 for 'Tokyo-DC Servers' (VLAN 30). Network: 192.168.7.128, Mask: 255.255.255.128, Wildcard: 0.0.0.127, Hosts: 192.168.7.129–192.168.7.254, Broadcast: 192.168.7.255. Efficiency: 79.37%.

### 22. Tokyo-Office Users: 192.168.8.0/25
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.8.0/25 for 'Tokyo-Office Users' (VLAN 31). Network: 192.168.8.0, Mask: 255.255.255.128, Wildcard: 0.0.0.127, Hosts: 192.168.8.1–192.168.8.126, Broadcast: 192.168.8.127. Efficiency: 63.49%.

### 23. Global VoIP: 192.168.8.128/25
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.8.128/25 for 'Global VoIP' (VLAN 60). Network: 192.168.8.128, Mask: 255.255.255.128, Wildcard: 0.0.0.127, Hosts: 192.168.8.129–192.168.8.254, Broadcast: 192.168.8.255. Efficiency: 63.49%.

### 24. Singapore-Office Users: 192.168.9.0/26
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.9.0/26 for 'Singapore-Office Users' (VLAN 41). Network: 192.168.9.0, Mask: 255.255.255.192, Wildcard: 0.0.0.63, Hosts: 192.168.9.1–192.168.9.62, Broadcast: 192.168.9.63. Efficiency: 96.77%.

### 25. Management VLAN: 192.168.9.64/27
**Category:** VLSM Allocation
**Citations:** RFC 1918 (Private Addressing), RFC 950 (Subnetting)

Allocated 192.168.9.64/27 for 'Management VLAN' (VLAN 99). Network: 192.168.9.64, Mask: 255.255.255.224, Wildcard: 0.0.0.31, Hosts: 192.168.9.65–192.168.9.94, Broadcast: 192.168.9.95. Efficiency: 100.0%.

### 26. Multi-Area OSPF + eBGP Redistribution selected
**Category:** Layer 3 Routing Protocol
**Citations:** RFC 2328 (OSPFv2), RFC 4271 (BGP-4), RFC 6996 (Private ASNs)

Network spans multiple Autonomous Systems across 4 sites with 12 subnets. Selected Multi-Area OSPF for internal routing domain isolation, failure containment, and route summarisation at ABR boundaries (RFC 2328). eBGP (RFC 4271) is additionally required for inter-AS path selection with policy-based path manipulation and route filtering at ASBR. Private ASN 65001 assigned per RFC 6996.
