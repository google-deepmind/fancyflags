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
from typing import Any, Callable, List, Mapping, Optional, Sequence, Tuple

from fancyflags import _definitions
# internal imports: usage_logging

# TODO(b/178129474): Improve support for typing.Sequence subtypes.
_TYPE_MAP = {
    List[bool]: _definitions.Sequence,
    List[float]: _definitions.Sequence,
    List[int]: _definitions.Sequence,
    List[str]: _definitions.Sequence,
    Sequence[bool]: _definitions.Sequence,
    Sequence[float]: _definitions.Sequence,
    Sequence[int]: _definitions.Sequence,
    Sequence[str]: _definitions.Sequence,
    Tuple[bool]: _definitions.Sequence,
    Tuple[float]: _definitions.Sequence,
    Tuple[int]: _definitions.Sequence,
    Tuple[str]: _definitions.Sequence,
    bool: _definitions.Boolean,
    float: _definitions.Float,
    int: _definitions.Integer,
    str: _definitions.String,
}

# Add optional versions of all types as well
_TYPE_MAP.update({Optional[tp]: parser for tp, parser in _TYPE_MAP.items()})

_MISSING_TYPE_ANNOTATION = "Missing type annotation for argument {name!r}"
_UNSUPPORTED_ARGUMENT_TYPE = (
    "No matching flag type for argument {{name!r}} with type annotation: "
    "{{annotation}}\n"
    "Supported types:\n{}".format("\n".join(str(t) for t in _TYPE_MAP)))
_MISSING_DEFAULT_VALUE = "Missing default value for argument {name!r}"


def auto(callable_fn: Callable[..., Any]) -> Mapping[str, _definitions.Item]:
  """Automatically builds fancyflag definitions from a callable's signature.

  Example usage:
  ```python
  # Function
  ff.DEFINE_dict('my_function_settings', **ff.auto(my_module.my_function))

  # Class constructor
  ff.DEFINE_dict('my_class_settings', **ff.auto(my_module.MyClass))
  ```

  Args:
    callable_fn: Generates flag definitions from this callable's signature. All
      arguments must have type annotations and default values. The following
      argument types are supported:

        * `bool`, `float`, `int`, or `str` scalars
        * Homogeneous sequences of these types
        * Optional scalars or sequences of these types

  Returns:
    Mapping from parameter names to fancyflags `Item`s, to be splatted into
    `ff.DEFINE_dict`.

  Raises:
    ValueError: If any of the arguments to `callable_fn` lacks a default value.
    TypeError: If any of the arguments to `callable_fn` lacks a type annotation.
    TypeError: If any of the arguments to `callable_fn` has an unsupported type.
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
    if param.annotation is inspect.Signature.empty:
      raise TypeError(_MISSING_TYPE_ANNOTATION.format(name=param.name))
    try:
      ff_type = _TYPE_MAP[param.annotation]
    except KeyError:
      raise TypeError(_UNSUPPORTED_ARGUMENT_TYPE.format(
          name=param.name, annotation=param.annotation))
    if param.default is inspect.Signature.empty:
      raise ValueError(_MISSING_DEFAULT_VALUE.format(name=param.name))

    help_string = param.name  # TODO(b/177673667): Parse this from docstring.
    ff_dict[param.name] = ff_type(param.default, help_string)

  return ff_dict
