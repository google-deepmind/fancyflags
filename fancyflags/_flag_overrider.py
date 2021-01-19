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
"""A subclass of flagsaver._FlagOverrider that works for arbitrary flag names.
"""

from absl.testing import flagsaver


class FlagOverrider(flagsaver._FlagOverrider):  # pylint: disable=protected-access
  """Overrides flags for the duration of the decorated function call.

  This subclass does not rely on **kwargs to supply the flag overrides_dict.
  Using **kwargs does not work for flag names containing dots, since these are
  not valid Python identifiers.
  """

  def __init__(self, overrides_dict):
    # Do NOT call parent constructor, since **unpacking overrides dict may not
    # work (given the premise of this class).
    self._overrides = overrides_dict
    self._saved_flag_values = None
