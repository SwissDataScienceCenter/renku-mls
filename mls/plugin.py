# -*- coding: utf-8 -*-
#
# Copyright 2020 - Viktor Gal
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

import os
import json
from copy import deepcopy
from pathlib import Path
from renku.core.plugins import hookimpl
from renku.core.models.cwl.annotation import Annotation

from .config import MLS_DIR
from .models import Run

class MLS(object):
    def __init__(self, run):
        self.run = run

    @property
    def renku_mls_path(self):
        """Return a ``Path`` instance of Renku MLS metadata folder."""
        return Path(self.run.client.renku_home).joinpath(MLS_DIR)

    def load_model(self, path):
        """Load MLS reference file."""
        if path and path.exists():
            model = json.load(path.open())
        return model


@hookimpl
def process_run_annotations(run):
    """``process_run_annotations`` hook implementation."""
    mls = MLS(run)

    for p in run.paths:
        if p.startswith(str(mls.renku_mls_path)):
            return [
                Annotation(
                    id='_:annotation',
                    source="MLS plugin",
                    body=mls.load_model(Path(p))
                )
            ]

    return []
