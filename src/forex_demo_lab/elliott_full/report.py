"""Compact local as-known-then viewer, including execution-event cursor stops."""
import json


def _choices(snapshot):
    nodes={n["id"]:n for n in snapshot.get("counts",[])}
    pivots={p["id"]:p for n in nodes.values() for p in n.get("pivot_records",[])}
    records=[c for c in snapshot.get("interpretations",[]) if c["terminal"] in pivots]
    choices=[]
    if records:
        latest=max(pivots[c["terminal"]]["index"] for c in records)
        for c in records:
            if pivots[c["terminal"]]["index"]!=latest or not all(i in nodes for i in c["legs"]):
                continue
            legs=[nodes[i] for i in c["legs"]]
            anchors=[legs[0]["pivot_records"][0]]+[n["pivot_records"][-1] for n in legs]
            choices.append({"id":c["id"],"family":c["kind"]+" count","side":c["side"],"pivot_records":anchors,
                            "state":"unresolved parent" if c.get("unresolved_parent_location") else
                                    "valid_at_resolution" if c["resolved"] else "insufficient_resolution"})
    if not choices:
        choices=[{k:v for k,v in c.items() if k in ("id","family","state","side","pivot_records")}
                 for c in snapshot.get("counts",[])]
    unique={}
    for c in choices:
        key=(c["family"],c["side"],c["state"],tuple((p["index"],p["price"]) for p in c.get("pivot_records",[])))
        unique.setdefault(key,c)
    return list(unique.values())[:3]


def viewer_data(report):
    snapshots=[{k:v for k,v in s.items() if k in ("time","frame","reason","context","pattern_window")} |
               {"counts":_choices(s)} for s in report["snapshots"]]
    events=[e for e in report["ledger"]["events"] if e["kind"] in ("entry","exit")]
    rows=list(snapshots)
    for i,event in enumerate(events):
        time=int(event["time"])
        available=[s for s in snapshots if s["time"]<=time]
        preferred=[s for s in available if s["frame"]=="H1"]
        base=(preferred or available or [{"frame":"H1","counts":[],"context":{}}])[-1]
        rows.append({**base,"time":time,"reason":event["kind"]+(": "+event["reason"] if event["kind"]=="exit" else ""),
                     "event_index":i,"execution":event})
    rows.sort(key=lambda s:(s["time"],s.get("event_index",-1)))
    return {"bars":report["bars"],"limitations":report.get("limitations",[]),
            "ledger":{"events":events},"snapshots":rows}


def render(report):
    data=json.dumps(viewer_data(report),default=str).replace("<","\\u003c").replace("&","\\u0026")
    return '''<!doctype html><meta charset="utf-8"><title>Elliott research replay</title>
<style>body{font:16px system-ui;max-width:1100px;margin:32px auto;background:#101925;color:#e2e8f0}input{width:100%}svg{background:#19283b;width:100%;height:300px}pre{white-space:pre-wrap}b{color:#73d8ca}</style>
<h1>Elliott research replay</h1><p><b>Invented software evidence</b> · market validation unavailable · orders unavailable</p>
<p id="limitations"></p><label for="cursor">Replay time: candles and executions</label><input id="cursor" aria-label="Replay time" type="range" min="0" value="0"><div id="stamp"></div><svg id="chart" aria-label="Observed prices, counts and execution fills" viewBox="0 0 1000 300"></svg><pre id="detail"></pre>
<script>const report='''+data+''';document.getElementById('limitations').textContent=report.limitations.join(' · ');const rows=report.snapshots;const cursor=document.getElementById('cursor');cursor.max=Math.max(0,rows.length-1);
function draw(){const s=rows[Number(cursor.value)];if(!s)return;document.getElementById('stamp').textContent='Available at '+new Date(s.time).toISOString()+' · '+s.frame+' · '+s.reason;
const bs=report.bars.filter(b=>b.timeframe===s.frame&&b.available<=s.time).slice(-180);
const actions=s.event_index===undefined?report.ledger.events.filter(e=>Number(e.time)<=s.time):report.ledger.events.slice(0,s.event_index+1);
const entry=actions.filter(e=>e.kind==='entry').at(-1);const prices=bs.map(b=>Number(b.close));const fills=actions.map(e=>Number(e.kind==='entry'?e.entry:e.exit));const bounds=prices.concat(fills,entry?[Number(entry.stop),Number(entry.target)]:[]);const lo=bounds.length?Math.min(...bounds):0,hi=bounds.length?Math.max(...bounds):1;
const x=t=>10+980*(Number(t)-Number(bs[0]?.end||s.time))/Math.max(1,Math.max(s.time,Number(bs.at(-1)?.end||s.time))-Number(bs[0]?.end||s.time));const y=p=>280-250*(Number(p)-lo)/Math.max(1e-9,hi-lo);
const chart=document.getElementById('chart');chart.innerHTML='';function element(tag,attrs,text){let e=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text!==undefined)e.textContent=text;chart.appendChild(e);}
element('polyline',{points:bs.map(b=>x(b.end)+','+y(b.close)).join(' '),fill:'none',stroke:'#73d8ca','stroke-width':2});
s.counts.forEach((count,n)=>{const color=['#ffc86a','#a69bff','#ef91af'][n];const ps=(count.pivot_records||[]).filter(p=>p.available<=s.time&&p.time>=Number(bs[0]?.end||0));element('polyline',{points:ps.map(p=>x(p.time)+','+y(p.price)).join(' '),fill:'none',stroke:color,'stroke-dasharray':n?'5 4':'none'});ps.forEach((p,j)=>element('text',{x:x(p.time),y:y(p.price)-8,fill:color,'font-size':12},String(j)));element('text',{x:12,y:16+n*15,fill:color,'font-size':12},(n?'Alternate: ':'Preferred: ')+count.family+' · '+count.state);});
if(entry){['stop','target'].forEach(k=>{element('line',{x1:0,x2:1000,y1:y(entry[k]),y2:y(entry[k]),stroke:k==='stop'?'#ff6b6b':'#80ed99','stroke-dasharray':'4 4'});element('text',{x:820,y:y(entry[k])-4,fill:'#fff','font-size':12},'Original '+k+' '+entry[k]);});}
actions.slice(-8).forEach(e=>{let p=e.kind==='entry'?e.entry:e.exit;let color=e.kind==='entry'?'#86c5ff':'#ff938c';element('circle',{cx:x(e.time),cy:y(p),r:5,fill:color});element('text',{x:Math.min(850,x(e.time)+8),y:y(p)-8,fill:color,'font-size':12},e.kind==='entry'?'Entry fill':'Exit fill ('+e.reason+')');});
document.getElementById('detail').textContent=JSON.stringify(s,null,2);}
cursor.addEventListener('input',draw);draw();</script>'''
