# NetArchitect: Recommendation & Config Engine
### Algorithmic Network Planning & Self-Explaining Architecture Engine
**Course Code:** CIC-307 • Computer Networks Mini-Project  
**Weight:** 100 Points | **Submission Deadline:** 10 November 2026  
**Status:** Complete & Validated (`state.yaml` tracked)

---

## 📌 Project Overview
**NetArchitect** is an algorithmic network planning and self-explaining architecture engine developed in Python 3.10+. It ingests enterprise network parameters (preset scenarios or custom JSON topologies), runs deterministic algorithmic rule engines adhering strictly to IEEE and RFC networking standards, and produces:
1. **Dynamic Bitwise VLSM Subnet Allocations** with mathematically verified zero-collision address spaces and inverted wildcard masks.
2. **Layer 1 Physical Media Recommendations** (Cat6a copper vs OM4 MMF vs OS2 SMF) with optical link-budget loss/margin calculations.
3. **Layer 3 Routing Protocol Determinations** (Single-Area OSPFv2, Multi-Area OSPFv2, and eBGP with route redistribution).
4. **100% Copy-Paste Ready Cisco IOS / IOS-XE Configurations** for Core Routers (Router-on-a-Stick with IEEE 802.1Q subinterfaces, OSPF/BGP processes, extended perimeter ACLs, IPsec VTI tunnels) and Core Switches (SVIs, 802.1Q trunks with explicit allowed-VLAN pruning, Rapid-PVST+, VTP transparent).
5. **Self-Explaining Engineering Rationales** citing physical limits, mathematical equations, and relevant standards (IEEE 802.3an, IEEE 802.3ae, IEEE 802.1Q, RFC 1918, RFC 2328, RFC 4271).

---

## 🏗️ System Architecture & Data Flow

```
                      ┌────────────────────────────────────────┐
                      │             INPUT INGESTION            │
                      │   • Preset Profile JSON (1, 2, or 3)   │
                      │   • Custom Topology JSON Input         │
                      └───────────────────┬────────────────────┘
                                          │
                     ┌────────────────────┴────────────────────┐
                     ▼                                         ▼
       ┌───────────────────────────┐             ┌───────────────────────────┐
       │   LAYER 1 MEDIA ENGINE    │             │     LAYER 3 VLSM ENGINE   │
       │ • Distance Thresholds     │             │ • Descending Sort         │
       │ • Cat6a vs OM4 vs OS2     │             │ • Power-of-2 Sizing       │
       │ • Physical Boundary Check │             │ • Non-Overlapping Blocks  │
       │ • Optical Budget (dB/km)  │             │ • Wildcard Mask Inversion │
       └─────────────┬─────────────┘             └─────────────┬─────────────┘
                     │                                         │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                             ┌───────────────────────────┐
                             │    L3 ROUTING ENGINE      │
                             │ • Subnet Count Threshold  │
                             │ • Multi-Site / Multi-AS   │
                             │ • OSPF Area 0 vs Multi    │
                             │ • eBGP Peering & ASN      │
                             └────────────┬──────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │          EXPLAINABLE EXPORTER          │
                      │ • Copy-Paste Ready Cisco IOS Config    │
                      │ • Router-on-a-Stick dot1Q Subinterfaces│
                      │ • Perimeter ACLs with Wildcard Masks   │
                      │ • Architectural Rationale Report (.md) │
                      └───────────────────┬────────────────────┘
                                          │
                     ┌────────────────────┴────────────────────┐
                     ▼                                         ▼
       ┌───────────────────────────┐             ┌───────────────────────────┐
       │         RICH CLI          │             │     FASTAPI DASHBOARD     │
       │ • Interactive Terminal    │             │ • Modern Dark-Mode UI     │
       │ • Colorful Status Tables  │             │ • Real-time REST API      │
       │ • Direct .cfg File Export │             │ • One-Click .cfg Download │
       └───────────────────────────┘             └───────────────────────────┘
```

---

## 🎯 Preset Scenarios

NetArchitect comes packaged with three enterprise-scale preset scenarios:

### Profile 1: Campus LAN (`campus_lan.json`)
- **Scale:** 3 Buildings, link distance < 400 m.
- **Capacity:** 1,600 endpoints across 10 subnets (Engineering, Labs, Faculty, Library, VoIP, CCTV, APs, Server Farm, Management).
- **Root Prefix:** `10.10.0.0/16`
- **Key Technologies:** Cat6a copper (access runs ≤ 100m) vs OM4 MMF (backbone runs 101–400m), IEEE 802.1Q VLANs, Rapid-PVST+, Single-Area OSPFv2 Area 0, Router-on-a-Stick with subinterfaces, perimeter firewall ACLs.
- **Export:** `exports/profile1_campus_lan_cisco.cfg`

### Profile 2: Metro MAN (`metro_man.json`)
- **Scale:** FinTech HQ + 2 Remote Branch / Data Center sites (15 km to 35 km).
- **Capacity:** 450 users across 9 subnets (Trading Floor, Back Office, Colo, Branch 1, Branch 2, VoIP, Management).
- **Root Prefix:** `172.16.0.0/18`
- **Key Technologies:** OS2 Single-Mode Fiber (10GBASE-LR at 15km, 10GBASE-ER at 35km), optical link-budget power calculations, Single-Area OSPF with sub-5ms latency topology.
- **Export:** `exports/profile2_metro_man_cisco.cfg`

### Profile 3: Global WAN (`global_wan.json`)
- **Scale:** 4 Global Cities (London, New York, Tokyo, Singapore) + AWS VPC / Azure VNet cloud integration.
- **Capacity:** 2,000+ IoT scanners and corporate endpoints across 12 subnets.
- **Root Prefix:** `192.168.0.0/16`
- **Key Technologies:** Multi-Area OSPF backbone (Area 0, 1, 2, 3), eBGP peering (AS 65001), route summarization, Route-based IPsec VPN (VTI / IKEv2) tunnels, perimeter extended ACLs.
- **Export:** `exports/profile3_global_wan_cisco.cfg`

---

## ⚙️ Algorithmic Rules & Boundary Enforcements

| Domain | Rule / Boundary Condition | Algorithmic Enforcement |
|:---|:---|:---|
| **L1 Media** | Run $\le 100\text{ m}$ | Selects Cat6a (10GBASE-T, IEEE 802.3an) |
| **L1 Media** | Run $101\text{ m} - 400\text{ m}$ | Selects OM4 MMF (10GBASE-SR, 850nm VCSEL, IEEE 802.3ae) |
| **L1 Media** | Run $> 400\text{ m}$ | Selects OS2 SMF (10GBASE-LR/ER, 1310/1550nm laser) |
| **L1 Boundary** | Copper forced on link $> 100\text{ m}$ | Raises `PhysicalDistanceViolationError` immediately |
| **L1 Budget** | Fiber optical power budget | $\text{Margin} = P_{tx} - P_{rx\_sens} - (\alpha \cdot d + \text{losses}) > 0\text{ dB}$ |
| **L3 VLSM** | Host requirement ordering | Sorted **DESCENDING** before allocation to eliminate fragmentation |
| **L3 VLSM** | Address space capacity | Raises `SubnetExhaustionError` if required addresses exceed root block |
| **L3 VLSM** | Subnet overlap prevention | Bitwise boundary verification guarantees zero overlapping subnets |
| **L3 VLSM** | Wildcard mask calculation | Bitwise NOT: $\text{Wildcard} = \text{Mask} \oplus \text{0xFFFFFFFF}$ |
| **L3 Routing** | Single AS, $< 50$ subnets | Single-Area OSPFv2 (Area 0, RFC 2328) |
| **L3 Routing** | Multi-site / $> 50$ subnets | Multi-Area OSPFv2 with Area 0 backbone |
| **L3 Routing** | Multi-AS / Cloud VPC | Multi-Area OSPF + eBGP redistribution (RFC 4271) |
| **Cisco IOS** | Switch trunking | `switchport trunk allowed vlan ...` (explicit pruning; no unconstrained trunks) |
| **Cisco IOS** | Router-on-a-stick | `encapsulation dot1Q <vlan_id>` before `ip address`; parent port `no shutdown` |
| **Cisco IOS** | Security policies | Extended ACLs generated using exact bitwise inverted wildcard masks |

---

## 🚀 Installation & Quick Start

### 1. Clone & Install Dependencies
```powershell
# Navigate to workspace
cd c:\Users\DELL\CN_Mini_Project

# Install required packages
pip install -r requirements.txt
```

### 2. Run via Rich CLI
```powershell
# List available scenario presets
python -m netarchitect.cli list-presets

# Run a preset scenario (e.g. Campus LAN)
python -m netarchitect.cli run --preset campus_lan

# Run with custom JSON file
python -m netarchitect.cli run --file path/to/custom_scenario.json

# Validate a scenario JSON file
python -m netarchitect.cli validate netarchitect/presets/campus_lan.json
```

### 3. Launch the Interactive Web Dashboard
```powershell
# Start FastAPI dev server
python -m netarchitect.web

# Open in browser:
# http://127.0.0.1:8000
```
The web dashboard features:
- One-click preset scenario loader (Campus LAN, Metro MAN, Global WAN).
- Full VLSM allocation breakdown table with color-coded utilization efficiency badges.
- Physical media decision table with transceiver and standard citations.
- Optical link-budget table with loss calculations and link viability status.
- Copy-to-Clipboard and Direct Download buttons for Cisco IOS `.cfg` files.

---

## 🧪 Automated Test Suite (pytest)

The test suite covers 100% of the boundary conditions mandated by `state.yaml`:
```powershell
python -m pytest tests/ -v
```

### Test Coverage Highlights (61 Test Cases Passed):
- `TestMediaEngine`:
  - Cat6a within and at 100m boundary.
  - OM4 MMF at 101m and 400m boundary.
  - OS2 SMF at 401m and 15 km long-haul.
  - `PhysicalDistanceViolationError` when copper > 100m or MMF > 400m.
  - Optical budget viability and margin verification.
  - Forced OS2 SMF on short links without `KeyError`.
- `TestVLSMEngine`:
  - Descending sort order verification.
  - Mathematically verified zero address overlap.
  - Comprehensive subnet attribute validation (Network, CIDR, Mask, Wildcard, Gateway, Broadcast, Hosts, Wastage, Efficiency).
  - `SubnetExhaustionError` trigger on root prefix overflow.
- `TestWildcardMask`:
  - Arbitrary prefix wildcard calculations (/8, /13, /16, /18, /20, /24, /25, /26, /27, /28, /29, /30, /32).
  - Bitwise complement invariant: $\text{Mask} \lor \text{Wildcard} = \text{0xFFFFFFFF}$ and $\text{Mask} \land \text{Wildcard} = 0$.
- `TestRoutingEngine`:
  - Single-Area OSPF vs Multi-Area OSPF threshold switching.
  - eBGP triggers for Multi-AS and Cloud VPC.
- `TestPresetIntegration`:
  - End-to-end execution for Campus LAN, Metro MAN, and Global WAN.
  - Cisco IOS configuration syntax verification.
  - Router subinterface `encapsulation dot1Q` presence.
  - Extended ACL bitwise wildcard mask integration.
  - IPsec VPN tunnel and crypto profile validation.

---

## 🛡️ AI Defense & Code Auditing Log
In strict compliance with Section 4 of the CIC-307 specification, complete post-mortems of AI-suggested networking code defects are documented in [`ai_audit_log.md`](file:///c:/Users/DELL/CN_Mini_Project/ai_audit_log.md):
1. **Router-on-a-Stick Subinterface IEEE 802.1Q Omission:** AI models omit `encapsulation dot1Q` prior to `ip address`, causing Cisco IOS CLI syntax errors and dropping tagged frames.
2. **Optical Transceiver Mismatch & KeyError on Forced SMF:** AI selector failed to update transceiver types when single-mode fiber was forced on short links, leading to runtime crashes and incorrect attenuation math.
3. **Inverted Wildcard Mask Confusion in ACLs:** AI models confuse subnet masks with inverted wildcard masks, creating severe firewall bypass vulnerabilities.
4. **Terminal Encoding Crashes on Windows:** Rich CLI panel rendering of Unicode emojis on default `cp1252` Windows consoles repaired with UTF-8 stream reconfiguration.

---

## 📁 Repository Directory Structure

```
c:\Users\DELL\CN_Mini_Project\
├── ai_audit_log.md                  # Mandatory AI Defense & Code Auditing Log (20 Pts)
├── README.md                        # Project architecture & execution manual
├── requirements.txt                 # Python dependencies
├── state.yaml                       # Operational & architectural state tracking file
├── exports/                         # Generated verification export deliverables
│   ├── profile1_campus_lan_cisco.cfg
│   ├── profile1_campus_lan_rationale.md
│   ├── profile2_metro_man_cisco.cfg
│   ├── profile2_metro_man_rationale.md
│   ├── profile3_global_wan_cisco.cfg
│   └── profile3_global_wan_rationale.md
├── netarchitect/                    # Core Python package
│   ├── __init__.py
│   ├── __main__.py                  # CLI launcher (`python -m netarchitect`)
│   ├── cli.py                       # Rich + Typer interactive terminal UI
│   ├── exceptions.py                # Domain exceptions (PhysicalDistanceViolationError, SubnetExhaustionError)
│   ├── models.py                    # Pydantic data schemas & contracts
│   ├── orchestrator.py              # Pipeline execution coordinator & exporters
│   ├── web.py                       # FastAPI web dashboard backend
│   ├── engines/                     # Algorithmic decision engines
│   │   ├── __init__.py
│   │   ├── config_generator.py      # Cisco IOS / IOS-XE configuration generator
│   │   ├── media_engine.py          # L1 Media & optical link-budget engine
│   │   ├── routing_engine.py        # L3 OSPF & BGP protocol engine
│   │   └── vlsm_engine.py           # Bitwise VLSM subnet allocator
│   ├── presets/                     # Pre-packaged scenario data
│   │   ├── __init__.py
│   │   ├── campus_lan.json
│   │   ├── metro_man.json
│   │   └── global_wan.json
│   └── static/                      # Web dashboard frontend assets
│       ├── app.js                   # Dashboard logic & API connector
│       ├── index.html               # Responsive HTML5 layout
│       └── style.css                # Dark-mode glassmorphism design system
└── tests/                           # Automated pytest suite
    └── test_all.py                  # 61 unit and integration tests
```
#   M i n i - P R O J E C T  
 