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

import enum
import functools
import inspect
import typing
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
_is_enum = lambda type_: inspect.isclass(type_) and issubclass(type_, enum.Enum)
_is_unsupported_type = lambda type_: not (type_ in _TYPE_MAP or _is_enum(type_))


def _get_typed_signature(fn: Callable[..., Any]) -> inspect.Signature:
  """Returns the signature of a callable with type annotations resolved.

  If postponed evaluation of type annotations (PEP 563) is enabled (e.g. via
  `from __future__ import annotations` in Python >= 3.7) then we will need to
  resolve the annotations from their string forms in order to access the real
  types within the signature.
  https://www.python.org/dev/peps/pep-0563/#resolving-type-hints-at-runtime

  Args:
    fn: A callable to get the signature of.

  Returns:
    An instance of `inspect.Signature`.
  """
  type_hints = typing.get_type_hints(fn) or {}
  orig_signature = inspect.signature(fn)
  new_params = []
  for key, orig_param in orig_signature.parameters.items():
    new_params.append(
        inspect.Parameter(
            name=key,
            default=orig_param.default,
            annotation=type_hints.get(key, orig_param.annotation),
            kind=orig_param.kind,
        ))
  return orig_signature.replace(parameters=new_params)


def auto(callable_fn: Callable[..., Any],
         strict: bool = True) -> Mapping[str, _definitions.Item]:
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
    strict: A bool, whether invalid input types and defaults should trigger an
      error (the default) or be silently ignored. Setting strict=False might
      silence real errors, but will allow decorated functions to contain
      non-default values, or values with defaults that can not be easily turned
      into a flag or overriden on the CLI.

  Returns:
    Mapping from parameter names to fancyflags `Item`s, to be splatted into
    `ff.DEFINE_dict`.

  Raises:
    ValueError: If any of the arguments to `callable_fn` lacks a default value.
    TypeError: If any of the arguments to `callable_fn` lacks a type annotation.
    TypeError: If any of the arguments to `callable_fn` has an unsupported type.
    TypeError: If `callable_fn` is not callable.
  """
  # usage_logging: auto

  if not callable(callable_fn):
    raise TypeError(f"Not a callable: {callable_fn}.")

  ff_dict = {}

  # Work around issue with metaclass-wrapped classes, such as Sonnet v2 modules.
  if isinstance(callable_fn, type):
    signature = _get_typed_signature(callable_fn.__init__)
    # Remove `self` from start of __init__ signature.
    unused_self, *parameters = signature.parameters.values()
  else:
    signature = _get_typed_signature(callable_fn)
    parameters = signature.parameters.values()

  for param in parameters:
    ff_exception = None

    # Check for potential errors.
    if param.annotation is inspect.Signature.empty:
      ff_exception = TypeError(_MISSING_TYPE_ANNOTATION.format(name=param.name))
    elif param.default is inspect.Signature.empty:
      ff_exception = ValueError(_MISSING_DEFAULT_VALUE.format(name=param.name))
    elif _is_unsupported_type(param.annotation):
      ff_exception = TypeError(_UNSUPPORTED_ARGUMENT_TYPE.format(
          name=param.name, annotation=param.annotation))

    # If we saw an error, decide whether to error or skip based on strictness.
    if ff_exception and strict:
      raise ff_exception
    elif ff_exception:
      continue
    else:
      if _is_enum(param.annotation):
        ff_type = functools.partial(
            _definitions.EnumClass, enum_class=param.annotation)
      else:
        ff_type = _TYPE_MAP[param.annotation]

      # TODO(b/177673667): Parse the help string from docstring.
      ff_dict[param.name] = ff_type(param.default, help_string=param.name)

  return ff_dict
