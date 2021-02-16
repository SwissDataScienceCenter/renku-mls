..
    Copyright 2017-2021 - Swiss Data Science Center (SDSC)
    A partnership between École Polytechnique Fédérale de Lausanne (EPFL) and
    Eidgenössische Technische Hochschule Zürich (ETHZ).

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

Getting Started
===============
.. _gettingstarted-reference:

Renku MLS is a renku plugin for machine learning models. Using Renku MLS
one can expose the machine learning models used in renku projects (e.g. 
hyper-parameters, evaluation metrics etc.).

Start by creating a Renku project, for details see the renku_ documentation.

.. _renku: https://renku-python.readthedocs.io/en/latest/gettingstarted.html#getting-started

In the project make sure that the machine learning models (e.g. scikit-learn, keras, xgboost etc) are exported
using mlschema-model-converters_ plugin.

.. _mlschema-model-converters: https://pypi.org/project/mlschema-converters/

.. code-block:: python 

    from xgboost import XGBClassifier
    from mlsconverters import export

    # model creation
    model = XGBClassifier()
    model.fit(X_train, y_train)

    # model eval
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    export(model, evaluation_measure=(accuracy_score, acc))

Using explicitly the `export` function the details of the supplied model are going to 
be exposed to renku's knowledge graph in JSON-LD format.

Renku MLS plugin provides couple of command line arguments for ease of quering the
knowledge graph for exposed machine learning models in a renku project.

Leaderboard
-----------
`renku mls leaderboard` provides a quick overview of the machine learning models
used in the project:

.. code-block:: console

   $ renku mls leaderboard 

The output of this command is a sorted list of models used and exposed in the project to renku.
The list is sorted by descending order of the provided evaluation measure (by default accuracy).
Moreover, it will provide information of the type of model that was used as well as the input
of those models.

Hyper-Parameters
----------------
`renku mls params` provides the hyper-parameter settings of a specific ML model in the project.
If no `run-id` is provided, hyper-paramaters of all the models in project will be listed.

.. code-block:: console

   $ renku mls params 
    
