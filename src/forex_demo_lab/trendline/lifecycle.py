"""Append-only invented lifecycle commands; automatic replay integration pending.

This journal verifies transition/consumption rules. Declared trigger commands are
an interface for later setup machines, not proof of a detected break or bounce.
"""
from dataclasses import dataclass, replace
from copy import copy
import hashlib
import json

from ..elliott_full.contracts import Bar
from . import data, lines, selection as s

VERSION = "TRL_LIFECYCLE_169_V1"
MAX_EVENTS = 10000
MAX_CHECKPOINT_BYTES = 16000000
TERMINAL = ("POKED","TRIGGERED","RETIRED")


def bindings():
    result = s.bindings()
    relative = "src/forex_demo_lab/trendline/lifecycle.py"
    result[relative] = hashlib.sha256((data.ROOT/relative).read_bytes()).hexdigest()
    return result


@dataclass(frozen=True)
class State:
    line_id: str
    line: s.ValidatedLine
    group_id: str
    status: str
    revision: int
    valid_since: tuple | None

    def record(self):
        return {"line_id":self.line_id,"line":self.line.record(),"group_id":self.group_id,
                "status":self.status,"revision":self.revision,
                "valid_since":None if self.valid_since is None else list(self.valid_since)}


class Journal:
    def __init__(self,source,profile="TRL_BRK3_E1",timeframe="H4"):
        self.source = data.Declaration.from_record(source.record())
        lines.validate_profile(profile,timeframe,"full")
        self.profile,self.timeframe = profile,timeframe
        self._scope = (profile,timeframe)
        self._source_sha = self.source.sha256
        self._source_json = self.source._json
        self._bindings = bindings()
        self._states,self._parents,self._consumed,self._requests = {},{},{},{}
        self._events = ()
        self._cursor = None

    def _check(self):
        if (self.source._json != self._source_json or bindings() != self._bindings
                or (self.profile,self.timeframe) != self._scope):
            raise ValueError("journal source/protocol/code binding changed")

    def fork(self):
        self._check()
        result = copy(self)
        result._bindings = dict(self._bindings)
        for name in ("_states","_parents","_consumed","_requests"):
            setattr(result,name,dict(getattr(self,name)))
        return result

    @property
    def states(self):return tuple(value for _,value in sorted(self._states.items()))

    @property
    def event_count(self):return len(self._events)

    def events_since(self,index):
        data.integer(index)
        return json.loads(data.canonical(self._events[index:]))

    def group_state(self,group_id):
        root = self._root(self._parents,group_id)
        return root,self._consumed[root]

    def _verified(self,snapshot,*,full=False,require_search=True):
        self._check()
        if not isinstance(snapshot,s.SelectedSnapshot):raise ValueError("typed selected snapshot required")
        r = snapshot.record()
        if (r["schema"] != s.VERSION or r["kind"] != "invented_trendline_selection" or r["data_level"] != "B"
                or r["declaration_sha256"] != self._source_sha or r["source_bindings"] != s.bindings()
                or r["profile"] != self.profile or r["timeframe"] != self.timeframe
                or r["coverage_state"] != "CURRENT" or (require_search and r["search_incomplete"] is not False)
                or r["orders_available"] is not False or r["entry_ready"] is not False
                or r["selection"]["ranked"] != [v.record() for v in snapshot.selected]
                or (full and r["penetration_role"] != "full") or r["latest_bar"] is None):
            raise ValueError("matching current invented snapshot with required penetration checks needed")
        bar = Bar(**r["latest_bar"])
        index,ordinal = r["bar_index"],r["publication_ordinal"]
        data.integer(index);data.integer(ordinal);data.integer(r["as_of"]);data.sha(bar.lineage)
        windows = self.source.calendar.frame(self.timeframe)
        if (index >= len(windows) or ordinal == 0 or ordinal > index+1 or bar.timeframe != self.timeframe
                or (bar.start,bar.end) != (windows[index].start,windows[index].end)
                or bar.available < bar.end+self.source.calendar.delay or r["as_of"] < bar.available):
            raise ValueError("snapshot publication cursor binding required")
        return (bar.available,ordinal,index),bar

    def _selected(self,snapshot,geometry_id):
        value = next((v for v in snapshot.selected if v.geometry_id == geometry_id),None)
        if value is None or value.profile != self.profile or value.ray.timeframe != self.timeframe:
            raise ValueError("geometry must survive current profile-local selection")
        return value

    def register(self,snapshot,geometry_id):
        cursor,_ = self._verified(snapshot,full=True)
        line = self._selected(snapshot,geometry_id)
        return self._execute({"op":"REGISTER","cursor":list(cursor),"payload":{"line":line.record()}})

    def validate(self,snapshot,line_id):
        cursor,_ = self._verified(snapshot,full=True)
        old = self._states.get(line_id)
        if old is None:raise ValueError("registered line required")
        line = self._selected(snapshot,old.line.geometry_id)
        if line.touch_ids != old.line.touch_ids:raise ValueError("changed touches require a new line instance")
        return self._execute({"op":"VALID","cursor":list(cursor),"payload":{"line_id":line_id}})

    def poke(self,snapshot,line_id):
        cursor,bar = self._verified(snapshot,require_search=False)
        return self._execute({"op":"POKE","cursor":list(cursor),"payload":{"line_id":line_id,"bar":bar.record()}})

    def retire(self,snapshot,line_id,*,replacement_geometry_id=None):
        cursor,_ = self._verified(snapshot,full=True,require_search=replacement_geometry_id is not None)
        replacement = None if replacement_geometry_id is None else self._selected(snapshot,replacement_geometry_id).record()
        return self._execute({"op":"RETIRE","cursor":list(cursor),"payload":{"line_id":line_id,"replacement":replacement}})

    def trigger_many(self,snapshot,line_ids):
        cursor,_ = self._verified(snapshot)
        if not isinstance(line_ids,(list,tuple)):raise ValueError("explicit simultaneous line ids required")
        return self._execute({"op":"TRIGGER","cursor":list(cursor),"payload":{"line_ids":sorted(line_ids)}})

    def merge_groups(self,snapshot,group_ids):
        cursor,_ = self._verified(snapshot)
        if not isinstance(group_ids,(list,tuple)):raise ValueError("explicit alias groups required")
        return self._execute({"op":"MERGE","cursor":list(cursor),"payload":{"group_ids":sorted(group_ids)}})

    @staticmethod
    def _root(parents,key):
        if key not in parents:raise ValueError("known opportunity group required")
        while parents[key] != key:key = parents[key]
        return key

    def _execute(self,command):
        self._check()
        data.fields(command,("op","cursor","payload"))
        cursor = command["cursor"]
        if not isinstance(cursor,list) or len(cursor) != 3:raise ValueError("three-part frame cursor required")
        for value in cursor:data.integer(value)
        cursor = tuple(cursor)
        cal = self.source.calendar
        windows = cal.frame(self.timeframe)
        if (cursor[2] >= len(windows) or cursor[1] == 0 or cursor[1] > cursor[2]+1
                or not windows[cursor[2]].end+cal.delay <= cursor[0] <= cal.end+60000):
            raise ValueError("bounded declared publication cursor required")
        request = data.digest(command)
        if request in self._requests:return self._requests[request]
        if self._cursor is not None and any(a < b for a,b in zip(cursor,self._cursor)):
            raise ValueError("journal cursor reversal")
        if len(self._events) >= MAX_EVENTS:raise ValueError("journal event bound; no truncation")
        states,parents,consumed = dict(self._states),dict(self._parents),dict(self._consumed)
        payload,op = command["payload"],command["op"]
        result = None
        if op == "REGISTER":
            data.fields(payload,("line",))
            line = s.ValidatedLine.from_record(payload["line"])
            if (line.profile != self.profile or line.ray.timeframe != self.timeframe
                    or line.touch_indices[0]+line.age != cursor[2]):raise ValueError("registration frame/index binding required")
            result = data.digest(["line_instance","EURUSD",self.profile,self.timeframe,line.geometry_id,line.touch_ids])
            if result in states:raise ValueError("existing line instance cannot be reset")
            group = data.digest(["opportunity","EURUSD",self.profile,self.timeframe,line.ray.kind,line.touch_ids])
            parents.setdefault(group,group);consumed.setdefault(group,False)
            states[result] = State(result,line,group,"CANDIDATE",1,None)
        elif op == "MERGE":
            data.fields(payload,("group_ids",))
            ids = payload["group_ids"]
            if not isinstance(ids,list) or not ids or len(set(ids)) != len(ids):raise ValueError("unique explicit alias groups required")
            roots = sorted({self._root(parents,i) for i in ids});result = roots[0]
            kinds = {state.line.ray.kind for state in states.values() if self._root(parents,state.group_id) in roots}
            if len(kinds) != 1:raise ValueError("aliases must share a line kind")
            was_consumed = any(consumed[i] for i in roots)
            for root in roots:parents[root] = result
            consumed[result] = was_consumed
        elif op == "TRIGGER":
            data.fields(payload,("line_ids",))
            ids = payload["line_ids"]
            if not isinstance(ids,list) or not ids or len(set(ids)) != len(ids):raise ValueError("unique simultaneous triggers required")
            for line_id in ids:
                old = states.get(line_id)
                if (old is None or old.status != "VALID" or old.valid_since is None
                        or cursor[2] <= old.valid_since[2] or cursor[1] <= old.valid_since[1]
                        or consumed[self._root(parents,old.group_id)]):
                    raise ValueError("pre-existing valid line and open opportunity required")
            for line_id in ids:
                old = states[line_id]
                consumed[self._root(parents,old.group_id)] = True
                states[line_id] = replace(old,status="TRIGGERED",revision=old.revision+1)
            result = tuple(ids)
        elif op in ("VALID","POKE","RETIRE"):
            fields = {"VALID":("line_id",),"POKE":("line_id","bar"),"RETIRE":("line_id","replacement")}[op]
            data.fields(payload,fields)
            old = states.get(payload["line_id"])
            if old is None or old.status in TERMINAL:raise ValueError("nonterminal registered line required")
            if op == "VALID":
                if old.status != "CANDIDATE":raise ValueError("candidate-to-valid transition required")
                updated = replace(old,status="VALID",valid_since=cursor,revision=old.revision+1)
            elif op == "POKE":
                bar = Bar(**payload["bar"]);data.sha(bar.lineage)
                window = windows[cursor[2]]
                if ((bar.start,bar.end,bar.available,bar.timeframe) != (window.start,window.end,cursor[0],self.timeframe)
                        or cursor[2] <= old.line.ray.a_index
                        or old.line.ray.correct_side_distance(cursor[2],bar.low if old.line.ray.kind == "support" else bar.high) >= 0):
                    raise ValueError("strict completed-bar penetration required")
                updated = replace(old,status="POKED",revision=old.revision+1)
            else:
                replacement = None if payload["replacement"] is None else s.ValidatedLine.from_record(payload["replacement"])
                if replacement is None:
                    if old.valid_since is None or cursor[2]-old.valid_since[2] <= 500:
                        raise ValueError("retirement requires more than500 valid untriggered bars")
                elif ((replacement.profile,replacement.ray.timeframe,replacement.ray.kind) !=
                      (old.line.profile,old.line.ray.timeframe,old.line.ray.kind)
                      or not set(old.line.touch_ids) < set(replacement.touch_ids)
                      or replacement.touch_indices[0]+replacement.age != cursor[2]):
                    raise ValueError("validated same-profile strict-superset replacement required")
                updated = replace(old,status="RETIRED",revision=old.revision+1)
            states[old.line_id] = updated;result = old.line_id
        else:raise ValueError("known lifecycle command required")
        previous = "0"*64 if not self._events else self._events[-1]["id"]
        event = {"sequence":len(self._events)+1,"previous":previous,"command":json.loads(data.canonical(command)),
                 "id":data.digest([previous,len(self._events)+1,command])}
        # Validation and derivation complete before committing any mutable frontier.
        self._states,self._parents,self._consumed = states,parents,consumed
        self._cursor = cursor
        self._events = (*self._events,event)
        self._requests[request] = result
        return result

    def _summary(self):
        return {"cursor":None if self._cursor is None else list(self._cursor),
                "lines":[{**state.record(),"resolved_group":self._root(self._parents,state.group_id),
                           "group_consumed":self._consumed[self._root(self._parents,state.group_id)]}
                          for _,state in sorted(self._states.items())],
                "groups":[{"id":i,"root":self._root(self._parents,i),
                           "consumed":self._consumed[self._root(self._parents,i)]} for i in sorted(self._parents)]}

    def report(self):
        self._check()
        return {"schema":VERSION,"kind":"invented_lifecycle_journal","data_level":"B",
                "source_bindings":dict(self._bindings),"declaration_sha256":self._source_sha,
                "profile":self.profile,"timeframe":self.timeframe,**self._summary(),
                "events":json.loads(data.canonical(self._events)),"entry_ready":False,"orders_available":False,
                "automatic_bar_replay":False,"trigger_detection_available":False,
                "limitations":["explicit source-bound lifecycle commands; not automatic transition inference",
                                "declared trigger interface does not detect a break/bounce or approve an entry",
                                "alias-merge decisions belong to later integration; consumed state always unions",
                                "checkpoint integrity is not source authentication or permission"]}

    def checkpoint(self):
        self._check()
        return {"schema":VERSION,"kind":"invented_lifecycle_checkpoint","declaration_sha256":self._source_sha,
                "profile":self.profile,"timeframe":self.timeframe,"source_bindings":dict(self._bindings),
                "events":json.loads(data.canonical(self._events)),"state_sha256":data.digest(self._summary())}

    @classmethod
    def restore(cls,source,record):
        data.fields(record,("schema","kind","declaration_sha256","profile","timeframe","source_bindings","events","state_sha256"))
        if len(data.canonical(record)) > MAX_CHECKPOINT_BYTES:raise ValueError("bounded checkpoint required")
        result = cls(source,record["profile"],record["timeframe"])
        if (record["schema"] != VERSION or record["kind"] != "invented_lifecycle_checkpoint"
                or record["declaration_sha256"] != result._source_sha or record["source_bindings"] != result._bindings
                or not isinstance(record["events"],list) or len(record["events"]) > MAX_EVENTS):
            raise ValueError("matching invented checkpoint bindings required")
        for sequence,event in enumerate(record["events"],1):
            result._execute(event["command"])
            if len(result._events) != sequence or event != result._events[-1]:raise ValueError("checkpoint event chain or legal replay mismatch")
        if data.digest(result._summary()) != record["state_sha256"]:raise ValueError("checkpoint state mismatch")
        return result
