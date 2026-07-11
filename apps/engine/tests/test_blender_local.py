from __future__ import annotations

from engineerforge_engine.adapters.blender.local import (
    BLENDER_CONVERT_SCRIPT,
    build_headless_command,
    find_blender_executable,
    parse_blender_version,
    parse_efc_result,
)


def _no_which(_name: str) -> str | None:
    return None


def _no_glob(_pattern: str) -> list[str]:
    return []


class TestFindBlenderExecutable:
    def test_env_override_wins_when_valid(self) -> None:
        result = find_blender_executable(
            env={"EFC_BLENDER_PATH": r"D:\tools\blender.exe"},
            platform="win32",
            which=lambda _: r"C:\other\blender.exe",
            glob_fn=_no_glob,
            exists=lambda p: p == r"D:\tools\blender.exe",
        )
        assert result == r"D:\tools\blender.exe"

    def test_invalid_override_does_not_fall_back(self) -> None:
        # an explicit-but-wrong override should surface as "not found",
        # not silently pick a different installation
        result = find_blender_executable(
            env={"EFC_BLENDER_PATH": r"D:\missing\blender.exe"},
            platform="win32",
            which=lambda _: r"C:\other\blender.exe",
            glob_fn=lambda _: [r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"],
            exists=lambda _: False,
        )
        assert result is None

    def test_path_lookup(self) -> None:
        result = find_blender_executable(
            env={},
            platform="linux",
            which=lambda name: "/usr/bin/blender" if name == "blender" else None,
            glob_fn=_no_glob,
            exists=lambda _: False,
        )
        assert result == "/usr/bin/blender"

    def test_windows_glob_picks_highest_version(self) -> None:
        installs = [
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        ]
        result = find_blender_executable(
            env={},
            platform="win32",
            which=_no_which,
            glob_fn=lambda pattern: installs if "Program Files\\Blender" in pattern else [],
            exists=lambda _: False,
        )
        assert result is not None and "Blender 5.0" in result

    def test_none_when_nothing_found(self) -> None:
        assert (
            find_blender_executable(
                env={}, platform="win32", which=_no_which, glob_fn=_no_glob, exists=lambda _: False
            )
            is None
        )


class TestParsers:
    def test_parse_blender_version(self) -> None:
        assert parse_blender_version("Blender 5.0.1\n\tbuild date: ...") == "5.0.1"
        assert parse_blender_version("Blender 4.2\n") == "4.2"
        assert parse_blender_version("garbage") == "unknown"

    def test_parse_efc_result_takes_last_valid_line(self) -> None:
        stdout = "\n".join(
            [
                "Blender quit",
                "EFC_RESULT {broken json",
                'EFC_RESULT {"ok": true, "objects": 1}',
                'EFC_RESULT {"ok": true, "objects": 2}',
            ]
        )
        assert parse_efc_result(stdout) == {"ok": True, "objects": 2}

    def test_parse_efc_result_none_when_absent(self) -> None:
        assert parse_efc_result("no markers here") is None


class TestCommandAndScript:
    def test_build_headless_command(self) -> None:
        cmd = build_headless_command("blender.exe", "job.py", ["a.stl", "b.glb"])
        assert cmd == [
            "blender.exe",
            "--background",
            "--factory-startup",
            "--python",
            "job.py",
            "--",
            "a.stl",
            "b.glb",
        ]
        assert build_headless_command("b", "s.py", None) == [
            "b",
            "--background",
            "--factory-startup",
            "--python",
            "s.py",
        ]

    def test_convert_script_has_version_fallback_operators(self) -> None:
        # modern 4.x+ operators AND legacy fallbacks must both be present
        for op in ("wm.stl_import", "import_mesh.stl", "wm.obj_export", "export_scene.obj"):
            assert op in BLENDER_CONVERT_SCRIPT
        assert "EFC_RESULT" in BLENDER_CONVERT_SCRIPT
        assert "read_factory_settings" in BLENDER_CONVERT_SCRIPT
