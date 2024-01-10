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

import collections.abc
import datetime
import enum
import functools
import inspect
import types
import typing
from typing import Any, Callable, Collection, Iterable, Literal, Mapping, MutableMapping, Optional, Type, TypeVar, Union
import warnings

from fancyflags import _definitions


_T = TypeVar("_T")

_ITEM_BY_TYPE = {
    bool: _definitions.Boolean,
    datetime.datetime: _definitions.DateTime,
    datetime.timedelta: _definitions.TimeDelta,
    float: _definitions.Float,
    int: _definitions.Integer,
    str: _definitions.String,
}

try:
  # The origin type of `Union[x,y]` is `typing.Union`, But using PEP604 syntax
  # the origin type of `x | y` is `types.UnionType`. Accept either when defined.
  _UNION_TYPES = frozenset({Union, types.UnionType})
except AttributeError:
  _UNION_TYPES = frozenset({Union})


_MISSING_TYPE_ANNOTATION = "Missing type annotation for argument {name!r}"
_UNSUPPORTED_ARGUMENT_TYPE = (
    "No matching flag type for argument {{name!r}} with type annotation: "
    "{{annotation}}\n"
)
_MISSING_DEFAULT_VALUE = "Missing default value for argument {name!r}"
_is_enum = lambda type_: inspect.isclass(type_) and issubclass(type_, enum.Enum)


def _is_sequence(type_: Type[Any]) -> bool:
  type_ = typing.get_origin(type_) or type_
  return (
      inspect.isclass(type_)
      and issubclass(type_, collections.abc.Sequence)
      and not issubclass(type_, (str, bytes, bytearray, memoryview))
  )


def get_typed_signature(fn: Callable[..., Any]) -> inspect.Signature:
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
        )
    )
  return orig_signature.replace(parameters=new_params)


def _auto_from_value(
    field_name: str,
    field_type: Type[_T],
    field_value: Union[_T, Literal[inspect.Parameter.empty]],
) -> Optional[_definitions.Item]:
  """Creates an Item for a single value."""

  # Resolve Optional[T] and T | None to T
  if typing.get_origin(field_type) in _UNION_TYPES:
    union_args = set(typing.get_args(field_type)) - {type(None)}
    if len(union_args) > 1:
      raise TypeError(
          _UNSUPPORTED_ARGUMENT_TYPE.format(
              name=field_name, annotation=field_type
          )
      )
    field_type = union_args.pop()

  # Look up the corresponding Item to create.
  if _is_enum(field_type):
    item_constructor = functools.partial(
        _definitions.EnumClass, enum_class=field_type
    )
  elif _is_sequence(field_type):
    args = typing.get_args(field_type)
    # TODO(b/178129474): Improve handling of args to ensure that parsed
    # sequences have the correct type.
    if args[0] not in _ITEM_BY_TYPE:
      raise TypeError(
          _UNSUPPORTED_ARGUMENT_TYPE.format(
              name=field_name, annotation=field_type
          )
      )
    item_constructor = _definitions.Sequence
  else:
    try:
      item_constructor = _ITEM_BY_TYPE[field_type]
    except KeyError as e:
      raise TypeError(
          _UNSUPPORTED_ARGUMENT_TYPE.format(
              name=field_name, annotation=field_type
          )
      ) from e

  # If there is no default argument for this parameter, we set the
  # corresponding `Flag` as `required`.
  if field_value is inspect.Parameter.empty:
    default = None
    required = True
  else:
    default = field_value
    required = False

  return item_constructor(
      default,
      help_string=field_name,
      required=required,
  )


def auto(
    callable_fn: Callable[..., Any],
    *,
    strict: bool = True,
    skip_params: Collection[str] = (),
) -> Mapping[str, _definitions.Item]:
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
      argument types are supported:  * `bool`, `float`, `int`, or `str` scalars
      * Homogeneous sequences of these types * Optional scalars or sequences of
      these types
    strict: A bool, whether invalid input types and defaults should trigger an
      error (the default) or be silently ignored. Setting strict=False might
      silence real errors, but will allow decorated functions to contain
      non-default values, or values with defaults that can not be easily turned
      into a flag or overriden on the CLI.
    skip_params: Optional parameter names to skip defining flags for.

  Returns:
    Mapping from parameter names to fancyflags `Item`s, to be splatted into
    `ff.DEFINE_dict`.

  Raises:
    ValueError: If any of the arguments to `callable_fn` lacks a default value.
    TypeError: If any of the arguments to `callable_fn` lacks a type annotation.
    TypeError: If any of the arguments to `callable_fn` has an unsupported type.
    TypeError: If `callable_fn` is not callable.
  """
  if not callable(callable_fn):
    raise TypeError(f"Not a callable: {callable_fn}.")

  # Work around issue with metaclass-wrapped classes, such as Sonnet v2 modules.
  if isinstance(callable_fn, type):
    signature = get_typed_signature(callable_fn.__init__)
    # Remove `self` from start of __init__ signature.
    unused_self, *parameters = signature.parameters.values()
  else:
    signature = get_typed_signature(callable_fn)
    parameters = signature.parameters.values()

  items: MutableMapping[str, _definitions.Item] = {}
  parameters: Iterable[inspect.Parameter]
  for param in parameters:
    if param.name in skip_params:
      continue
    try:
      if param.annotation is inspect.Parameter.empty:
        raise TypeError(_MISSING_TYPE_ANNOTATION.format(name=param.name))
      if item := _auto_from_value(param.name, param.annotation, param.default):
        items[param.name] = item
    except Exception as e:  # pylint:disable=broad-exception-caught
      if strict:
        raise
      warnings.warn(
          f"Caught an exception ({e}) when defining flags for "
          f"parameter {param.name} with type {param.annotation}; "
          "skipping because strict=False..."
      )
  return items
