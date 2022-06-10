# Changelog

All significant changes to this project will be documented here.

## [Unreleased]

*   Added support for functions or constructors without default arguments in
    `ff.DEFINE_auto`.
*   Added a `case_sensitive` argument to `ff.EnumClass` and set to `False` by
    default, to match the
    [corresponding change](https://github.com/abseil/abseil-py/commit/eb94d9587c6f2eade9617237fb6bba1364226a3b)
    in `DEFINE_enum_class`
*   Added support for variadic tuples in `ff.DEFINE_auto`.

## [1.1]

*   Made help strings optional for all `Item`s and `MultiItem`s.
*   Added `ff.DEFINE_auto`.
*   Dropped Python 3.6 support.
*   Added Python 3.10 support.
*   Added/improved type hints throughout.

## [1.0]

Release date: 2021-02-08

*   Initial release.

[Unreleased]: https://github.com/deepmind/fancyflags/compare/v1.1...HEAD
[1.1]: https://github.com/deepmind/fancyflags/compare/v1.0...v1.1
[1.0]: https://github.com/deepmind/fancyflags/releases/tag/v1.0
