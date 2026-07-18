"""
VEN Mentor — hidden production machinery inside MIWBS.

Not first-stage face verbs. Import when a story beat needs form production:

    from miwbs.mentor_workshop import Workshop
    from miwbs.mentor_skyline import skyline_ok, skyline_fail

Doctrine:
  - World DB on Day of Days holds only SELF (concept prime) until you produce more.
  - Types are not ambient KINDS furniture — they are taught in the workshop
    (and later may derive from primes).
  - Primes → type is the long game; this module is the workshop side channel.
"""

from .mentor_skyline import skyline_fail, skyline_ok
from .mentor_workshop import Workshop, parse_flags

__all__ = [
    "Workshop",
    "parse_flags",
    "skyline_ok",
    "skyline_fail",
]
