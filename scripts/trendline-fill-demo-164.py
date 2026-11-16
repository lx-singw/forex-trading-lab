"""Write sixteen explicitly invented Level B price exercises to a new directory."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from forex_demo_lab import elliott_sessions_146 as sessions
from forex_demo_lab.trendline import data as d
from forex_demo_lab.trendline import fills as f


def run(output):
    output = d.no_links(output)
    output.mkdir(exist_ok=False)
    start = sessions.START+24*sessions.HOUR
    end = start+24*sessions.HOUR
    calendar = {"kind":"invented_session_calendar_146","scope":{"start":start,"end":end},
                "finalization_delay_ms":0,
                "segments":[{"kind":"session","label":"session_invented",
                             "start":start,"end":end,"h1":list(range(start,end+1,sessions.HOUR)),
                             "h4":list(range(start,end+1,4*sessions.HOUR)),"partial":False}]}
    summaries = []
    for cost in ("base","adverse"):
        for side in ("LONG","SHORT"):
            for mode in ("gap_stop","ambiguous","target_open","late_decision"):
                name = f"{cost}_{side.lower()}_{mode}"
                folder = output/name
                folder.mkdir()
                bid = "1.1004" if side == "LONG" else "1.09948"
                rows = [{"start":t,"end":t+sessions.HOUR,"available_at":t+sessions.HOUR,
                         "open":bid,"high":"1.101" if side == "LONG" else "1.1",
                         "low":"1.1" if side == "LONG" else "1.099","close":bid,
                         "spread_pips":"1.2"} for t in range(start,end,sessions.HOUR)]
                if mode == "ambiguous":
                    rows[4].update(low="1.09",high="1.11")
                elif mode == "gap_stop":
                    rows[5].update(open="1.097" if side == "LONG" else "1.10288",
                                   close="1.097" if side == "LONG" else "1.10288",
                                   low="1.0968" if side == "LONG" else "1.1026",
                                   high="1.0972" if side == "LONG" else "1.103")
                elif mode == "target_open":
                    rows[5].update(open="1.106" if side == "LONG" else "1.09388",
                                   close="1.106" if side == "LONG" else "1.09388",low="1.09",high="1.11")
                d.write_new(folder/"hours.json",rows)
                source = {"schema":d.VERSION,"kind":"invented_trendline_source","symbol":"EURUSD",
                          "data_level":"B","geometry_basis":"bid_only",
                          "spread_semantics":"constant_per_h1_assumption","partition":"development",
                          "input_sha256":hashlib.sha256((folder/"hours.json").read_bytes()).hexdigest(),
                          "calendar":deepcopy(calendar)}
                d.write_new(folder/"source.json",source)
                declaration,hours = d.load_dataset(folder/"source.json",folder/"hours.json")
                model = f.PriceModel(declaration,cost)
                request = {"kind":"invented_b_price_request","direction":side,"trigger_end":rows[4]["start"],
                           "decision_at":{"time":rows[4]["start"]+(1 if mode == "late_decision" else 0),"ordinal":0},
                           "stop":"1.0985" if side == "LONG" else "1.1015",
                           "target":"1.105" if side == "LONG" else "1.095",
                           "atr":"0.0015","tick":"0.00001","exit_model":"E2"}
                d.write_new(folder/"request.json",request)
                entry = model.entry(request,f.Opening.from_hour(hours[4],1))
                expected_entry = {("base","LONG"):"1.10054",("base","SHORT"):"1.09946",
                                  ("adverse","LONG"):"1.10057",("adverse","SHORT"):"1.09943"}[cost,side]
                exit_result = None
                if mode == "late_decision":
                    assert entry["reason"] == "LATE_DECISION"
                else:
                    assert entry["status"] == "FILLED" and entry["price"] == expected_entry
                    position = f.Position.from_record(entry["position"])
                    selected = hours[4 if mode == "ambiguous" else 5]
                    exit_result = model.exit_hour(position,selected,as_of=selected.available_at,open_ordinal=1)
                    if mode == "target_open":
                        reason,price = "TARGET_OPEN_REACH",("1.105" if side == "LONG" else "1.095")
                    elif mode == "ambiguous":
                        reason = "STOP_ADVERSE_AMBIGUITY"
                        price = {("base","LONG"):"1.09848",("base","SHORT"):"1.10152",
                                 ("adverse","LONG"):"1.09845",("adverse","SHORT"):"1.10155"}[cost,side]
                    else:
                        reason = "STOP_OPEN_GAP"
                        price = {("base","LONG"):"1.09698",("base","SHORT"):"1.10302",
                                 ("adverse","LONG"):"1.09695",("adverse","SHORT"):"1.10305"}[cost,side]
                    assert exit_result["reason"] == reason and exit_result["price"] == price
                d.write_new(folder/"result.json",{"entry":entry,"exit":exit_result})
                summaries.append({"case":name,"entry_status":entry["status"],"entry_reason":entry["reason"],
                                  "entry_price":entry.get("price"),
                                  "exit_reason":None if exit_result is None else exit_result["reason"],
                                  "exit_price":None if exit_result is None else exit_result["price"],
                                  "price_risk_excess":None if exit_result is None else exit_result["price_risk_excess"]})
    summary = {"kind":"invented_price_component_exercises","sprint":164,"cases":summaries,
               "source_bindings":f.bindings(),"account_ledger_available":False,
               "market_cells_run":0,"returns_computed":False,"orders_available":False}
    d.write_new(output/"summary.json",summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("new_output_directory")
    print(json.dumps({"cases":len(run(parser.parse_args().new_output_directory)["cases"]),
                      "kind":"invented_price_component_exercises","orders_available":False}))
