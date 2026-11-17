"""Profile-local reduction and display ranking of already validated geometries."""
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json

from . import data, geometry as g, lines

VERSION = "TRL_SELECTION_169_V1"


def fraction(record):
    data.fields(record,("numerator","denominator"))
    n,d = record["numerator"],record["denominator"]
    if type(n) is not int or type(d) is not int or d <= 0:raise ValueError("exact rational record required")
    return Fraction(n,d)


@dataclass(frozen=True)
class ValidatedLine:
    geometry_id: str
    a_id: str
    b_id: str
    profile: str
    ray: g.Ray
    touch_ids: tuple
    touch_indices: tuple
    summed_distance: Fraction
    age: int

    def __post_init__(self):
        if not isinstance(self.ray,g.Ray):raise ValueError("typed ray required")
        lines.validate_profile(self.profile,self.ray.timeframe,"full")
        for value in (self.geometry_id,self.a_id,self.b_id,*self.touch_ids):data.sha(value)
        if (type(self.touch_ids) is not tuple or type(self.touch_indices) is not tuple
                or len(self.touch_ids) < 2 or len(self.touch_ids) != len(self.touch_indices)
                or len(set(self.touch_ids)) != len(self.touch_ids)):
            raise ValueError("unique ordered touch ids/indices required")
        for index in self.touch_indices:data.integer(index)
        data.integer(self.age)
        distance = g.exact(self.summed_distance)
        object.__setattr__(self,"summed_distance",distance)
        if (distance < 0 or any(b-a < 6 for a,b in zip(self.touch_indices,self.touch_indices[1:]))
                or self.a_id != self.touch_ids[0] or self.ray.a_index != self.touch_indices[0]
                or self.b_id not in self.touch_ids
                or self.ray.b_index != self.touch_indices[self.touch_ids.index(self.b_id)]
                or self.touch_indices[-1]+3 > self.touch_indices[0]+self.age
                or self.geometry_id != data.digest(["EURUSD",self.ray.timeframe,self.ray.kind,self.a_id,self.b_id])):
            raise ValueError("validated anchor/touch geometry metadata required")
        minimum = 2 if self.profile in ("TRL_BRK2_E1","TRL_BNC_E1") else 3
        if (len(self.touch_ids) < minimum or (self.profile == "TRL_BRK2_E1" and len(self.touch_ids) != 2)
                or (self.profile == "TRL_FXR_M" and self.span < 90)
                or (self.profile != "TRL_FXR_M" and self.age < (15 if self.ray.timeframe == "D1" else 30))):
            raise ValueError("frozen profile touch/age/span requirements required")

    @classmethod
    def from_candidate(cls,candidate,profile,timeframe):
        if (candidate.get("profile_valid") is not True or candidate.get("reasons") != []
                or candidate["profile_tests"]["passes"] is not True
                or candidate["profile_tests"]["reasons"] != []):
            raise ValueError("only fully profile-validated candidates can be reduced")
        r,t,m = candidate["ray"],candidate["touches"],candidate["profile_tests"]
        if r["timeframe"] != timeframe or t["reasons"] != [] or m["touch_count"] != len(t["touch_ids"]):
            raise ValueError("consistent profile/frame/touch metrics required")
        ray = g.Ray(r["kind"],r["a_index"],fraction(r["a_price"]),r["b_index"],fraction(r["b_price"]),timeframe)
        if fraction(r["slope"]) != ray.slope:raise ValueError("exact slope binding required")
        value = cls(candidate["id"],candidate["a_id"],candidate["b_id"],profile,ray,
                    tuple(t["touch_ids"]),tuple(t["touch_indices"]),fraction(t["summed_distance"]),m["age_bars"])
        if m["formation_span_bars"] != value.span:raise ValueError("formation span binding required")
        return value

    @classmethod
    def from_record(cls,value):
        data.fields(value,("geometry_id","a_id","b_id","profile","ray","touch_ids","touch_indices","summed_distance","age_bars"))
        r = value["ray"]
        ray = g.Ray(r["kind"],r["a_index"],fraction(r["a_price"]),r["b_index"],fraction(r["b_price"]),r["timeframe"])
        if r != ray.record():raise ValueError("canonical ray required")
        return cls(value["geometry_id"],value["a_id"],value["b_id"],value["profile"],ray,
                   tuple(value["touch_ids"]),tuple(value["touch_indices"]),fraction(value["summed_distance"]),value["age_bars"])

    @property
    def span(self):return self.touch_indices[-1]-self.touch_indices[0]

    @property
    def economic_key(self):
        return (-len(self.touch_ids),-self.age,-self.touch_indices[-1],self.touch_ids[0])

    @property
    def display_key(self):return (*self.economic_key,self.geometry_id)

    def record(self):
        return {"geometry_id":self.geometry_id,"a_id":self.a_id,"b_id":self.b_id,"profile":self.profile,
                "ray":self.ray.record(),"touch_ids":list(self.touch_ids),"touch_indices":list(self.touch_indices),
                "summed_distance":g.rational_record(self.summed_distance),"age_bars":self.age}


@dataclass(frozen=True)
class Reduction:
    kept: tuple
    discarded: tuple
    aliases: tuple

    def record(self):
        ties = {}
        for line in self.kept:ties.setdefault((line.profile,line.ray.timeframe,*line.economic_key),[]).append(line.geometry_id)
        return {"ranked":[line.record() for line in self.kept],
                "discarded":[{"profile":p,"timeframe":f,"geometry_id":i,"reason":r,"replaced_by":list(ids)} for p,f,i,r,ids in self.discarded],
                "aliases":[{"profile":p,"timeframe":f,"geometry_id":a,"representative":b} for p,f,a,b in self.aliases],
                "economic_ties":[{"profile":key[0],"timeframe":key[1],"geometry_ids":ids} for key,ids in sorted(ties.items()) if len(ids)>1],
                "trade_selection_available":False}


def reduce_lines(values):
    """Declared component API; typed metadata do not authenticate a source."""
    if not isinstance(values,(tuple,list)) or any(not isinstance(v,ValidatedLine) for v in values):
        raise ValueError("validated typed line collection required")
    by_id,frontiers = {},{}
    for value in values:
        scope = (value.profile,value.ray.timeframe)
        now = value.touch_indices[0]+value.age
        if scope in frontiers and frontiers[scope] != now:raise ValueError("one evaluation frontier per profile required")
        frontiers[scope] = now
        key = (value.profile,value.ray.timeframe,value.geometry_id)
        if key in by_id and by_id[key] != value:raise ValueError("conflicting duplicate geometry")
        by_id[key] = value
    groups = {}
    for value in by_id.values():
        groups.setdefault((value.profile,value.ray.timeframe,value.ray.kind,value.touch_ids),[]).append(value)
    representatives,discarded,aliases = [],[],[]
    for key,group in sorted(groups.items()):
        ordered = sorted(group,key=lambda v:(v.b_id != v.touch_ids[-1],v.summed_distance,v.geometry_id))
        winner = ordered[0];representatives.append(winner)
        for value in ordered[1:]:
            discarded.append((value.profile,value.ray.timeframe,value.geometry_id,"DUPLICATE_TOUCH_SET",(winner.geometry_id,)))
            aliases.append((value.profile,value.ray.timeframe,value.geometry_id,winner.geometry_id))
    def subset(a,b):
        return (a.profile,a.ray.timeframe,a.ray.kind) == (b.profile,b.ray.timeframe,b.ray.kind) and set(a.touch_ids) < set(b.touch_ids)
    kept = [a for a in representatives if not any(subset(a,b) for b in representatives)]
    for value in representatives:
        if value not in kept:
            discarded.append((value.profile,value.ray.timeframe,value.geometry_id,"STRICT_TOUCH_SUBSET",tuple(sorted(b.geometry_id for b in kept if subset(value,b)))))
    return Reduction(tuple(sorted(kept,key=lambda v:(v.profile,v.ray.timeframe,*v.display_key))),
                     tuple(sorted(discarded)),tuple(sorted(aliases)))


def bindings():
    result = lines.bindings()
    for relative in ("src/forex_demo_lab/trendline/selection.py","scripts/trendline-lines-169.py"):
        result[relative] = hashlib.sha256((data.ROOT/relative).read_bytes()).hexdigest()
    return result


@dataclass(frozen=True)
class SelectedSnapshot:
    _json: str
    selected: tuple

    def __post_init__(self):
        if type(self._json) is not str or type(self.selected) is not tuple or any(not isinstance(v,ValidatedLine) for v in self.selected):
            raise ValueError("immutable canonical snapshot and typed line tuple required")

    def record(self):return json.loads(self._json)


def select(source,bars,*,timeframe="H4",profile="TRL_BRK3_E1",role="full",as_of=None):
    bound = bindings()
    report = lines.inspect(source,bars,timeframe=timeframe,profile=profile,role=role,as_of=as_of)
    candidates = tuple(ValidatedLine.from_candidate(c,profile,timeframe) for c in report["candidates"] if c["profile_valid"])
    reduction = reduce_lines(candidates)
    publications = [bar for i,bar in enumerate(bars) if i == 0 or bar != bars[i-1]]
    report.update({"schema":VERSION,"kind":"invented_trendline_selection","source_bindings":bound,
                   "selection":reduction.record(),"publication_ordinal":len(publications),
                   "latest_bar":None if not publications else publications[-1].record(),
                   "lifecycle_integrated":False,"trade_selection_available":False})
    report["limitations"] = ["selection is display ranking, never an economic tie breaker",
                             "automatic lifecycle/trigger/group integration remains pending",
                             "actual source/run admission remains open"]
    if bindings() != bound:raise ValueError("selection source/protocol bindings changed")
    return SelectedSnapshot(data.canonical(report).decode(),reduction.kept)
