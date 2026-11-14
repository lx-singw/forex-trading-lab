"""Self-contained escaped local viewer, with future observations hidden by cursor."""
import html
import json


def render(report):
    # The viewer needs only three plotted alternatives. Full replay/checkpoint
    # trees belong in separate audit artifacts, not a repeated JavaScript literal.
    view={"bars":report["bars"],"limitations":report.get("limitations",[]),
          "ledger":{"events":[e for e in report["ledger"]["events"] if e["kind"] in ("entry","exit")]},
          "snapshots":[{k:v for k,v in s.items() if k in ("time","frame","reason","context")} |
                       {"counts":[{k:v for k,v in c.items() if k in ("id","family","state","side","pivot_records")}
                                  for c in s["counts"][:3]]} for s in report["snapshots"]]}
    data = json.dumps(view, default=str).replace("<", "\\u003c").replace("&", "\\u0026")
    return '''<!doctype html><meta charset="utf-8"><title>Elliott research replay</title>
<style>body{font:16px system-ui;max-width:1100px;margin:32px auto;background:#101925;color:#e2e8f0}input{width:100%}svg{background:#19283b;width:100%;height:300px}pre{white-space:pre-wrap}b{color:#73d8ca}</style>
<h1>Elliott research replay</h1><p><b>Invented software evidence</b> · market validation unavailable · orders unavailable</p>
<p id="limitations"></p><input id="cursor" type="range" min="0" value="0"><div id="stamp"></div><svg id="chart" viewBox="0 0 1000 300"></svg><pre id="detail"></pre>
<script>const report='''+data+'''; document.getElementById('limitations').textContent=report.limitations.join(' · ');const rows=report.snapshots;const cursor=document.getElementById('cursor');cursor.max=Math.max(0,rows.length-1);
function draw(){let i=Number(cursor.value),s=rows[i];if(!s)return;document.getElementById('stamp').textContent='Available at '+new Date(s.time).toISOString()+' · '+s.frame+' · '+s.reason;
const bs=report.bars.filter(b=>b.timeframe===s.frame&&b.available<=s.time).slice(-180);let ps=bs.map(b=>Number(b.close));let lo=Math.min(...ps),hi=Math.max(...ps);let points=ps.map((p,j)=>(10+j*980/Math.max(1,ps.length-1))+','+(280-260*(p-lo)/Math.max(1e-9,hi-lo))).join(' ');
const chart=document.getElementById('chart');chart.innerHTML='<polyline fill="none" stroke="#73d8ca" stroke-width="2" points="'+points+'"/>';
function element(tag,attrs,text){let e=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text!==undefined)e.textContent=text;chart.appendChild(e);}
const x=t=>10+980*(t-Number(bs[0]?.end||0))/Math.max(1,Number(bs.at(-1)?.end||1)-Number(bs[0]?.end||0));const y=p=>280-260*(Number(p)-lo)/Math.max(1e-9,hi-lo);
s.counts.slice(0,3).forEach((count,n)=>{const colors=['#ffc86a','#a69bff','#ef91af'];let pivots=(count.pivot_records||[]).filter(p=>p.available<=s.time&&p.time>=Number(bs[0]?.end||0));element('polyline',{points:pivots.map(p=>x(p.time)+','+y(p.price)).join(' '),fill:'none',stroke:colors[n],'stroke-dasharray':n?'5 4':'none'});pivots.forEach((p,j)=>element('text',{x:x(p.time),y:y(p.price)-8,fill:colors[n],'font-size':12},String(j)));element('text',{x:12,y:18+n*16,fill:colors[n],'font-size':12},(n?'Alternate: ':'Preferred: ')+count.family+' · '+count.state);});
let actions=report.ledger.events.filter(e=>['entry','exit'].includes(e.kind)&&Number(e.time)<=s.time);let held=actions.at(-1);if(held?.kind==='entry'){['stop','target'].forEach(k=>{element('line',{x1:0,x2:1000,y1:y(held[k]),y2:y(held[k]),stroke:k==='stop'?'#ff6b6b':'#80ed99','stroke-dasharray':'4 4'});element('text',{x:850,y:y(held[k])-4,fill:'#fff','font-size':12},k+' '+held[k]);});}
document.getElementById('detail').textContent=JSON.stringify(s,null,2);}
cursor.addEventListener('input',draw);draw();</script>'''
