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
"""Tests for definitions."""

import copy
import enum

from absl import flags
from absl.testing import absltest
from absl.testing import parameterized

# definitions almost exactly corresponds to the public API, so aliasing the
# import here for better illustrative tests.
from fancyflags import _definitions as ff
from fancyflags import _flags

FLAGS = flags.FLAGS


class MyEnum(enum.Enum):
  A = 1
  B = 2


class DifferentEnum(enum.Enum):
  C = 1
  D = 2


class FancyflagsTest(absltest.TestCase):

  def test_define_flat(self):
    flagholder = ff.DEFINE_dict(
        "flat_dict",
        integer_field=ff.Integer(1, "integer field"),
        string_field=ff.String(""),
        string_list_field=ff.StringList(["a", "b", "c"], "string list field"))

    # This should return a single dict with the default values specified above.
    expected = {
        "integer_field": 1,
        "string_field": "",
        "string_list_field": ["a", "b", "c"]
    }
    self.assertEqual(FLAGS.flat_dict, expected)
    self.assertEqual(flagholder.value, expected)

    # These flags should also exist, although we won't access them in practice.
    self.assertEqual(FLAGS["flat_dict.integer_field"].value, 1)
    self.assertEqual(FLAGS["flat_dict.string_field"].value, "")

    # Custom help string.
    self.assertEqual(FLAGS["flat_dict.integer_field"].help, "integer field")
    # Default help string.
    self.assertEqual(FLAGS["flat_dict.string_field"].help,
                     "flat_dict.string_field")

  def test_define_nested(self):
    flagholder = ff.DEFINE_dict(
        "nested_dict",
        integer_field=ff.Integer(1, "integer field"),
        sub_dict=dict(
            string_field=ff.String("", "string field")
        )
    )

    # This should return a single dict with the default values specified above.
    expected = {"integer_field": 1, "sub_dict": {"string_field": ""}}
    self.assertEqual(FLAGS.nested_dict, expected)
    self.assertEqual(flagholder.value, expected)

    # These flags should also exist, although we won't access them in practice.
    self.assertEqual(FLAGS["nested_dict.integer_field"].value, 1)
    self.assertEqual(FLAGS["nested_dict.sub_dict.string_field"].value, "")

  def test_no_name_error(self):
    with self.assertRaisesRegex(ValueError, "one positional argument"):
      ff.DEFINE_dict(
          integer_field=ff.Integer(1, "integer field"),
      )

  def test_no_kwargs_error(self):
    with self.assertRaisesRegex(ValueError, "one keyword argument"):
      ff.DEFINE_dict("no_kwargs")

  def test_too_many_positional_args_error(self):
    with self.assertRaisesRegex(ValueError, "at most two positional"):
      ff.DEFINE_dict(
          "name",
          ff.String("foo", "string"),
          ff.String("bar", "string"),
          integer_field=ff.Integer(1, "integer field")
      )

  def test_flag_name_error(self):
    with self.assertRaisesRegex(ValueError, "must be a string"):
      ff.DEFINE_dict(
          ff.String("name", "string flag"),
          ff.String("stringflag", "string"),
          integer_field=ff.Integer(1, "integer field")
      )

  def test_flag_values_error(self):
    with self.assertRaisesRegex(ValueError, "FlagValues instance"):
      ff.DEFINE_dict(
          "name",
          ff.String("stringflag", "string"),
          integer_field=ff.Integer(1, "integer field")
      )

  def test_define_valid_enum(self):
    ff.DEFINE_dict(
        "valid_enum",
        padding=ff.Enum("same", ["same", "valid"], "enum field"),
    )
    self.assertEqual(FLAGS.valid_enum, {"padding": "same"})

  def test_define_valid_case_insensitive_enum(self):
    ff.DEFINE_dict(
        "valid_case_sensitive",
        padding=ff.Enum("Same", ["same", "valid"], "enum field",
                        case_sensitive=False),
    )
    self.assertEqual(FLAGS.valid_case_sensitive, {"padding": "same"})

  def test_define_invalid_enum(self):
    with self.assertRaises(ValueError):
      ff.Enum("invalid", ["same", "valid"], "enum field")

  def test_define_invalid_case_sensitive_enum(self):
    with self.assertRaises(ValueError):
      ff.Enum("Same", ["same", "valid"], "enum field")

  def test_define_valid_enum_class(self):
    ff.DEFINE_dict(
        "valid_enum_class",
        my_enum=ff.EnumClass(MyEnum.A, MyEnum, "enum class field")
    )
    self.assertEqual(FLAGS.valid_enum_class, {"my_enum": MyEnum.A})

  def test_define_invalid_enum_class(self):
    with self.assertRaises(ValueError):
      ff.EnumClass(DifferentEnum.C, MyEnum)


class ExtractDefaultsTest(absltest.TestCase):

  def test_valid_flat(self):
    result = ff._extract_defaults(
        {
            "integer_field": ff.Integer(10, "Integer field"),
            "string_field": ff.String("default", "String field"),
        }
    )
    expected = {"integer_field": 10, "string_field": "default"}
    self.assertEqual(result, expected)

  def test_valid_nested(self):
    result = ff._extract_defaults(
        {
            "integer_field": ff.Integer(10, "Integer field"),
            "string_field": ff.String("default", "String field"),
            "nested": {
                "float_field": ff.Float(3.1, "Float field"),
            },
        }
    )
    expected = {
        "integer_field": 10,
        "string_field": "default",
        "nested": {"float_field": 3.1},
    }
    self.assertEqual(result, expected)

  def test_invalid_container(self):
    expected_message = ff._NOT_A_DICT_OR_ITEM.format("list")
    with self.assertRaisesWithLiteralMatch(TypeError, expected_message):
      ff._extract_defaults(
          {
              "integer_field": ff.Integer(10, "Integer field"),
              "string_field": ff.String("default", "String field"),
              "nested": [ff.Float(3.1, "Float field")],
          }
      )

  def test_invalid_flat_leaf(self):
    expected_message = ff._NOT_A_DICT_OR_ITEM.format("int")
    with self.assertRaisesWithLiteralMatch(TypeError, expected_message):
      ff._extract_defaults(
          {
              "string_field": ff.String("default", "String field"),
              "naughty_field": 100,
          }
      )

  def test_invalid_nested_leaf(self):
    expected_message = ff._NOT_A_DICT_OR_ITEM.format("bool")
    with self.assertRaisesWithLiteralMatch(TypeError, expected_message):
      ff._extract_defaults(
          {
              "string_field": ff.String("default", "String field"),
              "nested": {
                  "naughty_field": True,
              },
          }
      )

  def test_overriding_top_level_dict_flag_fails(self):
    ff.DEFINE_dict(
        "top_level_dict",
        integer_field=ff.Integer(1, "integer field")
    )
    # The error type and message get converted in the process.
    with self.assertRaisesRegex(flags.IllegalFlagValueError,
                                "Can't override a dict flag directly"):
      FLAGS(("./program", "--top_level_dict=3"))


class SequenceTest(absltest.TestCase):

  def test_sequence_defaults(self):
    ff.DEFINE_dict(
        "dict_with_sequences",
        int_sequence=ff.Sequence([1, 2, 3], "integer field"),
        float_sequence=ff.Sequence([3.14, 2.718], "float field"),
        mixed_sequence=ff.Sequence([100, "hello", "world"], "mixed field")
    )

    self.assertEqual(FLAGS.dict_with_sequences,
                     {"int_sequence": [1, 2, 3],
                      "float_sequence": [3.14, 2.718],
                      "mixed_sequence": [100, "hello", "world"]})


class MultiEnumTest(parameterized.TestCase):

  def test_defaults_parsing(self):
    enum_values = [1, 2, 3, 3.14, 2.718, 100, "hello", ["world"], {"planets"}]
    ff.DEFINE_dict(
        "dict_with_multienums",
        int_sequence=ff.MultiEnum([1, 2, 3], enum_values, "integer field"),
        float_sequence=ff.MultiEnum([3.14, 2.718], enum_values, "float field"),
        mixed_sequence=ff.MultiEnum([100, "hello", ["world"], {"planets"}],
                                    enum_values, "mixed field"),
        enum_sequence=ff.MultiEnum([MyEnum.A], MyEnum, "enum field")
    )

    self.assertEqual(FLAGS.dict_with_multienums,
                     {"int_sequence": [1, 2, 3],
                      "float_sequence": [3.14, 2.718],
                      "mixed_sequence": [100, "hello", ["world"], {"planets"}],
                      "enum_sequence": [MyEnum.A]})


class DefineSequenceTest(absltest.TestCase):

  # Follows test code in absl/flags/tests/flags_test.py

  def test_definition(self):
    num_existing_flags = len(FLAGS)

    ff.DEFINE_sequence("sequence", [1, 2, 3], "sequence flag")

    self.assertLen(FLAGS, num_existing_flags + 1)

    self.assertEqual(FLAGS.sequence, [1, 2, 3])
    self.assertEqual(FLAGS.flag_values_dict()["sequence"], [1, 2, 3])
    self.assertEqual(FLAGS["sequence"].default_as_str, "'[1, 2, 3]'")  # pytype: disable=attribute-error

  def test_parsing(self):
    # There are more extensive tests for the parser in argument_parser_test.py.
    # Here we just include a couple of end-to-end examples.

    ff.DEFINE_sequence("sequence0", [1, 2, 3], "sequence flag")
    FLAGS(("./program", "--sequence0=[4,5]"))
    self.assertEqual(FLAGS.sequence0, [4, 5])

    ff.DEFINE_sequence("sequence1", None, "sequence flag")
    FLAGS(("./program", "--sequence1=(4, 5)"))
    self.assertEqual(FLAGS.sequence1, (4, 5))


class DefineMultiEnumTest(absltest.TestCase):

  # Follows test code in absl/flags/tests/flags_test.py

  def test_definition(self):
    num_existing_flags = len(FLAGS)

    ff.DEFINE_multi_enum("multienum", [1, 2, 3], [1, 2, 3], "multienum flag")

    self.assertLen(FLAGS, num_existing_flags + 1)

    self.assertEqual(FLAGS.multienum, [1, 2, 3])
    self.assertEqual(FLAGS.flag_values_dict()["multienum"], [1, 2, 3])
    self.assertEqual(FLAGS["multienum"].default_as_str, "'[1, 2, 3]'")  # pytype: disable=attribute-error

  def test_parsing(self):
    # There are more extensive tests for the parser in argument_parser_test.py.
    # Here we just include a couple of end-to-end examples.

    ff.DEFINE_multi_enum("multienum0", [1, 2, 3], [1, 2, 3, 4, 5],
                         "multienum flag")
    FLAGS(("./program", "--multienum0=[4,5]"))
    self.assertEqual(FLAGS.multienum0, [4, 5])

    ff.DEFINE_multi_enum("multienum1", None, [1, 2, 3, 4, 5], "multienum flag")
    FLAGS(("./program", "--multienum1=(4, 5)"))
    self.assertEqual(FLAGS.multienum1, (4, 5))


class MultiEnumClassTest(parameterized.TestCase):

  def test_multi_enum_class(self):
    ff.DEFINE_dict(
        "dict_with_multi_enum_class",
        item=ff.MultiEnumClass([MyEnum.A], MyEnum, "multi enum"),
    )
    FLAGS(("./program",
           "--dict_with_multi_enum_class.item=A",
           "--dict_with_multi_enum_class.item=B",
           "--dict_with_multi_enum_class.item=A",))
    expected = [MyEnum.A, MyEnum.B, MyEnum.A]
    self.assertEqual(FLAGS.dict_with_multi_enum_class["item"], expected)


class MultiStringTest(parameterized.TestCase):

  def test_defaults_parsing(self):
    ff.DEFINE_dict(
        "dict_with_multistrings",
        no_default=ff.MultiString(None, "no default"),
        single_entry=ff.MultiString("a", "single entry"),
        single_entry_list=ff.MultiString(["a"], "single entry list"),
        multiple_entry_list=ff.MultiString(["a", "b"], "multiple entry list"),
    )

    self.assertEqual(FLAGS.dict_with_multistrings,
                     {"no_default": None,
                      "single_entry": ["a"],
                      "single_entry_list": ["a"],
                      "multiple_entry_list": ["a", "b"]})


class SerializationTest(absltest.TestCase):

  def test_basic_serialization(self):
    ff.DEFINE_dict(
        "to_serialize",
        integer_field=ff.Integer(1, "integer field"),
        boolean_field=ff.Boolean(False, "boolean field"),
        string_list_field=ff.StringList(["a", "b", "c"], "string list field"),
        enum_class_field=ff.EnumClass(MyEnum.A, MyEnum, "my enum field"),
    )

    initial_dict_value = copy.deepcopy(FLAGS["to_serialize"].value)

    # Parse flags, then serialize.
    FLAGS(["./program",
           "--to_serialize.boolean_field=True",
           "--to_serialize.integer_field", "1337",
           "--to_serialize.string_list_field=d,e,f",
           "--to_serialize.enum_class_field=B",
           ])
    self.assertEqual(FLAGS["to_serialize"].serialize(), _flags._EMPTY)
    self.assertEqual(FLAGS["to_serialize.boolean_field"].serialize(),
                     "--to_serialize.boolean_field=True")
    self.assertEqual(FLAGS["to_serialize.string_list_field"].serialize(),
                     "--to_serialize.string_list_field=d,e,f")

    parsed_dict_value = copy.deepcopy(FLAGS["to_serialize"].value)

    self.assertDictEqual(parsed_dict_value, {
        "boolean_field": True,
        "integer_field": 1337,
        "string_list_field": ["d", "e", "f"],
        "enum_class_field": MyEnum.B,
    })
    self.assertNotEqual(FLAGS["to_serialize"].value, initial_dict_value)

    # test a round trip
    serialized_args = [
        FLAGS[name].serialize() for name in FLAGS if name.startswith(
            "to_serialize.")]

    FLAGS.unparse_flags()  # Reset to defaults
    self.assertDictEqual(FLAGS["to_serialize"].value, initial_dict_value)

    FLAGS(["./program"] + serialized_args)
    self.assertDictEqual(FLAGS["to_serialize"].value, parsed_dict_value)

if __name__ == "__main__":
  absltest.main()
