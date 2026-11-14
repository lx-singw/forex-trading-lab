"""Common invented session observations for four independent paper accounts.

Unchanged controls accept only their original UTC-day/availability profile.
Unsupported controls stay unavailable; this adapter never qualifies market data.
"""
from copy import deepcopy
import hashlib
from itertools import groupby
from pathlib import Path
import re

from . import elliott_session_paper_148 as paper
from . import elliott_sessions_146 as observations
from .elliott_session_strategy_147 import Coverage
from .elliott_full import shared as legacy
from .elliott_full.contracts import Bar, Quote, D, digest, integer, precise

VERSION="FXDL_ELLIOTT_SESSION_COMPARISON149_V1"
CANDIDATES=("EW_FULL_V1","EWPB_D124","T12_D","CASH")
PROFILES=("base","adverse")
PARTITIONS=("development","later_validation")
DAY=24*observations.HOUR
MAX_BYTES=16*1024*1024
ROOT_FILES={"prefix.json","derived-bars.json","paper-events.json","control-input.json","control-freeze.json"}
ALLOWED_FILES=ROOT_FILES|{"legacy/"+name for name in legacy.FILES|{"prepared.json"}}
REPORT_FILES={candidate+"-"+profile+".json" for candidate in CANDIDATES for profile in PROFILES}


def source_bindings():
    path=Path(__file__).resolve()
    return {"comparison":{path.name:hashlib.sha256(path.read_bytes()).hexdigest()},"paper":paper.source_bindings()}


def policy():
    return {"kind":"invented_session_comparison_only","candidates":list(CANDIDATES),"profiles":list(PROFILES),
            "partitions":list(PARTITIONS),"cells":16,"fresh_cash_usd":"10000","capital_carried":False,
            "warmup_minimum_each_frame":253,"quotes_per_partition_maximum":256,
            "common_coverage":"all_completed_scheduled_bars_at_each_quote",
            "controls":"unchanged_UTC_midnight_24h_days_and_whole_day_closures_only",
            "unsupported_controls":"unavailable_null_summary","orders_available":False,"market_runner_available":False}


def read(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError("comparison_input_file")
    with path.open("rb") as file:raw=file.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:raise ValueError("comparison_input_size")
    return raw


def write(path,value):legacy.c.daily.write_new(path,value)


def file_hash(path):return hashlib.sha256(read(path)).hexdigest()


def report_hash(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError("comparison_report_file")
    result=hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda:file.read(1024*1024),b""):result.update(block)
    return result.hexdigest()


def hour_lineage(case,calendar_sha,row):
    return digest({"kind":"invented_session_hour149","case":case,"calendar_sha256":calendar_sha,
                   "row":{k:v for k,v in row.items() if k!="lineage"}})


def price(value):
    if type(value) is not str or len(value)>64:raise ValueError("bounded_decimal_string")
    number=D(value)
    if not D(".00000000000000000001")<=number<=D("1000000") or len(number.as_tuple().digits)>50:
        raise ValueError("invented_price_bound")
    return number


@precise
def validate(value):
    observations.fields(value,("kind","symbol","case","calendar","hours","quotes","partitions"))
    if value["kind"]!="invented_session_comparison_149" or value["symbol"]!="EURUSD":
        raise ValueError("invented_session_comparison_required")
    if type(value["case"]) is not str or not re.fullmatch(r"[a-z][a-z0-9_]{0,47}",value["case"]):
        raise ValueError("anonymous_comparison_case")
    calendar=observations.Calendar.from_record(value["calendar"]);coverage=Coverage(calendar)
    parts=value["partitions"]
    if type(parts) is not list or len(parts)!=2:raise ValueError("two_chronological_partitions_required")
    for i,part in enumerate(parts):
        observations.fields(part,("name","start_msc","end_msc","endpoint_source_msc"))
        for key in ("start_msc","end_msc","endpoint_source_msc"):integer(part[key])
        if (part["name"]!=PARTITIONS[i] or not calendar.start<=part["start_msc"]<=part["endpoint_source_msc"]<part["end_msc"]<=calendar.end
                or i and part["start_msc"]<parts[i-1]["end_msc"]):raise ValueError("partition_bounds_order")
    if type(value["hours"]) is not list or len(value["hours"])>20000:raise ValueError("comparison_hour_bound")
    hours=[];seen=set();calendar_sha=calendar.sha256
    for row in value["hours"]:
        observations.fields(row,set(paper.BAR_FIELDS)|{"observation"})
        for key in ("open","high","low","close"):price(row[key])
        bar=Bar(**{key:row[key] for key in paper.BAR_FIELDS});coverage.validate(bar)
        integer(row["observation"])
        if (bar.timeframe!="H1" or bar.start in seen or not bar.start<=row["observation"]<bar.end
                or row["lineage"]!=hour_lineage(value["case"],calendar_sha,row)):
            raise ValueError("comparison_hour_contract")
        seen.add(bar.start);hours.append(bar)
    if hours!=sorted(hours,key=lambda b:(b.available,b.start)):raise ValueError("hour_receipt_order")
    if type(value["quotes"]) is not list or len(value["quotes"])>512:raise ValueError("comparison_quote_bound")
    quotes=[];windows=calendar.frame("H1");by_start={row["start"]:row for row in value["hours"]}
    for i,row in enumerate(value["quotes"]):
        observations.fields(row,paper.QUOTE_FIELDS);price(row["bid"]);price(row["ask"])
        q=Quote(**row)
        if q.sequence!=i or i and (q.time<quotes[-1].time or q.source<quotes[-1].source):raise ValueError("quote_receipt_source_order")
        if i and q.source==quotes[-1].source and (q.bid,q.ask)!=(quotes[-1].bid,quotes[-1].ask):raise ValueError("quote_source_price_conflict")
        owners=[part for part in parts if part["start_msc"]<=q.source<part["end_msc"] and part["start_msc"]<=q.time<part["end_msc"]]
        if len(owners)!=1:raise ValueError("quote_crosses_or_outside_partition")
        window=next((w for w in windows if w.start<=q.source<w.end),None)
        source_hour=None if window is None else by_start.get(window.start)
        if source_hour is not None and q.time-q.source<=2000 and q.session_open:
            midpoint=(q.bid+q.ask)/2
            if (not D(source_hour["low"])<=midpoint<=D(source_hour["high"]) or q.source>source_hour["observation"]
                    or q.source==source_hour["observation"] and midpoint!=D(source_hour["close"])):
                raise ValueError("quote_hour_observation_conflict")
        quotes.append(q)
    for part in parts:
        if sum(part["start_msc"]<=q.time<part["end_msc"] for q in quotes)>256:raise ValueError("partition_quote_bound")
    return value


def freeze(path,manifest):
    raw=read(path);value=validate(legacy.c.daily._json(raw));sources=source_bindings()
    result={"version":VERSION,"kind":"invented_comparison_freeze_not_admission","input_sha256":hashlib.sha256(raw).hexdigest(),
            "sources":sources,"policy":policy(),"partitions":value["partitions"],"orders_available":False,"market_data_qualified":False}
    if sources!=source_bindings():raise ValueError("comparison_source_changed_during_freeze")
    write(manifest,result);return result


def load(path,manifest):
    raw=read(path);value=validate(legacy.c.daily._json(raw));f=legacy.c.daily._json(read(manifest))
    observations.fields(f,("version","kind","input_sha256","sources","policy","partitions","orders_available","market_data_qualified"))
    if (f["version"]!=VERSION or f["kind"]!="invented_comparison_freeze_not_admission" or f["input_sha256"]!=hashlib.sha256(raw).hexdigest()
            or f["sources"]!=source_bindings() or f["policy"]!=policy() or f["partitions"]!=value["partitions"]
            or f["orders_available"] is not False or f["market_data_qualified"] is not False):raise ValueError("comparison_freeze_binding")
    return value


def legacy_calendar(calendar):
    """Translate declared whole UTC closure days; never infer absent sessions."""
    value=calendar.record()
    if calendar.delay!=2000:raise ValueError("legacy_requires_2000ms_finalization_profile")
    rows=[]
    for row in value["segments"]:
        if row["start"]%DAY or row["end"]%DAY:raise ValueError("legacy_requires_UTC_midnight_days")
        if row["kind"]=="session":
            if (row["end"]-row["start"]!=DAY or row["partial"] or row["h1"]!=list(range(row["start"],row["end"],observations.HOUR))+[row["end"]]
                    or row["h4"]!=list(range(row["start"],row["end"],4*observations.HOUR))+[row["end"]]):
                raise ValueError("legacy_requires_full_24h_H1_H4_days")
        for start in range(row["start"],row["end"],DAY):
            rows.append({"session_id":len(rows),"start_msc":start,"end_msc":start+DAY,
                         "status":"trading" if row["kind"]=="session" else "closure"})
    result={"kind":"invented_calendar","calendar_id":"session_comparison149","available_msc":calendar.start,"sessions":rows}
    legacy.c.bars._calendar(result);return result


def legacy_input(value,part):
    calendar=observations.Calendar.from_record(value["calendar"]);coverage=Coverage(calendar)
    converted=legacy_calendar(calendar)
    selected=[row for row in value["quotes"] if part["start_msc"]<=row["time"]<part["end_msc"]]
    for q in (Quote(**row) for row in selected):
        if q.session_open!=coverage.is_open(q.source):raise ValueError("legacy_quote_session_flag_unrepresentable")
        if coverage.is_open(q.source)!=coverage.is_open(q.time):raise ValueError("legacy_source_receipt_session_mismatch")
    hours=[]
    for row in (row for row in value["hours"] if row["available"]<part["end_msc"]):
        for key in ("open","high","low","close"):legacy._float(row[key])
        clone=deepcopy(row);clone["lineage"]=legacy.hour_lineage(value["case"],clone);hours.append(clone)
    quotes=[]
    for i,row in enumerate(selected):
        legacy._float(row["bid"]);legacy._float(row["ask"])
        quotes.append({**row,"sequence":i})
    result={"kind":"invented_shared_hourly_v1","clock":"invented_utc_milliseconds","symbol":"EURUSD","case":value["case"],
            "calendar":converted,"hours":hours,"quotes":quotes,"partitions":deepcopy(value["partitions"])}
    legacy.validate(result);return result


def semantic_bar(bar):
    return (bar.timeframe,bar.start,bar.end,bar.available,bar.open,bar.high,bar.low,bar.close)


def scope(value,partition):
    calendar=observations.Calendar.from_record(value["calendar"]);coverage=Coverage(calendar)
    part=next((part for part in value["partitions"] if part["name"]==partition),None)
    if part is None:raise ValueError("comparison_partition")
    quotes=[Quote(**q) for q in value["quotes"] if part["start_msc"]<=q["time"]<part["end_msc"]]
    if not quotes or quotes[-1].source!=part["endpoint_source_msc"]:raise ValueError("missing_declared_endpoint")
    last=quotes[-1]
    if (last.time-last.source>2000 or not last.session_open or not coverage.is_open(last.source) or not coverage.is_open(last.time)
            or len(quotes)>1 and last.source==quotes[-2].source):raise ValueError("invalid_executable_endpoint")
    hours=[row for row in value["hours"] if row["available"]<part["end_msc"]]
    if any(row["available"]>last.time for row in hours):raise ValueError("endpoint_not_last_observation")
    stream=observations.Observations(calendar)
    for row in hours:stream.observe(Bar(**{key:row[key] for key in paper.BAR_FIELDS}))
    stream.advance(last.time);bars=stream.bars();histories={f:[] for f in observations.FRAMES};events=[];index=0
    previous={}
    for _,group in groupby(bars,key=lambda b:b.available):
        batch=tuple(group)
        if len(batch)>3 or len({b.timeframe for b in batch})!=len(batch):raise ValueError("ambiguous_same_clock_publications")
        for bar in batch:
            if bar.timeframe in previous and bar.start<previous[bar.timeframe].end:raise ValueError("source_order_backfill")
            previous[bar.timeframe]=bar
    warm=None
    for quote in quotes:
        while index<len(bars) and bars[index].available<=quote.time:
            now=bars[index].available;batch=[]
            while index<len(bars) and bars[index].available==now:
                bar=bars[index];histories[bar.timeframe].append(bar);batch.append(bar.record());index+=1
            events.append({"kind":"bars","value":batch})
        if any(coverage.issue(frame,histories[frame],quote.time) is not None for frame in observations.FRAMES):
            raise ValueError("missing_or_unavailable_completed_children")
        if warm is None:
            warm={f:len(rows) for f,rows in histories.items()}
            if min(warm.values())<253:raise ValueError("insufficient_common_253_bar_warmup")
        events.append({"kind":"quote","value":quote.record()})
    if index!=len(bars):raise ValueError("unobserved_bar_tail")
    events.append({"kind":"finish","value":last.record()})
    return calendar,part,hours,quotes,bars,events,warm


def collect(root):
    result={}
    for path in sorted(Path(root).rglob("*")):
        if path.is_symlink():raise ValueError("prepared_symlink")
        if path.is_file():
            name=path.relative_to(root).as_posix()
            if name=="prepared149.json" or name in REPORT_FILES:continue
            if name not in ALLOWED_FILES:raise ValueError("unexpected_prepared_artifact")
            result[name]=file_hash(path)
    return result


def prepare(path,manifest,partition,output):
    value=load(path,manifest)
    calendar,part,hours,quotes,bars,events,warm=scope(value,partition)
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    write(root/"prefix.json",{"kind":"invented_session_prefix149","case":value["case"],"partition":part,
                              "calendar":calendar.record(),"hours":hours,"quotes":[q.record() for q in quotes]})
    write(root/"derived-bars.json",{"kind":"invented_session_bars149","bars":[b.record() for b in bars]})
    write(root/"paper-events.json",{"calendar":calendar.record(),"events":events})
    reason=None
    try:
        converted=legacy_input(value,part)
        write(root/"control-input.json",converted);legacy.freeze(root/"control-input.json",root/"control-freeze.json")
        legacy.prepare(root/"control-input.json",root/"control-freeze.json",partition,root/"legacy")
        old=legacy.c.daily._json(read(root/"legacy/derived-bars.json"))
        old_bars=[Bar(**row) for row in old["bars"]]
        if [semantic_bar(b) for b in bars]!=[semantic_bar(b) for b in old_bars]:raise ValueError("legacy_bar_semantics_mismatch")
        expected=[(q.source,q.time,q.bid,q.ask) for q in quotes]
        for name in ("fills-input.json","compiled-input.json"):
            compiled=legacy.c.daily._json(read(root/"legacy"/name))
            if expected!=[(e["source_msc"],e["receipt_msc"],D(str(e["bid"])),D(str(e["ask"]))) for e in compiled["events"]]:
                raise ValueError("legacy_execution_quote_mismatch")
    except ValueError as error:reason=str(error)
    if load(path,manifest)!=value:raise ValueError("comparison_changed_during_preparation")
    record={"version":VERSION,"sources":source_bindings(),"input_sha256":file_hash(path),"freeze_sha256":file_hash(manifest),
            "partition":part,"warmup":warm,"controls_reason":reason,"files":collect(root),"orders_available":False}
    write(root/"prepared149.json",record);return record


class ComparisonReplay:
    def __init__(self,directory,candidate,profile="base"):
        if candidate not in CANDIDATES or profile not in PROFILES:raise ValueError("comparison_candidate_profile")
        self.root=Path(directory)
        if self.root.is_symlink():raise ValueError("prepared_directory")
        prepared=legacy.c.daily._json(read(self.root/"prepared149.json"))
        observations.fields(prepared,("version","sources","input_sha256","freeze_sha256","partition","warmup","controls_reason","files","orders_available"))
        if (prepared["version"]!=VERSION or prepared["sources"]!=source_bindings() or prepared["orders_available"] is not False
                or type(prepared["files"]) is not dict or prepared["files"]!=collect(self.root)):
            raise ValueError("comparison_prepared_binding")
        self.prepared=prepared;self.binding=file_hash(self.root/"prepared149.json")
        prefix=legacy.c.daily._json(read(self.root/"prefix.json"))
        if prefix.get("partition")!=prepared["partition"]:raise ValueError("comparison_prepared_partition")
        self.candidate,self.profile,self.cursor=candidate,profile,0
        if candidate=="EW_FULL_V1":
            source=legacy.c.daily._json(read(self.root/"paper-events.json"));observations.fields(source,("calendar","events"))
            if type(source["events"]) is not list or len(source["events"])>30000:raise ValueError("comparison_event_bound")
            self.engine=paper.PaperReplay(observations.Calendar.from_record(source["calendar"]),profile)
            self.events=deepcopy(source["events"])
        else:
            if prepared["controls_reason"] is not None:raise ValueError(prepared["controls_reason"])
            self.engine=legacy.SharedReplay(self.root/"legacy",candidate,profile)
            if self.engine.prepared["partition"]!=prepared["partition"]:raise ValueError("comparison_control_partition")
            self.events=deepcopy(self.engine.events)

    def _check_binding(self):
        if (self.prepared["sources"]!=source_bindings() or file_hash(self.root/"prepared149.json")!=self.binding
                or collect(self.root)!=self.prepared["files"]):raise ValueError("comparison_prepared_changed")

    @property
    def finished(self):
        return self.engine.ledger.finished if self.candidate=="EW_FULL_V1" else self.engine.engine.state["finished"]

    def step(self,event=None):
        if event is None:
            if self.cursor==len(self.events):return False
            event=self.events[self.cursor]
        if self.cursor and event==self.events[self.cursor-1]:return False
        if self.cursor>=len(self.events) or event!=self.events[self.cursor]:raise ValueError("comparison_event_binding")
        self.engine.step(event);self.cursor+=1;return True

    def run(self):
        while self.step():pass
        if self.candidate!="EW_FULL_V1":self.engine.run()
        return self.report()

    @precise
    def report(self):
        self._check_binding()
        if self.cursor!=len(self.events) or not self.finished:raise ValueError("unfinished_comparison_account")
        if self.candidate=="EW_FULL_V1":
            original=self.engine.state();ledger=self.engine.ledger
            summary={"initial_cash_usd":"10000","final_cash_usd":str(ledger.cash),"toy_net_usd":str(ledger.cash-D(10000)),
                     "closed_positions":len(ledger.trades)}
        else:
            original=self.engine.report();summary=original["summary"]
        return {"kind":"invented_session_account149","candidate":self.candidate,"profile":self.profile,
                "partition":deepcopy(self.prepared["partition"]),"summary":deepcopy(summary),"original_report":original,
                "orders_available":False,"market_status":"UNAVAILABLE","market_returns":None,"strategy_selected":False}

    def checkpoint(self):
        self._check_binding()
        payload={"version":VERSION,"sources":source_bindings(),"prepared_sha256":self.binding,"candidate":self.candidate,
                 "profile":self.profile,"cursor":self.cursor,"finished":self.finished,"inner":self.engine.checkpoint()}
        return {"payload":payload,"digest":digest(payload)}

    @classmethod
    def restore(cls,directory,checkpoint):
        observations.fields(checkpoint,("payload","digest"));p=checkpoint["payload"]
        observations.fields(p,("version","sources","prepared_sha256","candidate","profile","cursor","finished","inner"))
        if p["version"]!=VERSION or p["sources"]!=source_bindings() or digest(p)!=checkpoint["digest"]:
            raise ValueError("comparison_checkpoint_binding")
        result=cls(directory,p["candidate"],p["profile"])
        if p["prepared_sha256"]!=result.binding:raise ValueError("comparison_checkpoint_partition")
        integer(p["cursor"])
        if p["cursor"]>len(result.events) or type(p["finished"]) is not bool:raise ValueError("comparison_checkpoint_cursor")
        observations.fields(p["inner"],("payload","digest"))
        if type(p["inner"]["payload"]) is not dict:raise ValueError("comparison_checkpoint_inner")
        inner=p["inner"]["payload"]
        if result.candidate=="EW_FULL_V1":
            if inner.get("profile")!=result.profile:raise ValueError("comparison_checkpoint_identity")
            if inner.get("calendar")!=result.engine.decisions.coverage.calendar.record():raise ValueError("comparison_checkpoint_calendar")
            if inner.get("events")!=result.events[:p["cursor"]]:raise ValueError("comparison_checkpoint_prefix")
            result.engine=paper.PaperReplay.restore(p["inner"])
        else:
            if inner.get("profile")!=result.profile or inner.get("candidate")!=result.candidate:
                raise ValueError("comparison_checkpoint_identity")
            result.engine=legacy.SharedReplay.restore(result.root/"legacy",p["inner"])
            if result.engine.cursor!=p["cursor"]:raise ValueError("comparison_checkpoint_cursor")
        result.cursor=p["cursor"]
        if result.finished!=p["finished"]:raise ValueError("comparison_checkpoint_finish")
        return result


def evaluate(path,manifest,output):
    value=load(path,manifest);root=Path(output);root.mkdir(parents=True,exist_ok=False)
    write(root/"run-binding.json",{"input_sha256":file_hash(path),"freeze_sha256":file_hash(manifest),"sources":source_bindings()})
    cells=[];prepared_bindings={};report_bindings={}
    for part in value["partitions"]:
        directory=root/part["name"];common_error=None
        try:
            prepared=prepare(path,manifest,part["name"],directory)
            prepared_bindings[part["name"]]=(file_hash(directory/"prepared149.json"),prepared["files"])
        except ValueError as error:common_error=str(error)
        for profile in PROFILES:
            for candidate in CANDIDATES:
                report=None;reason=common_error
                if reason is None:
                    try:report=ComparisonReplay(directory,candidate,profile).run()
                    except ValueError as error:reason=str(error)
                if report is not None:
                    name=part["name"]+"/"+candidate+"-"+profile+".json"
                    write(root/name,report);report_bindings[name]=report_hash(root/name)
                cells.append({"candidate":candidate,"profile":profile,"partition":part["name"],
                              "invented_status":"computed" if report is not None else "unavailable","reason":reason,
                              "summary":None if report is None else report["summary"],"market_status":"UNAVAILABLE","market_returns":None})
    if load(path,manifest)!=value:raise ValueError("comparison_changed_during_run")
    for name,(binding,files) in prepared_bindings.items():
        if file_hash(root/name/"prepared149.json")!=binding or collect(root/name)!=files:
            raise ValueError("comparison_artifacts_changed_during_run")
    if any(report_hash(root/name)!=binding for name,binding in report_bindings.items()):
        raise ValueError("comparison_reports_changed_during_run")
    result={"kind":"invented_session_comparison149","cells":cells,"computed_invented_cells":sum(c["invented_status"]=="computed" for c in cells),
            "market_cells_run":0,"orders_available":False,"market_data_qualified":False,"strategy_selected":False,"capital_summed_as_portfolio":False,
            "report_sha256":report_bindings,
            "limitations":["Invented H1 observations, not qualified ticks or broker costs",
                           "Unsupported legacy calendars/availability remain unavailable; no reanchoring",
                           "Original control and new-ledger clocks/cost handling retain documented differences",
                           "Two software partitions do not establish untouched or minimum-duration market validation"]}
    write(root/"comparison-status.json",result);return result
