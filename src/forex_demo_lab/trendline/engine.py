"""Causal invented bar-by-bar lifecycle integration; no setup or order engine."""
import hashlib
import json

from ..elliott_full.contracts import Bar
from . import data, geometry as g, lines, selection as s, lifecycle as life, pivots

VERSION = "TRL_ENGINE_170_V1"
MAX_TRACE_BYTES = 32000000
MAX_CHECKPOINT_BYTES = 32000000
MAX_COMMANDS = 30000


def instance_id(line):
    return data.digest(["line_instance","EURUSD",line.profile,line.ray.timeframe,line.geometry_id,line.touch_ids])


def alias_groups(line,prior_states):
    """R5: alias only an exact union of prior same-scope strict-subset groups."""
    scope = (line.profile,line.ray.timeframe,line.ray.kind)
    prior = [state for state in prior_states
             if (state.line.profile,state.line.ray.timeframe,state.line.ray.kind) == scope
             and set(state.line.touch_ids) < set(line.touch_ids)]
    union = set().union(*(set(state.line.touch_ids) for state in prior))
    return tuple(sorted({state.group_id for state in prior})) if union == set(line.touch_ids) else ()


def bindings():
    result = life.bindings()
    for relative in ("src/forex_demo_lab/trendline/engine.py","scripts/trendline-replay-170.py"):
        result[relative] = hashlib.sha256((data.ROOT/relative).read_bytes()).hexdigest()
    return result


class Engine:
    def __init__(self,source,profile="TRL_BRK3_E1",timeframe="H4"):
        self.source = data.research_declaration(source)
        lines.validate_profile(profile,timeframe,"full")
        self.profile,self.timeframe = profile,timeframe
        self._scope = (profile,timeframe)
        self._source_sha = self.source.sha256
        self._source_json = self.source._json
        self._bindings = bindings()
        self._inspector = lines.Inspector(self.source,timeframe)
        self._journal = life.Journal(self.source,profile,timeframe)
        self._latest = None
        self._frames,self._commands = (),()
        self._views = {}
        self._trace_bytes = 0

    def _check(self):
        if (self.source._json != self._source_json or self._scope != (self.profile,self.timeframe)
                or self._bindings != bindings()):raise ValueError("engine source/profile/code bindings changed")

    @property
    def publications(self):return self._inspector.publications

    @property
    def clock(self):return self._inspector.clock

    @property
    def metrics(self):
        """Immutable indicator metrics for the most recent observed bar."""
        return self._inspector.metrics

    def _action_ids(self,inspector,snapshot,prior):
        report = snapshot.record()
        if (self.profile not in (*lines.STRATEGIES, lines.DLY_PROFILE)
                or report["search_incomplete"] or report["coverage_state"] != "CURRENT"):
            return ()
        observed = {i for i,_ in inspector.indexed}
        current = {c["id"]:c for c in report["candidates"] if c["profile_valid"]}
        result = []
        for state in prior:
            c = current.get(state.line.geometry_id)
            if (state.status == "VALID" and state.valid_since[2] < report["bar_index"]
                    and c is not None and tuple(c["touches"]["touch_ids"]) == state.line.touch_ids
                    and not self._journal.group_state(state.group_id)[1]
                    and all(i in observed for i in range(state.line.ray.a_index,report["bar_index"]+1))):
                result.append(state.line_id)
        return tuple(sorted(result))

    def observe(self,bar,*,declared_triggers=()):
        self._check()
        if not isinstance(bar,Bar):raise ValueError("typed completed bar required")
        bar = Bar(**bar.record())
        if not isinstance(declared_triggers,(list,tuple)):raise ValueError("explicit declared trigger ids required")
        for value in declared_triggers:data.sha(value)
        if len(set(declared_triggers)) != len(declared_triggers):raise ValueError("unique declared triggers required")
        triggers = tuple(sorted(declared_triggers))
        command = {"op":"BAR","bar":bar.record(),"declared_triggers":list(triggers)}
        if self.publications and bar == self.publications[-1]:
            previous = next(c for c in reversed(self._commands) if c["op"] == "BAR")
            if previous != command:raise ValueError("conflicting trigger retry on already committed bar")
            return self._last_bar_frame()
        staged = self._prepare_bar(bar)
        return self._finish_bar(bar, staged, triggers)

    def _prepare_bar(self, bar):
        self._bound()
        inspector = self._inspector.fork();inspector.observe(bar)
        full = s.from_inspector(inspector,self.profile,"full")
        action = s.from_inspector(inspector,self.profile,"action_break") if self.profile in lines.BREAK_PROFILES else full
        action_ids = self._action_ids(inspector,action,self._journal.states)
        return inspector, full, action, action_ids

    def _finish_bar(self, bar, staged, triggers):
        inspector, full, action, action_ids = staged
        command = {"op":"BAR","bar":bar.record(),"declared_triggers":list(triggers)}
        report = full.record();index = report["bar_index"]
        prior = self._journal.states
        if not set(triggers) <= set(action_ids):raise ValueError("declared trigger lacks pre-existing current eligible instance")
        journal = self._journal.fork();start_events = journal.event_count
        if triggers:journal.trigger_many(action,triggers)
        for state in journal.states:
            if (state.status not in life.TERMINAL and index > state.line.ray.a_index
                    and state.line.ray.correct_side_distance(index,bar.low if state.line.ray.kind == "support" else bar.high) < 0):
                journal.poke(full,state.line_id)
        for state in journal.states:
            if state.status not in life.TERMINAL and state.valid_since is not None and index-state.valid_since[2] > 500:
                journal.retire(full,state.line_id)
        for line in full.selected:
            line_id = instance_id(line)
            known = next((state for state in journal.states if state.line_id == line_id),None)
            if known is None:
                journal.register(full,line.geometry_id);journal.validate(full,line_id)
                groups = alias_groups(line,prior)
                if groups:
                    own = next(state.group_id for state in journal.states if state.line_id == line_id)
                    journal.merge_groups(full,sorted(set((*groups,own))))
            elif known.status == "CANDIDATE":journal.validate(full,line_id)
        for state in journal.states:
            if state.status in life.TERMINAL:continue
            replacement = next((line for line in full.selected
                                if line.ray.kind == state.line.ray.kind and set(state.line.touch_ids) < set(line.touch_ids)
                                and any(v.line_id == instance_id(line) and v.status == "VALID" for v in journal.states)),None)
            if replacement is not None:journal.retire(full,state.line_id,replacement_geometry_id=replacement.geometry_id)
        return self._commit(inspector,journal,full,command,action_ids,start_events)

    def _bound(self):
        if len(self._commands) >= MAX_COMMANDS:raise ValueError("bounded replay command count; no truncation")

    def advance(self,now):
        self._check();data.integer(now)
        if now == self.clock:return None if not self._frames else json.loads(self._frames[-1])
        self._bound()
        inspector = self._inspector.fork();inspector.advance(now)
        full = s.from_inspector(inspector,self.profile,"full")
        return self._commit(inspector,self._journal,full,{"op":"ADVANCE","now":now},(),self._journal.event_count)

    def _commit(self,inspector,journal,full,command,action_ids,start_events):
        report = full.record();index = report["bar_index"]
        selected = {instance_id(line) for line in full.selected}
        observed = {i for i,_ in inspector.indexed}
        global_reasons = list(report["snapshot_reasons"])
        metrics = inspector.metrics
        views,revisions = {},[]
        for state in journal.states:
            previous = self._views.get(state.line_id)
            old = None if previous is None else previous["view"]
            root,consumed = journal.group_state(state.group_id)
            terminal = state.status in life.TERMINAL
            frozen = old is not None and old["status"] in life.TERMINAL
            reasons = [state.status] if terminal else list(global_reasons)
            if consumed:reasons.append("GROUP_CONSUMED")
            if not terminal:
                if state.status != "VALID":reasons.append(state.status)
                if state.line_id not in selected:reasons.append("NOT_CURRENT_SELECTION")
                if index is None or not all(i in observed for i in range(state.line.ray.a_index,index+1)):
                    reasons.append("LINE_COVERAGE_INCOMPLETE")
            view = {"status":state.status,"geometry_id":state.line.geometry_id,"group_id":state.group_id,
                    "resolved_group":root,"group_consumed":consumed,
                    "touch_ids":list(state.line.touch_ids),"touch_indices":list(state.line.touch_indices),
                    "age_bars":old["age_bars"] if frozen else index-state.line.ray.a_index,
                    "line_value":old["line_value"] if frozen else g.rational_record(state.line.ray.value(index)),
                    "slope_tests":old["slope_tests"] if frozen else g.slope_tests(state.line.ray.slope,
                        None if metrics is None else metrics.atr_sma14,None if metrics is None else metrics.angle_range,
                        require_angle=self.profile == "TRL_FXR_M"),
                    "eligible":not reasons,"reasons":reasons,
                    "formed_now":False if terminal else state.valid_since is not None and state.valid_since[2] == index}
            if previous is None or view != old:
                revision = 1 if previous is None else previous["revision"]+1
                record = {"line_id":state.line_id,"revision":revision,
                          "previous":"0"*64 if previous is None else previous["id"],
                          "at":{"available_at":inspector.clock,"publication_ordinal":len(inspector.publications),"bar_index":index},
                          "view":view}
                record["id"] = data.digest(record);revisions.append(record);views[state.line_id] = record
            else:views[state.line_id] = previous
        frame = {"schema":VERSION,"event_type":command["op"],"as_of":inspector.clock,"bar_index":index,
                 "publication_ordinal":len(inspector.publications),"bar":command.get("bar"),
                 "search_incomplete":report["search_incomplete"],"coverage_state":report["coverage_state"],
                 "snapshot_reasons":global_reasons,"candidates":report["candidates"],"pair_rejections":report["pair_rejections"],
                 "selection":report["selection"],"revisions":revisions,
                 "eligible_line_ids":[instance_id(line) for line in full.selected if views[instance_id(line)]["view"]["eligible"]],
                 "action_line_ids":list(action_ids),"declared_trigger_ids":command.get("declared_triggers",[]),
                 "lifecycle_event_ids":[event["id"] for event in journal.events_since(start_events)],
                 "entry_ready":False,"orders_available":False,
                 "previous":"0"*64 if not self._frames else json.loads(self._frames[-1])["id"]}
        frame["id"] = data.digest(frame)
        encoded = data.canonical(frame).decode()
        if self._trace_bytes+len(encoded.encode()) > MAX_TRACE_BYTES:raise ValueError("bounded replay trace; no silent truncation")
        self._check()
        self._inspector,self._journal,self._latest = inspector,journal,full
        self._views = views
        self._frames = (*self._frames,encoded)
        self._commands = (*self._commands,json.loads(data.canonical(command)))
        self._trace_bytes += len(encoded.encode())
        return json.loads(encoded)

    def _last_bar_frame(self):
        return next(json.loads(frame) for frame in reversed(self._frames) if json.loads(frame)["event_type"] == "BAR")

    def report(self):
        self._check()
        return {"schema":VERSION,"kind":"invented_trendline_lifecycle_replay","data_level":"B",
                "profile":self.profile,"timeframe":self.timeframe,"declaration_sha256":self._source_sha,
                "input_sha256":self.source.record()["input_sha256"],"source_bindings":dict(self._bindings),
                "as_of":self.clock,"frames":[json.loads(frame) for frame in self._frames],
                "latest_views":json.loads(data.canonical([value for _,value in sorted(self._views.items())])),
                "journal":self._journal.report(),"latest_inspection":None if self._latest is None else self._latest.record(),
                "automatic_lifecycle_integrated":True,"trigger_detection_available":False,
                "actual_source_admitted":False,"market_cells_run":0,"returns_computed":False,
                "entry_ready":False,"orders_available":False,
                "limitations":["declared trigger interface only; no setup predicate or entry selection",
                                "historical VALID state is separate from current eligibility",
                                "checkpoint/trace bounds are software limits, not successful market qualification",
                                "invented replay provides software evidence only; actual source admission is open"]}

    def checkpoint(self):
        self._check()
        record = {"schema":VERSION,"kind":"invented_lifecycle_replay_checkpoint","declaration_sha256":self._source_sha,
                  "profile":self.profile,"timeframe":self.timeframe,"source_bindings":dict(self._bindings),
                  "commands":json.loads(data.canonical(self._commands)),"state_sha256":data.digest(self.report())}
        if len(data.canonical(record)) > MAX_CHECKPOINT_BYTES:raise ValueError("bounded replay checkpoint required")
        return record

    @classmethod
    def restore(cls,source,record):
        data.fields(record,("schema","kind","declaration_sha256","profile","timeframe","source_bindings","commands","state_sha256"))
        if len(data.canonical(record)) > MAX_CHECKPOINT_BYTES:raise ValueError("bounded replay checkpoint required")
        result = cls(source,record["profile"],record["timeframe"])
        if (record["schema"] != VERSION or record["kind"] != "invented_lifecycle_replay_checkpoint"
                or record["declaration_sha256"] != result._source_sha or record["source_bindings"] != result._bindings
                or not isinstance(record["commands"],list) or len(record["commands"]) > MAX_COMMANDS):
            raise ValueError("matching replay checkpoint bindings required")
        for index,command in enumerate(record["commands"],1):
            if command.get("op") == "BAR":
                data.fields(command,("op","bar","declared_triggers"))
                result.observe(Bar(**command["bar"]),declared_triggers=command["declared_triggers"])
            elif command.get("op") == "ADVANCE":
                data.fields(command,("op","now"));result.advance(command["now"])
            else:raise ValueError("known replay checkpoint command required")
            if len(result._commands) != index:raise ValueError("duplicate/no-op checkpoint command")
        if data.digest(result.report()) != record["state_sha256"]:raise ValueError("replay checkpoint state mismatch")
        return result
