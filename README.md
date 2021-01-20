# fancyflags

<!--* freshness: { owner: 'ydoron' reviewed: '2021-01-19' } *-->

TIP: Already a fancyflags user? Check out our [usage tips](#tips)!

Defines a flat or nested dict flag, with familiar "dot" overrides for fields.
These dict flags:

*   Can be overridden with “dot” notation, similar to
    [`config_flags`](https://github.com/google/ml_collections#usage).
*   Are typed and validated like standard flags, catching errors before they
    propagate into your program.
*   Are easy to mix and match with standard flags, without adding extra files to
    your codebase.
*   Can be unpacked into constructor/function calls, e.g.
    `replay(**FLAGS.replay)`.

## Quickstart

Say we have a class `Replay`, with arguments `capacity`, `priority_exponent` and
others. We can define a corresponding dict flag in our main script

```python
import fancyflags as ff

ff.DEFINE_dict(
    "replay",
    capacity=ff.Integer(int(1e6), "Maximum replay capacity."),
    priority_exponent=ff.Float(0.6, "Priority exponent."),
    importance_sampling_exponent=ff.Float(0.4, "Importance sampling exponent."),
    removal_strategy=ff.Enum("fifo", ["rand", "fifo", "max_value"],
                             "The prioritization method for replay removal.")
)
```

and `**unpack` the values directly into the `Replay` constructor

```python
replay = replay_lib.Replay(**FLAGS.replay)
```

i.e. this creates a flag named `replay`, with a default value of

```python
{
    "capacity": 1000000,
    "priority_exponent": 0.6,
    "importance_sampling_exponent": 0.4,
    "removal_strategy": "fifo",
}
```

and, for each item in the dict, a dot-delimited flag that can be overridden from
the command line. In this example the generated command line flags would be

```
replay.capacity
replay.priority_exponent
replay.importance_sampling_exponent
replay.removal_strategy
```

Overriding one of these flags from the command line updates the corresponding
entry in the dict flag (accessed via `FLAGS.replay`). For example, the override

```shell
python script_name.py -- --replay.capacity=2000 --replay.removal_strategy=max_value
```

sets the values in `FLAGS.replay` to

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
ff.DEFINE_dict(
    "replay",
    capacity=ff.Integer(int(1e6), "Maximum replay capacity."),
    exponents=dict(
        priority=ff.Float(0.6, "Priority exponent."),
        importance_sampling=ff.Float(0.4, "Importance sampling exponent."),
    )
)
```

In this example, the default value of the `replay` flag would be

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

## Defining a dict flag from a function or constructor.

fancyflags can generate a dict flag automatically based on a function or class
definition, with `ff.auto`. This will work if:

1.  The function or class constructor has type annotations.
1.  Each argument has a default value.
1.  The arguments are relatively simple types.

For example, if we had a `Replay` class that satisfied these constraints, we
could automatically generate a set of `replay.*` flags with:

```python
ff.DEFINE_dict('replay', **ff.auto(replay_lib.Replay))
```

## Notes on using `flagsaver`

abseil-py's [flagsaver](https://github.com/abseil/abseil-py/blob/master/absl/testing/flagsaver.py)
module is useful for safely overriding flag values in test code. However, since
it uses keyword arguments, overriding a flag with a dot in its name will result
in a `SyntaxError`:

```python
# Invalid Python syntax.
flagsaver.flagsaver(replay.capacity=100, replay.priority_exponent=0.5)
```

To work around this, first create a dictionary and then `**` unpack it:

```python
# Valid Python syntax.
flagsaver.flagsaver(**{'replay.capacity': 100, 'replay.priority_exponent': 0.5})
```

Also watch out for this gotcha if setting dict flag values inside a `flagsaver`
context. (If possible we recommend avoiding setting the flag values inside the
context altogether, and passing the override values directly to the `flagsaver`
function as above.)

This syntax does not work properly.

```python
with flagsaver.flagsaver():
  FLAGS.replay["capacity"] = 100
# The original value will not be restored correctly.
```

This syntax _does_ work properly.

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
`ff.MultiString`    | `ff.DEFINE_multi_string`

### Defining a new `ff.Item`

Given a `flags.ArgumentParser`, we can define an `ff.Item` in a few lines of
code.

For example, if we wanted to define an `ff.Item` that corresponded to
`flags.DEFINE_spaceseplist`, we would look for the parser that this definition
uses, and write:

```python
class SpaceSepList(ff.Item):

  def __init__(self, help_string)
    parser = flags.WhitespaceSeparatedListParser()
    super(SpaceSepList, self).__init__(default, help_string, parser)

```

Note that custom `ff.Item` definitions do not _need_ to be added to the
fancyflags library to work.

### Direct syntax

It's also possible to skip the `DEFINE_dict` call:

```python
replay_defs = dict(
    capacity=ff.Integer(int(1e6), "Maximum replay capacity."),
    priority_exponent=ff.Float(0.6, "Priority exponent."),
    importance_sampling_exponent=ff.Float(0.4, "Importance sampling exponent."),
    removal_strategy=ff.Enum("fifo", ["rand", "fifo", "max_value"],
                             "The prioritization method for replay removal.")
)

REPLAY = ff.define_flags("replay", replay_defs)
```

This example only defines the dot-delimited flags and does _not_ define a
dict-flag. The returned variable `REPLAY` holds the default values. Any
overrides to the dot-delimited flags will also update the corresponding item in
`REPLAY`.

### Tips

Any direct access, e.g. `FLAGS.dict_flag['item']` is an indication that you
might want to tweak your flag arrangement:

*   Try to align dict flags with constructors or functions, so that you always
    `**unpack` the items into their corresponding constructor or function.
*   If you need to access an item in a dict directly, e.g. because its value is
    used in multiple places, it likely makes sense to move that item to its own
    plain flag.
*   Check to see if you should have `**unpacked` somewhere up the call-stack,
    and convert function "config" args to individual items if needed.
*   Don't group things under a dict flag just because they're thematically
    related, and don't have one catch-all dict flag. Instead define individual
    dict flags to match the constructor or function calls as needed.
