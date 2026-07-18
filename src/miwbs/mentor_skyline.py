"""SKYLINE-RESULTS / ECHO report chrome (FOL-001 leaf 2) — mentor pack voice."""

from __future__ import annotations


def skyline_fail(errmsg: str, echo: str) -> str:
    """
    mint> …

      SKYLINE-RESULTS:  VEN MINT FAILED
      ERRMSG: …

    ### E C H O : …
    """
    err = (errmsg or "Unknown error").strip()
    ech = (echo or "").strip()
    lines = [
        "  SKYLINE-RESULTS:  VEN MINT FAILED",
        f"  ERRMSG: {err}",
        "",
        f"### E C H O : {ech}" if ech else "### E C H O :",
    ]
    return "\n".join(lines)


def skyline_ok(*, issued: str, echo: str) -> str:
    """
      SKYLINE-RESULTS:  VEN MINT SUCCESSFUL
      VEN-ID issued:    PVT-0001

    ### E C H O : …
    """
    vid = (issued or "—").strip()
    ech = (echo or "").strip()
    lines = [
        "  SKYLINE-RESULTS:  VEN MINT SUCCESSFUL",
        f"  VEN-ID issued:    {vid}",
        "",
        f"### E C H O : {ech}" if ech else "### E C H O :",
    ]
    return "\n".join(lines)
