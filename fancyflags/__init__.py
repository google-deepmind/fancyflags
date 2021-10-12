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

# pylint: disable=g-bad-import-order,g-import-not-at-top

# Add current module to disclaimed module ids.
from absl import flags
flags.disclaim_key_flags()

from fancyflags._metadata import __version__

# Define flags based on a dictionary or sequence.
from fancyflags._definitions import DEFINE_dict
from fancyflags._definitions import DEFINE_sequence
from fancyflags._definitions import define_flags

# Automatically build fancyflags defs from a callable signature.
from fancyflags._auto import auto
from fancyflags._define_auto import DEFINE_auto

# Currently supported types inside the dict.
from fancyflags._definitions import Boolean
from fancyflags._definitions import Enum
from fancyflags._definitions import EnumClass
from fancyflags._definitions import Float
from fancyflags._definitions import Integer
from fancyflags._definitions import MultiEnum
from fancyflags._definitions import MultiEnumClass
from fancyflags._definitions import MultiString
from fancyflags._definitions import Sequence
from fancyflags._definitions import String
from fancyflags._definitions import StringList

# Class for adding new flag types.
from fancyflags._definitions import Item

# usage_logging: import
