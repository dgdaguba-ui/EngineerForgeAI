"""CadKernelPort — compiles Feature Programs into geometry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..domain.feature_program import CompiledPart, FeatureProgram


class CadKernelPort(ABC):
    @abstractmethod
    def compile(self, program: FeatureProgram) -> tuple[CompiledPart, Any]:
        """Compile a program.

        Returns (compiled_part, native_solid). The native solid handle is
        kernel-specific and is retained by the parts service solely to hand
        back to :meth:`export_solid` (B-rep exports like STEP need it).
        """

    @abstractmethod
    def export_solid(self, native_solid: Any, dst_path: str) -> None:
        """Export the native solid to a B-rep/mesh format inferred from the
        destination extension (kernel-supported formats, e.g. STEP/STL)."""
