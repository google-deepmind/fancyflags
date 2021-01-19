# Copyright 2021 DeepMind Technologies Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or  implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Automatically builds flags from a callable signature."""

import inspect
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from fancyflags import _definitions
# internal imports: usage_logging

TYPE_MAP = {
    str: _definitions.String,
    bool: _definitions.Boolean,
    int: _definitions.Integer,
    float: _definitions.Float,
    List[int]: _definitions.Sequence,
    List[float]: _definitions.Sequence,
    List[str]: _definitions.Sequence,
    Tuple[int]: _definitions.Sequence,
    Tuple[float]: _definitions.Sequence,
    Tuple[str]: _definitions.Sequence,
    Sequence[int]: _definitions.Sequence,
    Sequence[float]: _definitions.Sequence,
    Sequence[str]: _definitions.Sequence,
}

# Add optional versions of all types as well
TYPE_MAP.update({Optional[tp]: parser for tp, parser in TYPE_MAP.items()})


def auto(callable_fn: Callable) -> Dict[str, _definitions.Item]:  # pylint: disable=g-bare-generic
  """Automatically builds fancyflag definitions from a callable's signature.

  Usage like:

      ff.DEFINE_dict('my_function_settings', **ff.auto(my_module.my_function))

  Or for class constructors:

      ff.DEFINE_dict('my_class_settings', **ff.auto(my_module.MyClass))

  Args:
    callable_fn: Generates flag definitions from this callable's signature. Must
      have type annotations and defaults.

  Returns:
    Dictionary mapping each parameter name to a fancyflags `Item`, to be
    splatted into `ff.DEFINE_dict`.
  """
  # usage_logging: auto

  ff_dict = {}

  # Work around issue with metaclass-wrapped classes, such as Sonnet v2 modules.
  if isinstance(callable_fn, type):
    signature = inspect.signature(callable_fn.__init__)
    # Remove `self` from start of __init__ signature.
    parameters = list(signature.parameters.values())[1:]
  else:
    signature = inspect.signature(callable_fn)
    parameters = signature.parameters.values()

  for param in parameters:
    try:
      ff_type = TYPE_MAP[param.annotation]
    except KeyError:
      raise TypeError("Can't find fancyflags flag type for argument with "
                      "type annotation: " + str(param.annotation))

    if param.default is inspect.Signature.empty:
      raise ValueError("Arguments must have a default in order to be converted "
                       "to flags: " + param.name)

    help_string = param.name  # TODO(b/177673667): Parse this from docstring.
    ff_dict[param.name] = ff_type(param.default, help_string)

  return ff_dict
