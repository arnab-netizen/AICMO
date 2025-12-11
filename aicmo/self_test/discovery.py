"""
Self-Test Engine Discovery

Dynamically discovers all generators, adapters, packagers, and validators in the codebase.
"""

import importlib
import inspect
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DiscoveryResult:
    """Result of discovering a component."""

    def __init__(self, name: str, module_path: str, callable_obj: Optional[Any] = None):
        self.name = name
        self.module_path = module_path
        self.callable = callable_obj

    def __repr__(self) -> str:
        return f"<{self.name} at {self.module_path}>"


def discover_generators(base_path: str = "/workspaces/AICMO") -> List[DiscoveryResult]:
    """
    Discover all generator modules in aicmo/generators/.

    Returns:
        List of DiscoveryResult with generator info
    """
    generators = []
    gen_path = Path(base_path) / "aicmo" / "generators"

    if not gen_path.exists():
        return generators

    for py_file in sorted(gen_path.glob("*.py")):
        if py_file.name.startswith("_"):
            continue

        module_name = py_file.stem
        full_module = f"aicmo.generators.{module_name}"

        try:
            mod = importlib.import_module(full_module)
            generators.append(DiscoveryResult(module_name, full_module, mod))
        except Exception as e:
            print(f"Warning: Could not import {full_module}: {e}")

    return generators


def discover_adapters(base_path: str = "/workspaces/AICMO") -> List[DiscoveryResult]:
    """
    Discover all adapter/gateway modules in aicmo/gateways/adapters/.

    Returns:
        List of DiscoveryResult with adapter info
    """
    adapters = []
    adapters_path = Path(base_path) / "aicmo" / "gateways" / "adapters"

    if not adapters_path.exists():
        return adapters

    for py_file in sorted(adapters_path.glob("*.py")):
        if py_file.name.startswith("_"):
            continue

        module_name = py_file.stem
        full_module = f"aicmo.gateways.adapters.{module_name}"

        try:
            mod = importlib.import_module(full_module)
            adapters.append(DiscoveryResult(module_name, full_module, mod))
        except Exception as e:
            print(f"Warning: Could not import {full_module}: {e}")

    return adapters


def discover_packagers(base_path: str = "/workspaces/AICMO") -> List[DiscoveryResult]:
    """
    Discover all packaging functions (e.g., generate_full_deck_pptx, generate_html_summary).

    Scans aicmo/delivery/ for functions that generate output files.

    Returns:
        List of DiscoveryResult with packager info
    """
    packagers = []
    delivery_path = Path(base_path) / "aicmo" / "delivery"

    if not delivery_path.exists():
        return packagers

    for py_file in sorted(delivery_path.glob("*.py")):
        if py_file.name.startswith("_"):
            continue

        module_name = py_file.stem
        full_module = f"aicmo.delivery.{module_name}"

        try:
            mod = importlib.import_module(full_module)

            # Look for functions that generate output files
            for name, obj in inspect.getmembers(mod, inspect.isfunction):
                if any(
                    pattern in name
                    for pattern in [
                        "generate_",
                        "create_",
                        "export_",
                        "package_",
                        "build_",
                    ]
                ):
                    packagers.append(DiscoveryResult(name, full_module, obj))
        except Exception as e:
            print(f"Warning: Could not import {full_module}: {e}")

    return packagers


def discover_validators(base_path: str = "/workspaces/AICMO") -> List[DiscoveryResult]:
    """
    Discover all validator functions in aicmo/quality/validators.py.

    Returns:
        List of DiscoveryResult with validator info
    """
    validators = []

    try:
        mod = importlib.import_module("aicmo.quality.validators")

        # Look for validator functions and classes
        for name, obj in inspect.getmembers(mod):
            if name.startswith("_"):
                continue
            if any(
                pattern in name.lower()
                for pattern in ["validate", "validator", "check", "verify"]
            ):
                validators.append(DiscoveryResult(name, "aicmo.quality.validators", obj))
    except Exception as e:
        print(f"Warning: Could not import validators module: {e}")

    return validators


def discover_benchmarks(base_path: str = "/workspaces/AICMO") -> List[DiscoveryResult]:
    """
    Discover all benchmark files in learning/benchmarks/.

    Returns:
        List of DiscoveryResult with benchmark info
    """
    benchmarks = []
    benchmarks_path = Path(base_path) / "learning" / "benchmarks"

    if not benchmarks_path.exists():
        return benchmarks

    for json_file in sorted(benchmarks_path.glob("*.json")):
        benchmark_name = json_file.stem
        benchmarks.append(
            DiscoveryResult(
                benchmark_name, str(json_file.relative_to(base_path)), None
            )
        )

    return benchmarks


def discover_cam_components(base_path: str = "/workspaces/AICMO") -> List[DiscoveryResult]:
    """
    Discover CAM (Campaign/Account Management) components.

    Returns:
        List of DiscoveryResult with CAM component info
    """
    components = []
    cam_path = Path(base_path) / "aicmo" / "cam"

    if not cam_path.exists():
        return components

    # Try to discover the main orchestrator
    try:
        mod = importlib.import_module("aicmo.cam.orchestrator")
        components.append(DiscoveryResult("orchestrator", "aicmo.cam.orchestrator", mod))
    except Exception as e:
        print(f"Warning: Could not import CAM orchestrator: {e}")

    # Discover CAM modules
    for py_file in sorted(cam_path.glob("*.py")):
        if py_file.name in ["__init__.py", "orchestrator.py"]:
            continue

        module_name = py_file.stem
        full_module = f"aicmo.cam.{module_name}"

        try:
            mod = importlib.import_module(full_module)
            components.append(DiscoveryResult(module_name, full_module, mod))
        except Exception as e:
            print(f"Warning: Could not import {full_module}: {e}")

    return components


def get_all_discoveries(
    base_path: str = "/workspaces/AICMO",
) -> Dict[str, List[DiscoveryResult]]:
    """
    Run all discovery functions and return results.

    Returns:
        Dictionary with keys: generators, adapters, packagers, validators, benchmarks, cam_components
    """
    return {
        "generators": discover_generators(base_path),
        "adapters": discover_adapters(base_path),
        "packagers": discover_packagers(base_path),
        "validators": discover_validators(base_path),
        "benchmarks": discover_benchmarks(base_path),
        "cam_components": discover_cam_components(base_path),
    }
