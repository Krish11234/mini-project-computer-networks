"""NetArchitect domain boundary-enforcement exceptions."""


class NetArchitectError(Exception):
    """Base exception for all NetArchitect domain errors."""
    pass


class PhysicalDistanceViolationError(NetArchitectError):
    """Raised when a requested cable medium cannot physically support the link distance."""

    def __init__(
        self,
        requested_medium: str,
        distance_m: float,
        max_distance_m: float,
        ieee_standard: str,
    ):
        self.requested_medium = requested_medium
        self.distance_m = distance_m
        self.max_distance_m = max_distance_m
        self.ieee_standard = ieee_standard
        super().__init__(
            f"PHYSICAL DISTANCE VIOLATION: {requested_medium} requested for "
            f"{distance_m}m link, but maximum reach per {ieee_standard} is "
            f"{max_distance_m}m. Signal attenuation will exceed acceptable "
            f"thresholds beyond this distance."
        )


class SubnetExhaustionError(NetArchitectError):
    """Raised when aggregate host demand exceeds total usable addresses in root prefix."""

    def __init__(
        self,
        root_prefix: str,
        available_hosts: int,
        requested_hosts: int,
    ):
        self.root_prefix = root_prefix
        self.available_hosts = available_hosts
        self.requested_hosts = requested_hosts
        super().__init__(
            f"SUBNET EXHAUSTION: Root prefix {root_prefix} provides "
            f"{available_hosts:,} usable host addresses, but {requested_hosts:,} "
            f"were requested. Cannot allocate non-overlapping VLSM blocks."
        )


class SubnetOverlapError(NetArchitectError):
    """Raised if a newly computed subnet block collides with an already-allocated block."""

    def __init__(self, new_block: str, existing_block: str):
        self.new_block = new_block
        self.existing_block = existing_block
        super().__init__(
            f"SUBNET OVERLAP DETECTED: Attempted to allocate {new_block} "
            f"which overlaps with existing allocation {existing_block}. "
            f"This violates the zero-overlap invariant."
        )


class ConfigGenerationError(NetArchitectError):
    """Raised when Cisco IOS configuration generation encounters an irrecoverable inconsistency."""
    pass

