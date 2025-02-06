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
"""Flag classes for defining dict, Item, MultiItem and Auto flags."""

import copy
import functools
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Optional, Sequence, TypeVar, Union

from absl import flags

_EMPTY = ""

_T = TypeVar("_T")
_CallableT = TypeVar("_CallableT", bound=Callable)


class DictFlag(flags.Flag):
  """Implements the shared dict mechanism. See also `ItemFlag`."""

  def __init__(self, shared_dict: MutableMapping[str, Any], *args, **kwargs):
    self._shared_dict = shared_dict
    super().__init__(*args, **kwargs)

  def _parse(self, value):
    # A `DictFlag` should not be overridable from the command line; only the
    # dotted `Item` flags should be. However, the _parse() method will still be
    # called in two situations:

    # 1. Via the base `Flag`'s constructor, which calls `_parse()` to process
    #    the default value, which will be the shared dict.
    # 2. When processing command line overrides. We don't want to allow this
    #    normally, however some libraries will serialize and deserialize all
    #    flags, e.g. to pass values between processes, so we accept a dummy
    #    empty serialized value for these cases. It's unlikely users will try to
    #    set the dict flag to an empty string from the command line.
    if value is self._shared_dict or value == _EMPTY:
      return self._shared_dict

    possible_overrides = "\n".join(
        f"  --{self.name}.{k}" for k in self._shared_dict
    )
    raise flags.IllegalFlagValueError(
        "Can't override a dict flag directly. Did you mean to override one of:"
        f"\n{possible_overrides}"
    )

  def serialize(self):
    # When serializing flags, we return a sentinel value that the `DictFlag`
    # will ignore when parsing. The value of this flag is determined by the
    # corresponding `Item` flags for serialization and deserialization.
    return _EMPTY

  def flag_type(self):
    return "dict"


class ItemFlag(flags.Flag[_T]):
  """Updates a shared dict whenever its own value changes.

  See also the `DictFlag` and `ff.Item` classes for usage.
  """

  def __init__(
      self,
      shared_dict: MutableMapping[str, Any],
      namespace: Sequence[str],
      parser: flags.ArgumentParser[_T],
      serializer: Optional[flags.ArgumentSerializer[_T]],
      *args,
      **kwargs
  ):
    self._shared_dict = shared_dict
    self._namespace = namespace
    super().__init__(
        *args,
        parser=parser,
        serializer=serializer,
        # absl treats boolean flags as a special case in order to support the
        # alternative `--foo`/`--nofoo` syntax.
        boolean=isinstance(parser, flags.BooleanParser),
        **kwargs
    )

  @property
  def value(self) -> Optional[_T]:
    return self._value

  @value.setter
  def value(self, value: Optional[_T]):
    self._value = value
    self._update_shared_dict()

  def parse(self, argument: Union[Optional[_T], str]):
    super().parse(argument)
    self._update_shared_dict()

  def _update_shared_dict(self):
    d = self._shared_dict
    for name in self._namespace[:-1]:
      assert isinstance(d[name], MutableMapping)
      d = d[name]
    d[self._namespace[-1]] = self._value


class MultiItemFlag(flags.MultiFlag[_T]):
  """Updates a shared dict whenever its own value changes.

  Used for flags that can appear multiple times on the command line.
  See also the `DictFlag` and `ff.Item` classes for usage.
  """

  def __init__(
      self,
      shared_dict: MutableMapping[str, Any],
      namespace: Sequence[str],
      parser: flags.ArgumentParser[Sequence[_T]],
      serializer: Optional[flags.ArgumentSerializer[Sequence[_T]]],
      *args,
      **kwargs
  ):
    self._shared_dict = shared_dict
    self._namespace = namespace
    super().__init__(parser, serializer, *args, **kwargs)

  @property
  def value(self) -> Optional[Sequence[_T]]:
    return self._value

  @value.setter
  def value(self, value: Optional[Sequence[_T]]):
    self._value = value
    self._update_shared_dict()

  def parse(self, arguments: Union[str, _T, Iterable[_T]]):
    super().parse(arguments)
    self._update_shared_dict()

  def _update_shared_dict(self):
    d = self._shared_dict
    for name in self._namespace[:-1]:
      assert isinstance(d[name], MutableMapping)
      d = d[name]
    d[self._namespace[-1]] = self._value


class AutoFlag(flags.Flag[_CallableT]):
  """Implements the shared dict mechanism."""

  def __init__(
      self, fn: _CallableT, fn_kwargs: Mapping[str, Any], *args, **kwargs
  ):
    self._fn = fn
    self._fn_kwargs = fn_kwargs
    super().__init__(*args, **kwargs)

  @property
  def value(self) -> _CallableT:
    kwargs = copy.deepcopy(self._fn_kwargs)
    return functools.partial(self._fn, **kwargs)

  @value.setter
  def value(self, value):
    # The flags `.value` gets set as part of the `flags.FLAG` constructor to a
    # default value. However the default value should be given by the initial
    # `fn_kwargs` instead, so a) the semantics of setting the value are unclear
    # and b) we may not be able to call `self._fn` at this point in execution.
    del value

  def _parse(self, value):
    # An `AutoFlag` should not be overridable from the command line; only the
    # dotted `Item` flags should be. However, the `_parse()` method will still
    # be called in two situations:

    # 1. In the base `Flag`'s constructor, which calls `_parse()` to process the
    #    default value, which will be None (as set in `DEFINE_auto`).
    # 2. When processing command line overrides. We don't want to allow this
    #    normally, however some libraries will serialize and deserialize all
    #    flags, e.g. to pass values between processes, so we accept a dummy
    #    empty serialized value for these cases. It's unlikely users will try to
    #    set the auto flag to an empty string from the command line.
    if value is None or value == _EMPTY:
      return None
    possible_overrides = "\n".join(
        f"  --{self.name}.{k}" for k in self._fn_kwargs.keys()
    )
    raise flags.IllegalFlagValueError(
        "Can't override an auto flag directly. Did you mean to override one of "
        f"\n{possible_overrides}"
    )

  def serialize(self):
    # When serializing a `FlagHolder` container, we must return *some* value for
    # this flag. We return an empty value that the `AutoFlag` will ignore when
    # parsing. The value of this flag is instead determined by the
    # corresponding `Item` flags for serialization and deserialization.
    return _EMPTY

  def flag_type(self):
    return "auto"


class HierarchicalAutoFlag(flags.Flag):
  """A Hierarchical version of AutoFlag.

  Used to construct structures beyond nested dictionaries, for example a
  dataclass containing nested dataclasses.
  """

  def __init__(
      self,
      fn: _CallableT,
      fn_kwargs: Mapping[str, Any],
      dependent_flagholders: Mapping[str, flags.FlagHolder],
      *args,
      **kwargs,
  ):
    """Initializes a new HierarchicalAutoFlag.

    Args:
      fn: The function or constructor that will return the value.
      fn_kwargs: The arguments to pass to the function or constructor.
      dependent_flagholders: A mapping from a subset of `fn` argument names to
        `FlagHolder`s. This is used to implement the construction according to a
        topological sort, for example for nested dataclasses.
      *args: Positional arguments to pass to the base `Flag` constructor.
      **kwargs: Keyword arguments to pass to the base `Flag` constructor.
    """
    self._fn = fn
    self._fn_kwargs = fn_kwargs
    self._dependent_flagholders = dependent_flagholders
    super().__init__(*args, **kwargs)

  @property
  def value(self) -> _CallableT:
    def build_dependencies(*args, **kwargs):
      # Note that this will reconstruct the dependencies every time
      # build_dependencies is called, which matches the semantics of
      # ff.DEFINE_auto.
      dependencies = {
          k: fh.value() for k, fh in self._dependent_flagholders.items()
      }
      # The precedence is: Flag values, found dependencies, and finally
      # overrides from the callsite. Note that this can even override
      # dependencies!
      actual_kwargs = {**self._fn_kwargs, **dependencies, **kwargs}
      return self._fn(*args, **actual_kwargs)

    return build_dependencies

  @value.setter
  def value(self, value):
    # See docs in `AutoFlag` for explanations on these behaviors.
    del value

  def _parse(self, value) -> None:
    # See docs in `AutoFlag` for explanations on these behaviors.
    if value is None or value == _EMPTY:
      return None
    raise flags.IllegalFlagValueError(
        "Can't override an auto flag directly. Did you mean to override one of "
        "its `Item`s instead?"
    )

  def serialize(self) -> str:
    # See docs in fancyflags' `AutoFlag` for explanations on these behaviors.
    return _EMPTY

  def flag_type(self) -> str:
    return "hierarchical_auto"
