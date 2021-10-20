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
"""Tests for fancyflags.auto."""

# Test that `auto` can still correctly infer parameter types when postponed
# evaluation of type annotations (PEP 563) is enabled.
from __future__ import annotations

import abc
import enum
from typing import List, Optional, Sequence, Tuple

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
        list_int: List[int] = [1, 2, 3],
        tuple_str: Tuple[str] = ('foo',),
        sequence_bool: Sequence[bool] = [True, False],
        optional_int: Optional[int] = None,
        optional_float: Optional[float] = None,
        optional_list_int: Optional[List[int]] = None,
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
        'sequence_bool': [True, False],
        'optional_int': None,
        'optional_float': None,
        'optional_list_int': None,
    }
    ff_dict = ff.auto(my_function)
    self.assertCountEqual(expected_settings, ff_dict)
    ff.DEFINE_dict('my_function_settings', **ff_dict)
    self.assertEqual(FLAGS.my_function_settings, expected_settings)

  def test_works_enum_fn(self):

    # pylint: disable=unused-argument
    def my_function(
        str_: str = 'foo',
        int_: int = 10,
        enum_: MyEnum = MyEnum.ZERO
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
          list_int: List[int] = [1, 2, 3],
          tuple_str: Tuple[str] = ('foo',),
          sequence_bool: Sequence[bool] = [True, False],
          optional_int: Optional[int] = None,
          optional_float: Optional[float] = None,
          optional_list_int: Optional[List[int]] = None,
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
        'sequence_bool': [True, False],
        'optional_int': None,
        'optional_float': None,
        'optional_list_int': None,
    }
    ff_dict = ff.auto(MyClass)
    self.assertCountEqual(expected_settings, ff_dict)
    ff.DEFINE_dict('my_class_settings', **ff_dict)
    self.assertEqual(FLAGS.my_class_settings, expected_settings)

  def test_works_metaclass(self):

    # This replicates an issue with Sonnet v2 modules, where the constructor
    # arguments are hidden by the metaclass.
    class MyMetaclass(abc.ABCMeta):

      def __call__(cls, *args, **kwargs):
        del args, kwargs

    class MyClass(metaclass=MyMetaclass):

      def __init__(self,
                   a: int = 10,
                   b: float = 1.0,
                   c: Sequence[int] = (1, 2, 3)):
        del a, b, c

    ff_dict = ff.auto(MyClass)
    self.assertEqual(['a', 'b', 'c'], list(ff_dict))

    ff.DEFINE_dict('my_meta_class_settings', **ff_dict)
    self.assertEqual(FLAGS.my_meta_class_settings['a'], 10)
    self.assertEqual(FLAGS.my_meta_class_settings['b'], 1.0)
    self.assertEqual(FLAGS.my_meta_class_settings['c'], (1, 2, 3))

  def test_error_if_missing_default_value(self):
    def my_function(a: int, b: float = 1.0, c: Sequence[int] = (1, 2, 3)):
      del a, b, c

    with self.assertRaisesWithLiteralMatch(
        ValueError, _auto._MISSING_DEFAULT_VALUE.format(name='a')):
      ff.auto(my_function)

  def test_error_if_missing_type_annotation(self):
    def my_function(a: int = 10, b=1.0, c: Sequence[int] = (1, 2, 3)):
      del a, b, c

    with self.assertRaisesWithLiteralMatch(
        TypeError, _auto._MISSING_TYPE_ANNOTATION.format(name='b')):
      ff.auto(my_function)

  def test_error_if_unsupported_type(self):

    def my_function(a: int = 10,
                    b: float = 1.0,
                    c: Sequence[object] = (1, 2, 3)):
      del a, b, c

    with self.assertRaisesWithLiteralMatch(
        TypeError,
        _auto._UNSUPPORTED_ARGUMENT_TYPE.format(
            name='c', annotation=Sequence[object])):
      ff.auto(my_function)

  def test_no_error_if_nonstrict_unsupported_type(self):

    def my_function(a: int = 10,
                    b: float = 1.0,
                    c: Sequence[object] = (1, 2, 3)):
      del a, b, c

    return_dict = ff.auto(my_function, strict=False)
    self.assertSetEqual(set(return_dict.keys()), {'a', 'b'})

  def test_error_if_not_callable(self):
    with self.assertRaises(TypeError):
      ff.auto(3)  # pytype: disable=wrong-arg-types

  # TODO(b/178129474): Improve support for typing.Sequence subtypes.
  @absltest.expectedFailure
  def test_supports_tuples_with_more_than_one_element(self):

    def my_function(three_ints: Tuple[int, int, int] = (1, 2, 3),
                    zero_or_more_strings: Tuple[str, ...] = ('foo', 'bar')):
      del three_ints, zero_or_more_strings
    expected_settings = {
        'three_ints': (1, 2, 3),
        'zero_or_more_strings': ('foo', 'bar'),
    }
    ff_dict = ff.auto(my_function)
    self.assertCountEqual(expected_settings, ff_dict)
    ff.DEFINE_dict('my_function_settings', **ff_dict)
    self.assertEqual(FLAGS.my_function_settings, expected_settings)

if __name__ == '__main__':
  absltest.main()
