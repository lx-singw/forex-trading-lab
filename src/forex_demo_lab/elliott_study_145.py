"""Metadata-only prospective Elliott study preflight. No price reader or admission.

Evidence hashes identify declarations, not verified provider facts. Even a complete
plan requires independent qualification and an implemented qualified-data runner.
"""
from datetime import date
import calendar
import hashlib
import json
from pathlib import Path
import re

from .elliott_full.controls import source_bindings as strategy_bindings

ROOT=Path(__file__).resolve().parents[2]
VERSION="FXDL_ELLIOTT_STUDY145_V1"
TRACKS=("qualified","hypothetical_cost_sensitivity")
CANDIDATES=("EW_FULL_V1","EWPB_D124","T12_D","CASH")
PROFILES=("base","adverse")
FRAMES=("D1","H4","H1")
PARTITIONS=("development","validation")
GATES=("source_use","prior_trials","clock_timezone_dst","session_calendar",
       "coverage_lineage","quote_availability","commission_swap","contract_margin_conversion")
LIMIT=256*1024
MIN_SESSIONS=253
MIN_MONTHS=24
PROFILE_SHA="fc9629f0922700e9ea8118cbf23460f550870a5ecf17ff14e6246833766faf6f"


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def digest(value):return hashlib.sha256(canonical(value)).hexdigest()


def fields(value,expected,reason):
    if type(value) is not dict or set(value)!=set(expected):raise ValueError(reason)


def integer(value,maximum,reason):
    if type(value) is not int or not 0<=value<=maximum:raise ValueError(reason)


def hash_value(value):
    if value is not None and (type(value) is not str or not re.fullmatch('[0-9a-f]{64}',value)):
        raise ValueError("evidence_hash")


def day(value):
    if type(value) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise ValueError("ISO_date_required")
    try:result=date.fromisoformat(value)
    except ValueError as exc:raise ValueError("ISO_date_required") from exc
    if not 1900<=result.year<=2100:raise ValueError("date_bound")
    return result


def span(value,nullable=False):
    fields(value,("start","end"),"interval_fields")
    if nullable and value["start"] is None and value["end"] is None:return None
    start,end=day(value["start"]),day(value["end"])
    if start>=end:raise ValueError("half_open_interval")
    return start,end


def overlap(a,b):return a[0]<b[1] and b[0]<a[1]


def add_months(start,months):
    ordinal=start.year*12+start.month-1+months
    year,month=divmod(ordinal,12);month+=1
    return date(year,month,min(start.day,calendar.monthrange(year,month)[1]))


def covered(target,intervals):
    cursor=target[0]
    for start,end in sorted(intervals):
        if end<=cursor:continue
        if start>cursor:return False
        cursor=max(cursor,end)
        if cursor>=target[1]:return True
    return False


def policy():
    return {"as_of":"2026-11-14","intervals":"half_open_UTC_dates","minimum_calendar_months":MIN_MONTHS,
            "minimum_complete_prior_sessions":MIN_SESSIONS,"cells_per_track":16,"maximum_initial_tracks":2,
            "date_policy":{"seen_development_only":["2024-01-01","2025-01-01"],
                           "consumed":["2025-01-01","2026-01-01"],
                           "quarantined":["2026-10-01","2026-11-01"],
                           "reserved_untouched":["2026-11-01","2027-01-01"]},
            "older_inputs":"2020-2023 qualification unresolved; no source assigned",
            "closed_routes":["closed_native090","sdk_attach_only"],
            "source_claims_are_qualification":False,"market_runner_available":False,"orders_available":False}


def draft():
    empty=lambda:{"start":None,"end":None}
    return {"schema":VERSION,"kind":"metadata_only_prospective_plan","case":"current_unassigned",
            "track":"qualified","source":{"alias":None,"route":None},
            "partitions":{name:{"interval":empty(),"warmup":{"interval":empty(),
                           "declared_complete_bars":{f:None for f in FRAMES}}} for name in PARTITIONS},
            "history":{"complete":False,"exposures":[]},"joint_study_sha256":None,
            "evidence":{gate:{"sha256":None,"intervals":[],"timeframes":[]} for gate in GATES},
            "costs":{"status":"unknown","profile_declaration_sha256":PROFILE_SHA,"contradictions":False},
            "prior_cells":{"qualified":0,"hypothetical_cost_sensitivity":0}}


def validate(plan):
    fields(plan,("schema","kind","case","track","source","partitions","history","joint_study_sha256","evidence","costs","prior_cells"),"metadata_plan_fields")
    if plan["schema"]!=VERSION or plan["kind"]!="metadata_only_prospective_plan":raise ValueError("metadata_plan_only")
    if type(plan["case"]) is not str or not re.fullmatch('[a-z][a-z0-9_]{0,63}',plan["case"]):raise ValueError("anonymous_case")
    if plan["track"] not in TRACKS:raise ValueError("study_track")
    fields(plan["source"],("alias","route"),"source_fields")
    alias=plan["source"]["alias"]
    if alias is not None and (type(alias) is not str or not re.fullmatch('source_[a-z][a-z0-9_]{0,47}',alias)):raise ValueError("anonymous_source_alias")
    if plan["source"]["route"] not in (None,"existing_historical","native_capture","closed_native090","sdk_attach_only"):
        raise ValueError("source_route")
    fields(plan["partitions"],PARTITIONS,"partition_names")
    for name in PARTITIONS:
        p=plan["partitions"][name];fields(p,("interval","warmup"),"partition_fields");span(p["interval"],True)
        fields(p["warmup"],("interval","declared_complete_bars"),"warmup_fields");span(p["warmup"]["interval"],True)
        fields(p["warmup"]["declared_complete_bars"],FRAMES,"warmup_frames")
        for count in p["warmup"]["declared_complete_bars"].values():
            if count is not None:integer(count,10000000,"warmup_count")
    fields(plan["history"],("complete","exposures"),"history_fields")
    if type(plan["history"]["complete"]) is not bool:raise ValueError("history_complete")
    rows=plan["history"]["exposures"]
    if type(rows) is not list or len(rows)>256:raise ValueError("exposure_count")
    for row in rows:
        fields(row,("interval","kind","track","joint_study_sha256"),"exposure_fields");span(row["interval"])
        if row["kind"] not in ("prices","returns","rule_adjustment","friend_example") or row["track"] not in (*TRACKS,"other"):
            raise ValueError("exposure_kind")
        hash_value(row["joint_study_sha256"])
    hash_value(plan["joint_study_sha256"])
    fields(plan["evidence"],GATES,"evidence_gates")
    for evidence in plan["evidence"].values():
        fields(evidence,("sha256","intervals","timeframes"),"evidence_fields");hash_value(evidence["sha256"])
        if type(evidence["intervals"]) is not list or len(evidence["intervals"])>16:raise ValueError("evidence_intervals")
        for interval in evidence["intervals"]:span(interval)
        frames=evidence["timeframes"]
        if type(frames) is not list or any(type(f) is not str or f not in FRAMES for f in frames) or len(set(frames))!=len(frames):
            raise ValueError("evidence_frames")
    fields(plan["costs"],("status","profile_declaration_sha256","contradictions"),"cost_fields")
    if plan["costs"]["status"] not in ("unknown","hypothetical_117","broker_evidence_declared") or type(plan["costs"]["contradictions"]) is not bool:
        raise ValueError("cost_status")
    if plan["costs"]["profile_declaration_sha256"]!=PROFILE_SHA:raise ValueError("fixed_profile_declaration")
    fields(plan["prior_cells"],TRACKS,"budget_fields")
    for count in plan["prior_cells"].values():integer(count,16,"prior_cell_count")
    return plan


def bindings():
    paths=("src/forex_demo_lab/elliott_study_145.py","scripts/elliott-study-145.py","tests/test_elliott_study_145.py")
    strategy=strategy_bindings()
    if strategy["frozen_controls"].get("config/research-candidates-117.json")!=PROFILE_SHA:
        raise ValueError("fixed_profile_reference_changed")
    return {"preflight":{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths},"strategy":strategy}


def read(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError("metadata_input_file")
    with path.open('rb') as stream:raw=stream.read(LIMIT+1)
    if len(raw)>LIMIT:raise ValueError("metadata_size")
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError("duplicate_json_field")
            result[key]=value
        return result
    def nonfinite(_):raise ValueError("nonfinite_json")
    try:return json.loads(raw,object_pairs_hook=pairs,parse_constant=nonfinite),hashlib.sha256(raw).hexdigest()
    except (UnicodeError,json.JSONDecodeError,RecursionError) as exc:raise ValueError("metadata_json") from exc


def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def freeze(path,output):
    plan,sha=read(path);validate(plan)
    result={"schema":VERSION,"kind":"frozen_metadata_plan_not_admission","plan_file_sha256":sha,
            "plan_sha256":digest(plan),"policy":policy(),"sources":bindings(),
            "market_data_access_available":False,"returns_available":False,"orders_available":False}
    write(output,result);return result


def assess(plan):
    validate(plan)
    issues=[]
    def issue(code,scope="all",state="MISSING"):
        item={"code":code,"scope":scope,"state":state}
        if item not in issues:issues.append(item)
    route=plan["source"]["route"]
    if plan["source"]["alias"] is None or route is None:issue("source_unassigned")
    elif route in policy()["closed_routes"]:issue("closed_route_not_renewed",state="BLOCKED")
    elif route=="native_capture":issue("no_bounded_native_capture_assigned",state="BLOCKED")
    if not plan["history"]["complete"]:issue("prior_trial_history_incomplete")
    if plan["prior_cells"][plan["track"]]+16>16:issue("initial_track_budget_exhausted",state="BLOCKED")
    periods={};segments=[]
    for name in PARTITIONS:
        p=plan["partitions"][name];period=span(p["interval"],True);warm=span(p["warmup"]["interval"],True)
        periods[name]=period
        if period is None:issue("partition_dates_unassigned",name)
        else:
            segments.append((name,"funded",period))
            if period[1]<add_months(period[0],MIN_MONTHS):issue("fewer_than_24_calendar_months",name,"BLOCKED")
        if warm is None:issue("warmup_dates_unassigned",name)
        else:
            segments.append((name,"warmup",warm))
            if period and warm[1]!=period[0]:issue("warmup_not_contiguous_with_partition",name,"BLOCKED")
        counts=p["warmup"]["declared_complete_bars"]
        for frame,count in counts.items():
            if count is None:issue("complete_warmup_count_missing_"+frame,name)
            elif count<MIN_SESSIONS:issue("insufficient_declared_warmup_"+frame,name,"BLOCKED")
    if all(periods.values()) and periods["development"][1]>periods["validation"][0]:
        issue("partitions_not_chronological_disjoint",state="BLOCKED")
    for name,role,period in segments:
        for status,bounds in policy()["date_policy"].items():
            restricted=(day(bounds[0]),day(bounds[1]))
            if overlap(period,restricted) and (status!="seen_development_only" or (name=="validation" and role=="funded")):
                issue("date_"+status,name,"BLOCKED")
    validation=periods.get("validation")
    if validation:
        for exposure in plan["history"]["exposures"]:
            if not overlap(validation,span(exposure["interval"])):continue
            joint=(exposure["kind"] in ("prices","returns") and exposure["track"] in TRACKS and exposure["track"]!=plan["track"]
                   and plan["joint_study_sha256"] is not None and exposure["joint_study_sha256"]==plan["joint_study_sha256"])
            issue("joint_pre_return_freeze_requires_review" if joint else "validation_previously_exposed","validation",
                  "DECLARED_UNVERIFIED" if joint else "BLOCKED")
    for gate,evidence in plan["evidence"].items():
        if evidence["sha256"] is None:
            issue("evidence_missing_"+gate);continue
        intervals=[span(item) for item in evidence["intervals"]]
        if set(evidence["timeframes"])!=set(FRAMES):issue("evidence_frames_incomplete_"+gate)
        for name,_,period in segments:
            if not covered(period,intervals):issue("evidence_scope_gap_"+gate,name,"BLOCKED")
        issue("evidence_not_independently_qualified_"+gate,state="DECLARED_UNVERIFIED")
    costs=plan["costs"]
    if costs["contradictions"]:issue("cost_contradiction_requires_new_declared_profile",state="BLOCKED")
    if costs["status"]=="unknown":issue("historical_costs_unknown")
    elif plan["track"]=="qualified" and costs["status"]!="broker_evidence_declared":
        issue("hypothetical_costs_cannot_pass_qualified_track",state="BLOCKED")
    if plan["track"]=="hypothetical_cost_sensitivity":
        issue("sensitivity_cannot_satisfy_broker_or_demo_gate",state="RESTRICTION")
    issue("qualified_market_runner_unavailable",state="UNAVAILABLE")
    issue("full_strategy_acceptance_incomplete",state="UNAVAILABLE")
    issue("independent_qualification_required",state="UNAVAILABLE")
    cells=[{"candidate":candidate,"profile":profile,"partition":part,"track":plan["track"],"status":"UNAVAILABLE","returns":None,
            "reason_codes":[i["code"] for i in issues if i["scope"] in ("all",part)]}
           for candidate in CANDIDATES for profile in PROFILES for part in PARTITIONS]
    return {"schema":VERSION,"kind":"metadata_only_preflight","status":"UNAVAILABLE","plan_sha256":digest(plan),
            "issues":issues,"cells":cells,"planned_cells":16,"market_cells_run":0,
            "market_data_read":False,"returns_computed":False,"native_queries":False,"orders_available":False,
            "limitations":["Hashed declarations are not source qualification or capture authority",
                           "Dates are proposals to check, not assigned data or renewed collection windows",
                           "No price files, provider routes or native accounts are opened"]}


def run(path,manifest,output):
    plan,sha=read(path);frozen,freeze_sha=read(manifest)
    sources=bindings()
    fields(frozen,("schema","kind","plan_file_sha256","plan_sha256","policy","sources","market_data_access_available","returns_available","orders_available"),"freeze_fields")
    validate(plan)
    if (frozen["schema"]!=VERSION or frozen["kind"]!="frozen_metadata_plan_not_admission" or frozen["plan_file_sha256"]!=sha
            or frozen["plan_sha256"]!=digest(plan) or frozen["policy"]!=policy() or frozen["sources"]!=sources
            or any(frozen[k] is not False for k in ("market_data_access_available","returns_available","orders_available"))):
        raise ValueError("metadata_freeze_binding")
    result=assess(plan)
    if bindings()!=sources:raise ValueError("preflight_sources_changed")
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    write(root/'preflight.json',result)
    lines=["# Metadata-only Elliott study preflight","","Status: UNAVAILABLE. No market data or returns accessed.","",
           "| Requirement | Scope | State |","| --- | --- | --- |"]
    lines.extend(f"| {i['code']} | {i['scope']} | {i['state']} |" for i in result['issues'])
    lines.extend(["","All 16 cells remain unavailable. Evidence hashes require independent review; they do not authorize data access or orders.",""])
    (root/'requirements.md').write_text('\n'.join(lines),encoding='utf-8')
    write(root/'run-binding.json',{"plan_sha256":digest(plan),"freeze_sha256":freeze_sha,"sources":sources})
    return result
