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
"""Tests for compatibility with absl.testing.flagsaver."""

from absl import flags
from absl.testing import absltest
from absl.testing import flagsaver
import fancyflags as ff

flags.DEFINE_string("string_flag", "unchanged", "flag to test with")

ff.DEFINE_dict(
    "test_dict_flag",
    dict=dict(
        nested=ff.Float(1.0, "nested flag"),
    ),
    unnested=ff.Integer(4, "unnested flag"),
)

FLAGS = flags.FLAGS


class FlagSaverTest(absltest.TestCase):

  def test_flagsaver_with_context_overrides(self):
    with flagsaver.flagsaver(**{
        "string_flag": "new value",
        "test_dict_flag.dict.nested": -1.0,
    }):
      self.assertEqual("new value", FLAGS.string_flag)
      self.assertEqual(-1.0, FLAGS.test_dict_flag["dict"]["nested"])
      self.assertEqual(4, FLAGS.test_dict_flag["unnested"])
      FLAGS.string_flag = "another value"

    self.assertEqual("unchanged", FLAGS.string_flag)
    self.assertEqual(1.0, FLAGS.test_dict_flag["dict"]["nested"])

  def test_flagsaver_with_decorator_overrides(self):

  # Modeled after test_decorator_with_overrides in
  # https://github.com/abseil/abseil-py/blob/master/absl/testing/tests/flagsaver_test.py  # pylint: disable=line-too-long

    @flagsaver.flagsaver(**{
        "string_flag": "new value",
        "test_dict_flag.dict.nested": -1.0,
    })
    def mutate_flags():
      return FLAGS.string_flag, FLAGS.test_dict_flag["dict"]["nested"]

    # Values should be overridden in the function.
    self.assertEqual(("new value", -1.0), mutate_flags())

    # But unchanged here.
    self.assertEqual("unchanged", FLAGS.string_flag)
    self.assertEqual(1.0, FLAGS.test_dict_flag["dict"]["nested"])

  def test_flagsaver_with_context_overrides_twice(self):
    # Checking that the flat -> dict flag sync works again after restoration.
    # This might fail if the underlying absl functions copied the dict as part
    # of restoration.

    with flagsaver.flagsaver(**{
        "string_flag": "new value",
        "test_dict_flag.dict.nested": -1.0,
    }):
      self.assertEqual("new value", FLAGS.string_flag)
      self.assertEqual(-1.0, FLAGS.test_dict_flag["dict"]["nested"])
      self.assertEqual(4, FLAGS.test_dict_flag["unnested"])
      FLAGS.string_flag = "another value"

    self.assertEqual("unchanged", FLAGS.string_flag)
    self.assertEqual(1.0, FLAGS.test_dict_flag["dict"]["nested"])

    # Same again!

    with flagsaver.flagsaver(**{
        "string_flag": "new value",
        "test_dict_flag.dict.nested": -1.0,
    }):
      self.assertEqual("new value", FLAGS.string_flag)
      self.assertEqual(-1.0, FLAGS.test_dict_flag["dict"]["nested"])
      self.assertEqual(4, FLAGS.test_dict_flag["unnested"])
      FLAGS.string_flag = "another value"

    self.assertEqual("unchanged", FLAGS.string_flag)
    self.assertEqual(1.0, FLAGS.test_dict_flag["dict"]["nested"])

  @absltest.skip("This fails because flagsaver does not do deep copies")
  def test_flagsaver_with_changes_within_context(self):
    """Overrides within a flagsaver context should be correctly restored."""
    with flagsaver.flagsaver():
      FLAGS.string_flag = "new_value"
      FLAGS["test_dict_flag.dict.nested"].value = -1.0
      FLAGS.test_dict_flag["unnested"] = -1.0
    self.assertEqual("unchanged", FLAGS.string_flag)  # Works.
    self.assertEqual(1.0, FLAGS.test_dict_flag["dict"]["nested"])  # Works.
    # TODO(b/177927157) Fix this behaviour.
    self.assertEqual(4, FLAGS.test_dict_flag["unnested"])  # Broken.

if __name__ == "__main__":
  absltest.main()
