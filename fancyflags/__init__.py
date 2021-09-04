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
"""An extended flags library. The main component is a nested dict flag."""

from absl import flags
from fancyflags import _auto
from fancyflags import _define_auto
from fancyflags import _definitions
from fancyflags import _metadata
# internal imports: usage_logging

__version__ = _metadata.__version__

# Add current module to disclaimed module ids.
flags.disclaim_key_flags()

# pylint: disable=invalid-name

# Function for automatically building fancyflags defs from a callable signature.
auto = _auto.auto

DEFINE_dict = _definitions.DEFINE_dict
define_flags = _definitions.define_flags
DEFINE_sequence = _definitions.DEFINE_sequence
DEFINE_auto = _define_auto.DEFINE_auto

# Currently supported types inside the dict.
Boolean = _definitions.Boolean
Enum = _definitions.Enum
EnumClass = _definitions.EnumClass
Float = _definitions.Float
Integer = _definitions.Integer
MultiEnum = _definitions.MultiEnum
MultiEnumClass = _definitions.MultiEnumClass
MultiString = _definitions.MultiString
Sequence = _definitions.Sequence
String = _definitions.String
StringList = _definitions.StringList

# Class for adding new flag types.
Item = _definitions.Item

# usage_logging: import
