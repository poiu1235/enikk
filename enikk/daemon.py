"""Compatibility exports for the old daemon module name."""
from .runtime import Daemon, GameRuntime, _rpc_registry, profile_from_config, rpc

__all__ = ["Daemon", "GameRuntime", "_rpc_registry", "profile_from_config", "rpc"]
