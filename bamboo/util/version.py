
from __future__ import annotations


class _VersionState:
    alpha = "alpha"
    beta = "beta"
    gamma = "gamma"
    stable = "stable"
    
    _states = (
        alpha, beta, gamma, stable
    )
    
    __instance = None
    
    def __new__(cls) -> _VersionState:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def __iter__(self):
        return iter(self._states)
    
    def __contains__(self, item: str):
        return item in self._states
    
    
VersionState = _VersionState()


def resolve_version(major: int, minor: int, patch: int, state: str) -> str:
    if state not in VersionState:
        raise ValueError("Invalid 'state' found.")
    
    return f"{major}.{minor}.{patch}_{state}"
