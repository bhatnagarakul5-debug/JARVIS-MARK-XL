"""
actions/project_autopilot.py — Stark One-Command Workspace & Project Builder for JARVIS Mark XL
Automates creation of new coding projects, directory structures, boilerplate files, and VS Code / DaVinci launch.
"""

import os
import sys
import subprocess
from pathlib import Path

def create_project_workspace(parameters: dict, player=None) -> str:
    """
    Creates project directory, starter files, and opens workspace.
    parameters:
        project_name (str): Name of the project (e.g. MyNewApp, AI_Tool)
        project_type (str): python | davinci | web | cpp | general (default: python)
    """
    params = parameters or {}
    project_name = params.get("project_name") or params.get("name") or "New_Stark_Project"
    project_type = (params.get("project_type") or params.get("type") or "python").lower().strip()

    # Clean project name
    project_name = "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in project_name])

    desktop_dir = Path.home() / "OneDrive" / "Desktop"
    if not desktop_dir.exists():
        desktop_dir = Path.home() / "Desktop"

    projects_dir = desktop_dir / "Projects"
    target_dir = projects_dir / project_name

    try:
        target_dir.mkdir(parents=True, exist_ok=True)

        created_files = []

        if project_type == "python":
            main_py = target_dir / "main.py"
            main_py.write_text(
                f'"""\n{project_name} — Created by JARVIS Project Auto-Pilot\n"""\n\n'
                'def main():\n'
                '    print("JARVIS Project Auto-Pilot: Environment Ready!")\n\n'
                'if __name__ == "__main__":\n'
                '    main()\n',
                encoding="utf-8"
            )
            created_files.append("main.py")

            readme_md = target_dir / "README.md"
            readme_md.write_text(f"# {project_name}\n\nAutomated workspace created by J.A.R.V.I.S. Mark XL.\n", encoding="utf-8")
            created_files.append("README.md")

            requirements_txt = target_dir / "requirements.txt"
            requirements_txt.write_text("# Project Dependencies\n", encoding="utf-8")
            created_files.append("requirements.txt")

        elif project_type in ["davinci", "video", "editing"]:
            raw_dir = target_dir / "Raw_Clips"
            raw_dir.mkdir(exist_ok=True)
            audio_dir = target_dir / "Audio_Music"
            audio_dir.mkdir(exist_ok=True)
            exports_dir = target_dir / "Exports"
            exports_dir.mkdir(exist_ok=True)

            readme_md = target_dir / "PROJECT_NOTES.md"
            readme_md.write_text(f"# Video Project: {project_name}\n\nFolder structure:\n- /Raw_Clips\n- /Audio_Music\n- /Exports\n", encoding="utf-8")
            created_files.extend(["Raw_Clips/", "Audio_Music/", "Exports/", "PROJECT_NOTES.md"])

        elif project_type in ["web", "html", "js"]:
            index_html = target_dir / "index.html"
            index_html.write_text(
                f'<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8">\n  <title>{project_name}</title>\n</head>\n<body>\n  <h1>{project_name}</h1>\n</body>\n</html>\n',
                encoding="utf-8"
            )
            style_css = target_dir / "style.css"
            style_css.write_text("/* Custom Styles */\nbody { background: #0a0a0a; color: #00f0ff; font-family: sans-serif; }\n", encoding="utf-8")
            created_files.extend(["index.html", "style.css"])

        else:
            readme_md = target_dir / "README.md"
            readme_md.write_text(f"# {project_name}\n\nWorkspace created by JARVIS.\n", encoding="utf-8")
            created_files.append("README.md")

        # Try launching VS Code in target dir
        vscode_opened = False
        try:
            subprocess.Popen(["code", str(target_dir)], shell=True)
            vscode_opened = True
        except Exception:
            pass

        if player and hasattr(player, "write_log"):
            player.write_log(f"SYS: Created project workspace '{project_name}' at {target_dir}")

        msg = f"Project workspace '{project_name}' ({project_type.upper()}) created at {target_dir}. Files created: {', '.join(created_files)}."
        if vscode_opened:
            msg += " Opened workspace in VS Code."
        return msg

    except Exception as e:
        return f"Failed to create project workspace: {e}"
