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
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from ci.prek import generate_skills


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"))


def _write_skill_definitions(defs_path: Path) -> None:
    _write(
        defs_path,
        """
        .. SKILL-DEF:: airflow-run-pytest
           description: >
             Run pytest for Airflow tests.
           compatibility: Requires uv installed on host.
        """,
    )


def test_generate_all_content_assembles_skill_and_reference(tmp_path):
    defs_path = tmp_path / ".agents" / "skill_definitions.rst"
    _write_skill_definitions(defs_path)

    _write(
        tmp_path / "z_tests.rst",
        """
        .. SKILL-FRAGMENT-START:: airflow-run-pytest
        Fragment from z file.
        .. SKILL-FRAGMENT-END
        """,
    )
    _write(
        tmp_path / "a_tests.rst",
        """
        .. SKILL-FRAGMENT-START:: airflow-run-pytest
        Fragment from a file.
        .. SKILL-FRAGMENT-END

        .. SKILL-FRAGMENT-START:: airflow-run-pytest ref=breeze-fallback
        Reference details.
        .. SKILL-FRAGMENT-END
        """,
    )

    generated = generate_skills.generate_all_content(
        str(tmp_path / "**" / "*.rst"),
        definitions_file=defs_path,
    )

    skill_path = ".agents/skills/airflow-run-pytest/SKILL.md"
    assert skill_path in generated

    skill_content = generated[skill_path]
    assert "name: airflow-run-pytest" in skill_content
    assert "Run pytest for Airflow tests." in skill_content
    assert skill_content.index("Fragment from a file.") < skill_content.index("Fragment from z file.")

    ref_path = ".agents/skills/airflow-run-pytest/references/breeze-fallback.md"
    assert generated[ref_path].strip() == "Reference details."


def test_generate_all_content_rejects_missing_fragment_end_tag(tmp_path):
    defs_path = tmp_path / ".agents" / "skill_definitions.rst"
    _write_skill_definitions(defs_path)
    _write(
        tmp_path / "missing_end.rst",
        """
        .. SKILL-FRAGMENT-START:: airflow-run-pytest
        Missing end marker here.
        """,
    )

    with pytest.raises(ValueError, match="Missing SKILL-FRAGMENT-END"):
        generate_skills.generate_all_content(str(tmp_path / "**" / "*.rst"), definitions_file=defs_path)


def test_generate_all_content_rejects_unknown_skill_fragment(tmp_path):
    defs_path = tmp_path / ".agents" / "skill_definitions.rst"
    _write_skill_definitions(defs_path)
    _write(
        tmp_path / "unknown_skill.rst",
        """
        .. SKILL-FRAGMENT-START:: airflow-run-prek
        Unknown skill id.
        .. SKILL-FRAGMENT-END
        """,
    )

    with pytest.raises(ValueError, match="unknown skill"):
        generate_skills.generate_all_content(str(tmp_path / "**" / "*.rst"), definitions_file=defs_path)


def test_generate_all_content_rejects_unsupported_fragment_argument(tmp_path):
    defs_path = tmp_path / ".agents" / "skill_definitions.rst"
    _write_skill_definitions(defs_path)
    _write(
        tmp_path / "unsupported_arg.rst",
        """
        .. SKILL-FRAGMENT-START:: airflow-run-pytest order=1
        Order is no longer supported.
        .. SKILL-FRAGMENT-END
        """,
    )

    with pytest.raises(ValueError, match="Unsupported SKILL-FRAGMENT argument"):
        generate_skills.generate_all_content(str(tmp_path / "**" / "*.rst"), definitions_file=defs_path)


def test_generate_all_content_requires_body_fragments_for_each_skill(tmp_path):
    defs_path = tmp_path / ".agents" / "skill_definitions.rst"
    _write_skill_definitions(defs_path)
    _write(
        tmp_path / "only_ref.rst",
        """
        .. SKILL-FRAGMENT-START:: airflow-run-pytest ref=breeze-fallback
        Ref only.
        .. SKILL-FRAGMENT-END
        """,
    )

    with pytest.raises(ValueError, match="No body fragments found for skill 'airflow-run-pytest'"):
        generate_skills.generate_all_content(str(tmp_path / "**" / "*.rst"), definitions_file=defs_path)


def test_generate_all_content_is_deterministic_when_glob_is_unsorted(tmp_path, monkeypatch):
    defs_path = tmp_path / ".agents" / "skill_definitions.rst"
    _write_skill_definitions(defs_path)

    file_a = tmp_path / "a_tests.rst"
    file_b = tmp_path / "b_tests.rst"
    _write(
        file_a,
        """
        .. SKILL-FRAGMENT-START:: airflow-run-pytest
        Fragment A.
        .. SKILL-FRAGMENT-END
        """,
    )
    _write(
        file_b,
        """
        .. SKILL-FRAGMENT-START:: airflow-run-pytest
        Fragment B.
        .. SKILL-FRAGMENT-END
        """,
    )

    monkeypatch.setattr(
        generate_skills,
        "glob",
        lambda _pattern, recursive=True: [str(file_b), str(file_a), str(defs_path)],
    )

    generated = generate_skills.generate_all_content("ignored", definitions_file=defs_path)
    body = generated[".agents/skills/airflow-run-pytest/SKILL.md"]
    assert body.index("Fragment A.") < body.index("Fragment B.")


def test_airflow_run_pytest_skill_uses_source_document_commands():
    pattern = str(generate_skills.CONTRIBUTING_DOCS_ROOT / "**" / "*.rst")

    generated_once = generate_skills.generate_all_content(
        pattern,
        definitions_file=generate_skills.SKILL_DEFINITIONS_FILE,
    )
    generated_twice = generate_skills.generate_all_content(
        pattern,
        definitions_file=generate_skills.SKILL_DEFINITIONS_FILE,
    )

    assert generated_once == generated_twice

    skill_path = ".agents/skills/airflow-run-pytest/SKILL.md"
    skill_content = generated_once[skill_path]
    assert "uv run pytest" in skill_content
    assert "breeze testing core-tests --db-reset" in skill_content
    assert "breeze testing providers-tests --db-reset" in skill_content
    assert "<PROJECT>" not in skill_content
    assert "breeze run pytest" not in skill_content

    non_db_shell_ref = ".agents/skills/airflow-run-pytest/references/non-db-shell.md"
    db_shell_ref = ".agents/skills/airflow-run-pytest/references/db-shell.md"
    assert "breeze shell --backend none --python 3.10" in generated_once[non_db_shell_ref]
    assert "breeze shell --backend postgres --python 3.10" in generated_once[db_shell_ref]
