# -*- coding: utf-8 -*-
#
# Copyright 2017-2023 Swiss Data Science Center (SDSC)
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
"""Pytest config."""
import importlib

INCLUDE_FIXTURES = ["tests.fixtures"]


def pytest_configure(config):
    """Run global setup before executing tests."""

    for _fixture in INCLUDE_FIXTURES:
        module = importlib.import_module(_fixture)
        globals().update(
            {n: getattr(module, n) for n in module.__all__}
            if hasattr(module, "__all__")
            else {k: v for (k, v) in module.__dict__.items() if not k.startswith("_")}
        )
