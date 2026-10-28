"""Device automation must reject unsafe origins, ambiguous devices and emulators."""

import subprocess
from pathlib import Path

import pytest
from android_test_support import authorized_device, loopback_port


@pytest.mark.parametrize(
    "origin",
    [
        "https://production.example",
        "http://192.168.1.2:3000",
        "http://localhost:22",
        "http://user:secret@localhost:3000",
        "http://localhost:3000/app",
        "http://localhost:3000?external=1",
    ],
)
def test_android_reverse_refuses_non_owned_origin(origin: str) -> None:
    with pytest.raises(ValueError, match="owned localhost"):
        loopback_port(origin)


@pytest.mark.parametrize(
    "rows",
    [
        "",
        "synthetic unauthorized",
        "synthetic offline",
        "emulator-5554 device",
        "first device\nsecond device",
    ],
)
def test_android_requires_one_authorized_physical_device(
    monkeypatch: pytest.MonkeyPatch, rows: str
) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(["adb"], 0, "List of devices attached\n" + rows, "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(ValueError, match="authorized physical"):
        authorized_device(Path("adb"))


def test_android_reverse_uses_explicit_loopback_port() -> None:
    assert loopback_port("http://localhost:15391") == 15391
