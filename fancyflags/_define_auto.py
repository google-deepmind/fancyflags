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
"""Automatic flags via ff.auto-compatible callables."""

from typing import Callable, TypeVar

from absl import flags
from fancyflags import _auto
from fancyflags import _definitions
from fancyflags import _flags

_T = TypeVar('_T')

# Add current module to disclaimed module ids.
flags.disclaim_key_flags()

def DEFINE_auto(  # pylint: disable=invalid-name
    name: str,
    fn: Callable[..., _T],
    help_string: str,
    flag_values: flags.FlagValues = flags.FLAGS,
) -> flags.FlagHolder[Callable[..., _T]]:
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
    help_string: The help string for this flag.
    flag_values: An optional `flags.FlagValues` instance.

  Returns:
    A `flags.FlagHolder`.
  """
  arguments = _auto.auto(fn)
  # Define the individual flags.
  defaults = _definitions.define_flags(name, arguments, flag_values=flag_values)
  # Define a holder flag.
  return flags.DEFINE_flag(
      _flags.AutoFlag(
          fn,
          defaults,
          name=name,
          default=None,
          parser=flags.ArgumentParser(),
          serializer=None,
          help_string=help_string),
      flag_values=flag_values)
