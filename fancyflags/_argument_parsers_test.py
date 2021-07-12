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
"""Tests for argument_parsers."""

from absl.testing import absltest
from absl.testing import parameterized
from fancyflags import _argument_parsers


class SequenceParserTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    self.parser = _argument_parsers.SequenceParser()

  @parameterized.parameters(
      ([1, 2, 3],),
      ([],),
      ((),),
      (["hello", "world"],),
      ((3.14, 2.718),),
      ((1, -1.0),),
  )
  def test_parse_input_sequence(self, input_sequence):
    result = self.parser.parse(input_sequence)
    self.assertEqual(result, input_sequence)

  @parameterized.parameters(
      (u"[1, 2, 3]", [1, 2, 3]),
      ("[]", []),
      ("()", ()),
      ("['hello', 'world']", ["hello", "world"]),
      ("(3.14, 2.718)", (3.14, 2.718)),
      ("(1, -1.0)", (1, -1.0),),
  )
  def test_parse_input_string(self, input_string, expected):
    result = self.parser.parse(input_string)
    self.assertEqual(result, expected)

    # Check that the string-formatted expected result also matches the input
    self.assertEqual("{}".format(expected), input_string)

  @parameterized.parameters(
      ("[\"hello\", u\"world\"]", ["hello", u"world"]),
      ("(1,2,3)", (1, 2, 3)),
  )
  def test_parse_input_string_different_format(self, input_string, expected):
    # The parser/ast result should also work for slightly different formatting.
    result = self.parser.parse(input_string)
    self.assertEqual(result, expected)

  def test_parse_none(self):
    result = self.parser.parse(None)
    self.assertEqual(result, [])

  @parameterized.parameters(
      ({1, 2, 3},),
      (100,),
  )
  def test_parse_invalid_input_type(self, input_item):
    with self.assertRaisesRegex(TypeError, "Unsupported type"):
      self.parser.parse(input_item)

  @parameterized.parameters(
      ("'hello world'",),
      ("{1: 3}",),
  )
  def test_parse_invalid_evaluated_type(self, input_string):
    with self.assertRaisesRegex(TypeError, "evaluated as"):
      self.parser.parse(input_string)

  @parameterized.parameters(
      # No nested anything.
      ([1, [2, 3]],),
      ([1, (2, 3)],),
      ((1, [2, 3]),),
      ((1, (2, 3)),),
      # Nothing outside the listed primitive types.
      ([1, set()],),
  )
  def test_parse_invalid_entries(self, input_item):
    with self.assertRaisesRegex(TypeError, "contains unsupported"):
      self.parser.parse(input_item)

  def test_empty_string(self):
    with self.assertRaisesWithLiteralMatch(
        ValueError, _argument_parsers._EMPTY_STRING_ERROR_MESSAGE):
      self.parser.parse("")


class MultiEnumParserTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    self.parser = _argument_parsers.MultiEnumParser(
        ["a", "a", ["a"], "b", "c", 1, [2], {
            "a": "d"
        }])

  @parameterized.parameters(('["a"]', ["a"]),
                            ('[["a"], "a"]', [["a"], "a"]),
                            ('[1, "a", {"a": "d"}]', [1, "a", {"a": "d"}])
                           )
  def test_parse_input(self, inputs, target):
    self.assertEqual(self.parser.parse(inputs), target)

  @parameterized.parameters(("'a'", "evaluated as a"),
                            (1, "Unsupported type"),
                            ({"a"}, "Unsupported type"),
                            ("''", "evaluated as a")
                           )
  def test_invalid_input_type(self, input_item, regex):
    with self.assertRaisesRegex(TypeError, regex):
      self.parser.parse(input_item)

  @parameterized.parameters("[1, 2]",
                            '["a", ["b"]]')
  def test_out_of_enum_values(self, inputs):
    with self.assertRaisesRegex(ValueError, "Argument values should be one of"):
      self.parser.parse(inputs)

    with self.assertRaisesRegex(ValueError, "Argument values should be one of"):
      self.parser.parse(inputs)


if __name__ == "__main__":
  absltest.main()
