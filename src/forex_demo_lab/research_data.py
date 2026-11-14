"""New research versions with declared clock assumptions and no feed splicing."""
import csv
from datetime import datetime,timezone
import gzip
import io
import json
import math
from pathlib import Path

from .cli import code_digest,write_json
from .histdata import hourly
from .reconstruction import checked_capture
from .tick_audit import sha256
from .tick_dataset import FIELDS,read_ticks


def mt5_month_ticks(root):
    manifest=json.loads((root/"month.json").read_text())
    if (manifest.get("kind")!="bounded_mt5_month_capture" or manifest.get("source_label_offset_hours")!=2
            or manifest.get("month")!="202401"):
        raise ValueError("Unexpected month capture convention")
    cursor=int(datetime.fromisoformat(manifest.get("source_label_start","2024-01-01T02:00:00+00:00")).timestamp()*1000)
    ending=int(datetime.fromisoformat(manifest.get("source_label_end_exclusive","2024-02-01T02:00:00+00:00")).timestamp()*1000)
    sequence=0
    for window in manifest["windows"]:
        name=window["folder"]
        if Path(name).name!=name or name in (".",".."):
            raise ValueError("Invalid capture folder")
        folder=root/name
        if sha256(folder/"capture.json")!=window["capture_sha256"]:raise ValueError("Chunk manifest changed")
        metadata,ticks,lower,upper=checked_capture(folder)
        if lower!=cursor or upper>ending or len(ticks)!=window["ticks"]:
            raise ValueError("Month chunks overlap, have gaps or changed counts")
        for tick in ticks:
            yield {"sequence":sequence,"time_msc":tick["time_msc"]-2*3600000,"bid":tick["bid"],"ask":tick["ask"]}
            sequence+=1
        cursor=upper
    if cursor!=ending or sequence!=manifest["ticks"]:
        raise ValueError("Month capture incomplete")


def shifted_histdata(source, milliseconds):
    if milliseconds not in (0,-3600000):raise ValueError("Only the declared July clock scenarios are supported")
    for tick in read_ticks(source):
        yield {**tick,"time_msc":tick["time_msc"]+milliseconds}


def build(ticks,output,origin):
    if output.exists():raise FileExistsError("Research dataset destination exists")
    output.mkdir(parents=True,exist_ok=False)
    count=0;first=None;previous=None;gaps=[]
    partial=output/"ticks.csv.gz.partial"
    with partial.open("xb") as binary,gzip.GzipFile(filename="",mode="wb",fileobj=binary,mtime=0) as zipped, \
            io.TextIOWrapper(zipped,encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS);writer.writeheader()
        def record():
            nonlocal count,first,previous
            for tick in ticks:
                ms=tick["time_msc"]
                if (tick["sequence"]!=count or previous is not None and ms<previous
                        or not all(math.isfinite(tick[s]) for s in ("bid","ask")) or not 0<tick["bid"]<=tick["ask"]):
                    raise ValueError("Research dataset order/sequence failure")
                if first is None:first=ms
                if previous is not None and ms-previous>3600000:
                    a=datetime.fromtimestamp(previous/1000,timezone.utc)
                    b=datetime.fromtimestamp(ms/1000,timezone.utc)
                    weekend=a.weekday()==4 and b.weekday()==6 and 40*3600000<ms-previous<60*3600000
                    gaps.append({"after_ms":previous,"before_ms":ms,"seconds":(ms-previous)/1000,
                                 "classification":"weekend_pattern_not_certified" if weekend else "unresolved"})
                previous=ms;count+=1;writer.writerow(tick);yield tick
        bars=list(hourly(record()))
    if not count:raise ValueError("Empty research dataset")
    partial.rename(output/"ticks.csv.gz")
    with (output/"hourly-diagnostic.csv").open("x",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(bars[0]));writer.writeheader();writer.writerows(bars)
    metadata={**origin,"schema_version":1,"symbol":"EURUSD","role":"development","ticks":count,
              "first_ms":first,"last_ms":previous,"observed_hours":len(bars),"gaps_over_one_hour":gaps,
              "data_sha256":sha256(output/"ticks.csv.gz"),"hourly_sha256":sha256(output/"hourly-diagnostic.csv"),
              "code_sha256":code_digest(),"complete_market_history_verified":False,
              "provider_certified_clock":False,"broker_execution_conditions_verified":False,
              "limitations":["Bounded provisional development research only; no performance or forward validation",
                             "No feed splicing, interpolation or timestamp reordering",
                             "Clock interpretations are explicitly scoped assumptions supported by sampled evidence"]}
    write_json(output/"provenance.json",metadata)
    return metadata


def compare_hourly(left,right,lower_hour=None,upper_hour=None):
    def read(path):
        with path.open(newline="") as stream:
            return {int(r["hour"]):float(r["bid_close"]) for r in csv.DictReader(stream)}
    a,b=read(left),read(right)
    excluded=[h for h in b if lower_hour is not None and h<lower_hour or upper_hour is not None and h>=upper_hour]
    b={h:v for h,v in b.items() if h not in excluded}
    common=sorted(a.keys()&b.keys())
    errors=[abs(a[h]-b[h])/.0001 for h in common]
    return {"overlapping_hours":len(common),"reference_hours":len(b),
            "reference_hours_outside_requested_scope":excluded,
            "within_one_pip_fraction":sum(e<=1+1e-9 for e in errors)/len(errors) if errors else 0,
            "maximum_close_difference_pips":max(errors,default=None),
            "missing_reference_hours":sorted(b.keys()-a.keys()),
            "differences_over_one_pip":[{"utc_hour":h,"difference_pips":e} for h,e in zip(common,errors) if e>1+1e-9]}
