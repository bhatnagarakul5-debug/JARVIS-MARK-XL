"""
core/skills_engine.py — J.A.R.V.I.S. Mark 58 (Apex Core) Dynamic Skills Engine
Dynamically discovers, loads, registers, and reloads action skill modules at runtime.
"""

import os
import sys
import importlib
import inspect
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ACTIONS_DIR = BASE_DIR / "actions"

class SkillsEngine:
    """Singleton manager for dynamic action skill discovery, registration, and reloading."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.loaded_skills = {}
            cls._instance.discover_skills()
        return cls._instance

    def discover_skills(self) -> dict:
        """Discovers all valid python action modules in actions/ directory."""
        if not ACTIONS_DIR.exists():
            return self.loaded_skills

        sys_path = str(ACTIONS_DIR)
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)

        for file_path in ACTIONS_DIR.glob("*.py"):
            if file_path.name.startswith("_") or file_path.name == "setup.py":
                continue
            module_name = f"actions.{file_path.stem}"
            try:
                mod = importlib.import_module(module_name)
                funcs = [name for name, obj in inspect.getmembers(mod, inspect.isfunction) if not name.startswith("_")]
                self.loaded_skills[file_path.stem] = {
                    "module": mod,
                    "functions": funcs,
                    "path": str(file_path)
                }
            except Exception as e:
                print(f"[SkillsEngine] Warning loading {module_name}: {e}")

        return self.loaded_skills

    def reload_skill(self, skill_name: str) -> str:
        """Reloads a specific skill module dynamically at runtime."""
        skill_name = skill_name.lower().strip().replace(".py", "")
        module_key = f"actions.{skill_name}"
        if skill_name in self.loaded_skills:
            try:
                mod = self.loaded_skills[skill_name]["module"]
                reloaded = importlib.reload(mod)
                funcs = [name for name, obj in inspect.getmembers(reloaded, inspect.isfunction) if not name.startswith("_")]
                self.loaded_skills[skill_name] = {
                    "module": reloaded,
                    "functions": funcs,
                    "path": self.loaded_skills[skill_name]["path"]
                }
                return f"Mark 58 Apex Engine: Skill '{skill_name}' successfully reloaded at runtime."
            except Exception as e:
                return f"Failed to reload skill '{skill_name}': {e}"
        else:
            # Attempt to discover and import new skill
            try:
                mod = importlib.import_module(module_key)
                funcs = [name for name, obj in inspect.getmembers(mod, inspect.isfunction) if not name.startswith("_")]
                self.loaded_skills[skill_name] = {
                    "module": mod,
                    "functions": funcs,
                    "path": str(ACTIONS_DIR / f"{skill_name}.py")
                }
                return f"Mark 58 Apex Engine: New skill '{skill_name}' dynamically loaded!"
            except Exception as e:
                return f"Skill '{skill_name}' not found or invalid: {e}"

    def list_skills(self) -> str:
        """Lists all active loaded skills and their exported functions."""
        self.discover_skills()
        lines = [f"=== J.A.R.V.I.S. Mark 58 Active Skill Modules ({len(self.loaded_skills)}) ==="]
        for name, data in sorted(self.loaded_skills.items()):
            fn_count = len(data['functions'])
            lines.append(f"• {name.ljust(22)} ({fn_count} functions)")
        return "\n".join(lines)


skills_engine = SkillsEngine()

def mark_58_skills_control(parameters: dict, player=None) -> str:
    """Action handler for Mark 58 Apex Core Dynamic Skills Control."""
    params = parameters or {}
    action = (params.get("action") or "list").lower().strip()
    skill_name = params.get("skill_name", "").strip()

    if action in ("reload", "refresh", "load"):
        if not skill_name:
            return skills_engine.list_skills()
        return skills_engine.reload_skill(skill_name)

    return skills_engine.list_skills()

# Backward compatibility aliases
mark_41_skills_control = mark_58_skills_control
mark_45_skills_control = mark_58_skills_control
