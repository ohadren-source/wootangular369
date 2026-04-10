"""
lilypod/runtime/filter.py
Thin wrapper around core.filter.WootangularFilter.

GI;WG? — Good Intent, Will Good?
5 questions. In order. All must pass.
Real Recognize Really. The filter no benchmark passes.

Usage:
    from lilypod.runtime.filter import run_filter, THE_SHIT, BOOLSHIT, DEFER
    result = run_filter(candidate)
"""

from core.filter import WootangularFilter, FilterResult

# BOOL++ result constants — same names, same values, both substrates
THE_SHIT = FilterResult.THE_SHIT   # "the_shit"  — BIND. Real recognize really.
BOOLSHIT = FilterResult.BOOLSHIT   # "boolshit"  — JRAGONATE. Logged.
DEFER    = FilterResult.DEFER      # "defer"     — Door stays open.

_filter = WootangularFilter()


def run_filter(candidate: dict) -> dict:
    """
    Run the GI;WG? filter on a candidate dict.
    5 questions. In order. All must pass.

    Returns dict with keys: result, failed_at, justification, questions.
    result is one of: THE_SHIT / BOOLSHIT / DEFER.
    """
    return _filter.run(candidate)
