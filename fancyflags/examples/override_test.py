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
"""Test for flag overrides in fancyflags.."""

from absl import flags
from absl.testing import absltest
import fancyflags as ff


SETTINGS = ff.DEFINE_dict(
    "settings",
    integer_field=ff.Integer(1, "integer field"),
    string_field=ff.String(None, "string field"),
    nested=dict(float_field=ff.Float(0.0, "float field")),
    sequence_field=ff.Sequence([1, 2, 3], "sequence field"),
    another_sequence_field=ff.Sequence((3.14, 2.718), "another sequence field"),
    string_list_field=ff.StringList(["a"], "string list flag."),
)


class OverrideTest(absltest.TestCase):

  def test_give_me_a_name(self):
    expected = dict(
        integer_field=5,
        string_field=None,  # Not overridden in BUILD args.
        nested=dict(
            float_field=3.2,
        ),
        sequence_field=[4, 5, 6],
        another_sequence_field=[3.0, 2.0],
        string_list_field=["a", "bunch", "of", "overrides"],
    )
    self.assertEqual(flags.FLAGS.settings, expected)
    self.assertEqual(SETTINGS.value, expected)


if __name__ == "__main__":
  absltest.main()
