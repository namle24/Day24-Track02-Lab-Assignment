"""RBAC helpers for the MedViet FastAPI service."""

from __future__ import annotations

from functools import wraps
from pathlib import Path
from typing import Optional

try:
    import casbin
except ImportError:  # pragma: no cover - used only in minimal local envs
    casbin = None

from fastapi import Header, HTTPException


MOCK_USERS = {
    "token-alice": {"username": "alice", "role": "admin"},
    "token-bob": {"username": "bob", "role": "ml_engineer"},
    "token-carol": {"username": "carol", "role": "data_analyst"},
    "token-dave": {"username": "dave", "role": "intern"},
}


class SimpleEnforcer:
    """Fallback Casbin-compatible enforcer for environments without casbin."""

    POLICIES = {
        ("admin", "patient_data", "read"),
        ("admin", "patient_data", "write"),
        ("admin", "patient_data", "delete"),
        ("admin", "training_data", "read"),
        ("admin", "aggregated_metrics", "read"),
        ("admin", "model_artifacts", "read"),
        ("admin", "model_artifacts", "write"),
        ("ml_engineer", "training_data", "read"),
        ("ml_engineer", "aggregated_metrics", "read"),
        ("ml_engineer", "model_artifacts", "read"),
        ("ml_engineer", "model_artifacts", "write"),
        ("data_analyst", "aggregated_metrics", "read"),
        ("data_analyst", "reports", "write"),
        ("intern", "sandbox_data", "read"),
        ("intern", "sandbox_data", "write"),
    }

    def enforce(self, role: str, resource: str, action: str) -> bool:
        return (role, resource, action) in self.POLICIES


def _build_enforcer():
    base_dir = Path(__file__).resolve().parent
    if casbin is None:
        return SimpleEnforcer()
    return casbin.Enforcer(str(base_dir / "model.conf"), str(base_dir / "policy.csv"))


enforcer = _build_enforcer()


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Parse Bearer token and return mock user information."""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.split(" ", 1)[1]
    user = MOCK_USERS.get(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user


def require_permission(resource: str, action: str):
    """Decorator checking whether the current user's role can access resource."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401, detail="Missing current user")

            role = current_user["role"]
            allowed = enforcer.enforce(role, resource, action)

            if not allowed:
                raise HTTPException(
                    status_code=403,
                    detail=f"Role '{role}' cannot '{action}' on '{resource}'",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
