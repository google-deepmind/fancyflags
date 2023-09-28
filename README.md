# fancyflags

<!--* freshness: { owner: 'ydoron' reviewed: '2023-09-28' } *-->

![PyPI Python version](https://img.shields.io/pypi/pyversions/fancyflags)
![PyPI version](https://badge.fury.io/py/fancyflags.svg)

## Introduction

`fancyflags` is a Python library that extends
[`absl.flags`](https://github.com/abseil/abseil-py) with additional structured
flag types.

`fancyflags` provides flags corresponding to structures such as
[dicts](#dict-flags), [dataclasses, and (somewhat) arbitrary callables](#auto).

These flags are typed and validated like regular `absl` flags, catching errors
before they propagate into your program. To override values, users can access
familiar "dotted" flag names.

TIP: Already a `fancyflags` user? Check out our [usage tips](#tips)!

## A short note on design philosophy:

`fancyflags` promotes mixing with regular `absl` flags. In many cases a few
regular `absl` flags are all you need!

`fancyflags` does not require you to modify library code: it should only be used
in your "main" file

`fancyflags` is not a dependency injection framework, and avoids
programming-language-like power features. We prefer that users write regular
Python for wiring up their code, because it's explicit, simple to understand,
and allows static analysis tools to identify problems.

## Installation

`fancyflags` can be installed from PyPI using `pip`:

```shell
pip install fancyflags
```

It can also be installed directly from our GitHub repository:

```shell
pip install git+git://github.com/deepmind/fancyflags.git
```

or alternatively by checking out a local copy of our repository and running:

```shell
pip install /path/to/local/fancyflags/
```

## Dict flags

If we have a class `Replay`, with arguments `capacity`, `priority_exponent` and
others, we can define a corresponding dict flag in our main script

```python
import fancyflags as ff

_REPLAY_FLAG = ff.DEFINE_dict(
    "replay",
    capacity=ff.Integer(int(1e6)),
    priority_exponent=ff.Float(0.6),
    importance_sampling_exponent=ff.Float(0.4),
    removal_strategy=ff.Enum("fifo", ["rand", "fifo", "max_value"])
)
```

and `**unpack` the values directly into the `Replay` constructor

```python
replay_lib.Replay(**_REPLAY_FLAG.value)
```

`ff.DEFINE_dict` creates a flag named `replay`, with a default value of

```python
{
    "capacity": 1000000,
    "priority_exponent": 0.6,
    "importance_sampling_exponent": 0.4,
    "removal_strategy": "fifo",
}
```

For each item in the dict, `ff.DEFINE_dict` also generates a dot-delimited
"item" flag that can be overridden from the command line. In this example the
item flags would be

```
replay.capacity
replay.priority_exponent
replay.importance_sampling_exponent
replay.removal_strategy
```

Overriding an item flag from the command line updates the corresponding entry in
the dict flag. The value of the dict flag can be accessed by the return value
of `ff.DEFINE_dict` (`_REPLAY_FLAG.value` in the example above), or via the
`FLAGS.replay` attribute of the `absl.flags` module. For example, the override

```shell
python script_name.py -- --replay.capacity=2000 --replay.removal_strategy=max_value
```

sets `_REPLAY_FLAG.value` to

```python
{
    "capacity": 2000,  # <-- Overridden
    "priority_exponent": 0.6,
    "importance_sampling_exponent": 0.4,
    "removal_strategy": "max_value",  # <-- Overridden
}
```

## Nested dicts

fancyflags also supports nested dictionaries:

```python
_NESTED_REPLAY_FLAG = ff.DEFINE_dict(
    "replay",
    capacity=ff.Integer(int(1e6)),
    exponents=dict(
        priority=ff.Float(0.6),
        importance_sampling=ff.Float(0.4),
    )
)
```

In this example, `_NESTED_REPLAY_FLAG.value` would be

```python
{
    "capacity": 1000000,
    "exponents" : {
      "priority": 0.6,
      "importance_sampling": 0.4,
    }
}
```

and the generated flags would be

```
replay.capacity
replay.exponents.priority
replay.exponents.importance_sampling
```

### Help strings

fancyflags uses the item flag's name as the default help string, however this
can also be set manually:

```python
_NESTED_REPLAY_FLAG = ff.DEFINE_dict(
    "replay",
    capacity=ff.Integer(int(1e6), "Maximum size of replay buffer."),
    exponents=dict(
        priority=ff.Float(0.6),  # Help string: "replay.exponents.priority"
        importance_sampling=ff.Float(0.4, "Importance sampling coefficient."),
    )
)
```

## "Auto" flags for functions and other structures {#auto}

`fancyflags` also provides `ff.DEFINE_auto` which automatically generates a flag
declaration corresponding to the signature of a given callable. The return value
will also carry the correct type information.

For example the callable could be a constructor

```python
_REPLAY = ff.DEFINE_auto('replay', replay_lib.Replay)
```

or it could be a container type, such as a `dataclass`

```python
@dataclasses.dataclass
class DataSettings:
  dataset_name: str = 'mnist'
  split: str = 'train'
  batch_size: int = 128

# In main script.
# Exposes flags: --data.dataset_name --data.split and --data.batch_size.
_DATA_SETTINGS = ff.DEFINE_auto('data', datasets.DataSettings)

def main(argv):
  # del argv  # Unused.
  dataset = datasets.load(_DATA_SETTINGS.value())
  # ...
```

or any other callable that satisfies the `ff.auto` requirements. It's also
possible to override keyword arguments in the call to `.value()`, e.g.

```python
test_settings = _DATA_SETTINGS.value(split='test')
```

## Defining a dict flag from a function or constructor.

The function `ff.auto` returns a dictionary of `ff.Items` given a function or
constructor. This is used to build `ff.DEFINE_dict` and is also exposed in the
top-level API.

`ff.auto` can be used with `ff.DEFINE_dict` as follows:

```python
_WRITER_KWARGS = ff.DEFINE_dict('writer', **ff.auto(logging.Writer))
```
`ff.auto` may be useful for creating kwarg dictionaries in situations where
`ff.DEFINE_auto` is not suitable, for example to pass kwargs into nested
function calls.

## Auto requirements

`ff.DEFINE_auto` and `ff.auto` will work if:

1.  The function or class constructor has type annotations.
1.  Each argument has a default value.
1.  The types of the arguments are relatively simple types (`int`, `str`,
    `bool`, `float`, or sequences thereof).

## Notes on using `flagsaver`

abseil-py's [flagsaver](https://github.com/abseil/abseil-py/blob/master/absl/testing/flagsaver.py)
module is useful for safely overriding flag values in test code. Here's how to
make it work well with fancyflags.

### Making dotted names work with `flagsaver` keyword arguments

Since `flagsaver` relies on keyword arguments, overriding a flag with a dot in
its name will result in a `SyntaxError`:

```python
# Invalid Python syntax.
flagsaver.flagsaver(replay.capacity=100, replay.priority_exponent=0.5)
```

To work around this, first create a dictionary and then `**` unpack it:

```python
# Valid Python syntax.
flagsaver.flagsaver(**{'replay.capacity': 100, 'replay.priority_exponent': 0.5})
```

### Be careful when setting flag values inside a `flagsaver` context

If possible we recommend that you avoid setting the flag values inside the
context altogether, and instead pass the override values directly to the
`flagsaver` function as shown above. However, if you _do_ need to set values
inside the context, be aware of this gotcha:

This syntax does not work properly:

```python
with flagsaver.flagsaver():
  FLAGS.replay["capacity"] = 100
# The original value will not be restored correctly.
```

This syntax _does_ work properly:

```python
with flagsaver.flagsaver():
  FLAGS["replay.capacity"].value = 100
# The original value *will* be restored correctly.
```

## fancyflags in more detail

### What is an `ff.Float` or `ff.Integer`?

`ff.Float` and `ff.Integer` are both `ff.Item`s. An `ff.Item` is essentially a
mapping from a default value and a help string, to a specific type of flag.

The `ff.DEFINE_dict` function traverses its keyword arguments (and any nested
dicts) to determine the name of each flag. It calls the `.define()` method of
each `ff.Item`, passing it the name information, and the `ff.Item` then defines
the appropriate dot-delimited flag.

### What `ff.Item`s are available?

ff.Item             | Corresponding Flag
:------------------ | :------------------------------
`ff.Boolean`        | `flags.DEFINE_boolean`
`ff.Integer`        | `flags.DEFINE_integer`
`ff.Enum`           | `flags.DEFINE_enum`
`ff.EnumClass`      | `flags.DEFINE_enum_class`
`ff.Float`          | `flags.DEFINE_float`
`ff.Sequence`       | `ff.DEFINE_sequence`
`ff.String`         | `flags.DEFINE_string`
`ff.StringList`     | `flags.DEFINE_list`
`ff.MultiEnum`      | `ff.DEFINE_multi_enum`
`ff.MultiEnumClass` | `flags.DEFINE_multi_enum_class`
`ff.MultiString`    | `flags.DEFINE_multi_string`
`ff.DateTime`       | -

### Defining a new `ff.Item`

Given a `flags.ArgumentParser`, we can define an `ff.Item` in a few lines of
code.

For example, if we wanted to define an `ff.Item` that corresponded to
`flags.DEFINE_spaceseplist`, we would look for the parser that this definition
uses, and write:

```python
class SpaceSepList(ff.Item):

  def __init__(self, default, help_string)
    parser = flags.WhitespaceSeparatedListParser()
    super(SpaceSepList, self).__init__(default, help_string, parser)

```

Note that custom `ff.Item` definitions do not _need_ to be added to the
fancyflags library to work.

### Defining `Item` flags only

We also expose a `define_flags` function, which defines flags from a flat or
nested dictionary that maps names to `ff.Item`s. This function is used as part
of `ff.DEFINE_dict` and `ff.DEFINE_auto`, and may be useful for writing
extensions on top of `fancyflags`.

```python
_writer_items = dict(
    path=ff.String('/path/to/logdir', "Output directory."),
    log_every_n=ff.Integer(100, "Number of calls between writes to disk."),
)

_WRITER_KWARGS = ff.define_flags("writer", _writer_items)
```

This example defines the flags `replay.capacity` and `replay.priority_exponent`
only: does _not_ define a dict-flag. The return value (`REPLAY`) is a
dictionary that contains the default values. Any overrides to the individual
flags will also update the corresponding item in this dictionary.

### Tips

Any direct access, e.g. `_DICT_FLAG.value['item']` is an indication that you
may want to change your flag structure:

*   Try to align dict flags with constructors or functions, so that you always
    `**unpack` the items into their corresponding constructor or function.
*   If you need to access an item in a dict directly, e.g. because its value is
    used in multiple places, consider moving that item to its own plain flag.
*   Check to see if you should have `**unpacked` somewhere up the call-stack,
    and convert function "config" args to individual items if needed.
*   Don't group things under a dict flag just because they're thematically
    related, and don't have one catch-all dict flag. Instead, define individual
    dict flags to match the constructor or function calls as needed.
