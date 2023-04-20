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
import datetime
import enum

from typing import Any, Callable

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

  def test_define_with_global_flagvalues(self):
    # Since ff.DEFINE_dict uses an optional positional argument to specify a
    # custom FlagValues instance, we run nearly the same test as below to make
    # sure both global (default) and custom FlagValues work.
    unused_flagholder = ff.DEFINE_dict(
        "flat_dict",
        integer_field=ff.Integer(1, "integer field"),
        string_field=ff.String(""),
        string_list_field=ff.StringList(["a", "b", "c"], "string list field"))

    expected = {
        "integer_field": 1,
        "string_field": "",
        "string_list_field": ["a", "b", "c"]
    }
    self.assertEqual(FLAGS.flat_dict, expected)

    # These flags should also exist, although we won't access them in practice.
    self.assertEqual(FLAGS["flat_dict.integer_field"].value, 1)
    self.assertEqual(FLAGS["flat_dict.string_field"].value, "")

    # Custom help string.
    self.assertEqual(FLAGS["flat_dict.integer_field"].help, "integer field")
    # Default help string.
    self.assertEqual(FLAGS["flat_dict.string_field"].help,
                     "flat_dict.string_field")

  def test_define_with_custom_flagvalues(self):
    # Since ff.DEFINE_dict uses an optional positional argument to specify a
    # custom FlagValues instance, we run nearly the same test as above to make
    # sure both global (default) and custom FlagValues work.
    flag_values = flags.FlagValues()
    unused_flagholder = ff.DEFINE_dict(
        "flat_dict",
        flag_values,
        integer_field=ff.Integer(1, "integer field"),
        string_field=ff.String(""),
        string_list_field=ff.StringList(["a", "b", "c"], "string list field"))

    expected = {
        "integer_field": 1,
        "string_field": "",
        "string_list_field": ["a", "b", "c"]
    }
    flag_values(("./program", ""))
    self.assertEqual(flag_values.flat_dict, expected)

    # These flags should also exist, although we won't access them in practice.
    self.assertEqual(flag_values["flat_dict.integer_field"].value, 1)
    self.assertEqual(flag_values["flat_dict.string_field"].value, "")

    # Custom help string.
    self.assertEqual(flag_values["flat_dict.integer_field"].help,
                     "integer field")
    # Default help string.
    self.assertEqual(flag_values["flat_dict.string_field"].help,
                     "flat_dict.string_field")

  def test_define_flat(self):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        "flat_dict",
        flag_values,
        integer_field=ff.Integer(1, "integer field"),
        string_field=ff.String(""),
        string_list_field=ff.StringList(["a", "b", "c"], "string list field"))

    # This should return a single dict with the default values specified above.
    expected = {
        "integer_field": 1,
        "string_field": "",
        "string_list_field": ["a", "b", "c"]
    }
    flag_values(("./program", ""))
    self.assertEqual(flag_values.flat_dict, expected)
    self.assertEqual(flag_holder.value, expected)

  def test_define_nested(self):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        "nested_dict",
        flag_values,
        integer_field=ff.Integer(1, "integer field"),
        sub_dict=dict(
            string_field=ff.String("", "string field")
        )
    )

    # This should return a single dict with the default values specified above.
    expected = {"integer_field": 1, "sub_dict": {"string_field": ""}}

    flag_values(("./program", ""))
    self.assertEqual(flag_values.nested_dict, expected)
    self.assertEqual(flag_holder.value, expected)

    # These flags should also exist, although we won't access them in practice.
    self.assertEqual(flag_values["nested_dict.integer_field"].value, 1)
    self.assertEqual(flag_values["nested_dict.sub_dict.string_field"].value, "")

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
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        "valid_enum",
        flag_values,
        padding=ff.Enum("same", ["same", "valid"], "enum field"),
    )

    flag_values(("./program", ""))
    self.assertEqual(flag_holder.value, {"padding": "same"})

  def test_define_valid_case_insensitive_enum(self):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        "valid_case_sensitive",
        flag_values,
        padding=ff.Enum("Same", ["same", "valid"], "enum field",
                        case_sensitive=False),
    )
    flag_values(("./program", ""))
    self.assertEqual(flag_holder.value, {"padding": "same"})

  def test_define_invalid_enum(self):
    with self.assertRaises(ValueError):
      ff.Enum("invalid", ["same", "valid"], "enum field")

  def test_define_invalid_case_sensitive_enum(self):
    with self.assertRaises(ValueError):
      ff.Enum("Same", ["same", "valid"], "enum field")

  def test_define_valid_enum_class(self):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        "valid_enum_class",
        flag_values,
        my_enum=ff.EnumClass(MyEnum.A, MyEnum, "enum class field")
    )
    flag_values(("./program", ""))
    self.assertEqual(flag_holder.value, {"my_enum": MyEnum.A})

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
    flag_values = flags.FlagValues()
    ff.DEFINE_dict(
        "top_level_dict",
        flag_values,
        integer_field=ff.Integer(1, "integer field")
    )
    # The error type and message get converted in the process.
    with self.assertRaisesRegex(flags.IllegalFlagValueError,
                                "Can't override a dict flag directly"):
      flag_values(("./program", "--top_level_dict=3"))


class DateTimeTest(parameterized.TestCase):

  @parameterized.named_parameters(
      dict(
          testcase_name="default_str",
          default="2001-01-01",
          expected=datetime.datetime(2001, 1, 1)),
      dict(
          testcase_name="default_datetime",
          default=datetime.datetime(2001, 1, 1),
          expected=datetime.datetime(2001, 1, 1)),
      dict(
          testcase_name="no_default",
          default=None,
          expected=None))
  def test_define_datetime_default(self, default, expected):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        "dict_with_datetime",
        flag_values,
        my_datetime=ff.DateTime(default, "datetime field"),
    )
    flag_values(("./program", ""))
    self.assertEqual(flag_holder.value, {"my_datetime": expected})

  def test_define_datetime_invalid_default_raises(self):
    with self.assertRaisesRegex(ValueError, r"invalid"):
      ff.DEFINE_dict(
          "dict_with_datetime",
          my_datetime=ff.DateTime("42", "datetime field"),
      )

  def test_define_and_parse_invalid_value_raises(self):
    flag_name = "dict_with_datetime"
    flag_values = flags.FlagValues()
    ff.DEFINE_dict(
        flag_name,
        flag_values,
        my_datetime=ff.DateTime(None, "datetime field"),
    )

    with self.assertRaisesRegex(flags.IllegalFlagValueError, r"invalid"):
      flag_values["dict_with_datetime.my_datetime"].parse("2001")


class SequenceTest(absltest.TestCase):

  def test_sequence_defaults(self):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        "dict_with_sequences",
        flag_values,
        int_sequence=ff.Sequence([1, 2, 3], "integer field"),
        float_sequence=ff.Sequence([3.14, 2.718], "float field"),
        mixed_sequence=ff.Sequence([100, "hello", "world"], "mixed field")
    )

    flag_values(("./program", ""))
    self.assertEqual(flag_holder.value,
                     {"int_sequence": [1, 2, 3],
                      "float_sequence": [3.14, 2.718],
                      "mixed_sequence": [100, "hello", "world"]})


class MultiEnumTest(parameterized.TestCase):

  def test_defaults_parsing(self):
    flag_values = flags.FlagValues()
    enum_values = [1, 2, 3, 3.14, 2.718, 100, "hello", ["world"], {"planets"}]
    ff.DEFINE_dict(
        "dict_with_multienums",
        flag_values,
        int_sequence=ff.MultiEnum([1, 2, 3], enum_values, "integer field"),
        float_sequence=ff.MultiEnum([3.14, 2.718], enum_values, "float field"),
        mixed_sequence=ff.MultiEnum([100, "hello", ["world"], {"planets"}],
                                    enum_values, "mixed field"),
        enum_sequence=ff.MultiEnum([MyEnum.A], MyEnum, "enum field")
    )

    expected = {
        "int_sequence": [1, 2, 3],
        "float_sequence": [3.14, 2.718],
        "mixed_sequence": [100, "hello", ["world"], {"planets"}],
        "enum_sequence": [MyEnum.A],
    }
    flag_values(("./program", ""))
    self.assertEqual(flag_values.dict_with_multienums, expected)


class DefineSequenceTest(absltest.TestCase):

  # Follows test code in absl/flags/tests/flags_test.py

  def test_definition(self):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_sequence(
        name="sequence",
        default=[1, 2, 3],
        help="sequence flag",
        flag_values=flag_values,
    )

    flag_values(("./program", ""))
    self.assertEqual(flag_holder.value, [1, 2, 3])
    self.assertEqual(flag_values.flag_values_dict()["sequence"], [1, 2, 3])
    self.assertEqual(flag_values["sequence"].default_as_str, "'[1, 2, 3]'")  # pytype: disable=attribute-error

  def test_end_to_end_with_default(self):
    # There are more extensive tests for the parser in argument_parser_test.py.
    # Here we just include a couple of end-to-end examples.
    flag_values = flags.FlagValues()

    flag_holder = ff.DEFINE_sequence(
        "sequence",
        [1, 2, 3],
        "sequence flag",
        flag_values=flag_values,
    )
    flag_values(("./program", "--sequence=[4,5]"))
    self.assertEqual(flag_holder.value, [4, 5])

  def test_end_to_end_without_default(self):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_sequence(
        "sequence",
        None,
        "sequence flag",
        flag_values=flag_values,
    )
    flag_values(("./program", "--sequence=(4, 5)"))
    self.assertEqual(flag_holder.value, (4, 5))


class DefineMultiEnumTest(absltest.TestCase):

  # Follows test code in absl/flags/tests/flags_test.py

  def test_definition(self):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_multi_enum(
        "multienum",
        [1, 2, 3],
        [1, 2, 3],
        "multienum flag",
        flag_values=flag_values,
    )

    flag_values(("./program", ""))
    self.assertEqual(flag_holder.value, [1, 2, 3])
    self.assertEqual(flag_values.multienum, [1, 2, 3])
    self.assertEqual(flag_values.flag_values_dict()["multienum"], [1, 2, 3])
    self.assertEqual(flag_values["multienum"].default_as_str, "'[1, 2, 3]'")  # pytype: disable=attribute-error

  def test_end_to_end_with_default(self):
    # There are more extensive tests for the parser in argument_parser_test.py.
    # Here we just include a couple of end-to-end examples.
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_multi_enum(
        "multienum0",
        [1, 2, 3],
        [1, 2, 3, 4, 5],
        "multienum flag",
        flag_values=flag_values,
    )
    flag_values(("./program", "--multienum0=[4,5]"))
    self.assertEqual(flag_holder.value, [4, 5])

  def test_end_to_end_without_default(self):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_multi_enum(
        "multienum1",
        None,
        [1, 2, 3, 4, 5],
        "multienum flag",
        flag_values=flag_values,
    )
    flag_values(("./program", "--multienum1=(4, 5)"))
    self.assertEqual(flag_holder.value, (4, 5))


class MultiEnumClassTest(parameterized.TestCase):

  def test_multi_enum_class(self):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        "dict_with_multi_enum_class",
        flag_values,
        item=ff.MultiEnumClass(
            [MyEnum.A],
            MyEnum,
            "multi enum",
        ),
    )
    flag_values((
        "./program",
        "--dict_with_multi_enum_class.item=A",
        "--dict_with_multi_enum_class.item=B",
        "--dict_with_multi_enum_class.item=A",
    ))
    expected = {"item": [MyEnum.A, MyEnum.B, MyEnum.A]}
    self.assertEqual(flag_holder.value, expected)


class MultiStringTest(parameterized.TestCase):

  def test_defaults_parsing(self):
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        "dict_with_multistrings",
        flag_values,
        no_default=ff.MultiString(None, "no default"),
        single_entry=ff.MultiString("a", "single entry"),
        single_entry_list=ff.MultiString(["a"], "single entry list"),
        multiple_entry_list=ff.MultiString(["a", "b"], "multiple entry list"),
    )
    flag_values(("./program", ""))
    expected = {
        "no_default": None,
        "single_entry": ["a"],
        "single_entry_list": ["a"],
        "multiple_entry_list": ["a", "b"]
    }
    self.assertEqual(flag_holder.value, expected)


class SerializationTest(absltest.TestCase):

  def test_basic_serialization(self):
    flag_values = flags.FlagValues()
    ff.DEFINE_dict(
        "to_serialize",
        flag_values,
        integer_field=ff.Integer(1, "integer field"),
        boolean_field=ff.Boolean(False, "boolean field"),
        string_list_field=ff.StringList(["a", "b", "c"], "string list field"),
        enum_class_field=ff.EnumClass(MyEnum.A, MyEnum, "my enum field"),
    )

    initial_dict_value = copy.deepcopy(flag_values["to_serialize"].value)

    # Parse flags, then serialize.
    flag_values([
        "./program",
        "--to_serialize.boolean_field=True",
        "--to_serialize.integer_field",
        "1337",
        "--to_serialize.string_list_field=d,e,f",
        "--to_serialize.enum_class_field=B",
    ])
    self.assertEqual(flag_values["to_serialize"].serialize(), _flags._EMPTY)
    self.assertEqual(flag_values["to_serialize.boolean_field"].serialize(),
                     "--to_serialize.boolean_field=True")
    self.assertEqual(flag_values["to_serialize.string_list_field"].serialize(),
                     "--to_serialize.string_list_field=d,e,f")

    parsed_dict_value = copy.deepcopy(flag_values["to_serialize"].value)

    self.assertDictEqual(parsed_dict_value, {
        "boolean_field": True,
        "integer_field": 1337,
        "string_list_field": ["d", "e", "f"],
        "enum_class_field": MyEnum.B,
    })
    self.assertNotEqual(flag_values["to_serialize"].value, initial_dict_value)

    # test a round trip
    serialized_args = [
        flag_values[name].serialize() for name in flag_values
        if name.startswith("to_serialize.")]

    flag_values.unparse_flags()  # Reset to defaults
    self.assertDictEqual(flag_values["to_serialize"].value, initial_dict_value)

    flag_values(["./program"] + serialized_args)
    self.assertDictEqual(flag_values["to_serialize"].value, parsed_dict_value)

# Format:
# test name, flag define function, item, default value, override value
NAMES_ITEMS_AND_FLAGS = (
    # Booleans fail because of legacy absl flags behaviour of
    # --flagname and --noflagname
    # which shows up in serialisation.
    # ("boolean", flags.DEFINE_boolean, ff.Boolean, True, "false"),
    ("integer", flags.DEFINE_integer, ff.Integer, 1, "2"),
    ("float", flags.DEFINE_float, ff.Float, 1.0, "2.0"),
    ("sequence", ff.DEFINE_sequence, ff.Sequence, (1, "x"), (2.0, "y")),
    ("string", flags.DEFINE_string, ff.String, "one", "two"),
    ("stringlist", flags.DEFINE_list, ff.StringList, ["a", "b"], "['c', 'd']"),
)


class FlagAndItemEquivalence(parameterized.TestCase):

  @parameterized.named_parameters(*NAMES_ITEMS_AND_FLAGS)
  def test_equivalence(
      self,
      define_function: Callable[..., flags.FlagHolder],
      item_constructor: type(ff.Item),
      default: Any,
      override: str,
  ):
    flag_values = flags.FlagValues()
    flag_holder = define_function(
        "name.item",
        default,
        "help string",
        flag_values=flag_values,
    )

    ff_flagvalues = flags.FlagValues()
    shared_values = ff.define_flags(
        "name",
        {"item": item_constructor(default, "help string")},
        flag_values=ff_flagvalues,
    )

    with self.subTest("Check serialisation equivalence before parsing"):
      self.assertEqual(flag_values["name.item"].serialize(),
                       ff_flagvalues["name.item"].serialize())
      self.assertEqual(flag_values.flags_into_string(),
                       ff_flagvalues.flags_into_string())

    with self.subTest("Apply overrides and check equivalence after parsing"):
      # The flag holder gets updated at this point:
      flag_values(("./program", f"--name.item={override}"))
      # The shared_values dict gets updated at this point:
      ff_flagvalues(("./program", f"--name.item={override}"))
      self.assertNotEqual(flag_holder.value, default)
      self.assertEqual(flag_holder.value, shared_values["item"])

if __name__ == "__main__":
  absltest.main()
