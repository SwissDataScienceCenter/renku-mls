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

from setuptools import find_packages, setup

install_requires = [
    "deepdiff",
    "mlschema-converters",
    "prettytable",
    "pyld",
    "rdflib",
    "renku>=1.2.0",
]
packages = find_packages()
version_file = open("VERSION")

setup(
    name="renku-mls",
    description="Renku MLS plugin",
    keywords="Renku MLS",
    license="Apache License 2.0",
    author="Renku team @ SDSC",
    author_email="renku@datascience.ch",
    install_requires=install_requires,
    packages=packages,
    entry_points={
        "renku": ["mls = renkumls.plugin"],
        "renku.cli_plugins": ["mls = renkumls.plugin:mls"],
    },
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    version=version_file.read().strip(),
    classifiers=[
        "Environment :: Plugins",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
    ],
)
