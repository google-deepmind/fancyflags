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
"""Install script for fancyflags."""

from importlib import util
import setuptools


def _get_version():
  spec = util.spec_from_file_location('_metadata', 'fancyflags/_metadata.py')
  mod = util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  return mod.__version__


setuptools.setup(
    name='fancyflags',
    version=_get_version(),
    description='A Python library for defining dictionary-valued flags.',
    author='DeepMind',
    license='Apache License, Version 2.0',
    packages=setuptools.find_packages(),
    install_requires=['absl-py'],
    tests_require=['pytest'],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
)
