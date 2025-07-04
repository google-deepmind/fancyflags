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

# Test that `auto` can still correctly infer parameter types when postponed
# evaluation of type annotations (PEP 563) is enabled.
from __future__ import annotations

import abc
from collections.abc import Sequence
import dataclasses
import enum
import re
import sys
import unittest

from absl import flags
from absl.testing import absltest
import fancyflags as ff
from fancyflags import _auto

FLAGS = flags.FLAGS


class MyEnum(enum.Enum):
  ZERO = 0
  ONE = 1


class AutoTest(absltest.TestCase):

  def test_works_fn(self):
    # pylint: disable=unused-argument
    def my_function(
        str_: str = 'foo',
        int_: int = 10,
        float_: float = 1.0,
        bool_: bool = False,
        list_int: list[int] = [1, 2, 3],
        tuple_str: tuple[str] = ('foo',),  # pylint: disable=g-one-element-tuple
        variadic_tuple_str: tuple[str, ...] = ('foo', 'bar'),
        sequence_bool: Sequence[bool] = [True, False],
        optional_int: int | None = None,
        optional_float: float | None = None,
        optional_list_int: list[int] | None = None,
    ):  # pylint: disable=dangerous-default-value
      pass

    # pylint: enable=unused-argument
    expected_settings = {
        'str_': 'foo',
        'int_': 10,
        'float_': 1.0,
        'bool_': False,
        'list_int': [1, 2, 3],
        'tuple_str': ('foo',),
        'variadic_tuple_str': ('foo', 'bar'),
        'sequence_bool': [True, False],
        'optional_int': None,
        'optional_float': None,
        'optional_list_int': None,
    }
    ff_dict = ff.auto(my_function)
    self.assertEqual(expected_settings.keys(), ff_dict.keys())
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        'my_function_settings',
        flag_values,
        **ff_dict,
    )
    flag_values(('./program', ''))
    self.assertEqual(flag_holder.value, expected_settings)

  @absltest.skipIf(
      condition=sys.version_info < (3, 9),
      reason='Generics syntax for standard collections requires Python >= 3.9',
  )
  def test_works_fn_pep585(self):

    def my_function(
        list_int: list[int] = [1, 2, 3],
        tuple_str: tuple[str] = ('foo',),  # pylint: disable=g-one-element-tuple
        variadic_tuple_str: tuple[str, ...] = ('foo', 'bar'),
        optional_list_int: list[int] | None = None,
        sequence_str: Sequence[str] = ('bar', 'baz'),
    ):  # pylint: disable=dangerous-default-value
      # Unused.
      del (
          list_int,
          tuple_str,
          variadic_tuple_str,
          optional_list_int,
          sequence_str,
      )

    expected_settings = {
        'list_int': [1, 2, 3],
        'tuple_str': ('foo',),
        'variadic_tuple_str': ('foo', 'bar'),
        'optional_list_int': None,
        'sequence_str': ('bar', 'baz'),
    }
    ff_dict = ff.auto(my_function)
    self.assertEqual(expected_settings.keys(), ff_dict.keys())
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        'my_function_settings',
        flag_values,
        **ff_dict,
    )
    flag_values(('./program', ''))
    self.assertEqual(flag_holder.value, expected_settings)

  def test_works_enum_fn(self):
    # pylint: disable=unused-argument
    def my_function(
        str_: str = 'foo', int_: int = 10, enum_: MyEnum = MyEnum.ZERO
    ):
      pass

    # pylint: enable=unused-argument
    expected_settings = {
        'str_': 'foo',
        'int_': 10,
        'enum_': MyEnum.ZERO,
    }
    ff_dict = ff.auto(my_function)
    self.assertCountEqual(expected_settings, ff_dict)

  def test_works_class(self):
    class MyClass:

      # pylint: disable=unused-argument
      def __init__(
          self,
          str_: str = 'foo',
          int_: int = 10,
          float_: float = 1.0,
          bool_: bool = False,
          list_int: list[int] = [1, 2, 3],
          tuple_str: tuple[str] = ('foo',),  # pylint: disable=g-one-element-tuple
          variadic_tuple_str: tuple[str, ...] = ('foo', 'bar'),
          sequence_bool: Sequence[bool] = [True, False],
          optional_int: int | None = None,
          optional_float: float | None = None,
          optional_list_int: list[int] | None = None,
      ):  # pylint: disable=dangerous-default-value
        pass

      # pylint: enable=unused-argument

    expected_settings = {
        'str_': 'foo',
        'int_': 10,
        'float_': 1.0,
        'bool_': False,
        'list_int': [1, 2, 3],
        'tuple_str': ('foo',),
        'variadic_tuple_str': ('foo', 'bar'),
        'sequence_bool': [True, False],
        'optional_int': None,
        'optional_float': None,
        'optional_list_int': None,
    }
    ff_dict = ff.auto(MyClass)
    self.assertEqual(expected_settings.keys(), ff_dict.keys())
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        'my_class_settings',
        flag_values,
        **ff_dict,
    )
    flag_values(('./program', ''))
    self.assertEqual(flag_holder.value, expected_settings)

  @absltest.skipIf(
      condition=sys.version_info < (3, 9),
      reason='Generics syntax for standard collections requires Python >= 3.9',
  )
  def test_works_class_pep585(self):
    class MyClass:

      def __init__(
          self,
          list_int: list[int] = [1, 2, 3],
          tuple_str: tuple[str] = ('foo',),  # pylint: disable=g-one-element-tuple
          variadic_tuple_str: tuple[str, ...] = ('foo', 'bar'),
          optional_list_int: list[int] | None = None,
          sequence_str: Sequence[str] = ('bar', 'baz'),
      ):  # pylint: disable=dangerous-default-value
        # Unused.
        del (
            list_int,
            tuple_str,
            variadic_tuple_str,
            optional_list_int,
            sequence_str,
        )

    expected_settings = {
        'list_int': [1, 2, 3],
        'tuple_str': ('foo',),
        'variadic_tuple_str': ('foo', 'bar'),
        'optional_list_int': None,
        'sequence_str': ('bar', 'baz'),
    }
    ff_dict = ff.auto(MyClass)
    self.assertEqual(expected_settings.keys(), ff_dict.keys())
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        'my_class_settings',
        flag_values,
        **ff_dict,
    )
    flag_values(('./program', ''))
    self.assertEqual(flag_holder.value, expected_settings)

  def test_works_metaclass(self):
    # This replicates an issue with Sonnet v2 modules, where the constructor
    # arguments are hidden by the metaclass.
    class MyMetaclass(abc.ABCMeta):

      def __call__(cls, *args, **kwargs):
        del args, kwargs

    class MyClass(metaclass=MyMetaclass):

      def __init__(
          self, a: int = 10, b: float = 1.0, c: Sequence[int] = (1, 2, 3)
      ):
        del a, b, c

    expected = {'a': 10, 'b': 1.0, 'c': (1, 2, 3)}
    ff_dict = ff.auto(MyClass)
    self.assertEqual(ff_dict.keys(), expected.keys())

    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        'my_meta_class_settings',
        flag_values,
        **ff_dict,
    )
    flag_values(('./program', ''))
    self.assertEqual(flag_holder.value, expected)

  def test_required_item_with_no_default(self):
    def my_function(a: int, b: float = 1.0, c: Sequence[int] = (1, 2, 3)):
      del a, b, c

    items = ff.auto(my_function)
    self.assertTrue(items['a'].required)
    self.assertFalse(items['b'].required)
    self.assertFalse(items['c'].required)

  def test_error_if_missing_type_annotation(self):
    def my_function(a: int = 10, b=1.0, c: Sequence[int] = (1, 2, 3)):
      del a, b, c

    with self.assertRaisesWithLiteralMatch(
        TypeError, _auto._MISSING_TYPE_ANNOTATION.format(name='b')
    ):
      ff.auto(my_function)

  def test_error_if_unsupported_type(self):

    def my_function(
        a: int = 10, b: float = 1.0, c: Sequence[object] = (1, 2, 3)
    ):
      del a, b, c

    with self.assertRaisesRegex(
        TypeError,
        "for argument 'c'.*annotation: " + re.escape(f'{Sequence[object]!r}'),
    ):
      ff.auto(my_function)

  def test_no_error_if_nonstrict_unsupported_type(self):

    def my_function(
        a: int = 10, b: float = 1.0, c: Sequence[object] = (1, 2, 3)
    ):
      del a, b, c

    items = ff.auto(my_function, strict=False)
    self.assertSetEqual(set(items.keys()), {'a', 'b'})

  def test_no_error_if_nonstrict_no_type_annotation(self):
    def my_function(a, b: int = 3):
      del a, b

    items = ff.auto(my_function, strict=False)
    self.assertSetEqual(set(items.keys()), {'b'})

  def test_error_if_not_callable(self):
    with self.assertRaises(TypeError):
      ff.auto(3)  # pytype: disable=wrong-arg-types

  def test_supports_tuples_with_more_than_one_element(self):

    def my_function(
        three_ints: tuple[int, int, int] = (1, 2, 3),
        zero_or_more_strings: tuple[str, ...] = ('foo', 'bar'),
    ):
      del three_ints, zero_or_more_strings

    expected = {
        'three_ints': (1, 2, 3),
        'zero_or_more_strings': ('foo', 'bar'),
    }
    ff_dict = ff.auto(my_function)
    self.assertEqual(expected.keys(), ff_dict.keys())
    flag_values = flags.FlagValues()
    flag_holder = ff.DEFINE_dict(
        'my_function_settings',
        flag_values,
        **ff_dict,
    )
    flag_values(('./program', ''))
    self.assertEqual(flag_holder.value, expected)

  def test_skip_params(self):
    def my_function(a: int, b: str = 'hi'):
      del a, b

    items = ff.auto(my_function, skip_params={'b'})
    self.assertSetEqual(set(items.keys()), {'a'})

  @unittest.skipIf(
      sys.version_info < (3, 11),
      'InitVar support requires Python >= 3.11 due to'
      ' https://github.com/python/cpython/issues/88962',
  )
  def test_dataclass_init_var(self):
    @dataclasses.dataclass
    class WithInitVar:
      x: float = 0.0
      int_init_var: dataclasses.InitVar[int] = 0
      str_init_var: dataclasses.InitVar[str] = 'foo'
      tuple_init_var: dataclasses.InitVar[tuple[int]] = (1,)  # pylint: disable=g-one-element-tuple

    items = ff.auto(WithInitVar)
    self.assertSetEqual(
        set(items.keys()),
        {'x', 'int_init_var', 'str_init_var', 'tuple_init_var'},
    )


if __name__ == '__main__':
  absltest.main()
