"""Prospective trendline source/run metadata checks; no market-data admission.

Reuse unchanged145 chronology/exposure/evidence logic and add the declared
28-cell trendline scope. Evidence references are hashes, never opened as paths.
"""
from copy import deepcopy
from datetime import datetime, time, timezone
import hashlib
import re

from .. import elliott_study_145 as legacy
from . import data, fills

VERSION = "TRL_STUDY_165_V1"
TRACKS = legacy.TRACKS
PARTITIONS = legacy.PARTITIONS
FRAMES = legacy.FRAMES
GATE_MAP = {key:("availability_model" if key == "quote_availability" else key) for key in legacy.GATES}
EXTRA_GATES = ("bar_price_semantics", "entry_spread_semantics")
GATES = (*GATE_MAP.values(), *EXTRA_GATES)
ROOT_FIELDS = ("schema", "kind", "case", "track", "source", "partitions", "history",
               "joint_study_sha256", "evidence", "costs", "prior_cells", "paired_exit",
               "data_level", "geometry_basis", "spread_semantics", "input_sha256",
               "calendar_sha256", "latency", "endpoints", "uncertainty_sha256")


def policy():
    value = deepcopy(legacy.policy())
    value.update(as_of="2026-11-16", cells_per_track=28,
                 minimum_complete_prior_bars={"H1":253,"H4":390,"D1":253},
                 candidates=list(data.CANDIDATES), paired_exit_analysis_budget=1,
                 geometry_only_cannot_admit_execution=True)
    return value


def draft():
    value = legacy.draft()
    value.update(schema=VERSION,kind="trendline_metadata_only_plan",case="current_unassigned",
                 track="hypothetical_cost_sensitivity",data_level="B",geometry_basis=None,
                 spread_semantics=None,input_sha256=None,calendar_sha256=None,
                 uncertainty_sha256=None,paired_exit={"planned":True,"prior_analyses":0},
                 latency={"availability_assumption":None,"finalization_delay_ms":None},
                 endpoints={part:{"liquidation_at":None} for part in PARTITIONS})
    value["evidence"] = {key:{"sha256":None,"intervals":[],"timeframes":[]} for key in GATES}
    value["history"].update(undated_price_exposure_count=None,tried_alternatives_count=None)
    return value


def _core(value):
    """Adapt only metadata; disable legacy16-cell counters in favour of our28."""
    result = {key:deepcopy(value[key]) for key in legacy.draft()}
    result.update(schema=legacy.VERSION,kind="metadata_only_prospective_plan")
    if result["source"]["route"] in ("provider_api","existing_export"):
        result["source"]["route"] = "existing_historical"
    result["history"] = {key:deepcopy(value["history"][key]) for key in ("complete","exposures")}
    result["evidence"] = {old:deepcopy(value["evidence"][new]) for old,new in GATE_MAP.items()}
    result["prior_cells"] = {track:0 for track in TRACKS}
    return result


def _evidence(value):
    legacy.fields(value,("sha256","intervals","timeframes"),"evidence_fields")
    legacy.hash_value(value["sha256"])
    if type(value["intervals"]) is not list or len(value["intervals"]) > 16:
        raise ValueError("bounded evidence intervals")
    for span in value["intervals"]:
        legacy.span(span)
    frames = value["timeframes"]
    if (type(frames) is not list or any(type(f) is not str or f not in FRAMES for f in frames)
            or len(set(frames)) != len(frames)):
        raise ValueError("unique evidence timeframes required")


def instant(value):
    if type(value) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",value):
        raise ValueError("explicit UTC liquidation timestamp required")
    result = datetime.fromisoformat(value[:-1]+"+00:00")
    if not 1900 <= result.year <= 2100:
        raise ValueError("liquidation date bound")
    return result


def validate(value):
    data.fields(value,ROOT_FIELDS)
    if value["schema"] != VERSION or value["kind"] != "trendline_metadata_only_plan":
        raise ValueError("trendline metadata plan required")
    if value["case"] not in ("current_unassigned","invented_claims","twelve_data_candidate"):
        raise ValueError("anonymous fixed case category required")
    data.fields(value["source"],("alias","route"))
    if value["source"]["alias"] not in (None,"source_twelve_data","source_oanda_export",
                                         "source_existing_export","source_invented_claims"):
        raise ValueError("anonymous fixed source category required")
    if value["source"]["route"] not in (None,"existing_historical","existing_export","provider_api",
                                         "native_capture","closed_native090","sdk_attach_only"):
        raise ValueError("declared route category required")
    data.fields(value["history"],("complete","exposures","undated_price_exposure_count","tried_alternatives_count"))
    for key in ("undated_price_exposure_count","tried_alternatives_count"):
        if value["history"][key] is not None:
            legacy.integer(value["history"][key],1000000,"bounded history count")
    data.fields(value["evidence"],GATES)
    for record in value["evidence"].values():
        _evidence(record)
    data.fields(value["prior_cells"],TRACKS)
    for count in value["prior_cells"].values():
        legacy.integer(count,28,"28-cell prior count required")
    data.fields(value["paired_exit"],("planned","prior_analyses"))
    if type(value["paired_exit"]["planned"]) is not bool:
        raise ValueError("paired analysis declaration required")
    legacy.integer(value["paired_exit"]["prior_analyses"],1000,"paired analysis count")
    if value["data_level"] not in ("B","Q"):
        raise ValueError("research data level required")
    allowed_basis = (None,"bid_only","mid_candles_source") if value["data_level"] == "B" else (None,"mid_sync")
    if value["geometry_basis"] not in allowed_basis:
        raise ValueError("level/geometry declaration mismatch")
    expected = {"bid_only":"constant_per_h1_assumption","mid_candles_source":"not_available",
                "mid_sync":"recorded_bid_ask"}
    if value["spread_semantics"] not in (None,*expected.values()):
        raise ValueError("spread declaration")
    if (value["geometry_basis"] is not None
            and value["spread_semantics"] not in (None,expected[value["geometry_basis"]])):
        raise ValueError("geometry/spread declaration mismatch")
    for key in ("input_sha256","calendar_sha256","uncertainty_sha256"):
        legacy.hash_value(value[key])
    data.fields(value["latency"],("availability_assumption","finalization_delay_ms"))
    if value["latency"]["availability_assumption"] not in (None,"bar_close_hypothesis","recorded_receipt_order"):
        raise ValueError("availability assumption")
    if value["latency"]["finalization_delay_ms"] is not None:
        legacy.integer(value["latency"]["finalization_delay_ms"],60000,"finalization delay")
    data.fields(value["endpoints"],PARTITIONS)
    for row in value["endpoints"].values():
        data.fields(row,("liquidation_at",))
        if row["liquidation_at"] is not None:
            instant(row["liquidation_at"])
    legacy.validate(_core(value))
    return value


def assess(value):
    validate(value)
    old = legacy.assess(_core(value))
    issues = []

    def issue(code,scope="all",state="MISSING"):
        item = {"code":code,"scope":scope,"state":state}
        if item not in issues:
            issues.append(item)

    for row in old["issues"]:
        issue(row["code"].replace("quote_availability","availability_model"),row["scope"],row["state"])
    if value["prior_cells"][value["track"]] + 28 > 28:
        issue("initial_28_cell_track_budget_exhausted",state="BLOCKED")
    if not value["paired_exit"]["planned"]:
        issue("paired_exit_analysis_not_declared",state="BLOCKED")
    elif value["paired_exit"]["prior_analyses"] + 1 > 1:
        issue("initial_paired_analysis_budget_exhausted",state="BLOCKED")
    for key in ("undated_price_exposure_count","tried_alternatives_count"):
        count = value["history"][key]
        if count is None:
            issue(key+"_missing")
        elif key == "undated_price_exposure_count" and count:
            issue("undated_price_exposure_requires_validation_review","validation","BLOCKED")
    if value["data_level"] == "B":
        issue("level_B_cannot_satisfy_qualified_broker_or_demo_gate",state="RESTRICTION")
        if value["track"] == "qualified":
            issue("level_B_not_qualified_execution_data",state="BLOCKED")
        issue("unchanged_control_input_compatibility_not_qualified",state="UNAVAILABLE")
    if value["geometry_basis"] == "mid_candles_source":
        issue("mid_only_execution_side_data_unavailable",state="BLOCKED")
    for key in ("geometry_basis","spread_semantics","input_sha256","calendar_sha256","uncertainty_sha256"):
        if value[key] is None:
            issue(key+"_unassigned")
    for key,claim in value["latency"].items():
        if claim is None:
            issue(key+"_unassigned")
    if value["data_level"] == "Q" and value["latency"]["availability_assumption"] == "bar_close_hypothesis":
        issue("level_Q_requires_observed_receipt_order",state="BLOCKED")
    if value["data_level"] == "B" and value["latency"]["finalization_delay_ms"]:
        issue("nonzero_delay_can_skip_immediate_H1_opens",state="RESTRICTION")
    segments = []
    for name in PARTITIONS:
        partition = value["partitions"][name]
        period = legacy.span(partition["interval"],True)
        warmup = legacy.span(partition["warmup"]["interval"],True)
        for role,bounds in (("funded",period),("warmup",warmup)):
            if bounds:
                segments.append((name,role,bounds))
        counts = partition["warmup"]["declared_complete_bars"]
        if counts["H4"] is not None and counts["H4"] < 390:
            issue("insufficient_FXR_390_H4_angle_history",name,"BLOCKED")
        if all(count is not None for count in counts.values()) and not counts["H1"] >= counts["H4"] >= counts["D1"]:
            issue("declared_child_parent_counts_inconsistent",name,"BLOCKED")
        endpoint = value["endpoints"][name]["liquidation_at"]
        if endpoint is None:
            issue("liquidation_timestamp_unassigned",name)
        else:
            at = instant(endpoint)
            if period and not datetime.combine(period[0],time(),timezone.utc) <= at < datetime.combine(period[1],time(),timezone.utc):
                issue("liquidation_outside_partition",name,"BLOCKED")
            issue("liquidation_calendar_and_quote_coverage_require_review",name,"DECLARED_UNVERIFIED")
    for gate in EXTRA_GATES:
        proof = value["evidence"][gate]
        if proof["sha256"] is None:
            issue("evidence_missing_"+gate)
            continue
        if set(proof["timeframes"]) != set(FRAMES):
            issue("evidence_frames_incomplete_"+gate)
        for name,_,bounds in segments:
            if not legacy.covered(bounds,[legacy.span(item) for item in proof["intervals"]]):
                issue("evidence_scope_gap_"+gate,name,"BLOCKED")
        issue("evidence_not_independently_qualified_"+gate,state="DECLARED_UNVERIFIED")
    return {"schema":VERSION,"kind":"trendline_metadata_preflight_not_admission","status":"UNAVAILABLE",
            "plan_sha256":data.digest(value),"data_level":value["data_level"],"track":value["track"],
            "geometry_basis":value["geometry_basis"],"issues":issues,"planned_cells":28,
            "cells":[{"candidate":candidate,"profile":profile,"partition":part,"track":value["track"],
                      "status":"UNAVAILABLE","returns":None,
                      "reason_codes":[i["code"] for i in issues if i["scope"] in ("all",part)]}
                     for candidate in data.CANDIDATES for profile in ("base","adverse") for part in PARTITIONS],
            "market_cells_run":0,"market_data_read":False,"returns_computed":False,
            "native_queries":False,"orders_available":False,"demo_eligible":False,
            "limitations":["reuse145 chronology/evidence checks without changing its16-cell scope",
                            "hashes, counts and flags are claims, not independent source qualification",
                            "no market reader, strategy acceptance or native capture authority"]}


def bindings():
    result = fills.bindings()
    for relative in ("src/forex_demo_lab/elliott_study_145.py",
                     "src/forex_demo_lab/trendline/study.py",
                     "scripts/trendline-study-165.py"):
        result[relative] = hashlib.sha256((data.ROOT/relative).read_bytes()).hexdigest()
    return result


def freeze(plan_path,output_path):
    value,raw_sha = data.read_json(plan_path,256*1024)
    validate(value)
    declaration = {"schema":VERSION,"kind":"frozen_metadata_not_admission",
                   "plan_file_sha256":raw_sha,"plan_sha256":data.digest(value),
                   "policy":policy(),"sources":bindings(),"market_data_access_available":False,
                   "returns_available":False,"orders_available":False}
    data.write_new(output_path,declaration)
    return declaration


def run(plan_path,freeze_path,output_path):
    value,raw_sha = data.read_json(plan_path,256*1024)
    frozen,freeze_sha = data.read_json(freeze_path,256*1024)
    validate(value)
    expected = {"schema":VERSION,"kind":"frozen_metadata_not_admission",
                "plan_file_sha256":raw_sha,"plan_sha256":data.digest(value),
                "policy":policy(),"sources":bindings(),"market_data_access_available":False,
                "returns_available":False,"orders_available":False}
    if data.canonical(frozen) != data.canonical(expected):
        raise ValueError("metadata freeze plan/policy/source binding mismatch")
    result = assess(value)
    if bindings() != expected["sources"]:
        raise ValueError("preflight sources changed during assessment")
    output = data.no_links(output_path)
    output.mkdir(exist_ok=False)
    data.write_new(output/"preflight.json",result)
    data.write_new(output/"run-binding.json",{"plan_sha256":data.digest(value),"freeze_sha256":freeze_sha,
                                             "sources":expected["sources"]})
    return result
