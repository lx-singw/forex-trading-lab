"""Explicit unavailable market study and default-off demo boundary.

No MT5 SDK imports or order-submission implementation. The native port is a future
dependency, so these checks cannot certify an actual connected account.
"""
from itertools import product


def study_status():
    reasons = ["No eligible source/run manifest assigned", "No qualified D1/H4/H1 history",
               "No verified historical execution/cost context", "Full strategy acceptance incomplete"]
    return {"status": "UNAVAILABLE", "reasons": reasons,
            "cells": [{"candidate":c,"profile":p,"partition":s,"status":"UNAVAILABLE","returns":None}
                      for c,p,s in product(("EW_FULL_V1","EWPB_D124","T12_D","CASH"),
                                           ("base","adverse"),("development","validation"))]}


class DemoBoundary:
    """Fail-closed inactive boundary, with no secret/account data serialization."""
    def __init__(self):
        self.enabled = False
        self.reconciled = False
        self.pending = False
        self.halted = False

    def check_actual_mode(self, mode, identity_unchanged):
        # ACCOUNT_TRADE_MODE_DEMO=0, CONTEST=1, REAL=2. Caller must query native
        # ACCOUNT_TRADE_MODE; a server name or fixture cannot prove native mode.
        if type(mode) is not int or mode != 0 or identity_unchanged is not True:
            self.halted = True
            raise ValueError("actual DEMO/continuity required")

    def submission_status(self):
        return {"available":False,"reason":"native adapter and qualified evidence unavailable",
                "pending_requires_reconciliation":self.pending,"halted":self.halted}

    def record_ambiguous_outcome(self):
        self.pending, self.reconciled, self.halted = True, False, True

    def request_retry(self):
        raise ValueError("no submission or blind retry available")
