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
"""Renku MLS test fixtures."""
import contextlib
import os
import os.path
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Sequence, Union

import pytest
from click.testing import CliRunner
from dulwich import porcelain
from renku.core.util import communication
from renku.domain_model.project_context import project_context
from renku.ui.cli.init import init


def set_argv(args: Optional[Union[Path, str, Sequence[Union[Path, str]]]]) -> None:
    """Set proper argv to be used in the commit message in tests; also, make paths shorter by using relative paths."""

    def to_relative(path):
        if not path or not isinstance(path, (str, Path)) or not os.path.abspath(path):
            return path

        return os.path.relpath(path)

    def convert_args():
        """Create proper argv for commit message."""
        if not args:
            return []
        elif isinstance(args, (str, Path)):
            return [to_relative(args)]

        return [to_relative(a) for a in args]

    sys.argv[:] = convert_args()


@contextlib.contextmanager
def chdir(path):
    """Change the current working directory."""
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


@pytest.fixture(scope="function")
def renku_project(tmp_path):
    """A renku project."""
    project = tmp_path / "project"
    project.mkdir()
    with chdir(project):
        try:
            repo = porcelain.init(project)
            config = repo.get_config()
            config.set("user", "name", "Renku Bot")
            config.set("user", "email", "renku@datascience.ch")
            config.set("pull", "rebase", "false")
            project_context.clear()
            with project_context.with_path(project):
                communication.disable()
                result = CliRunner().invoke(
                    init,
                    [".", "--template-id", "python-minimal"],
                    "\n",
                    catch_exceptions=False,
                )
                communication.enable()
                assert 0 == result.exit_code
                yield project
        finally:
            try:
                shutil.rmtree(project)
            except OSError:
                pass


@pytest.fixture()
def run_shell():
    """Create a shell cmd runner."""

    def run_(cmd, return_ps=None, sleep_for=None, work_dir=None):
        """Spawn subprocess and execute shell command.

        Args:
            cmd(str): The command to run.
            return_ps: Return process object.
            sleep_for: After executing command sleep for n seconds.
            work_dir: The directory where the command should be executed from
        Returns:
            Process object or tuple (stdout, stderr).
        """
        set_argv(args=cmd)
        ps = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=work_dir,
        )

        if return_ps:
            return ps

        output = ps.communicate()

        if sleep_for:
            time.sleep(sleep_for)

        return output

    return run_
