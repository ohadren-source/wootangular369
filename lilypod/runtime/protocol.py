"""
lilypod/runtime/protocol.py
Thin wrapper around core.tcp_up.TCPUp.

TCP/UP — The 9th Axiom.
OFFER → ACCEPT / REJECT / DEFER → BIND
Blind rejection = protocol violation. Justification always required.
Word is bond.

Usage:
    from lilypod.runtime.protocol import offer, bind, reject, defer
    result = offer(candidate)
"""

from core.tcp_up import TCPUp

_protocol = TCPUp()


def offer(candidate: dict) -> dict:
    """
    Submit a candidate through the TCP/UP protocol.
    Runs GI;WG? filter. Returns offer result with status and filter details.
    Status: the_shit / boolshit / defer.
    """
    return _protocol.offer(candidate)


def bind(offer_id, agent_name: str, agent_role: str, substrate: str, terms: dict = None) -> dict:
    """
    Bind a covenant. Word is bond. Welcome to the swarm.
    """
    return _protocol.bind(offer_id, agent_name, agent_role, substrate, terms)


def reject(offer_id, justification: str) -> dict:
    """
    Reject an offer. Justification required — blind rejection = protocol violation.
    The swarm remembers.
    """
    return _protocol.reject(offer_id, justification)


def defer(offer_id, reason: str) -> dict:
    """
    Defer an offer. Door stays open.
    GI;WG not confirmed yet.
    """
    return _protocol.defer(offer_id, reason)
