"""Shared pytest setup.

Some tests import scripts that live in BuildStream `local` source
directories (for example files/kde-linux-system/generate-initramfs/). Python
would write a `__pycache__` directory beside them. BuildStream stages the
whole directory, so that changes the cache key of the element and of
everything that depends on it, and a local build then misses the cache that
`just bootstrap-cache` seeded (tuna-os/tromso#539). Never write bytecode.
"""

import sys

sys.dont_write_bytecode = True
