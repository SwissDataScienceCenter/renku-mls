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

import configparser
import datetime
import re
import uuid
from functools import partial
from pathlib import Path

import attr

from renku.core.utils.doi import is_doi

from renku.core.models import jsonld

NoneType = type(None)

ML_SCHEMA = {'mls': 'http://www.w3.org/ns/mls#'}
XML_SCHEMA = {'xsd': 'http://www.w3.org/2001/XMLSchema#'}

_path_attr = partial(
    jsonld.ib,
    converter=Path,
)

def _convert_implementation(obj):
    """Convert implementation object."""
    if isinstance(obj, dict):
        return Implementation.from_jsonld(obj)


def _convert_algorithm(obj):
    """Convert implementation object."""
    if isinstance(obj, dict):
        return Algorithm.from_jsonld(obj)


def _convert_input(value):
    """Convert input object."""
    input_values = []
    for v in value:
        if 'value' in v:
            input_values.append(HyperParameterSetting.from_jsonld(v))
    return input_values


def _convert_output(value):
    """Convert output object."""
    output_values = []
    for v in value:
        if 'value' in v:
            output_values.append(ModelEvaluation.from_jsonld(v))
    return output_values


def _convert_parameter_value(obj):
    """Convert parameter value."""
    if isinstance(obj, dict):
        # TODO: should be interpreted type value
        return obj["@value"]


def _convert_parameters(value):
    """Convert hyperparameter object."""
    return [HyperParameter.from_jsonld(v) for v in value]


@jsonld.s(
    type='mls:EvaluationMeasure',
    slots=True,
    context=ML_SCHEMA
)
class EvaluationMeasure:
    _id = jsonld.ib(default=None, context='@id', kw_only=True)

@jsonld.s(
    type='mls:ModelEvaluation',
    slots=True,
    context={
        **ML_SCHEMA,
        **XML_SCHEMA,
        'specified_by': 'mls:specifiedBy'
    }
)
class ModelEvaluation:
    _id = jsonld.ib(default=None, context='@id', kw_only=True)
    value = jsonld.ib(
        default=None,
        context='mls:hasValue',
        kw_only=True
    )
    specified_by = jsonld.ib(default=None, context='mls:specifiedBy', kw_only=True)


@jsonld.s(
    type='mls:HyperParameter',
    slots=True,
    context=ML_SCHEMA
)
class HyperParameter:
    _id = jsonld.ib(default=None, context='@id', kw_only=True)


@jsonld.s(
    type='mls:Algorithm',
    slots=True,
    context=ML_SCHEMA
)
class Algorithm:
    _id = jsonld.ib(default=None, context='@id', kw_only=True)


@jsonld.s(
    type='mls:HyperParameterSetting',
    slots=True,
    context={
        **ML_SCHEMA,
        **XML_SCHEMA,
        'specified_by': 'mls:specifiedBy'
    }
)
class HyperParameterSetting:
    value = jsonld.ib(
        default=None,
        context='mls:hasValue',
        kw_only=True
    )
    specified_by = jsonld.ib(default=None, context='mls:specifiedBy', kw_only=True)


@jsonld.s(
    type='mls:Implementation',
    context={
        **ML_SCHEMA,
        'dcterms': 'http://purl.org/dc/terms/'
    }
)
class Implementation:
    """Repesent an ML Schema defined Model."""

    EDITABLE_FIELDS = []

    _id = jsonld.ib(default=None, context='@id', kw_only=True)

    identifier = jsonld.ib(
        default=attr.Factory(uuid.uuid4),
        context='schema:identifier',
        kw_only=True,
        converter=str
    )

    name = jsonld.ib(
        default=None, type=str, context='dcterms:title', kw_only=True
    )

    parameters = jsonld.container.list(
        HyperParameter,
        default=None,
        converter=_convert_parameters,
        context='mls:hasHyperParameter',
        kw_only=True
    )

    implements = jsonld.ib(
        default=None,
        context='mls:implements',
        type=Algorithm,
        converter=_convert_algorithm,
        kw_only=True)

    version = jsonld.ib(default=None, context='dcterms:hasVersion', kw_only=True)

    @property
    def display_name(self):
        """Get dataset display name."""
        name = re.sub(' +', ' ', self.name.lower()[:24])

        def to_unix(el):
            """Parse string to unix friendly name."""
            parsed_ = re.sub('[^a-zA-Z0-9]', '', re.sub(' +', ' ', el))
            parsed_ = re.sub(' .+', '.', parsed_.lower())
            return parsed_

        short_name = [to_unix(el) for el in name.split()]

        if self.version:
            version = to_unix(self.version)
            name = '{0}_{1}'.format('_'.join(short_name), version)
            return name

        return '.'.join(short_name)

    @property
    def uid(self):
        """UUID part of identifier."""
        return self.identifier.split('/')[-1]

    @property
    def short_id(self):
        """Shorter version of identifier."""
        if is_doi(self._id):
            return self._id
        return str(self.uid)[:8]

    @property
    def editable(self):
        """Subset of attributes which user can edit."""
        obj = self.asjsonld()
        data = {field_: obj.pop(field_) for field_ in self.EDITABLE_FIELDS}
        return data


@jsonld.s(
    type='mls:Run',
    context={
        **ML_SCHEMA,
        'dcterms': 'http://purl.org/dc/terms/',
    },
)
class Run(object):
    identifier = jsonld.ib(
        default=attr.Factory(uuid.uuid4),
        context='schema:identifier',
        kw_only=True,
        converter=str
    )

    executes = jsonld.ib(
        default=None,
        type=Implementation,
        converter=_convert_implementation,
        context='mls:executes',
        kw_only=True
    )

    input_values = jsonld.container.list(
        HyperParameterSetting,
        converter=_convert_input,
        context='mls:hasInput',
        kw_only=True
    )

    output_values = jsonld.container.list(
        ModelEvaluation,
        converter=_convert_output,
        context='mls:hasOutput',
        kw_only=True
    )

    realizes = jsonld.ib(
        default=None,
        context='mls:implements',
        type=Algorithm,
        converter=_convert_algorithm,
        kw_only=True)

    version = jsonld.ib(default=None, context='dcterms:hasVersion', kw_only=True)

    name = jsonld.ib(
        default=None, type=str, context='dcterms:title', kw_only=True
    )

