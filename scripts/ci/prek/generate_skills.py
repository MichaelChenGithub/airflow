#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""
Parse ``.. SKILL-START`` / ``.. SKILL-END`` blocks from RST files and generate
agent skill files under ``.agents/skills/``.

Block format in RST (the indented body is an RST comment and is ignored by Sphinx).
The block body is YAML; ``body:`` uses a YAML literal block scalar (``|``).

``type: skill`` — generates ``SKILL.md``::

    .. SKILL-START
       type: skill
       id: <skill-id>
       description: >
         One-line trigger description for the agent index.
       compatibility: Optional override (default: Requires git, uv, and Apache Airflow Breeze)
       body: |
         ## Markdown body here
    .. SKILL-END

``type: ref`` — generates ``references/<id>.md`` inside the parent skill::

    .. SKILL-START
       type: ref
       skill: <skill-id>
       id: <ref-id>
       body: |
         ## Reference content here
    .. SKILL-END

Output mapping:

- ``type: skill``  →  ``.agents/skills/<id>/SKILL.md``
- ``type: ref``    →  ``.agents/skills/<skill>/references/<id>.md``
"""
from __future__ import annotations

import re
import sys
from glob import glob
from pathlib import Path

import yaml

AIRFLOW_ROOT = Path(__file__).parents[3].resolve()
AGENTS_SKILLS_ROOT = AIRFLOW_ROOT / ".agents" / "skills"
CONTRIBUTING_DOCS_ROOT = AIRFLOW_ROOT / "contributing-docs"

_DEFAULT_COMPATIBILITY = "Requires git, uv, and Apache Airflow Breeze"

_BLOCK_RE = re.compile(r"\.\. SKILL-START\n(.*?)\.\. SKILL-END", re.DOTALL)


def _parse_blocks_from_rst(rst_path: Path) -> list[dict]:
    text = rst_path.read_text()
    blocks = []
    for match in _BLOCK_RE.finditer(text):
        raw = match.group(1)
        dedented = "\n".join(
            line[3:] if line.startswith("   ") else line for line in raw.splitlines()
        )
        block = yaml.safe_load(dedented)
        if isinstance(block, dict):
            block["_source"] = str(rst_path)
            blocks.append(block)
    return blocks


def generate_all_content(rst_glob: str) -> dict[str, str]:
    """
    Return ``{ relative_output_path: content }`` for all blocks found.

    Shared by ``generate_skills.py`` (write to disk) and any future
    validation script (hash check).
    """
    result: dict[str, str] = {}
    for rst_path_str in glob(rst_glob, recursive=True):
        for block in _parse_blocks_from_rst(Path(rst_path_str)):
            block_type = block.get("type")
            if block_type == "skill":
                skill_id = block.get("id")
                if not skill_id:
                    print(
                        f"WARNING: type=skill block missing 'id' in {block['_source']}",
                        file=sys.stderr,
                    )
                    continue
                description = str(block.get("description", "")).strip()
                compatibility = str(block.get("compatibility", _DEFAULT_COMPATIBILITY)).strip()
                body = block.get("body", "")
                content = (
                    f"---\n"
                    f"name: {skill_id}\n"
                    f"description: {description}\n"
                    f"compatibility: {compatibility}\n"
                    f"---\n\n"
                    f"{body}"
                )
                result[f".agents/skills/{skill_id}/SKILL.md"] = content
            elif block_type == "ref":
                skill_id = block.get("skill")
                ref_id = block.get("id")
                if not skill_id or not ref_id:
                    print(
                        f"WARNING: type=ref block missing 'skill' or 'id' in {block['_source']}",
                        file=sys.stderr,
                    )
                    continue
                body = block.get("body", "")
                result[f".agents/skills/{skill_id}/references/{ref_id}.md"] = body
            else:
                print(
                    f"WARNING: unknown block type {block_type!r} in {block['_source']}",
                    file=sys.stderr,
                )
    return result


def main() -> int:
    rst_glob = str(CONTRIBUTING_DOCS_ROOT / "**" / "*.rst")
    content_map = generate_all_content(rst_glob)
    if not content_map:
        print("No SKILL blocks found.", file=sys.stderr)
        return 1
    written = 0
    for rel_path, content in content_map.items():
        out = AIRFLOW_ROOT / rel_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content)
        print(f"  wrote {rel_path}")
        written += 1
    print(f"Done. {written} file(s) written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
