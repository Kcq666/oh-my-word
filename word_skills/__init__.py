"""Shared document tooling and the repository-level Skill registry."""
__version__ = "0.3.0"

from .registry import load_registry, skill_by_name
from .router import list_skills, route

__all__ = ["__version__", "load_registry", "skill_by_name", "list_skills", "route"]
