"""Port for executing a validated freeform CAD script into geometry.

Kept behind an interface so the sandbox implementation (subprocess + audit hook)
can be swapped — e.g. for a container-backed runner once one is available —
without touching the application layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..domain.feature_program import MassProps, RawMesh


@dataclass
class FreeformRunResult:
    """The geometry produced by running a freeform script."""

    mesh: RawMesh
    mass_props: MassProps
    #: Path to an exported STEP of the result (in a temp dir the runner owns).
    step_path: str
    warnings: list[str] = field(default_factory=list)


class FreeformRunnerPort(ABC):
    @abstractmethod
    def run(self, code: str, timeout_s: float = 20.0) -> FreeformRunResult:
        """Execute a *pre-validated* script in isolation and return its geometry.

        Implementations must run the code out-of-process with a hard timeout and
        must not trust the code — validation (see ``domain.script_guard``) has
        already run, but the runner is the enforcement boundary.
        """
