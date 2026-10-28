"""Physical Chrome transport; never installs apps or reads personal device files."""

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def adb_command(adb: Path, serial: str, *arguments: str) -> str:
    result = subprocess.run(
        [str(adb), "-s", serial, *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    if result.returncode:
        raise RuntimeError("Android test transport failed; raw diagnostics withheld")
    return result.stdout.strip()


def authorized_device(adb: Path) -> str:
    result = subprocess.run(
        [str(adb), "devices", "-l"],
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    devices = [line.split() for line in result.stdout.splitlines()[1:] if line.strip()]
    if (
        len(devices) != 1
        or len(devices[0]) < 2
        or devices[0][1] != "device"
        or devices[0][0].startswith("emulator-")
    ):
        raise ValueError("Exactly one authorized physical Android device is required")
    return devices[0][0]


def loopback_port(origin: str) -> int:
    target = urlsplit(origin)
    if (
        target.scheme != "http"
        or target.hostname != "localhost"
        or not target.port
        or target.username
        or target.password
        or target.query
        or target.fragment
        or target.path not in {"", "/"}
        or target.port < 1024
    ):
        raise ValueError("Android reverse transport requires the owned localhost origin")
    return target.port


def run_android(environment: dict[str, str], origin: str, cache: Path) -> None:
    adb = Path(os.environ.get("LOCALAPPDATA", "")) / "Android/Sdk/platform-tools/adb.exe"
    if not adb.is_file():
        raise ValueError("Use the existing Android SDK; adb is unavailable")
    serial = authorized_device(adb)
    if adb_command(adb, serial, "shell", "getprop", "ro.kernel.qemu") == "1":
        raise ValueError("An emulator cannot satisfy physical-device acceptance")
    port = loopback_port(origin)
    mapping = f"tcp:{port}"
    if any(
        mapping in line.split()
        for line in adb_command(adb, serial, "reverse", "--list").splitlines()
    ):
        raise ValueError("Refusing to replace an existing reverse mapping")
    chrome = adb_command(adb, serial, "shell", "dumpsys", "package", "com.android.chrome")
    version = re.search(r"versionName=([^\s]+)", chrome)
    information = {
        "device_reference": hashlib.sha256(serial.encode()).hexdigest()[:12],
        "model": adb_command(adb, serial, "shell", "getprop", "ro.product.model"),
        "manufacturer": adb_command(adb, serial, "shell", "getprop", "ro.product.manufacturer"),
        "android": adb_command(adb, serial, "shell", "getprop", "ro.build.version.release"),
        "sdk": adb_command(adb, serial, "shell", "getprop", "ro.build.version.sdk"),
        "chrome": version.group(1) if version else "unavailable",
        "physical": True,
        "transport": "ADB USB reverse to owned HTTP localhost; Chrome CDP",
        "hosted_https_auth_tested": False,
    }
    (cache / "android-device.json").write_text(json.dumps(information, indent=2), encoding="utf-8")
    debugger_port: str | None = None
    try:
        adb_command(adb, serial, "reverse", mapping, mapping)
        adb_command(
            adb,
            serial,
            "shell",
            "am",
            "start",
            "-a",
            "android.intent.action.VIEW",
            "-d",
            origin + "/?physical-test=" + cache.name,
            "-p",
            "com.android.chrome",
            "--ez",
            "create_new_tab",
            "true",
        )
        debugger_port = adb_command(
            adb, serial, "forward", "tcp:0", "localabstract:chrome_devtools_remote"
        )
        if not debugger_port.isdecimal():
            raise ValueError("Invalid owned CDP port")
        (cache / "android-transport.json").write_text(
            json.dumps({"reverse": mapping, "forward": "tcp:" + debugger_port, "active": True}),
            encoding="utf-8",
        )
        node_environment = {
            **environment,
            "ANDROID_ADB_PATH": str(adb),
            "ANDROID_SERIAL": serial,
            "ANDROID_CDP_URL": "http://127.0.0.1:" + debugger_port,
            "ANDROID_TEST_ORIGIN": origin,
            "ANDROID_TEST_ARTIFACTS": str(cache),
        }
        subprocess.run(
            [
                "node",
                "scripts/live-social-android.mjs"
                if environment.get("ANDROID_LIVE_TEST") == "true"
                else "scripts/social-browser.mjs"
                if environment.get("ANDROID_SOCIAL_TEST") == "true"
                else "scripts/android-auth.mjs",
            ],
            cwd=ROOT / "frontend",
            env=node_environment,
            check=True,
            timeout=1800 if environment.get("ANDROID_LIVE_TEST") == "true" else 900,
        )
    finally:
        if debugger_port:
            adb_command(adb, serial, "forward", "--remove", "tcp:" + debugger_port)
        adb_command(adb, serial, "reverse", "--remove", mapping)
        (cache / "android-transport.json").write_text(
            json.dumps(
                {"reverse": mapping, "forward": "tcp:" + str(debugger_port), "active": False}
            ),
            encoding="utf-8",
        )
        print("Removed this Android run's USB port mappings.", flush=True)
