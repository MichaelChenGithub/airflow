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
Generate agent skill files under ``.agents/skills/`` from ``contributing-docs``.

``SKILL-DEF`` blocks live in ``contributing-docs/.agents/skill_definitions.rst``.
They provide stable skill metadata (description + optional compatibility).

``SKILL-FRAGMENT`` blocks live in ``contributing-docs/**/*.rst`` and provide the
body fragments that are assembled in deterministic order.

Definition format::

    .. SKILL-DEF:: airflow-run-pytest
       description: >
         Run pytest for Airflow tests.
       compatibility: Requires uv installed on host.

Fragment format::

    .. SKILL-FRAGMENT-START:: airflow-run-pytest
    .. code-block:: bash

       uv run --project <PROJECT> pytest <path> -xvs
    .. SKILL-FRAGMENT-END

Optional reference fragment::

    .. SKILL-FRAGMENT-START:: airflow-run-pytest ref=breeze-fallback
    Additional reference details.
    .. SKILL-FRAGMENT-END

Output mapping:

- ``SKILL-DEF`` + body fragments → ``.agents/skills/<id>/SKILL.md``
- reference fragments            → ``.agents/skills/<id>/references/<ref>.md``
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from glob import glob
from pathlib import Path

import yaml

AIRFLOW_ROOT = Path(__file__).parents[3].resolve()
AGENTS_SKILLS_ROOT = AIRFLOW_ROOT / ".agents" / "skills"
CONTRIBUTING_DOCS_ROOT = AIRFLOW_ROOT / "contributing-docs"
SKILL_DEFINITIONS_FILE = CONTRIBUTING_DOCS_ROOT / ".agents" / "skill_definitions.rst"

_DEFAULT_COMPATIBILITY = "Requires git, uv, and Apache Airflow Breeze"
_SKILL_ID_PATTERN = r"[a-z0-9][a-z0-9_-]*"
_REF_ID_PATTERN = r"[a-z0-9][a-z0-9-]*"

_SKILL_DEF_RE = re.compile(rf"\.\. SKILL-DEF::\s+(?P<skill_id>{_SKILL_ID_PATTERN})\s*$")
_FRAGMENT_START_RE = re.compile(
    rf"\.\. SKILL-FRAGMENT-START::\s+(?P<skill_id>{_SKILL_ID_PATTERN})(?P<args>.*)$"
)
_FRAGMENT_END_RE = re.compile(r"\.\. SKILL-FRAGMENT-END\s*$")
_REF_ID_RE = re.compile(rf"^{_REF_ID_PATTERN}$")


@dataclass(frozen=True)
class SkillDefinition:
    skill_id: str
    description: str
    compatibility: str


@dataclass(frozen=True)
class SkillFragment:
    skill_id: str
    ref_id: str | None
    content: str
    source_path: str
    start_line: int


def _dedent_rst_directive_block(lines: list[str]) -> str:
    return "\n".join(line[3:] if line.startswith("   ") else line for line in lines).strip()


def _relative_source_path(path: Path) -> str:
    try:
        return path.relative_to(AIRFLOW_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def parse_skill_definitions(definitions_path: Path) -> dict[str, SkillDefinition]:
    if not definitions_path.exists():
        raise ValueError(f"Missing SKILL definitions file: {definitions_path}")

    lines = definitions_path.read_text().splitlines()
    definitions: dict[str, SkillDefinition] = {}

    idx = 0
    while idx < len(lines):
        match = _SKILL_DEF_RE.match(lines[idx].strip())
        if not match:
            idx += 1
            continue

        skill_id = match.group("skill_id")
        if skill_id in definitions:
            raise ValueError(f"Duplicate SKILL-DEF for '{skill_id}' in {definitions_path}:{idx + 1}")

        idx += 1
        yaml_lines: list[str] = []
        while idx < len(lines):
            line = lines[idx]
            if _SKILL_DEF_RE.match(line.strip()):
                break
            if line and not line.startswith("   "):
                break
            yaml_lines.append(line)
            idx += 1

        raw_yaml = _dedent_rst_directive_block(yaml_lines)
        if not raw_yaml:
            raise ValueError(f"SKILL-DEF '{skill_id}' has no metadata in {definitions_path}")

        metadata = yaml.safe_load(raw_yaml)
        if not isinstance(metadata, dict):
            raise ValueError(f"SKILL-DEF '{skill_id}' metadata must be a mapping in {definitions_path}")

        description = str(metadata.get("description", "")).strip()
        if not description:
            raise ValueError(f"SKILL-DEF '{skill_id}' missing 'description' in {definitions_path}")

        compatibility = str(metadata.get("compatibility", _DEFAULT_COMPATIBILITY)).strip()
        definitions[skill_id] = SkillDefinition(
            skill_id=skill_id,
            description=description,
            compatibility=compatibility,
        )

    if not definitions:
        raise ValueError(f"No SKILL-DEF blocks found in {definitions_path}")

    return definitions


def _parse_fragment_args(raw_args: str, *, source_path: Path, line_number: int) -> str | None:
    args = raw_args.strip()
    if not args:
        return None

    parsed: dict[str, str] = {}
    for token in args.split():
        if "=" not in token:
            raise ValueError(
                f"Invalid SKILL-FRAGMENT argument '{token}' in {source_path}:{line_number}. "
                "Expected key=value syntax."
            )
        key, value = token.split("=", 1)
        if key in parsed:
            raise ValueError(f"Duplicate SKILL-FRAGMENT argument '{key}' in {source_path}:{line_number}")
        parsed[key] = value

    unsupported = sorted(set(parsed) - {"ref"})
    if unsupported:
        raise ValueError(
            f"Unsupported SKILL-FRAGMENT argument(s) {unsupported} in "
            f"{source_path}:{line_number}. Supported keys: ref."
        )

    ref_id = parsed.get("ref")
    if ref_id and not _REF_ID_RE.match(ref_id):
        raise ValueError(
            f"Invalid ref id '{ref_id}' in {source_path}:{line_number}. "
            "Use lowercase letters, digits, and dashes."
        )
    return ref_id


def parse_skill_fragments(rst_path: Path) -> list[SkillFragment]:
    lines = rst_path.read_text().splitlines()
    fragments: list[SkillFragment] = []
    source_path = _relative_source_path(rst_path)

    idx = 0
    while idx < len(lines):
        start_match = _FRAGMENT_START_RE.match(lines[idx].strip())
        if not start_match:
            idx += 1
            continue

        start_line = idx + 1
        skill_id = start_match.group("skill_id")
        ref_id = _parse_fragment_args(
            start_match.group("args") or "",
            source_path=rst_path,
            line_number=start_line,
        )

        idx += 1
        content_lines: list[str] = []
        found_end = False
        while idx < len(lines):
            current_line = lines[idx].strip()
            if _FRAGMENT_START_RE.match(current_line):
                raise ValueError(
                    f"Nested SKILL-FRAGMENT-START before SKILL-FRAGMENT-END in {rst_path}:{idx + 1}"
                )
            if _FRAGMENT_END_RE.match(current_line):
                found_end = True
                break
            content_lines.append(lines[idx])
            idx += 1

        if not found_end:
            raise ValueError(f"Missing SKILL-FRAGMENT-END for block in {rst_path}:{start_line}")

        content = "\n".join(content_lines).strip("\n")
        if not content.strip():
            raise ValueError(f"Empty SKILL-FRAGMENT block in {rst_path}:{start_line}")

        fragments.append(
            SkillFragment(
                skill_id=skill_id,
                ref_id=ref_id,
                content=content,
                source_path=source_path,
                start_line=start_line,
            )
        )
        idx += 1

    return fragments


def _sort_fragments(fragments: list[SkillFragment]) -> list[SkillFragment]:
    return sorted(fragments, key=lambda fragment: (fragment.source_path, fragment.start_line))


def generate_all_content(
    rst_glob: str, definitions_file: Path | str = SKILL_DEFINITIONS_FILE
) -> dict[str, str]:
    """
    Return ``{ relative_output_path: content }`` for all generated skill files.

    The order of assembled fragments is deterministic:
    1. Source file path (relative POSIX path)
    2. Fragment start line number
    """
    definitions = parse_skill_definitions(Path(definitions_file))
    definitions_file_path = Path(definitions_file).resolve()

    body_fragments: defaultdict[str, list[SkillFragment]] = defaultdict(list)
    reference_fragments: defaultdict[tuple[str, str], list[SkillFragment]] = defaultdict(list)

    rst_paths = sorted(Path(path).resolve() for path in glob(rst_glob, recursive=True))
    for rst_path in rst_paths:
        if rst_path.resolve() == definitions_file_path:
            continue
        for fragment in parse_skill_fragments(rst_path):
            if fragment.skill_id not in definitions:
                raise ValueError(
                    f"SKILL-FRAGMENT references unknown skill '{fragment.skill_id}' in "
                    f"{fragment.source_path}:{fragment.start_line}"
                )
            if fragment.ref_id:
                reference_fragments[(fragment.skill_id, fragment.ref_id)].append(fragment)
            else:
                body_fragments[fragment.skill_id].append(fragment)

    result: dict[str, str] = {}
    for skill_id in sorted(definitions):
        definition = definitions[skill_id]
        sorted_body_fragments = _sort_fragments(body_fragments.get(skill_id, []))
        if not sorted_body_fragments:
            raise ValueError(f"No body fragments found for skill '{skill_id}'")

        body = "\n\n".join(fragment.content for fragment in sorted_body_fragments)
        content = (
            f"---\n"
            f"name: {definition.skill_id}\n"
            f"description: {definition.description}\n"
            f"compatibility: {definition.compatibility}\n"
            f"---\n\n"
            f"{body}\n"
        )
        result[f".agents/skills/{skill_id}/SKILL.md"] = content

        ref_ids = sorted(ref_id for sid, ref_id in reference_fragments if sid == skill_id)
        for ref_id in ref_ids:
            sorted_ref_fragments = _sort_fragments(reference_fragments[(skill_id, ref_id)])
            result[f".agents/skills/{skill_id}/references/{ref_id}.md"] = (
                "\n\n".join(fragment.content for fragment in sorted_ref_fragments) + "\n"
            )

    return result


def main() -> int:
    rst_glob = str(CONTRIBUTING_DOCS_ROOT / "**" / "*.rst")
    try:
        content_map = generate_all_content(rst_glob, definitions_file=SKILL_DEFINITIONS_FILE)
    except (ValueError, yaml.YAMLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if not content_map:
        print("No SKILL blocks found.", file=sys.stderr)
        return 1
    written = 0
    for rel_path in sorted(content_map):
        content = content_map[rel_path]
        out = AIRFLOW_ROOT / rel_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content)
        print(f"  wrote {rel_path}")
        written += 1
    print(f"Done. {written} file(s) written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
