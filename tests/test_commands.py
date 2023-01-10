# -*- coding: utf-8 -*-
#
# Copyright 2020-2023 - Swiss Data Science Center
# A partnership between École Polytechnique Fédérale de Lausanne (EPFL) and
# Eidgenössische Technische Hochschule Zürich (ETHZ).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Renku MLS leaderboard tests."""

from click.testing import CliRunner

from renkumls.plugin import leaderboard, params


def test_leaderboard(project_with_script, run_shell):
    """Test that a leaderboard can be gotten for several runs."""
    script_file, write_script = project_with_script

    write_script(42)

    output = run_shell(f"renku run --no-output -- python {str(script_file)}")
    assert b"" == output[0]
    assert output[1] is None

    write_script(123)

    output = run_shell(f"renku run --no-output -- python {str(script_file)}")
    assert b"" == output[0]
    assert output[1] is None

    result = CliRunner().invoke(leaderboard, [], "\n", catch_exceptions=False)
    assert result.exit_code == 0
    assert len(result.output.splitlines()) == 6
    assert result.output.count("xgboost.sklearn.XGBClassifier") == 2
    assert result.output.count("script.py") == 2


def test_parameters(project_with_script, run_shell):
    """Test that a model parameters can be shown for several runs."""
    script_file, write_script = project_with_script

    write_script(42)

    output = run_shell(f"renku run --no-output -- python {str(script_file)}")
    assert b"" == output[0]
    assert output[1] is None

    write_script(99)

    output = run_shell(f"renku run --no-output -- python {str(script_file)}")
    assert b"" == output[0]
    assert output[1] is None

    result = CliRunner().invoke(params, [], "\n", catch_exceptions=False)
    assert result.exit_code == 0
    assert len(result.output.splitlines()) == 6
    assert "sampling_method" in result.output
    assert '"n_estimators": "100"' in result.output
    assert "gamma" in result.output
