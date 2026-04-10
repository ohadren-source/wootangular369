"""
lilypod/scaffold.py
Project scaffolding engine for `lilypod init`.

Copies templates from lilypod/templates/project/ into a new project directory,
strips the .tpl extension, and substitutes {{PROJECT_NAME}} with the given name.

Janina pattern. No ORM. No abstraction layers. Direct.
For Lilian. For Lily.
"""

import os
import shutil


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates", "project")


def scaffold_project(project_name: str) -> None:
    """
    Create a new wootangular-compatible project directory.

    Walks lilypod/templates/project/, copies every .tpl file (stripping .tpl),
    and substitutes {{PROJECT_NAME}} with project_name in every file.
    Prints boot instructions on success.
    """
    target_dir = os.path.abspath(project_name)

    if os.path.exists(target_dir):
        print(f"ERROR: Directory '{target_dir}' already exists. Choose a different name.")
        return

    os.makedirs(target_dir)

    for root, dirs, files in os.walk(TEMPLATES_DIR):
        # Compute relative path from templates root
        rel_root = os.path.relpath(root, TEMPLATES_DIR)
        target_root = os.path.join(target_dir, rel_root) if rel_root != "." else target_dir

        # Create subdirectory in target if needed
        if rel_root != ".":
            os.makedirs(target_root, exist_ok=True)

        for filename in files:
            src_path = os.path.join(root, filename)

            # Strip .tpl extension for output filename
            if filename.endswith(".tpl"):
                out_filename = filename[:-4]
            else:
                out_filename = filename

            dst_path = os.path.join(target_root, out_filename)

            with open(src_path, "r", encoding="utf-8") as f:
                content = f.read()

            content = content.replace("{{PROJECT_NAME}}", project_name)

            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(content)

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  LILYPOD — Project Scaffolded: {project_name:<29} ║
╚══════════════════════════════════════════════════════════════╝

Project created at: {target_dir}

Boot sequence:
  1. cd {project_name}
  2. Set DATABASE_URL env var (PostgreSQL)
  3. pip install -r requirements.txt
  4. python api/server.py

The lily grows in the swamp.
Rooted in mud. Blooms above it.

BOOL++: TRUE(1) · FALSE(0) · NULL_Φ(2)
Albert's Axiom: E = m ↔ c² [NULL_Φ(T, ΔS)]

VENIM.US · VIDEM.US · VINCIM.US
For Lilian. For Lily. 🌸
""")
