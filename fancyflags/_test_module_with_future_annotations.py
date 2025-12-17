# Copyright 2025 DeepMind Technologies Limited.
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
"""A test module that contains future annotations.

In some circumstances, the behavior of some typing function (e.g.
`typing.get_type_hints` can differ depending on if the types are lazily
evaluated or not). The easiest way to properly test this is to have a module
with `from __future__ import annotations` imported that we use for testing.
"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class RandomClass:
  z: int = 0


@dataclasses.dataclass
class DataclassWithForwardReference:
  x: RandomClass | None = None
