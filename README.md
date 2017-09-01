Carton
======

If you label the boxes right, moving is a breeze!

Disclaimer
----------

Carton is still a work in progress, and contributions in the form of bug
reports or pull requests are more than welcome. However, if you do plan on
using the software as-is, be warned that the repository structure and API may
change at any point in time.

What is Carton?
---------------

Carton is a dotfiles manager. It's designed to be extensive and extensible. It
attempts to cover the most use cases with little to no dependencies. As of this
writing, Carton depends only on the Python 3 interpreter, with one exception,
macOS users need AppKit, which is installed via the `pyobjc` package.

Carton was built to allow grouping your dotfiles from all machines into a
single repository, to save the logistics headache, and allow you to most likely
store everything on a single Git repository. This takes in account that not all
machines have the same environment, and it allows you to deploy collections of
files, called "patches", only when the current machine satisfies given
conditions.
