"""One invented H1 history for four strategies; no market or native admission.

H1 OHLC and last-observation times are declared invented inputs, not tick-derived
or certified prices. H4/D1 bars are derived exclusively from complete H1 children.
"""
from copy import deepcopy
from dataclasses import fields
from pathlib import Path

from . import controls as c
from .contracts import Bar, Quote, D, digest, precise, validate_bundle
from .engine import Engine
from .bars import PERIOD

VERSION = "EW_FULL_V1_SHARED_HOURLY"
CANDIDATES = ("EW_FULL_V1",) + c.CANDIDATES
HOUR = PERIOD["H1"]
DAY = PERIOD["D1"]
BAR_FIELDS = {f.name for f in fields(Bar)}
FILES = {"prefix-input.json", "derived-bars.json", "ew-full-input.json", "daily-input.json",
         "fills-input.json", "fills-frozen.json", "wave-input.json", "wave-frozen.json",
         "wave-report.json", "compiled-input.json", "compiled-frozen.json"}


def policy():
    return {"input": "invented_H1_midpoint_OHLC_and_last_observation",
            "H4_children": 4, "D1_children": 24, "completion_grace_ms": 2000,
            "max_execution_quotes_per_partition": 256,
            "publication": "maximum_child_availability", "missing_children": "unavailable_no_interpolation",
            "controls": "unchanged_118_120_124_125", "market_admission": False}


def hour_lineage(case, row):
    return digest({"kind": "invented_shared_hour", "case": case,
                   "row": {k:v for k,v in row.items() if k != "lineage"}})


def _float(value):
    result = float(value)
    if D(str(result)) != D(value):
        raise ValueError("legacy_float_roundtrip")
    return result


@precise
def validate(value):
    c.daily._fields(value, {"kind", "clock", "symbol", "case", "calendar", "hours", "quotes", "partitions"}, "shared_fields")
    if value["kind"] != "invented_shared_hourly_v1" or value["clock"] != "invented_utc_milliseconds" or value["symbol"] != "EURUSD":
        raise ValueError("invented_shared_hourly_required")
    c.daily._name(value["case"], "shared_case")
    c.bars._calendar(value["calendar"])
    sessions = value["calendar"]["sessions"]
    by_start = {s["start_msc"]:s for s in sessions}
    if type(value["hours"]) is not list or not 1 <= len(value["hours"]) <= 20000:
        raise ValueError("shared_hour_count")
    hours = []
    for row in value["hours"]:
        c.daily._fields(row, BAR_FIELDS | {"observation"}, "shared_hour_fields")
        b = Bar(**{k:row[k] for k in BAR_FIELDS})
        session = by_start.get(b.start//DAY*DAY)
        c.daily._integer(row["observation"], b.start, b.end-1, "shared_observation")
        if (b.timeframe != "H1" or b.end-b.start != HOUR or b.start % HOUR
                or b.available < b.end+2000 or b.available > c.daily.MAX_TIME or session is None
                or session["status"] != "trading" or row["lineage"] != hour_lineage(value["case"], row)):
            raise ValueError("shared_hour_contract")
        hours.append(b)
    if type(value["quotes"]) is not list or not 1 <= len(value["quotes"]) <= 512:
        raise ValueError("shared_quote_count")
    # The original bar contract also checks overlap and publication order.
    _, quotes = validate_bundle({"kind":"invented_ew_full_v1", "symbol":"EURUSD",
                                 "bars":[b.record() for b in hours], "quotes":value["quotes"]})
    hourly_rows = {r["start"]:r for r in value["hours"]}
    for i,q in enumerate(quotes):
        session = by_start.get(q.source//DAY*DAY)
        if (q.sequence != i or session is None or q.time >= sessions[-1]["end_msc"]
                or q.session_open != (session["status"] == "trading")):
            raise ValueError("shared_quote_contract")
        if i and q.source == quotes[i-1].source and (q.bid,q.ask) != (quotes[i-1].bid,quotes[i-1].ask):
            raise ValueError("shared_source_price_conflict")
        row = hourly_rows.get(q.source//HOUR*HOUR)
        if row is not None and q.time-q.source<=2000 and q.session_open:
            midpoint = (q.bid+q.ask)/2
            if (not D(row["low"]) <= midpoint <= D(row["high"]) or q.source > row["observation"]
                    or (q.source == row["observation"] and midpoint != D(row["close"]))):
                raise ValueError("shared_quote_hour_conflict")
    c.old_elliott.runs._partitions(value["partitions"], {"calendar":value["calendar"]})
    for part in value["partitions"]:
        if sum(part["start_msc"] <= q.source and q.time < part["end_msc"] for q in quotes) > 256:
            raise ValueError("shared_partition_quote_limit")
    return value


def freeze(path, output):
    value = validate(c.daily._json(c.daily._read(path)))
    frozen = {"version":VERSION, "input_sha256":c._hash(path), "sources":c.source_bindings(),
              "partitions":value["partitions"], "policy":policy(), "candidates":list(CANDIDATES),
              "profiles":list(c.PROFILES), "orders_available":False, "market_data_qualified":False}
    c.daily.write_new(output, frozen)
    return frozen


def _load(path, manifest):
    value = validate(c.daily._json(c.daily._read(path)))
    f = c.daily._json(c.daily._read(manifest))
    c.daily._fields(f, {"version", "input_sha256", "sources", "partitions", "policy", "candidates", "profiles",
                       "orders_available", "market_data_qualified"}, "shared_freeze_fields")
    if (f["version"] != VERSION or f["input_sha256"] != c._hash(path) or f["sources"] != c.source_bindings()
            or f["partitions"] != value["partitions"] or f["policy"] != policy()
            or f["candidates"] != list(CANDIDATES) or f["profiles"] != list(c.PROFILES)
            or f["orders_available"] is not False or f["market_data_qualified"] is not False):
        raise ValueError("shared_freeze_binding")
    return value


@precise
def derive(hours, calendar, clock):
    """Complete children only; unavailable children are not borrowed from a suffix."""
    observed = {row["start"]:row for row in hours if row["available"] <= clock}
    output = [Bar(**{k:r[k] for k in BAR_FIELDS}) for r in observed.values()]
    missing = []
    for session in calendar["sessions"]:
        if session["status"] != "trading":
            continue
        for start in range(session["start_msc"], min(session["end_msc"],clock-2000), HOUR):
            if start+HOUR+2000 <= clock and start not in observed:
                missing.append(start)
        for frame in ("H4", "D1"):
            period = PERIOD[frame]
            for start in range(session["start_msc"], session["end_msc"], period):
                if start+period+2000 > clock:
                    continue
                children = [observed.get(t) for t in range(start,start+period,HOUR)]
                if any(child is None for child in children):
                    continue
                output.append(Bar(frame,start,start+period,max(r["available"] for r in children),
                                  children[0]["open"],max(D(r["high"]) for r in children),
                                  min(D(r["low"]) for r in children),children[-1]["close"],
                                  digest({"frame":frame,"children":[r["lineage"] for r in children]})))
    output.sort(key=lambda b:(b.available,{"D1":0,"H4":1,"H1":2}[b.timeframe],b.start))
    return output, {"missing_hour_count":len(missing), "missing_hour_starts":missing,
                    "bars":{f:sum(b.timeframe==f for b in output) for f in PERIOD}}


def prepare(path, manifest, partition, output):
    value = _load(path, manifest)
    matches = [p for p in value["partitions"] if p["name"] == partition]
    if len(matches) != 1:
        raise ValueError("shared_partition")
    part = matches[0]
    root = Path(output);root.mkdir(parents=True,exist_ok=False)
    quotes = [Quote(**q) for q in value["quotes"] if part["start_msc"] <= q["source"] and q["time"] < part["end_msc"]]
    if not quotes or quotes[-1].source != part["endpoint_source_msc"]:
        raise ValueError("shared_missing_endpoint")
    last = quotes[-1]
    if last.time-last.source > 2000 or not last.session_open or (len(quotes)>1 and last.source==quotes[-2].source):
        raise ValueError("shared_invalid_endpoint")
    hours = [r for r in value["hours"] if r["available"] < part["end_msc"]]
    if any(r["available"] > last.time for r in hours):
        raise ValueError("shared_endpoint_not_last_observation")
    calendar = {**value["calendar"], "sessions":[s for s in value["calendar"]["sessions"] if s["start_msc"] < part["end_msc"]]}
    prefix = {"kind":"invented_shared_hourly_prefix", "case":"shared_"+partition, "partition":part,
              "calendar":calendar, "hours":hours, "quotes":[q.record() for q in quotes]}
    c.daily.write_new(root/"prefix-input.json",prefix)
    derived, coverage = derive(hours,calendar,last.time)
    c.daily.write_new(root/"derived-bars.json", {"policy":policy(), "coverage":coverage,"bars":[b.record() for b in derived]})
    if coverage["missing_hour_count"]:
        raise ValueError("shared_missing_completed_hours")
    warm = {f:sum(b.timeframe==f and b.available <= quotes[0].time for b in derived) for f in PERIOD}
    if any(count < 253 for count in warm.values()):
        raise ValueError("shared_insufficient_common_warmup")
    bundle = {"kind":"invented_ew_full_v1", "symbol":"EURUSD", "bars":[b.record() for b in derived],
              "quotes":[q.record() for q in quotes], "boundary":{"end_time":part["end_msc"],
              "quote_sequence":last.sequence,"quote_source":last.source,"quote_time":last.time}}
    validate_bundle(bundle)
    c.daily.write_new(root/"ew-full-input.json",bundle)
    daily_rows = []
    observations = {r["start"]:r["observation"] for r in hours}
    for b in (b for b in derived if b.timeframe=="D1"):
        session = next(s for s in calendar["sessions"] if s["start_msc"]==b.start)
        row = {"session_id":session["session_id"],"start_msc":b.start,"end_msc":b.end,
               "available_msc":b.available,"observation_msc":observations[b.end-HOUR],
               **{k:_float(getattr(b,k)) for k in ("open","high","low","close")}}
        row["lineage_sha256"] = c.daily.bar_lineage(prefix["case"],calendar["calendar_id"],session,row)
        daily_rows.append(row)
    latest = daily_rows[-1]
    features = {"format":c.daily.VERSION,"kind":"invented_daily_fixture","clock":"invented_utc_milliseconds",
                "symbol":"EURUSD","case":prefix["case"],"calendar":calendar,"bars":daily_rows,
                "target_session_id":latest["session_id"],"decision_msc":latest["available_msc"]}
    c.daily.snapshot(features)
    c.daily.write_new(root/"daily-input.json",features)
    account = {"kind":"invented_flat_cash","trade_mode":0,"currency":"USD","available_msc":part["start_msc"],"balance_usd":10000}
    events, messages = [], []
    for i,q in enumerate(quotes):
        if q.source < part["start_msc"] or not q.time < part["end_msc"]:
            raise ValueError("shared_quote_partition")
        quote = {"source_msc":q.source,"receipt_msc":q.time,"bid":_float(q.bid),"ask":_float(q.ask)}
        target = c.fills.risk._latest(features,q.time)
        if target is None:
            raise ValueError("shared_no_daily_feature")
        available = next(b["available_msc"] for b in daily_rows if b["session_id"]==target)
        events.append({"sequence":i,**quote,"target_session_id":target,"feature_decision_msc":available})
        messages.append({"sequence":i,"kind":"quote",**quote})
    compiled = {"format":c.fills.VERSION,"kind":"invented_daily_fills_fixture","clock":"invented_utc_milliseconds",
                "symbol":"EURUSD","case":prefix["case"],"features":features,"initial_account":account,"events":events}
    c.daily.write_new(root/"fills-input.json",compiled)
    c.fills.freeze_fixture(root/"fills-input.json",root/"fills-frozen.json")
    wave_input = {"format":c.old_elliott.waves.VERSION,"kind":"invented_wave_detector","clock":"invented_utc_milliseconds",
                  "symbol":"EURUSD","case":prefix["case"],"daily":features}
    c.daily.write_new(root/"wave-input.json",wave_input)
    c.old_elliott.waves.freeze_fixture(root/"wave-input.json",root/"wave-frozen.json")
    waves = c.old_elliott.waves.Replay(root/"wave-input.json",root/"wave-frozen.json").run()
    c.daily.write_new(root/"wave-report.json",waves)
    artifacts = {p.name:c._hash(p) for p in sorted(root.iterdir()) if p.is_file()}
    original_prefix = {"case":prefix["case"],"calendar":calendar,"initial_account":account,"messages":messages}
    old_compiled = c.old_elliott._compile(original_prefix,{"final_state":{"bars":daily_rows}},waves,part,artifacts)
    c.daily.write_new(root/"compiled-input.json",old_compiled)
    c.old_elliott._freeze_compiled(root/"compiled-input.json",root/"compiled-frozen.json",artifacts)
    prepared = {"version":VERSION,"sources":c.source_bindings(),"input_sha256":c._hash(path),"freeze_sha256":c._hash(manifest),
                "partition":part,"coverage":coverage,"warmup":warm,
                "files":{p.name:c._hash(p) for p in sorted(root.iterdir()) if p.is_file()},"orders_available":False}
    c.daily.write_new(root/"prepared.json",prepared)
    return prepared


class SharedReplay:
    """Frozen source derivations and prefix-verified checkpoints for all four accounts."""
    def __init__(self,directory,candidate,profile="base"):
        if candidate not in CANDIDATES or profile not in c.PROFILES:
            raise ValueError("shared_candidate_or_profile")
        self.root = Path(directory)
        if self.root.is_symlink():
            raise ValueError("shared_directory")
        p = c.daily._json(c.daily._read(self.root/"prepared.json"))
        c.daily._fields(p,{"version","sources","input_sha256","freeze_sha256","partition","coverage","warmup","files","orders_available"},"shared_prepared_fields")
        if p["version"] != VERSION or p["sources"] != c.source_bindings() or p["orders_available"] is not False or type(p["files"]) is not dict or set(p["files"]) != FILES:
            raise ValueError("shared_prepared_binding")
        if any(c._hash(self.root/name)!=h for name,h in p["files"].items()):
            raise ValueError("shared_artifact_binding")
        compiled = c.daily._json(c.daily._read(self.root/"compiled-input.json"))
        if p["partition"] != compiled["partition"]:
            raise ValueError("shared_partition_binding")
        self.prepared,self.candidate,self.profile = p,candidate,profile
        self.binding = c._hash(self.root/"prepared.json")
        self.cursor = 0
        if candidate == "EW_FULL_V1":
            bundle = c.daily._json(c.daily._read(self.root/"ew-full-input.json"))
            bars,quotes = validate_bundle(bundle)
            self.events = [];i=0
            for q in quotes:
                while i<len(bars) and bars[i].available<=q.time:
                    self.events.append({"kind":"bar","value":bars[i].record()});i+=1
                self.events.append({"kind":"quote","value":q.record()})
            if i!=len(bars):
                raise ValueError("shared_unobserved_tail")
            self.events.append({"kind":"finish","value":quotes[-1].record()})
            self.engine = Engine(profile)
        else:
            self.engine_type = c.old_elliott.Account if candidate=="EWPB_D124" else c.fills.Replay
            prefix = "compiled" if candidate=="EWPB_D124" else "fills"
            self.paths = (self.root/(prefix+"-input.json"),self.root/(prefix+"-frozen.json"))
            self.engine = self.engine_type(*self.paths,profile,candidate)
            self.events = deepcopy(self.engine._fixture["events"])

    def step(self,event=None):
        if event is None:
            if self.cursor==len(self.events):
                return False
            event = self.events[self.cursor]
        if self.cursor and event==self.events[self.cursor-1]:
            return False
        if self.cursor>=len(self.events) or event!=self.events[self.cursor]:
            raise ValueError("shared_event_binding")
        self.engine.step(event)
        self.cursor+=1
        return True

    def run(self):
        while self.step():
            pass
        if self.candidate!="EW_FULL_V1":
            self.engine.finish()
        return self.report()

    @precise
    def report(self):
        if self.cursor!=len(self.events):
            raise ValueError("shared_unfinished_report")
        if self.candidate=="EW_FULL_V1":
            if not self.engine.ledger.finished:
                raise ValueError("shared_unfinished_ledger")
            original = {"ledger":self.engine.ledger.state(),"snapshots":deepcopy(self.engine.strategy.snapshots)}
            summary = {"initial_cash_usd":"10000","final_cash_usd":str(self.engine.ledger.cash),
                       "toy_net_usd":str(self.engine.ledger.cash-D(10000)),"closed_positions":len(self.engine.ledger.trades)}
        else:
            original = self.engine.report();summary=original["summary"]
        return {"kind":"invented_shared_hourly_account","candidate":self.candidate,"profile":self.profile,
                "partition":deepcopy(self.prepared["partition"]),"summary":summary,"original_report":original,
                "market_data_qualified":False,"orders_available":False,"strategy_selected":False,"real_money_execution_available":False}

    def checkpoint(self):
        p = {"version":VERSION,"sources":c.source_bindings(),"prepared_sha256":self.binding,
             "candidate":self.candidate,"profile":self.profile,"cursor":self.cursor,"inner":self.engine.checkpoint()}
        return {"payload":p,"digest":digest(p)}

    @classmethod
    def restore(cls,directory,checkpoint):
        c.daily._fields(checkpoint,{"payload","digest"},"shared_checkpoint_fields")
        p=checkpoint["payload"]
        c.daily._fields(p,{"version","sources","prepared_sha256","candidate","profile","cursor","inner"},"shared_checkpoint_payload")
        if p["version"]!=VERSION or p["sources"]!=c.source_bindings() or digest(p)!=checkpoint["digest"]:
            raise ValueError("shared_checkpoint_binding")
        result=cls(directory,p["candidate"],p["profile"])
        if p["prepared_sha256"]!=result.binding:
            raise ValueError("shared_checkpoint_partition")
        c.daily._integer(p["cursor"],0,len(result.events),"shared_checkpoint_cursor")
        if result.candidate=="EW_FULL_V1":
            if p["inner"]["payload"]["events"]!=result.events[:p["cursor"]]:
                raise ValueError("shared_checkpoint_prefix")
            result.engine=Engine.restore(p["inner"])
        else:
            result.engine=result.engine_type.restore(*result.paths,p["inner"],result.profile,result.candidate)
            if result.engine.state["cursor"]!=p["cursor"]:
                raise ValueError("shared_checkpoint_cursor")
        result.cursor=p["cursor"]
        return result


def evaluate(path,manifest,output):
    value=_load(path,manifest)
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    c.daily.write_new(root/"run-binding.json",{"input_sha256":c._hash(path),"freeze_sha256":c._hash(manifest),"sources":c.source_bindings()})
    cells=[]
    for part in value["partitions"]:
        directory=root/part["name"];error=None
        try:
            prepare(path,manifest,part["name"],directory)
        except ValueError as exc:
            error=str(exc)
        for profile in c.PROFILES:
            for candidate in CANDIDATES:
                reason=error;report=None
                if reason is None:
                    try:
                        report=SharedReplay(directory,candidate,profile).run()
                    except ValueError as exc:
                        reason=str(exc)
                if report is not None:
                    c.daily.write_new(directory/f"{candidate}-{profile}.json",report)
                cells.append({"candidate":candidate,"profile":profile,"partition":part["name"],
                              "invented_status":"computed" if report is not None else "unavailable","reason":reason,
                              "summary":None if report is None else report["summary"],"market_status":"UNAVAILABLE","market_returns":None})
    if _load(path,manifest)!=value:
        raise ValueError("shared_input_changed_during_run")
    result={"kind":"invented_shared_hourly_comparison","cells":cells,"computed_invented_cells":sum(r["invented_status"]=="computed" for r in cells),
            "market_cells_run":0,"orders_available":False,"market_data_qualified":False,"real_money_execution_available":False,
            "capital_summed_as_portfolio":False,"strategy_selected":False,
            "limitations":["Declared invented H1 OHLC; not tick-derived or qualified prices",
                           "Original control clocks/stop rules retained; new-ledger timing parity not established",
                           "Zero-signal examples test abstention; no market advantage or trading acceptance implied"]}
    c.daily.write_new(root/"comparison-status.json",result)
    return result
