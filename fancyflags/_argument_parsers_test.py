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

import datetime

from absl.testing import absltest
from absl.testing import parameterized
from fancyflags import _argument_parsers


UTC = datetime.timezone.utc
TZINFO_4HRS = datetime.timezone(datetime.timedelta(hours=4))


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
      ("[1, 2, 3]", [1, 2, 3]),
      ("[]", []),
      ("()", ()),
      ("['hello', 'world']", ["hello", "world"]),
      ("(3.14, 2.718)", (3.14, 2.718)),
      (
          "(1, -1.0)",
          (1, -1.0),
      ),
  )
  def test_parse_input_string(self, input_string, expected):
    result = self.parser.parse(input_string)
    self.assertEqual(result, expected)

    # Check that the string-formatted expected result also matches the input
    self.assertEqual("{}".format(expected), input_string)

  @parameterized.parameters(
      ('["hello", u"world"]', ["hello", "world"]),
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
        ValueError, _argument_parsers._EMPTY_STRING_ERROR_MESSAGE
    ):
      self.parser.parse("")

  @parameterized.parameters(
      # ValueError from ast.literal_eval
      "[foo, bar]",
      # SyntaxError from ast.literal_eval
      "['foo', 'bar'",
      "[1 2]",
  )
  def test_parse_string_literal_error(self, input_string):
    with self.assertRaisesRegex(ValueError, ".*as a python literal.*"):
      self.parser.parse(input_string)

  def test_string_too_long(self):
    # Test string length validation
    long_string = "[" + "1," * 50000 + "1]"  # Very long string
    with self.assertRaisesRegex(ValueError, "Input string too long"):
      self.parser.parse(long_string)

  def test_dangerous_patterns(self):
    # Test dangerous pattern detection
    with self.assertRaisesRegex(ValueError, "unsafe pattern"):
      self.parser.parse("__import__('os').system('ls')")

    with self.assertRaisesRegex(ValueError, "unsafe pattern"):
      self.parser.parse("exec('print(1)')")

  def test_excessive_nesting(self):
    # Test depth validation
    # Create deeply nested structure
    nested = "[" * 15 + "1" + "]" * 15
    with self.assertRaisesRegex(ValueError, "nesting too deep"):
      self.parser.parse(nested)

  def test_sequence_too_long(self):
    # Test sequence length validation
    # Create a very long sequence
    large_seq = [1] * 15000
    with self.assertRaisesRegex(ValueError, "Sequence too long"):
      self.parser.parse(large_seq)


class MultiEnumParserTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    self.parser = _argument_parsers.MultiEnumParser(
        ["a", "a", ["a"], "b", "c", 1, [2], {"a": "d"}]
    )

  @parameterized.parameters(
      ('["a"]', ["a"]),
      ('[["a"], "a"]', [["a"], "a"]),
      ('[1, "a", {"a": "d"}]', [1, "a", {"a": "d"}]),
  )
  def test_parse_input(self, inputs, target):
    self.assertEqual(self.parser.parse(inputs), target)

  @parameterized.parameters(
      ("'a'", "evaluated as a"),
      (1, "Unsupported type"),
      ({"a"}, "Unsupported type"),
      ("''", "evaluated as a"),
  )
  def test_invalid_input_type(self, input_item, regex):
    with self.assertRaisesRegex(TypeError, regex):
      self.parser.parse(input_item)

  @parameterized.parameters("[1, 2]", '["a", ["b"]]')
  def test_out_of_enum_values(self, inputs):
    with self.assertRaisesRegex(ValueError, "Argument values should be one of"):
      self.parser.parse(inputs)

    with self.assertRaisesRegex(ValueError, "Argument values should be one of"):
      self.parser.parse(inputs)

  def test_string_validation(self):
    # Test dangerous pattern detection in MultiEnumParser
    with self.assertRaisesRegex(ValueError, "unsafe pattern"):
      self.parser.parse("__import__('sys')")


class PossiblyNaiveDatetimeFlagTest(parameterized.TestCase):

  def test_parser_flag_type(self):
    parser = _argument_parsers.PossiblyNaiveDatetimeParser()
    self.assertEqual("datetime.datetime", parser.flag_type())

  @parameterized.named_parameters(
      dict(
          testcase_name="date_string",
          value="2011-11-04",
          expected=datetime.datetime(2011, 11, 4, 0, 0),
      ),
      dict(
          testcase_name="second_string",
          value="2011-11-04T00:05:23",
          expected=datetime.datetime(2011, 11, 4, 0, 5, 23),
      ),
      dict(
          testcase_name="fractions_string",
          value="2011-11-04 00:05:23.283",
          expected=datetime.datetime(2011, 11, 4, 0, 5, 23, 283000),
      ),
      # It's OK to disable the g-tzinfo-datetime check here because it is meant
      # to prevent users from passing the output of pytz.timezone() as tzinfo
      # into the datetime constructor (see https://peps.python.org/pep-0431/).
      # We are not using pytz here, but apparently pylint cannot detect that.
      dict(
          testcase_name="utc_string",
          value="2011-11-04 00:05:23.283+00:00",
          expected=datetime.datetime(2011, 11, 4, 0, 5, 23, 283000, tzinfo=UTC),  # pylint: disable=g-tzinfo-datetime
      ),
      dict(
          testcase_name="offset_string",
          value="2011-11-04T00:05:23+04:00",
          expected=datetime.datetime(2011, 11, 4, 0, 5, 23, tzinfo=TZINFO_4HRS),  # pylint: disable=g-tzinfo-datetime
      ),
      dict(
          testcase_name="datetime",
          value=datetime.datetime(2011, 11, 4, 0, 0),
          expected=datetime.datetime(2011, 11, 4, 0, 0),
      ),
  )
  def test_parse(self, value, expected):
    parser = _argument_parsers.PossiblyNaiveDatetimeParser()
    result = parser.parse(value)

    self.assertIsInstance(result, datetime.datetime)
    self.assertEqual(expected, result)

  def test_parse_separator_plus_or_minus_raises(self):
    parser = _argument_parsers.PossiblyNaiveDatetimeParser()
    with self.assertRaisesRegex(ValueError, r"separator between date and time"):
      # Avoid confusion of 1970-01-01T08:00:00 vs. 1970-01-01T00:00:00-08:00
      parser.parse("1970-01-01-08:00")

  def test_empty_string(self):
    # Test empty string validation
    parser = _argument_parsers.PossiblyNaiveDatetimeParser()
    with self.assertRaisesRegex(ValueError, "Empty datetime string"):
      parser.parse("")

    with self.assertRaisesRegex(ValueError, "Empty datetime string"):
      parser.parse("   ")

  def test_string_too_long(self):
    # Test string length validation
    parser = _argument_parsers.PossiblyNaiveDatetimeParser()
    long_string = "2023-01-01" + "x" * 100
    with self.assertRaisesRegex(ValueError, "too long"):
      parser.parse(long_string)

  def test_wrong_type(self):
    # Test type validation
    parser = _argument_parsers.PossiblyNaiveDatetimeParser()
    with self.assertRaisesRegex(TypeError, "Expected string or datetime"):
      parser.parse(123)


class PossiblyNaiveTimeDeltaFlagTest(parameterized.TestCase):

  def test_parser_flag_type(self):
    parser = _argument_parsers.PossiblyNaiveTimeDeltaParser()
    self.assertEqual("datetime.timedelta", parser.flag_type())

  @parameterized.named_parameters(
      dict(
          testcase_name="simple_seconds",
          value="17s",
          expected=datetime.timedelta(seconds=17),
      ),
      dict(
          testcase_name="all_units",
          value="17w 3d 5h 19m 22s 10ms 42us",
          expected=datetime.timedelta(
              weeks=17,
              days=3,
              hours=5,
              minutes=19,
              seconds=22,
              milliseconds=10,
              microseconds=42,
          ),
      ),
      dict(
          testcase_name="normalization",
          value="89m 125s",
          expected=datetime.timedelta(minutes=89, seconds=125),
      ),
      dict(
          testcase_name="spacing",
          value="2 h  34 m",
          expected=datetime.timedelta(hours=2, minutes=34),
      ),
      dict(
          testcase_name="bad",
          value="53u",
          expected=datetime.timedelta(),
          raises=ValueError,
      ),
  )
  def test_parse(self, value, expected, raises=None):
    parser = _argument_parsers.PossiblyNaiveTimeDeltaParser()

    if raises is None:
      result = parser.parse(value)
      self.assertIsInstance(result, datetime.timedelta)
      self.assertEqual(expected, result)
    else:
      with self.assertRaises(raises):
        parser.parse(value)

  def test_empty_string(self):
    # Test empty string validation
    parser = _argument_parsers.PossiblyNaiveTimeDeltaParser()
    with self.assertRaisesRegex(ValueError, "Empty timedelta string"):
      parser.parse("")

    with self.assertRaisesRegex(ValueError, "Empty timedelta string"):
      parser.parse("   ")

  def test_string_too_long(self):
    # Test string length validation
    parser = _argument_parsers.PossiblyNaiveTimeDeltaParser()
    long_string = "1d" + "x" * 200
    with self.assertRaisesRegex(ValueError, "too long"):
      parser.parse(long_string)

  def test_wrong_type(self):
    # Test type validation
    parser = _argument_parsers.PossiblyNaiveTimeDeltaParser()
    with self.assertRaisesRegex(TypeError, "Expected string or timedelta"):
      parser.parse(123)

  def test_excessive_values(self):
    # Test protection against extremely large timedelta values
    parser = _argument_parsers.PossiblyNaiveTimeDeltaParser()
    with self.assertRaisesRegex(ValueError, "too large"):
      parser.parse("999999w")  # Too many weeks


if __name__ == "__main__":
  absltest.main()
