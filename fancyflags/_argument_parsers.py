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
import datetime
import enum
import re

from absl import flags


BASIC_SEQUENCE_TYPES = (list, tuple)

# We assume a sequence contains only these types. Python has no primitive types.
SIMPLE_TYPES = (bool, float, int, str)

NOT_A_SIMPLE_TYPE_MESSAGE = """
Input list contains unsupported type {{}}, however each element in a sequence
must be a {} or {}.
""".format(
    ", ".join(type_.__name__ for type_ in SIMPLE_TYPES[:-1]),
    SIMPLE_TYPES[-1].__name__,
)

_EMPTY_STRING_ERROR_MESSAGE = """
Empty sequences should be given explicitly as [] or () and not as an empty
string"""

# Maximum depth for nested structures to prevent excessive recursion.
_MAX_DEPTH = 10

# Maximum number of elements in a sequence to prevent memory issues.
_MAX_SEQUENCE_LENGTH = 10000

# Maximum string length to prevent extremely large inputs.
_MAX_STRING_LENGTH = 100000


def _validate_string_input(argument):
  """Validates string input before parsing.

  Args:
    argument: The string to validate.

  Raises:
    ValueError: If validation fails.
  """
  if len(argument) > _MAX_STRING_LENGTH:
    raise ValueError(
        "Input string too long ({} chars). Maximum allowed: {}".format(
            len(argument), _MAX_STRING_LENGTH)
    )

  # Check for potentially dangerous patterns.
  dangerous_patterns = [
      "__import__",
      "exec", 
      "eval",
      "open",
      "file",
      "input",
      "raw_input"
  ]

  for pattern in dangerous_patterns:
    if pattern in argument:
      raise ValueError(
          "Input contains potentially unsafe pattern: '{}'".format(pattern)
      )


def _validate_sequence_depth(obj, current_depth=0):
  """Validates sequence nesting depth.

  Args:
    obj: The object to check.
    current_depth: Current nesting depth.

  Raises:
    ValueError: If depth exceeds maximum.
  """
  if current_depth > _MAX_DEPTH:
    raise ValueError(
        "Sequence nesting too deep (depth > {}). "
        "This could indicate malformed input.".format(_MAX_DEPTH)
    )

  if isinstance(obj, BASIC_SEQUENCE_TYPES):
    if len(obj) > _MAX_SEQUENCE_LENGTH:
      raise ValueError(
          "Sequence too long ({} elements). Maximum allowed: {}".format(
              len(obj), _MAX_SEQUENCE_LENGTH)
      )

    for item in obj:
      _validate_sequence_depth(item, current_depth + 1)


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
      ValueError: If the input is an empty string or validation fails.
    """
    if argument is None:
      return []
    elif isinstance(argument, BASIC_SEQUENCE_TYPES):
      result = argument[:]
      # Validate existing sequences too
      _validate_sequence_depth(result)
    elif isinstance(argument, str):
      if not argument:
        raise ValueError(_EMPTY_STRING_ERROR_MESSAGE)

      # Enhanced string validation
      _validate_string_input(argument)

      try:
        result = ast.literal_eval(argument)
      except (ValueError, SyntaxError) as e:
        raise ValueError(
            "Failed to parse \"{}\" as a python literal: {}".format(
                argument, e)
        ) from e

      if not isinstance(result, BASIC_SEQUENCE_TYPES):
        raise TypeError(
            "Input string should represent a list or tuple, however it "
            "evaluated as a {}.".format(type(result).__name__)
        )

      # Validate the parsed result
      _validate_sequence_depth(result)
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
      ValueError: Raised if an argument element didn't match anything in enum
        or validation fails.
    """
    if arguments is None:
      return []
    elif isinstance(arguments, BASIC_SEQUENCE_TYPES):
      result = arguments[:]
      _validate_sequence_depth(result)
    elif isinstance(arguments, enum.EnumMeta):
      result = arguments
    elif isinstance(arguments, str):
      # Enhanced string validation
      _validate_string_input(arguments)

      try:
        result = ast.literal_eval(arguments)
      except (ValueError, SyntaxError) as e:
        raise ValueError(
            "Failed to parse \"{}\" as a python literal: {}".format(
                arguments, e)
        ) from e

      if not isinstance(result, BASIC_SEQUENCE_TYPES):
        raise TypeError(
            "Input string should represent a list or tuple, however it "
            "evaluated as a {}.".format(type(result).__name__)
        )

      _validate_sequence_depth(result)
    else:
      raise TypeError("Unsupported type {}.".format(type(arguments).__name__))

    if not all(arg in self.enum_values for arg in result):
      raise ValueError(
          "Argument values should be one of <{}>".format(
              "|".join(str(value) for value in self.enum_values)
          )
      )
    else:
      return result

  def flag_type(self):
    return "multi enum"


class PossiblyNaiveDatetimeParser(flags.ArgumentParser):
  """Parses an ISO format datetime string into a datetime.datetime."""

  def parse(self, value) -> datetime.datetime:
    if isinstance(value, datetime.datetime):
      return value

    # Enhanced input validation for datetime strings
    if not isinstance(value, str):
      raise TypeError("Expected string or datetime, got {}".format(
          type(value).__name__))

    if len(value.strip()) == 0:
      raise ValueError("Empty datetime string not allowed")

    if len(value) > 50:  # Reasonable limit for ISO datetime strings
      raise ValueError("Datetime string too long: {} characters".format(
          len(value)))

    # Handle ambiguous cases such as 2000-01-01+01:00, where the part after the
    # '+' sign looks like timezone info but is actually just the time.
    if value[10:11] in ("+", "-"):
      # plus/minus as separator between date and time (can be any character)
      raise ValueError(
          "datetime value {!r} uses {!r} as separator "
          "between date and time (excluded to avoid confusion between "
          "time and offset). Use any other character instead, e.g. "
          "{!r}".format(value, value[10], value[:10] + 'T' + value[11:])
      )

    try:
      return datetime.datetime.fromisoformat(value)
    except ValueError as e:
      raise ValueError("invalid datetime value {!r}: {}".format(value, e)) from None

  def flag_type(self):
    return "datetime.datetime"


class PossiblyNaiveTimeDeltaParser(flags.ArgumentParser):
  """Parses a string into a datetime.timedelta.

  Accepts a string in human-readable format, e.g.

  '1d 5h 2s' or '3w 10ms'

  where the units range from weeks ('w') to microseconds ('us').
  """

  def __init__(self):
    super().__init__()
    units = [
        ("weeks", "w"),
        ("days", "d"),
        ("hours", "h"),
        ("minutes", "m"),
        ("seconds", "s"),
        ("milliseconds", "ms"),
        ("microseconds", "us"),
    ]
    groups = []
    for name, unit in units:
      groups.append("((?P<{}>\\d+)\\s*{}\\s*)?".format(name, unit))
    self._re = re.compile("".join(groups))

  def parse(self, value) -> datetime.timedelta:
    if isinstance(value, datetime.timedelta):
      return value

    # Enhanced input validation for timedelta strings
    if not isinstance(value, str):
      raise TypeError("Expected string or timedelta, got {}".format(
          type(value).__name__))

    if len(value.strip()) == 0:
      raise ValueError("Empty timedelta string not allowed")

    if len(value) > 100:  # Reasonable limit for timedelta strings
      raise ValueError("Timedelta string too long: {} characters".format(
          len(value)))

    match = self._re.fullmatch(value.strip())
    if not match:
      raise ValueError("invalid timedelta value {!r}".format(value))

    # Map back to kwargs that datetime.timedelta understands.
    kwargs = {k: int(v) for k, v in match.groupdict().items() if v}

    # Validate the resulting timedelta isn't excessive
    try:
      result = datetime.timedelta(**kwargs)
      # Check if the timedelta is reasonable (less than 1000 years)
      if abs(result.total_seconds()) > 365.25 * 24 * 3600 * 1000:
        raise ValueError("Timedelta too large: {}".format(result))
      return result
    except OverflowError as e:
      raise ValueError("Timedelta values too large: {}".format(e)) from None

  def flag_type(self):
    return "datetime.timedelta"
