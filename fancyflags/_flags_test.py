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
"""Tests for fancyflags._flags."""

from absl import flags
from absl.testing import absltest
from fancyflags import _flags


class FlagsTest(absltest.TestCase):

  def test_update_shared_dict(self):
    # Tests that the shared dict is updated when the flag value is updated.
    shared_dict = {'a': {'b': 'value'}}
    namespace = ('a', 'b')
    flag_values = flags.FlagValues()

    flags.DEFINE_flag(
        _flags.ItemFlag(
            shared_dict,
            namespace,
            parser=flags.ArgumentParser(),
            serializer=flags.ArgumentSerializer(),
            name='a.b',
            default='bar',
            help_string='help string'),
        flag_values=flag_values)

    flag_values['a.b'].value = 'new_value'
    with self.subTest(name='setter'):
      self.assertEqual(shared_dict, {'a': {'b': 'new_value'}})

    flag_values(('./program', '--a.b=override'))
    with self.subTest(name='override_parse'):
      self.assertEqual(shared_dict, {'a': {'b': 'override'}})

  def test_update_shared_dict_multi(self):
    # Tests that the shared dict is updated when the flag value is updated.
    shared_dict = {'a': {'b': ['value']}}
    namespace = ('a', 'b')
    flag_values = flags.FlagValues()

    flags.DEFINE_flag(
        _flags.MultiItemFlag(
            shared_dict,
            namespace,
            parser=flags.ArgumentParser(),
            serializer=flags.ArgumentSerializer(),
            name='a.b',
            default=['foo', 'bar'],
            help_string='help string'),
        flag_values=flag_values)

    flag_values['a.b'].value = ['new', 'value']
    with self.subTest(name='setter'):
      self.assertEqual(shared_dict, {'a': {'b': ['new', 'value']}})

    flag_values(('./program', '--a.b=override1', '--a.b=override2'))
    with self.subTest(name='override_parse'):
      self.assertEqual(shared_dict, {'a': {'b': ['override1', 'override2']}})

if __name__ == '__main__':
  absltest.main()
