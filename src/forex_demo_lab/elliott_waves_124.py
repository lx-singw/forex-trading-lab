"""Causal invented close-swing observations; no account, fills or order interface."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib

from . import daily_features_118 as daily

VERSION = "FXDL_EW124_V1"
CANDIDATE = "EWPB_D124"
CONFIG_SHA256 = "f9b192b522d22c33705afd7f595c4d09b84948f2cbfc5f95db640a06e910690e"
DEPENDENCIES = daily.DEPENDENCIES + (
    "src/forex_demo_lab/elliott_waves_124.py", "src/forex_demo_lab/elliott_fixture_124.py",
    "scripts/elliott-waves-124.py", "tests/test_elliott_waves_124.py",
    "config/elliott-waves-124.json", "docs/ELLIOTT-WAVES-124-PLAN.md", "docs/ELLIOTT-WAVES-124-PROTOCOL.md",
)
D = lambda n: Decimal(str(n))


def rules():
    raw = daily._read(daily.ROOT / "config/elliott-waves-124.json")
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA256:
        raise ValueError("fixed_wave_rules_changed")
    return daily._json(raw)


def source_bindings():
    return {n: hashlib.sha256(daily._read(daily.ROOT / n)).hexdigest() for n in DEPENDENCIES}


def validate_fixture(value):
    daily._fields(value, {"format", "kind", "clock", "symbol", "case", "daily"}, "wave_fixture_fields")
    if (value["format"] != VERSION or value["kind"] != "invented_wave_detector"
            or value["clock"] != "invented_utc_milliseconds" or value["symbol"] != "EURUSD"):
        raise ValueError("invented_wave_fixture_required")
    daily._name(value["case"], "wave_fixture_case")
    observed = daily.snapshot(value["daily"])
    if observed.case != value["case"]:
        raise ValueError("wave_case_mismatch")
    bars = value["daily"]["bars"]
    for bar in bars:
        if any(bar[k] > 1000000 for k in ("open", "high", "low", "close")):
            raise ValueError("wave_price_bound")
    selected = [b for b in bars if b["session_id"] <= observed.target_session_id]
    if any(a["available_msc"] > b["available_msc"] for a, b in zip(selected, selected[1:])):
        raise ValueError("wave_availability_order")
    return value


def freeze_fixture(path, output):
    raw = daily._read(path)
    value = validate_fixture(daily._json(raw))
    sources = source_bindings()
    if sources["config/research-candidates-117.json"] != daily.DECLARATION_SHA256:
        raise ValueError("fixed_declaration_changed")
    manifest = {"format": "FXDL_EW124_FREEZE_V1", "kind": "invented_wave_freeze",
                "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                "fixture_sha256": hashlib.sha256(raw).hexdigest(), "case": value["case"],
                "sources": sources, "rules": rules(), "market_data_qualified": False,
                "returns_available": False, "orders_available": False, "real_money_execution_available": False}
    daily.write_new(output, manifest)
    return manifest


def _utc_freeze(value):
    try:
        if type(value) is not str:
            raise ValueError()
        instant = datetime.fromisoformat(value)
        if instant.utcoffset() is None or instant.utcoffset().total_seconds() != 0:
            raise ValueError()
    except ValueError as exc:
        raise ValueError("wave_freeze_time") from exc


class Replay:
    def __init__(self, path, manifest_path):
        raw, mraw = daily._read(path), daily._read(manifest_path)
        value, manifest = daily._json(raw), daily._json(mraw)
        daily._fields(manifest, {"format", "kind", "frozen_at_utc", "fixture_sha256", "case", "sources", "rules",
                                "market_data_qualified", "returns_available", "orders_available", "real_money_execution_available"}, "wave_manifest_fields")
        if (manifest["format"] != "FXDL_EW124_FREEZE_V1" or manifest["kind"] != "invented_wave_freeze"
                or manifest["fixture_sha256"] != hashlib.sha256(raw).hexdigest()
                or daily._canonical(manifest["sources"]) != daily._canonical(source_bindings())
                or daily._canonical(manifest["rules"]) != daily._canonical(rules())
                or any(manifest[k] is not False for k in ("market_data_qualified", "returns_available", "orders_available", "real_money_execution_available"))):
            raise ValueError("wave_freeze_binding")
        _utc_freeze(manifest["frozen_at_utc"])
        self._fixture = deepcopy(validate_fixture(value))
        if manifest["case"] != value["case"]:
            raise ValueError("wave_freeze_case")
        self._bars = [b for b in value["daily"]["bars"] if b["session_id"] <= value["daily"]["target_session_id"]]
        self._fixture_sha, self._manifest_sha = hashlib.sha256(raw).hexdigest(), hashlib.sha256(mraw).hexdigest()
        self._rules = rules()
        self._state = {"cursor": 0, "confirmed_pivots": [], "swing_chain": [], "active_setup": None,
                       "considered_patterns": [], "signals": [], "outcomes": [],
                       "observed_bar_hashes": [], "calendar_prefix_sha256": None, "observed_prefix_sha256": None}

    @property
    def state(self):
        return deepcopy(self._state)

    def _context(self, index, state):
        bar = self._bars[index]
        calendar = self._fixture["daily"]["calendar"]
        prefix = {**calendar, "sessions": [s for s in calendar["sessions"] if s["session_id"] <= bar["session_id"]]}
        state["observed_bar_hashes"].append(bar["lineage_sha256"])
        state["calendar_prefix_sha256"] = daily._digest(prefix)
        state["observed_prefix_sha256"] = daily._digest({"calendar": prefix, "bars": state["observed_bar_hashes"]})

    def _pivot(self, index):
        if index < 2:
            return None
        left, center, right = self._bars[index - 2:index + 1]
        a, b, c = (D(row["close"]) for row in (left, center, right))
        kind = "low" if b < a and b < c else "high" if b > a and b > c else None
        if kind is None:
            return None
        pivot = {"kind": kind, "bar_index": index - 1, "session_id": center["session_id"], "close": str(b),
                 "observation_msc": center["observation_msc"], "confirmation_bar_index": index,
                 "confirmation_session_id": right["session_id"], "confirmed_available_msc": right["available_msc"],
                 "center_bar_sha256": center["lineage_sha256"], "confirmation_bar_sha256": right["lineage_sha256"]}
        pivot["pivot_id"] = daily._digest(pivot)
        return pivot

    def _form(self, index, pivots, identity):
        a, b, c = pivots
        side = 1 if a["kind"] == "low" else -1
        p0, p1, p2 = (D(p["close"]) for p in pivots)
        if not (p0 < p2 < p1 if side == 1 else p0 > p2 > p1):
            return None, "invalid_pullback_geometry"
        impulse = abs(p1 - p0)
        if impulse / p0 < D(self._rules["minimum_impulse_fraction"]):
            return None, "insufficient_impulse"
        fraction = abs(p1 - p2) / impulse
        if not D(self._rules["retracement_minimum"]) <= fraction <= D(self._rules["retracement_maximum"]):
            return None, "retracement_outside_band"
        segment = self._bars[b["bar_index"]:c["bar_index"] + 1]
        extreme = min(D(r["low"]) for r in segment) if side == 1 else max(D(r["high"]) for r in segment)
        origin = D(self._bars[a["bar_index"]]["low" if side == 1 else "high"])
        if (extreme <= origin if side == 1 else extreme >= origin):
            return None, "origin_invalidated_by_pullback"
        level = D(self._bars[b["bar_index"]]["high" if side == 1 else "low"])
        current = self._bars[index]
        if (D(current["low"]) <= extreme if side == 1 else D(current["high"]) >= extreme):
            return None, "confirmation_invalidation"
        if side * (D(current["close"]) - level) > 0:
            return None, "breakout_before_confirmation"
        return {"pattern_id": identity, "side": side, "pivots": deepcopy(pivots),
                "armed_bar_index": index, "armed_session_id": current["session_id"],
                "armed_available_msc": current["available_msc"], "breakout_level": str(level),
                "prospective_invalidation": str(extreme), "impulse_fraction": str(impulse / p0),
                "retracement_fraction": str(fraction)}, None

    def _apply(self, index, state):
        self._context(index, state)
        bar, actions = self._bars[index], []
        setup = state["active_setup"]
        signal = None
        if setup:
            side, stop, level = setup["side"], D(setup["prospective_invalidation"]), D(setup["breakout_level"])
            invalid = D(bar["low"]) <= stop if side == 1 else D(bar["high"]) >= stop
            age = index - setup["armed_bar_index"]
            crossing = side * (D(self._bars[index - 1]["close"]) - level) <= 0 < side * (D(bar["close"]) - level)
            reason = "setup_invalidated" if invalid else "setup_expired" if age > self._rules["setup_expiry_trading_bars"] else None
            if reason is None and crossing:
                if index + 1 < self._rules["warmup_trading_bars"]:
                    reason = "breakout_suppressed_warmup"
                else:
                    delta = D(bar["close"]) - D(self._bars[index - self._rules["trend_lookback_trading_bars"]]["close"])
                    trend = 1 if delta > 0 else -1 if delta < 0 else 0
                    reason = "breakout_observed" if trend == side else "breakout_suppressed_trend"
                    if trend == side:
                        signal = {"kind": "invented_wave_breakout_observation", "candidate": CANDIDATE,
                            "side": side, "pattern_id": setup["pattern_id"], "pivots": deepcopy(setup["pivots"]),
                            "source_observation_msc": bar["observation_msc"], "available_msc": bar["available_msc"],
                            "decision_msc": bar["available_msc"], "breakout_session_id": bar["session_id"],
                            "setup_confirmed_available_msc": setup["armed_available_msc"],
                            "observed_close": str(D(bar["close"])), "breakout_level": setup["breakout_level"],
                            "prospective_invalidation": setup["prospective_invalidation"], "trend_side": trend,
                            "observed_prefix_sha256": state["observed_prefix_sha256"],
                            "calendar_prefix_sha256": state["calendar_prefix_sha256"], "rules_sha256": daily._digest(self._rules)}
                        state["signals"].append(signal)
            if reason:
                actions.append({"pattern_id": setup["pattern_id"], "reason": reason, "age_trading_bars": age})
                state["active_setup"] = None
        pivot = self._pivot(index)
        swing_action = None
        if pivot:
            state["confirmed_pivots"].append(pivot)
            chain = state["swing_chain"]
            if chain and chain[-1]["kind"] == pivot["kind"]:
                more = D(pivot["close"]) > D(chain[-1]["close"]) if pivot["kind"] == "high" else D(pivot["close"]) < D(chain[-1]["close"])
                if more:
                    chain[-1] = pivot
                    swing_action = "replaced_more_extreme"
                else:
                    swing_action = "ignored_same_kind"
            else:
                chain.append(pivot)
                swing_action = "appended"
            if swing_action != "ignored_same_kind" and len(chain) >= 3:
                pivots = chain[-3:]
                identity = daily._digest({"candidate": CANDIDATE, "pivots": [p["pivot_id"] for p in pivots], "rules": daily._digest(self._rules)})
                if identity not in state["considered_patterns"]:
                    state["considered_patterns"].append(identity)
                    formed, reason = self._form(index, pivots, identity)
                    if formed and state["active_setup"]:
                        reason = "setup_slot_busy"
                    if formed and reason is None:
                        state["active_setup"] = formed
                        reason = "setup_armed"
                    actions.append({"pattern_id": identity, "reason": reason})
        state["outcomes"].append({"bar_index": index, "session_id": bar["session_id"], "available_msc": bar["available_msc"],
            "confirmed_pivot": deepcopy(pivot), "swing_action": swing_action, "setup_actions": actions,
            "signal": deepcopy(signal), "observed_prefix_sha256": state["observed_prefix_sha256"]})
        state["cursor"] = index + 1

    def step(self, index=None, bar=None):
        cursor = self._state["cursor"]
        if index is None:
            if cursor == len(self._bars):
                return False
            index = cursor
        daily._integer(index, 0, len(self._bars) - 1, "wave_event_index")
        if bar is not None and daily._canonical(bar) != daily._canonical(self._bars[index]):
            raise ValueError("wave_event_conflict")
        if index == cursor - 1:
            return False
        if index != cursor:
            raise ValueError("wave_event_sequence")
        state = self.state
        with localcontext() as ctx:
            ctx.prec = self._rules["decimal_precision"]
            self._apply(index, state)
        self._state = state
        return True

    def run(self):
        while self.step():
            pass
        return self.report()

    def report(self):
        return {"kind": "invented_wave_observation_report", "candidate": CANDIDATE, "case": self._fixture["case"],
                "fixture_sha256": self._fixture_sha, "manifest_sha256": self._manifest_sha,
                "complete": self._state["cursor"] == len(self._bars), "final_state": self.state,
                "confirmed_pivots": len(self._state["confirmed_pivots"]), "signal_observations": len(self._state["signals"]),
                "trades": None, "returns": None, "fill_adapter_implemented": False, "market_data_qualified": False,
                "paper_evaluation_available": False, "orders_available": False, "real_money_execution_available": False}

    def checkpoint(self):
        payload = {"schema": "elliott_waves124_checkpoint_v1", "fixture_sha256": self._fixture_sha,
                   "manifest_sha256": self._manifest_sha, "cursor": self._state["cursor"], "state": self.state}
        return {"payload": payload, "sha256": daily._digest(payload)}

    @classmethod
    def restore(cls, path, manifest_path, checkpoint):
        daily._fields(checkpoint, {"payload", "sha256"}, "wave_checkpoint_envelope")
        payload = checkpoint["payload"]
        daily._fields(payload, {"schema", "fixture_sha256", "manifest_sha256", "cursor", "state"}, "wave_checkpoint_fields")
        result = cls(path, manifest_path)
        if (checkpoint["sha256"] != daily._digest(payload) or payload["schema"] != "elliott_waves124_checkpoint_v1"
                or payload["fixture_sha256"] != result._fixture_sha or payload["manifest_sha256"] != result._manifest_sha):
            raise ValueError("wave_checkpoint_binding")
        cursor = daily._integer(payload["cursor"], 0, len(result._bars), "wave_checkpoint_cursor")
        for _ in range(cursor):
            result.step()
        if daily._canonical(result.state) != daily._canonical(payload["state"]):
            raise ValueError("wave_checkpoint_reconstructed_state")
        return result


def evaluate_fixture(path, manifest_path, output):
    report = Replay(path, manifest_path).run()
    daily.write_new(output, report)
    return report
