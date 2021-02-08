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
"""Flag classes for defining dict, Item and MultiItem flags."""

from absl import flags

_EMPTY = ""


class DictFlag(flags.Flag):
  """Implements the shared dict mechanism. See also `ItemFlag`."""

  def __init__(self, shared_dict, *args, **kwargs):
    self._shared_dict = shared_dict
    super().__init__(*args, **kwargs)

  def _parse(self, value):
    # A dict flag should not be overridable from the command line; only the
    # dotted Item flags should be. However, the _parse() method will still be
    # called in two situations:

    # 1. In the base Flag's __init__ method, which calls _parse() to process the
    #    default value, which will be the shared dict.
    # 2. When processing command line overrides. We don't want to allow this
    #    normally, however some libraries will serialize and deserialize all
    #    flags, e.g. to pass values between processes, so we accept a dummy
    #    empty serialized value for these cases. It's unlikely users will try to
    #    set the dict flag to an empty string from the command line.
    if value is self._shared_dict or value == _EMPTY:
      return self._shared_dict
    raise flags.IllegalFlagValueError(
        "Can't override a dict flag directly. Did you mean to override one of "
        "its `Item`s instead?")

  def serialize(self):
    return _EMPTY

  def flag_type(self):
    return "dict"

# TODO(b/170423907): Pytype doesn't correctly infer that these have type
#                    `property`.
_flag_value_property = flags.Flag.value  # type: property
_multi_flag_value_property = flags.MultiFlag.value  # type: property


class ItemFlag(flags.Flag):
  """Updates a shared dict whenever its own value changes.

  See also the `DictFlag` and `ff.Item` classes for usage.
  """

  def __init__(self, shared_dict, namespace, *args, **kwargs):
    self._shared_dict = shared_dict
    self._namespace = namespace
    super().__init__(*args, **kwargs)

  # `super().value = value` doesn't work, see https://bugs.python.org/issue14965
  @_flag_value_property.setter
  def value(self, value):
    _flag_value_property.fset(self, value)
    self._update_shared_dict()

  def parse(self, argument):
    super().parse(argument)
    self._update_shared_dict()

  def _update_shared_dict(self):
    d = self._shared_dict
    for name in self._namespace[:-1]:
      d = d[name]
    d[self._namespace[-1]] = self.value


class MultiItemFlag(flags.MultiFlag):
  """Updates a shared dict whenever its own value changes.

  Used for flags that can appear multiple times on the command line.
  See also the `DictFlag` and `ff.Item` classes for usage.
  """

  def __init__(self, shared_dict, namespace, *args, **kwargs):
    self._shared_dict = shared_dict
    self._namespace = namespace
    super().__init__(*args, **kwargs)

  # `super().value = value` doesn't work, see https://bugs.python.org/issue14965
  @_multi_flag_value_property.setter
  def value(self, value):
    _multi_flag_value_property.fset(self, value)
    self._update_shared_dict()

  def parse(self, argument):
    super().parse(argument)
    self._update_shared_dict()

  def _update_shared_dict(self):
    d = self._shared_dict
    for name in self._namespace[:-1]:
      d = d[name]
    d[self._namespace[-1]] = self.value
