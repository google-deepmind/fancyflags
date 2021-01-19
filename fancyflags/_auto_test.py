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

import abc
from typing import List, Optional, Sequence

from absl import flags
from absl.testing import absltest
import fancyflags as ff

FLAGS = flags.FLAGS


class AutoTest(absltest.TestCase):

  def test_works_fn(self):

    # pylint: disable=unused-argument
    def my_function(
        a: int = 10,
        b: float = 1.0,
        c: List[int] = [1, 2, 3],
        d: Optional[int] = None,
        e: Optional[float] = None,
        f: Optional[List[int]] = None,
    ):  # pylint: disable=dangerous-default-value
      pass

    # pylint: enable=unused-argument

    ff_dict = ff.auto(my_function)
    self.assertEqual(list('abcdef'), list(ff_dict))

    ff.DEFINE_dict('my_function_settings', **ff_dict)
    self.assertEqual(FLAGS.my_function_settings['a'], 10)
    self.assertEqual(FLAGS.my_function_settings['b'], 1.0)
    self.assertEqual(FLAGS.my_function_settings['c'], [1, 2, 3])
    self.assertIsNone(FLAGS.my_function_settings['d'])
    self.assertIsNone(FLAGS.my_function_settings['e'])
    self.assertIsNone(FLAGS.my_function_settings['f'])

  def test_works_class(self):

    class MyClass:

      # pylint: disable=unused-argument
      def __init__(
          self,
          a: int = 10,
          b: float = 1.0,
          c: List[int] = [1, 2, 3],
          d: Optional[int] = None,
          e: Optional[float] = None,
          f: Optional[List[int]] = None,
      ):  # pylint: disable=dangerous-default-value
        pass

      # pylint: enable=unused-argument

    ff_dict = ff.auto(MyClass)
    self.assertEqual(list('abcdef'), list(ff_dict))

    ff.DEFINE_dict('my_class_settings', **ff_dict)
    self.assertEqual(FLAGS.my_class_settings['a'], 10)
    self.assertEqual(FLAGS.my_class_settings['b'], 1.0)
    self.assertEqual(FLAGS.my_class_settings['c'], [1, 2, 3])
    self.assertIsNone(FLAGS.my_class_settings['e'])
    self.assertIsNone(FLAGS.my_class_settings['d'])
    self.assertIsNone(FLAGS.my_class_settings['f'])

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

  def test_fails_default(self):
    def my_function(a: int, b: float = 1.0, c: List[int] = [1, 2, 3]):  # pylint: disable=dangerous-default-value
      del a
      del b
      del c

    with self.assertRaises(ValueError):
      ff.auto(my_function)

  def test_fails_types(self):
    def my_function(a: int = 10, b=1.0, c: List[int] = [1, 2, 3]):  # pylint: disable=dangerous-default-value
      del a
      del b
      del c

    with self.assertRaises(TypeError):
      ff.auto(my_function)


if __name__ == '__main__':
  absltest.main()
