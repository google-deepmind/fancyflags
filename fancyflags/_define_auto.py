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
"""Automatic flags via ff.auto-compatible callables and example structures."""

import dataclasses
import typing
from typing import Any, Callable, Collection, Dict, Mapping, Optional, Protocol, Type, TypeVar, Union
import warnings

from absl import flags
from fancyflags import _auto
from fancyflags import _definitions
from fancyflags import _flags

_F = TypeVar("_F", bound=Callable)

# Add current module to disclaimed module ids.
flags.disclaim_key_flags()


def DEFINE_auto(  # pylint: disable=invalid-name
    name: str,
    fn: _F,
    help_string: Optional[str] = None,
    flag_values: flags.FlagValues = flags.FLAGS,
    *,
    strict: bool = True,
    skip_params: Collection[str] = (),
) -> flags.FlagHolder[_F]:
  """Defines a flag for an `ff.auto`-compatible constructor or callable.

  Automatically defines a set of dotted `ff.Item` flags corresponding to the
  constructor arguments and their default values.

  Overriding the value of a dotted flag will update the arguments used to invoke
  `fn`. This flag's value returns a callable `fn` with these values as bound
  arguments,

  Example usage:

  ```python
  # Defined in, e.g., datasets library.

  @dataclasses.dataclass
  class DataSettings:
    dataset_name: str = 'mnist'
    split: str = 'train'
    batch_size: int = 128

  # In main script.
  # Exposes flags: --data.dataset_name --data.split and --data.batch_size.
  DATA_SETTINGS = ff.DEFINE_auto('data', datasets.DataSettings, 'Data config')

  def main(argv):
    # del argv  # Unused.
    dataset = datasets.load(DATA_SETTINGS.value())
    # ...
  ```

  Args:
    name: The name for the top-level flag.
    fn: An `ff.auto`-compatible `Callable`.
    help_string: Optional help string for this flag. If not provided, this will
      default to '{fn's module}.{fn's name}'.
    flag_values: An optional `flags.FlagValues` instance.
    strict: Whether to skip flag definitions for arguments without type hints,
      or for arguments with unknown types.
    skip_params: Optional parameter names to skip defining flags for.

  Returns:
    A `flags.FlagHolder`.
  """
  arguments = _auto.auto(fn, strict=strict, skip_params=skip_params)
  # Define the individual flags.
  defaults = _definitions.define_flags(name, arguments, flag_values=flag_values)
  help_string = help_string or f"{fn.__module__}.{fn.__name__}"
  # Define a holder flag.
  return flags.DEFINE_flag(
      flag=_flags.AutoFlag(
          fn,
          defaults,
          name=name,
          default=None,
          parser=flags.ArgumentParser(),
          serializer=None,
          help_string=help_string,
      ),
      flag_values=flag_values,
  )


class _IsDataclass(Protocol):
  __dataclass_fields__: Dict[str, dataclasses.Field[Any]]


_D = TypeVar("_D", bound=Union[_IsDataclass, Mapping[str, Any]])


def _maybe_narrow_union_type(
    field_type: Type[Any], field_value: Any
) -> Type[Any]:
  """Attempt to narrow to type given by the field value."""
  if not _auto.is_union(field_type):
    return field_type

  if field_value is None:
    # We don't want to narrow optional types where the value is None, because
    # later we won't know the original type.

    # If None is not part of the union, this shouldn't happen at all, but
    # returning the original type is reasonable behaviour and equivalent to the
    # last branch below.
    return field_type
  elif type(field_value) in typing.get_args(field_type):
    # Here we can narrow to the type present in the union.
    return type(field_value)
  else:
    # Here the type is not present in the union. We return the original type and
    # leave decisions on how to handle the union to another layer.
    return field_type


def _should_recurse_from_value(value: Any) -> bool:
  return dataclasses.is_dataclass(value) or isinstance(value, Mapping)


def DEFINE_from_instance(  # pylint: disable=invalid-name
    name: str,
    value: _D,
    help_string: Optional[str] = None,
    flag_values: flags.FlagValues = flags.FLAGS,
    should_recurse: Callable[[Any], bool] = _should_recurse_from_value,
) -> flags.FlagHolder[Callable[..., _D]]:
  """Recursively defines flags from a mapping or dataclass instance.

  Args:
    name: The name for the top-level flag.
    value: An instance of a dataclass or a mapping. The structure will be used
      to define nested flags. The return value of the flagholder will be a
      callable that returns a structure matching the provided dataclass or
      mapping.
    help_string: Optional help string for this flag.
    flag_values: An optional `flags.FlagValues` instance.
    should_recurse: An optional custom function that takes a value and returns
      whether it should be recursively defined as a flag. By default this will
      recurse on dataclasses and mappings.

  Returns:
    A `flags.FlagHolder`.
  """
  recursed = {}

  if dataclasses.is_dataclass(value):
    names_to_types = {
        k: v
        for k, v in typing.get_type_hints(type(value).__init__).items()
        if k != "return"
    }
    names_to_values = {k: getattr(value, k) for k in names_to_types}
  elif isinstance(value, Mapping):
    names_to_values = value
    names_to_types = {k: type(v) for k, v in value.items()}
  else:
    raise TypeError(f"Not a dataclass instance or mapping: {value}.")

  for field_name, field_value in names_to_values.items():
    if should_recurse(field_value):
      component_name = f"{name}.{field_name}"
      flagholder = DEFINE_from_instance(
          component_name,
          value=field_value,
          flag_values=flag_values,
          should_recurse=should_recurse,
      )
      recursed[field_name] = flagholder

  remaining_params = {}
  unsupported_params = {}
  for field_name, field_type in names_to_types.items():
    if field_name in recursed:
      continue
    field_value = names_to_values[field_name]
    field_type = _maybe_narrow_union_type(field_type, field_value)
    try:
      # pylint:disable-next=protected-access
      item = _auto.auto_from_value(field_name, field_type, field_value)
    except Exception as e:  # pylint:disable=broad-exception-caught
      warnings.warn(
          f"Caught an exception ({e}) when defining flags for "
          f"parameter {field_name} with type {field_value}; "
          "skipping because strict=False..."
      )
      item = None
    if item is not None:
      remaining_params[field_name] = item
    else:
      # Use the field_value if the type isn't supported by ff for overriding.
      unsupported_params[field_name] = field_value

  defaults = _definitions.define_flags(
      name, remaining_params, flag_values=flag_values
  )
  defaults.update(unsupported_params)

  return flags.DEFINE_flag(
      flag=_flags.HierarchicalAutoFlag(
          fn=type(value),
          fn_kwargs=defaults,
          dependent_flagholders=recursed,
          name=name,
          default=None,
          parser=flags.ArgumentParser(),
          serializer=None,
          help_string=help_string,
      ),
      flag_values=flag_values,
  )
