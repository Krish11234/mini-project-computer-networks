"""NetArchitect Layer 1 Physical Media Selection Engine."""

from __future__ import annotations

from netarchitect.exceptions import PhysicalDistanceViolationError
from netarchitect.models import (
    LinkInput,
    MediaDecision,
    MediaType,
    OpticalBudget,
    Rationale,
    TransceiverType,
)

_CAT6A_MAX_M = 100.0
_OM4_MAX_M = 400.0

_TRANSCEIVER_SPECS: dict[TransceiverType, dict] = {
    TransceiverType.SFP_10GBASESR: {
        "tx_power_dBm": -1.0,
        "rx_sensitivity_dBm": -11.1,
        "fiber_attenuation_dB_per_km": 3.5,  # OM4 @ 850 nm
    },
    TransceiverType.SFP_10GBASELR: {
        "tx_power_dBm": -0.5,
        "rx_sensitivity_dBm": -14.4,
        "fiber_attenuation_dB_per_km": 0.35,  # OS2 @ 1310 nm
    },
    TransceiverType.SFP_10GBASEER: {
        "tx_power_dBm": -1.0,
        "rx_sensitivity_dBm": -15.8,
        "fiber_attenuation_dB_per_km": 0.22,  # OS2 @ 1550 nm
    },
}


def _validate_forced_medium(link: LinkInput) -> None:
    """Raise if a user-forced medium violates physical distance limits."""
    if link.forced_medium is None:
        return

    if link.forced_medium == MediaType.CAT6A and link.distance_m > _CAT6A_MAX_M:
        raise PhysicalDistanceViolationError(
            requested_medium="Cat6a (10GBASE-T)",
            distance_m=link.distance_m,
            max_distance_m=_CAT6A_MAX_M,
            ieee_standard="IEEE 802.3an",
        )
    if link.forced_medium == MediaType.OM4_MMF and link.distance_m > _OM4_MAX_M:
        raise PhysicalDistanceViolationError(
            requested_medium="OM4 Multimode Fiber (10GBASE-SR)",
            distance_m=link.distance_m,
            max_distance_m=_OM4_MAX_M,
            ieee_standard="IEEE 802.3ae (10GBASE-SR, 850 nm)",
        )


def _select_medium(distance_m: float) -> tuple[MediaType, TransceiverType, float, str]:
    """Return (media, transceiver, max_reach, ieee_std) based on distance."""
    if distance_m <= _CAT6A_MAX_M:
        return (
            MediaType.CAT6A,
            TransceiverType.RJ45_10GBASET,
            _CAT6A_MAX_M,
            "IEEE 802.3an (10GBASE-T)",
        )
    if distance_m <= _OM4_MAX_M:
        return (
            MediaType.OM4_MMF,
            TransceiverType.SFP_10GBASESR,
            _OM4_MAX_M,
            "IEEE 802.3ae (10GBASE-SR, 850 nm VCSEL)",
        )
    # > 400 m — choose LR (≤ 10 km) or ER (≤ 40 km)
    if distance_m <= 10_000:
        return (
            MediaType.OS2_SMF,
            TransceiverType.SFP_10GBASELR,
            10_000,
            "IEEE 802.3ae (10GBASE-LR, 1310 nm)",
        )
    return (
        MediaType.OS2_SMF,
        TransceiverType.SFP_10GBASEER,
        40_000,
        "IEEE 802.3ae (10GBASE-ER, 1550 nm)",
    )


def _build_rationale(
    distance_m: float,
    medium: MediaType,
    transceiver: TransceiverType,
    max_reach: float,
    ieee_std: str,
) -> str:
    """Produce an engineering rationale with physical & standard citations."""
    if medium == MediaType.CAT6A:
        return (
            f"Link distance {distance_m}m is within the {max_reach}m channel "
            f"reach of Cat6a twisted-pair copper ({ieee_std}). Cat6a provides "
            f"500 MHz bandwidth, supports 10GBASE-T with RJ-45 termination, "
            f"and enables cost-effective PoE/PoE+ power delivery. No optical "
            f"transceivers are required, minimising per-port cost."
        )
    if medium == MediaType.OM4_MMF:
        return (
            f"Link distance {distance_m}m exceeds the 100m Cat6a copper limit "
            f"(IEEE 802.3an) but is within the {max_reach}m reach of OM4 "
            f"50/125 µm multimode fibre with {transceiver.value} transceiver "
            f"({ieee_std}). OM4 provides an effective modal bandwidth of "
            f"4700 MHz·km at 850 nm, sufficient for 10 Gbps at this distance."
        )
    # OS2 SMF
    return (
        f"Link distance {distance_m}m exceeds the 400m OM4 MMF limit "
        f"(10GBASE-SR). Selected OS2 9/125 µm single-mode fibre with "
        f"{transceiver.value} transceiver ({ieee_std}), max reach "
        f"{max_reach}m. Single-mode fibre eliminates modal dispersion, and "
        f"the optical link budget must be verified to ensure adequate "
        f"receive power margin at this distance."
    )

def decide_media(link: LinkInput) -> tuple[MediaDecision, Rationale, OpticalBudget | None]:
    """
    Evaluate a single link and return:
      1. MediaDecision  – recommended medium with justification
      2. Rationale       – explainability payload
      3. OpticalBudget   – computed link budget (None for copper)
    """
    # Enforce boundary violations if user forces a medium
    _validate_forced_medium(link)

    medium, transceiver, max_reach, ieee_std = _select_medium(link.distance_m)

    # If the user forced a valid medium, honour it
    if link.forced_medium is not None:
        medium = link.forced_medium
        # Re-derive transceiver for the forced medium
        if medium == MediaType.CAT6A:
            transceiver, max_reach, ieee_std = (
                TransceiverType.RJ45_10GBASET, _CAT6A_MAX_M, "IEEE 802.3an"
            )
        elif medium == MediaType.OM4_MMF:
            transceiver, max_reach, ieee_std = (
                TransceiverType.SFP_10GBASESR, _OM4_MAX_M,
                "IEEE 802.3ae (10GBASE-SR, 850 nm VCSEL)",
            )
        elif medium == MediaType.OS2_SMF:
            if link.distance_m <= 10_000:
                transceiver, max_reach, ieee_std = (
                    TransceiverType.SFP_10GBASELR,
                    10_000.0,
                    "IEEE 802.3ae (10GBASE-LR, 1310 nm)",
                )
            else:
                transceiver, max_reach, ieee_std = (
                    TransceiverType.SFP_10GBASEER,
                    40_000.0,
                    "IEEE 802.3ae (10GBASE-ER, 1550 nm)",
                )

    rationale_text = _build_rationale(
        link.distance_m, medium, transceiver, max_reach, ieee_std,
    )

    decision = MediaDecision(
        link_id=link.link_id,
        source_node=link.source_node,
        destination_node=link.destination_node,
        distance_m=link.distance_m,
        recommended_medium=medium,
        transceiver=transceiver,
        max_reach_m=max_reach,
        ieee_standard=ieee_std,
        rationale=rationale_text,
    )

    rationale = Rationale(
        decision_category="Layer 1 Physical Media",
        decision_summary=f"{link.source_node} ↔ {link.destination_node}: {medium.value}",
        physical_justification=rationale_text,
        rfc_ieee_citations=[ieee_std],
        detail=rationale_text,
    )

    # Optical budget (only for fibre links)
    budget: OpticalBudget | None = None
    if medium in (MediaType.OM4_MMF, MediaType.OS2_SMF):
        specs = _TRANSCEIVER_SPECS[transceiver]
        budget = OpticalBudget(
            link_id=link.link_id,
            tx_power_dBm=specs["tx_power_dBm"],
            rx_sensitivity_dBm=specs["rx_sensitivity_dBm"],
            fiber_attenuation_dB_per_km=specs["fiber_attenuation_dB_per_km"],
            distance_km=link.distance_m / 1000.0,
            num_connectors=2,
            num_splices=max(0, int(link.distance_m / 2000) - 1),  # splice every 2 km
        ).compute()

    return decision, rationale, budget


def decide_all_media(
    links: list[LinkInput],
) -> tuple[list[MediaDecision], list[Rationale], list[OpticalBudget]]:
    """Process every link in the scenario and return aggregated results."""
    decisions: list[MediaDecision] = []
    rationales: list[Rationale] = []
    budgets: list[OpticalBudget] = []

    for link in links:
        dec, rat, bud = decide_media(link)
        decisions.append(dec)
        rationales.append(rat)
        if bud is not None:
            budgets.append(bud)

    return decisions, rationales, budgets
