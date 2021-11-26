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
"""Tests for fancyflags._define_auto."""

import copy
import dataclasses
from typing import Sequence

from absl import flags
from absl.testing import absltest

from fancyflags import _define_auto
from fancyflags import _flags


@dataclasses.dataclass
class Point:
  x: float = 0.0
  y: float = 0.0
  label: str = ''


def greet(greeting: str = 'Hello', targets: Sequence[str] = ('world',)) -> str:
  return greeting + ' ' + ', '.join(targets)


class DefineAutoTest(absltest.TestCase):

  def test_dataclass(self):
    flag_values = flags.FlagValues()
    flag_holder = _define_auto.DEFINE_auto(
        'point', Point, flag_values=flag_values)
    flag_values(
        ('./program', '--point.x=2.0', '--point.y=-1.5', '--point.label=p'))
    expected = Point(2.0, -1.5, 'p')
    self.assertEqual(expected, flag_holder.value())

  def test_function(self):
    flag_values = flags.FlagValues()
    flag_holder = _define_auto.DEFINE_auto(
        'greet', greet, flag_values=flag_values)
    flag_values((
        './program',
        '--greet.greeting=Hi there',
        '--greet.targets=(\'Alice\', \'Bob\')',
    ))
    expected = 'Hi there Alice, Bob'
    self.assertEqual(expected, flag_holder.value())

  def test_override_kwargs(self):
    flag_values = flags.FlagValues()
    flag_holder = _define_auto.DEFINE_auto(
        'point', Point, flag_values=flag_values)
    flag_values(
        ('./program', '--point.x=2.0', '--point.y=-1.5', '--point.label=p'))
    expected = Point(3.0, -1.5, 'p')
    # Here we override one of the arguments.
    self.assertEqual(expected, flag_holder.value(x=3.0))

  def test_overriding_top_level_auto_flag_fails(self):
    flag_values = flags.FlagValues()
    _define_auto.DEFINE_auto('point', Point, flag_values=flag_values)
    with self.assertRaisesRegex(flags.IllegalFlagValueError,
                                'Can\'t override an auto flag directly'):
      flag_values(('./program', '--point=2.0'))

  def test_basic_serialization(self):
    flag_values = flags.FlagValues()
    _define_auto.DEFINE_auto('point', Point, flag_values=flag_values)

    # Accessing flag_holder.value would raise an error here, since flags haven't
    # been parsed yet. For consistency we access the value via flag_values
    # throughout the test, rather than through a returned `FlagHolder`.
    initial_point_value = copy.deepcopy(flag_values['point'].value())

    # Parse flags, then serialize.
    flag_values(
        ('./program', '--point.x=1.2', '--point.y=3.5', '--point.label=p'))

    self.assertEqual(flag_values['point'].serialize(), _flags._EMPTY)
    self.assertEqual(flag_values['point.x'].serialize(), '--point.x=1.2')
    self.assertEqual(flag_values['point.label'].serialize(), '--point.label=p')

    parsed_point_value = copy.deepcopy(flag_values['point'].value())

    self.assertEqual(parsed_point_value, Point(x=1.2, y=3.5, label='p'))
    self.assertNotEqual(parsed_point_value, initial_point_value)

    # Test a round trip.
    serialized_args = [
        flag_values[name].serialize()
        for name in flag_values
        if name.startswith('point.')
    ]

    flag_values.unparse_flags()  # Reset to defaults
    self.assertEqual(flag_values['point'].value(), initial_point_value)

    flag_values(['./program'] + serialized_args)
    self.assertEqual(flag_values['point'].value(), parsed_point_value)

  def test_disclaimed_module(self):
    flag_values = flags.FlagValues()
    _ = _define_auto.DEFINE_auto(
        'greet', greet, 'help string', flag_values=flag_values)
    defining_module = flag_values.find_module_defining_flag('greet')

    # The defining module should be the calling module, not the module where
    # the flag is defined. Otherwise the help for a module's flags will not be
    # printed unless the user uses --helpfull.
    self.assertIn('_define_auto_test', defining_module)

  def test_help_strings(self):
    flag_values = flags.FlagValues()

    # Should default to module.name, since the `greet` docstring is empty.
    _define_auto.DEFINE_auto('greet', greet, flag_values=flag_values)
    # Should use the custom help string.
    _define_auto.DEFINE_auto(
        'point', Point, help_string='custom', flag_values=flag_values)

    self.assertEqual(flag_values['greet'].help, f'{greet.__module__}.greet')
    self.assertEqual(flag_values['point'].help, 'custom')


if __name__ == '__main__':
  absltest.main()
