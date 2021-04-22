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
import re
import json
import click
import rdflib
from copy import deepcopy
from pathlib import Path

from renku.core.models.cwl.annotation import Annotation
from renku.core.incubation.command import Command
from renku.core.plugins import hookimpl
from renku.core.models.provenance.provenance_graph import ProvenanceGraph
from renku.core.errors import RenkuException

from prettytable import PrettyTable
from deepdiff import DeepDiff

from mlsconverters.models import Run
from mlsconverters.io import MLS_DIR, COMMON_DIR


class MLS(object):
    def __init__(self, run):
        self.run = run

    @property
    def renku_mls_path(self):
        """Return a ``Path`` instance of Renku MLS metadata folder."""
        return Path(self.run.client.renku_home).joinpath(MLS_DIR).joinpath(COMMON_DIR)

    def load_model(self, path):
        """Load MLS reference file."""
        if path and path.exists():
            return json.load(path.open())
        return {}


@hookimpl
def process_run_annotations(run):
    """``process_run_annotations`` hook implementation."""
    mls = MLS(run)

    annotations = []
    for p in mls.renku_mls_path.iterdir():
        mls_annotation = mls.load_model(p)
        model_id = mls_annotation["@id"]
        annotation_id = "{activity}/annotations/mls/{id}".format(
            activity=run._id, id=model_id
        )
        p.unlink()
        annotations.append(
            Annotation(id=annotation_id, source="MLS plugin", body=mls_annotation)
        )
    return annotations


def _run_id(activity_id):
    return str(activity_id).split("/")[-1]


def _load_provenance_graph(client):
    if not client.provenance_graph_path.exists():
        raise RenkuException(
            """Provenance graph has not been generated!
Please run 'renku graph generate' to create the project's provenance graph
"""
        )
    return ProvenanceGraph.from_json(client.provenance_graph_path)


def _graph(revision, paths):
    # FIXME: use (revision, paths) filter
    cmd_result = Command().command(_load_provenance_graph).build().execute()

    provenance_graph = cmd_result.output
    provenance_graph.custom_bindings = {
        "mls": "http://www.w3.org/ns/mls#",
        "oa": "http://www.w3.org/ns/oa#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
    }
    return provenance_graph


def _create_leaderboard(data, metric, format=None):
    leaderboard = PrettyTable()
    leaderboard.field_names = ["Run ID", "Model", "Inputs", metric]
    leaderboard.align["Model"] = "l"
    leaderboard.align["Inputs"] = "l"
    leaderboard.align[metric] = "r"
    for commit, v in data.items():
        if metric in v:
            v["inputs"].sort()
            leaderboard.add_row([commit, v["model"], v["inputs"], v[metric]])
    leaderboard.sortby = metric
    leaderboard.reversesort = True
    return leaderboard


@click.group()
def mls():
    pass


@mls.command()
@click.option(
    "--revision",
    default="HEAD",
    help="The git revision to generate the log for, default: HEAD",
)
@click.option("--format", default="ascii", help="Choose an output format.")
@click.option("--metric", default="accuracy", help="Choose metric for the leaderboard")
@click.argument("paths", type=click.Path(exists=False), nargs=-1)
def leaderboard(revision, format, metric, paths):
    """Leaderboard based on evaluation metrics of machine learning models"""
    graph = _graph(revision, paths)
    leaderboard = dict()
    for r in graph.query(
        """SELECT DISTINCT ?type ?value ?run ?runId ?dsPath where {{
        ?em a mls:ModelEvaluation ;
        mls:hasValue ?value ;
        mls:specifiedBy ?type ;
        ^mls:hasOutput/mls:implements/rdfs:label ?run ;
        ^mls:hasOutput/^oa:hasBody/oa:hasTarget ?runId ;
        ^mls:hasOutput/^oa:hasBody/oa:hasTarget/prov:qualifiedUsage/prov:entity/prov:atLocation ?dsPath
        }}"""
    ):
        run_id = _run_id(r.runId)
        metric_type = r.type.split("#")[1]
        if run_id in leaderboard:
            leaderboard[run_id]["inputs"].append(r.dsPath.__str__())
            continue
        leaderboard[run_id] = {
            metric_type: r.value.value,
            "model": r.run,
            "inputs": [r.dsPath.__str__()],
        }
    if len(paths):
        filtered_board = dict()
        for path in paths:
            filtered_board.update(
                dict(filter(lambda x: path in x[1]["inputs"], leaderboard.items()))
            )
        print(_create_leaderboard(filtered_board, metric))
    else:
        print(_create_leaderboard(leaderboard, metric))


@mls.command()
@click.option(
    "--revision",
    default="HEAD",
    help="The git revision to generate the log for, default: HEAD",
)
@click.option("--format", default="ascii", help="Choose an output format.")
@click.option(
    "--diff", nargs=2, help="Print the difference between two model revisions"
)
@click.argument("paths", type=click.Path(exists=False), nargs=-1)
def params(revision, format, paths, diff):
    """List the hyper-parameter settings of machine learning models"""

    def _param_value(rdf_iteral):
        if not type(rdf_iteral) != rdflib.term.Literal:
            return rdf_iteral
        if rdf_iteral.isnumeric():
            return rdf_iteral.__str__()
        else:
            return rdf_iteral.toPython()

    graph = _graph(revision, paths)
    model_params = dict()
    for r in graph.query(
        """SELECT ?runId ?algo ?hp ?value where {{
        ?run a mls:Run ;
        mls:hasInput ?in .
        ?in a mls:HyperParameterSetting .
        ?in mls:specifiedBy/rdfs:label ?hp .
        ?in mls:hasValue ?value .
        ?run mls:implements/rdfs:label ?algo ;
        ^oa:hasBody/oa:hasTarget ?runId
        }}"""
    ):
        run_id = _run_id(r.runId)
        if run_id in model_params:
            model_params[run_id]["hp"][str(r.hp)] = _param_value(r.value)
        else:
            model_params[run_id] = dict(
                {"algorithm": str(r.algo), "hp": {str(r.hp): _param_value(r.value)}}
            )

    if len(diff) > 0:
        for r in diff:
            if r not in model_params:
                print("Unknown revision provided for diff parameter: {}".format(r))
                return
        if model_params[diff[0]]["algorithm"] != model_params[diff[1]]["algorithm"]:
            print("Model:")
            print("\t- {}".format(model_params[diff[0]]["algorithm"]))
            print("\t+ {}".format(model_params[diff[1]]["algorithm"]))
        else:
            params_diff = DeepDiff(
                model_params[diff[0]], model_params[diff[1]], ignore_order=True
            )
            output = PrettyTable()
            output.field_names = ["Hyper-Parameter", "Old", "New"]
            output.align["Hyper-Parameter"] = "l"
            if "values_changed" not in params_diff:
                print(output)
                return
            for k, v in params_diff["values_changed"].items():
                parameter_name = re.search(r"\['(\w+)'\]$", k).group(1)
                output.add_row(
                    [
                        parameter_name,
                        _param_value(v["new_value"]),
                        _param_value(v["old_value"]),
                    ]
                )
            print(output)
    else:
        output = PrettyTable()
        output.field_names = ["Run ID", "Model", "Hyper-Parameters"]
        output.align["Run ID"] = "l"
        output.align["Model"] = "l"
        output.align["Hyper-Parameters"] = "l"
        for runid, v in model_params.items():
            output.add_row([runid, v["algorithm"], json.dumps(v["hp"])])
        print(output)
