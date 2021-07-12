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
"""Argument parsers."""

import ast
import enum

from absl import flags

BASIC_SEQUENCE_TYPES = (list, tuple)

# We assume a sequence contains only these types. Python has no primitive types.
SIMPLE_TYPES = (bool, float, int, str)

NOT_A_SIMPLE_TYPE_MESSAGE = """
Input list contains unsupported type {{}}, however each element in a sequence
must be a {} or {}.
""".format(", ".join(type_.__name__ for type_ in SIMPLE_TYPES[:-1]),
           SIMPLE_TYPES[-1].__name__)

_EMPTY_STRING_ERROR_MESSAGE = """
Empty sequences should be given explicitly as [] or () and not as an empty
string"""


class SequenceParser(flags.ArgumentParser):
  """Parser of simple sequences containing simple Python values."""

  def parse(self, argument):
    """Parses the argument as a string-formatted sequence (list or tuple).

    Essentially reverses the result of `"{}".format(a_sequence)`

    Args:
      argument: The flag value as a string, list, tuple or None. Examples of
        valid input strings are `"(1,2,3)"` and `[0.2, 0.3, 1.0]`.

    Returns:
      The parsed sequence.

    Raises:
      TypeError: If the input type is not supported, or if the input is not a
        flat sequence that only contains simple Python values.
      ValueError: If the input is an empty string.
    """
    if argument is None:
      return []
    elif isinstance(argument, BASIC_SEQUENCE_TYPES):
      result = argument[:]
    elif isinstance(argument, str):
      if not argument:
        raise ValueError(_EMPTY_STRING_ERROR_MESSAGE)
      result = ast.literal_eval(argument)
      if not isinstance(result, BASIC_SEQUENCE_TYPES):
        raise TypeError(
            "Input string should represent a list or tuple, however it "
            "evaluated as a {}.".format(type(result).__name__))
    else:
      raise TypeError("Unsupported type {}.".format(type(argument).__name__))

    # Make sure the result is a flat sequence of simple types.
    for value in result:
      if not isinstance(value, SIMPLE_TYPES):
        raise TypeError(NOT_A_SIMPLE_TYPE_MESSAGE.format(type(value).__name__))

    return result

  def flag_type(self):
    """See base class."""
    return "sequence"


class MultiEnumParser(flags.ArgumentParser):
  """Parser of multiple enum values.

  This parser allows the flag values to be sequences of any type, unlike
  flags.DEFINE_multi_enum which only allows strings.
  """

  def __init__(self, enum_values):
    if not enum_values:
      raise ValueError("enum_values cannot be empty")
    if any(not value for value in enum_values):
      raise ValueError("No element of enum_values can be empty")

    super().__init__()
    self.enum_values = enum_values

  def parse(self, arguments):
    """Determines validity of arguments.

    Args:
      arguments: list, tuple, or enum of flag values. Each value may be any type


    Returns:
      The input list, tuple or enum if valid.

    Raises:
      TypeError: If the input type is not supported.
      ValueError: Raised if an argument element didn't match anything in enum.
    """
    if arguments is None:
      return []
    elif isinstance(arguments, BASIC_SEQUENCE_TYPES):
      result = arguments[:]
    elif isinstance(arguments, enum.EnumMeta):
      result = arguments
    elif isinstance(arguments, str):
      result = ast.literal_eval(arguments)

      if not isinstance(result, BASIC_SEQUENCE_TYPES):
        raise TypeError(
            "Input string should represent a list or tuple, however it "
            "evaluated as a {}.".format(type(result).__name__))
    else:
      raise TypeError("Unsupported type {}.".format(type(arguments).__name__))

    if not all(arg in self.enum_values for arg in result):
      raise ValueError("Argument values should be one of <{}>".format(
          "|".join(str(value) for value in self.enum_values)))
    else:
      return result

  def flag_type(self):
    return "multi enum"
