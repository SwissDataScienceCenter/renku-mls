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
import inspect

from click.testing import CliRunner
from dulwich import porcelain
from dulwich.repo import Repo

from renkumls.plugin import leaderboard, params


def test_leaderboard(renku_project, run_shell):
    """Test that a leaderboard can be gotten for several runs."""
    repo = Repo(renku_project)
    script = """
        from xgboost import XGBClassifier
        from sklearn.metrics import accuracy_score
        from sklearn.datasets import load_breast_cancer
        from sklearn.model_selection import train_test_split
        from mlsconverters import export

        cancer = load_breast_cancer()
        X_train, X_test, y_train, y_test = train_test_split(cancer.data, cancer.target, random_state={state})

        X_train = cancer.data
        y_train = cancer.target

        # model creation
        model = XGBClassifier()
        model.fit(X_train, y_train)

        # model eval
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_test)
        export(model, evaluation_measure=(accuracy_score, acc))
    """
    script_file = renku_project / "script.py"
    script_file.write_text(inspect.cleandoc(script.format(state=42)))
    porcelain.add(repo, script_file)
    porcelain.commit(repo, "first commit")

    output = run_shell(f"renku run --no-output -- python {str(script_file)}")
    assert b"" == output[0]
    assert output[1] is None

    script_file.write_text(inspect.cleandoc(script.format(state=99)))
    porcelain.add(repo, script_file)
    porcelain.commit(repo, "second commit")

    output = run_shell(f"renku run --no-output -- python {str(script_file)}")
    assert b"" == output[0]
    assert output[1] is None

    result = CliRunner().invoke(leaderboard, [], "\n", catch_exceptions=False)
    assert result.exit_code == 0
    assert len(result.output.splitlines()) == 6
    assert result.output.count("xgboost.sklearn.XGBClassifier") == 2
    assert result.output.count("script.py") == 2


def test_parameters(renku_project, run_shell):
    """Test that a leaderboard can be gotten for several runs."""
    repo = Repo(renku_project)
    script = """
        from xgboost import XGBClassifier
        from sklearn.metrics import accuracy_score
        from sklearn.datasets import load_breast_cancer
        from sklearn.model_selection import train_test_split
        from mlsconverters import export

        cancer = load_breast_cancer()
        X_train, X_test, y_train, y_test = train_test_split(cancer.data, cancer.target, random_state={state})

        X_train = cancer.data
        y_train = cancer.target

        # model creation
        model = XGBClassifier()
        model.fit(X_train, y_train)

        # model eval
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_test)
        export(model, evaluation_measure=(accuracy_score, acc))
    """
    script_file = renku_project / "script.py"
    script_file.write_text(inspect.cleandoc(script.format(state=42)))
    porcelain.add(repo, script_file)
    porcelain.commit(repo, "first commit")

    output = run_shell(f"renku run --no-output -- python {str(script_file)}")
    assert b"" == output[0]
    assert output[1] is None

    script_file.write_text(inspect.cleandoc(script.format(state=99)))
    porcelain.add(repo, script_file)
    porcelain.commit(repo, "second commit")

    output = run_shell(f"renku run --no-output -- python {str(script_file)}")
    assert b"" == output[0]
    assert output[1] is None

    result = CliRunner().invoke(params, [], "\n", catch_exceptions=False)
    assert result.exit_code == 0
    assert len(result.output.splitlines()) == 6
    assert "sampling_method" in result.output
    assert '"n_estimators": "100"' in result.output
    assert "gamma" in result.output
