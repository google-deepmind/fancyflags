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
import copy
import dataclasses
import sys
from typing import Any, Callable, Mapping, Sequence
import unittest

from absl import flags
from absl.testing import absltest
from fancyflags import _define_auto
from fancyflags import _flags


@dataclasses.dataclass
class Point:
  x: float = 0.0
  y: float = 0.0
  label: str = ''
  enable: bool = False


@dataclasses.dataclass
class NestedDataClass:
  inner: Point = dataclasses.field(default_factory=Point)
  some_attr: int = 3


@dataclasses.dataclass
class HasUnsupportedField:
  f: Callable[[], int] = lambda: 0


@dataclasses.dataclass
class NestedWithDict:
  point: Point = dataclasses.field(default_factory=Point)
  mapping: Mapping[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class WithInitFalseAndInitValue:
  x: float = 0.0
  y: float = 0.0
  # This tests that we do not skip defining flags for an InitVar.
  init_var: dataclasses.InitVar[int] = 0
  init_var_holder: int = dataclasses.field(init=False, repr=False, default=0)
  # This tests that we correctly skip defining flags for fields with init=False.
  ignored: bool = dataclasses.field(init=False, repr=False, default=False)

  def __post_init__(self, init_var: int):
    self.init_var_holder = init_var


def greet(greeting: str = 'Hello', targets: Sequence[str] = ('world',)) -> str:
  return greeting + ' ' + ', '.join(targets)  # pytype: disable=unsupported-operands


class DefineAutoTest(absltest.TestCase):

  def test_dataclass(self):
    flag_values = flags.FlagValues()
    flag_holder = _define_auto.DEFINE_auto(
        'point', Point, flag_values=flag_values
    )
    flag_values((
        './program',
        '--point.x=2.0',
        '--point.y=-1.5',
        '--point.label=p',
        '--nopoint.enable',
    ))
    expected = Point(2.0, -1.5, 'p', False)
    self.assertEqual(expected, flag_holder.value())

  def test_dataclass_nodefaults(self):
    # Given a class constructor with non-default (required) argument(s)...

    @dataclasses.dataclass
    class MySettings:
      foo: str
      bar: int = 3

    # If we define auto flags for it...
    flag_values = flags.FlagValues()
    flag_holder = _define_auto.DEFINE_auto(
        'thing', MySettings, flag_values=flag_values
    )

    # Then the corresponding flag is required: not passing it should error.
    with self.assertRaisesRegex(flags.IllegalFlagValueError, 'thing.foo'):
      flag_values(('./program', ''))

    # Passing the required flag should work as normal.
    flag_values(('./program', '--thing.foo=hello'))
    expected = MySettings('hello', 3)
    self.assertEqual(expected, flag_holder.value())

  def test_function(self):
    flag_values = flags.FlagValues()
    flag_holder = _define_auto.DEFINE_auto(
        'greet', greet, flag_values=flag_values
    )
    flag_values((
        './program',
        '--greet.greeting=Hi there',
        "--greet.targets=('Alice', 'Bob')",
    ))
    expected = 'Hi there Alice, Bob'
    self.assertEqual(expected, flag_holder.value())

  def test_override_kwargs(self):
    flag_values = flags.FlagValues()
    flag_holder = _define_auto.DEFINE_auto(
        'point', Point, flag_values=flag_values
    )
    flag_values((
        './program',
        '--point.x=2.0',
        '--point.y=-1.5',
        '--point.label=p',
        '--point.enable',
    ))
    expected = Point(3.0, -1.5, 'p', True)
    # Here we override one of the arguments.
    self.assertEqual(expected, flag_holder.value(x=3.0))

  def test_overriding_top_level_auto_flag_fails(self):
    flag_values = flags.FlagValues()
    _define_auto.DEFINE_auto('point', Point, flag_values=flag_values)
    with self.assertRaisesRegex(
        flags.IllegalFlagValueError, "Can't override an auto flag directly"
    ):
      flag_values(('./program', '--point=2.0'))

  def test_basic_serialization(self):
    flag_values = flags.FlagValues()
    _define_auto.DEFINE_auto('point', Point, flag_values=flag_values)

    # Accessing flag_holder.value would raise an error here, since flags haven't
    # been parsed yet. For consistency we access the value via flag_values
    # throughout the test, rather than through a returned `FlagHolder`.
    initial_point_value = copy.deepcopy(flag_values['point'].value())

    # Parse flags, then serialize.
    flag_values((
        './program',
        '--point.x=1.2',
        '--point.y=3.5',
        '--point.label=p',
        '--point.enable=True',
    ))

    self.assertEqual(flag_values['point'].serialize(), _flags._EMPTY)
    self.assertEqual(flag_values['point.x'].serialize(), '--point.x=1.2')
    self.assertEqual(flag_values['point.label'].serialize(), '--point.label=p')
    self.assertEqual(flag_values['point.enable'].serialize(), '--point.enable')

    parsed_point_value = copy.deepcopy(flag_values['point'].value())

    self.assertEqual(
        parsed_point_value, Point(x=1.2, y=3.5, label='p', enable=True)
    )
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
        'greet', greet, 'help string', flag_values=flag_values
    )
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
        'point', Point, help_string='custom', flag_values=flag_values
    )

    self.assertEqual(flag_values['greet'].help, f'{greet.__module__}.greet')
    self.assertEqual(flag_values['point'].help, 'custom')

  def test_manual_nostrict_overrides_no_default(self):
    # Given a function without type hints...
    def my_function(a):
      return a + 1  # pytype: disable=unsupported-operands

    # If we define an auto flag using this function in non-strict mode...
    flag_values = flags.FlagValues()
    flag_holder = _define_auto.DEFINE_auto(
        'foo', my_function, flag_values=flag_values, strict=False
    )

    # Calling the function without arguments should error.
    flag_values(('./program', ''))
    with self.assertRaises(TypeError):
      flag_holder.value()  # pytype: disable=missing-parameter

    # Calling with arguments should work fine.
    self.assertEqual(flag_holder.value(a=2), 3)  # pytype: disable=wrong-arg-types

  def test_skip_params(self):
    flag_values = flags.FlagValues()
    _define_auto.DEFINE_auto(
        'greet', greet, flag_values=flag_values, skip_params=('targets',)
    )
    self.assertNotIn('greet.targets', flag_values)

  @unittest.skipIf(
      sys.version_info < (3, 11),
      'InitVar support requires Python >= 3.11 due to'
      ' https://github.com/python/cpython/issues/88962',
  )
  def test_dataclass_with_init_false(self):
    flag_values = flags.FlagValues()
    flag_holder = _define_auto.DEFINE_auto(
        'with_init_false', WithInitFalseAndInitValue, flag_values=flag_values
    )
    flag_values((
        './program',
        '--with_init_false.x=2.0',
        '--with_init_false.y=-1.5',
        '--with_init_false.init_var=10',
    ))
    expected = WithInitFalseAndInitValue(x=2.0, y=-1.5, init_var=10)
    self.assertEqual(expected.init_var_holder, 10)
    self.assertEqual(expected, flag_holder.value())


class DefineAutoFromValueTest(absltest.TestCase):

  def test_shallow_dataclass(self):
    flag_values = flags.FlagValues()
    point = Point(y=1.0, label='p')
    flag_holder = _define_auto.DEFINE_from_instance(
        'point', point, flag_values=flag_values
    )
    flag_values(('./program', '--point.x=2.0', '--point.label=q'))
    expected = Point(2.0, 1.0, 'q')
    self.assertEqual(expected, flag_holder.value())

  def test_nested_dataclass(self):
    flag_values = flags.FlagValues()
    defaults = NestedDataClass(inner=Point(y=1.0), some_attr=2)
    flag_holder = _define_auto.DEFINE_from_instance(
        'nested', defaults, flag_values=flag_values
    )
    flag_values(('./program', '--nested.inner.x=2.0', '--nested.some_attr=4'))
    expected = NestedDataClass(some_attr=4, inner=Point(2.0, 1.0))
    self.assertEqual(expected, flag_holder.value())

  def test_nested_dataclass_with_unsupported_field(self):
    """Tests that unsupported fields (e.g. a function) are used for defaults."""
    flag_values = flags.FlagValues()
    defaults = HasUnsupportedField(f=lambda: 1)  # change from returning 0
    flag_holder = _define_auto.DEFINE_from_instance(
        'config', defaults, flag_values=flag_values
    )
    flag_values(('./program',))
    value = flag_holder.value()
    self.assertEqual(value.f(), 1)

  def test_nested_dataclass_with_mapping(self):
    flag_values = flags.FlagValues()
    defaults = NestedWithDict(
        point=Point(y=1.0),
        mapping=dict(
            p=Point(y=2.0),
            z='z',
        ),
    )
    flag_holder = _define_auto.DEFINE_from_instance(
        'nested', defaults, flag_values=flag_values
    )
    flag_values(
        ('./program', '--nested.mapping.p.x=1.0', '--nested.mapping.z=zz')
    )
    expected = NestedWithDict(
        point=Point(y=1.0), mapping=dict(p=Point(x=1.0, y=2.0), z='zz')
    )
    self.assertEqual(expected, flag_holder.value())

  @unittest.skipIf(
      sys.version_info < (3, 11),
      'InitVar support requires Python >= 3.11 due to'
      ' https://github.com/python/cpython/issues/88962',
  )
  def test_dataclass_with_init_false(self):
    flag_values = flags.FlagValues()
    defaults = WithInitFalseAndInitValue(x=1.0, y=2.0)
    flag_holder = _define_auto.DEFINE_from_instance(
        'with_init_false', defaults, flag_values=flag_values
    )
    flag_values((
        './program',
        '--with_init_false.x=2.0',
        '--with_init_false.y=-1.5',
        '--with_init_false.init_var=10',
    ))
    expected = WithInitFalseAndInitValue(x=2.0, y=-1.5, init_var=10)
    self.assertEqual(expected.init_var_holder, 10)
    self.assertEqual(expected, flag_holder.value())


if __name__ == '__main__':
  absltest.main()
