# Changelog

All significant changes to this project will be documented here.

## [Unreleased]

## [1.3]

Release date: 2025-07-04

*   Move from `setup.py` and `requirements.txt` to `pyproject.toml`.
*   Added Python 3.12 and 3.13 support.
*   Dropped Python 3.9 support.
*   Made `_auto_from_value` public as `ff.auto_from_value`.
*   Dropped Python 3.8 support.
*   Added `ff.DEFINE_from_instance`.

## [1.2]

Release date: 2023-07-04

*   Added support for DateTime flag type for `ff.DEFINE_auto`.
*   Added option to skip defining flags for a subset of arguments in `ff.auto`.
*   Added support for functions or constructors without default arguments in
    `ff.DEFINE_auto`.
*   Added a `case_sensitive` argument to `ff.EnumClass` and set to `False` by
    default, to match the
    [corresponding change](https://github.com/abseil/abseil-py/commit/eb94d9587c6f2eade9617237fb6bba1364226a3b)
    in `DEFINE_enum_class`
*   Added support for variadic tuples in `ff.DEFINE_auto`.
*   Added support for `--foo`/`--nofoo` syntax for passing boolean flags, made
    this the default way of serializing such flags.
*   Dropped Python 3.7 support.
*   Added Python 3.11 support.

## [1.1]

Release date: 2021-11-27

*   Made help strings optional for all `Item`s and `MultiItem`s.
*   Added `ff.DEFINE_auto`.
*   Dropped Python 3.6 support.
*   Added Python 3.10 support.
*   Added/improved type hints throughout.

## [1.0]

Release date: 2021-02-08

*   Initial release.

[Unreleased]: https://github.com/deepmind/fancyflags/compare/v1.3...HEAD
[1.3]: https://github.com/deepmind/fancyflags/compare/v1.2...v1.3
[1.2]: https://github.com/deepmind/fancyflags/compare/v1.1...v1.2
[1.1]: https://github.com/deepmind/fancyflags/compare/v1.0...v1.1
[1.0]: https://github.com/deepmind/fancyflags/releases/tag/v1.0
