"""Independent cached-stream reconstruction and all-three-interval arithmetic."""
import csv
from datetime import datetime,timezone
from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path

DAYS=('2022-01-07','2022-07-08','2022-11-04','2023-01-06','2023-07-07','2023-11-03')
EPOCH=datetime(1970,1,1)
SHIFTS={'end_label':-60000,'literal_start':0,'future_control':60000}


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def bounds(day):
    base=(datetime.strptime(day,'%Y-%m-%d')-EPOCH).days*86400000
    return base+36000000,base+54000000


def reconstruct(day,source):
    start,end=bounds(day);bars={};previous=None;last_source=None
    if source=='broker':path=Path(f'data/clock-012/{day}/ticks.csv.gz')
    else:path=Path(f'data/normalization-015/{day[:7].replace("-","")}/ticks.csv.gz')
    with gzip.open(path,'rt',newline='') as f:
        reader=csv.reader(f);header=next(reader)
        expected=['sequence','time_msc','bid','ask','flags'] if source=='broker' else [
            'sequence','source_sequence','source_label','candidate_time_msc','bid','ask','volume']
        if header!=expected:raise ValueError('Independent schema differs')
        for sequence,fields in enumerate(reader):
            if int(fields[0])!=sequence:raise ValueError('Independent sequence differs')
            if source=='broker':
                stamp=int(fields[1])-(3 if day[5:7]=='07' else 2)*3600000
                source_row=sequence;bid,ask=fields[2:4]
            else:
                if not fields[2].startswith(day):continue
                delta=datetime.fromisoformat(fields[2])-EPOCH
                manual=delta.days*86400000+delta.seconds*1000+delta.microseconds//1000
                manual+=(4 if day[5:7]=='07' else 5)*3600000
                stamp=int(fields[3])
                if stamp!=manual:raise ValueError('Selected candidate calendar differs')
                source_row=int(fields[1]);bid,ask=fields[4:6]
            if not start<=stamp<end:continue
            if previous is not None and (stamp<previous or source_row<=last_source):
                raise ValueError('Independent quote order differs')
            previous,last_source=stamp,source_row
            bid,ask=Decimal(bid),Decimal(ask)
            if not bid.is_finite() or not ask.is_finite() or not 0<bid<=ask:raise ValueError('Independent price invalid')
            key=stamp-stamp%60000
            if key not in bars:
                bars[key]={'minute_start_ms':key,'quotes':0,'first_ms':stamp,'first_source_row':source_row,
                    **{side+'_'+k:str(price) for side,price in [('bid',bid),('ask',ask)] for k in ('open','high','low')}}
            bar=bars[key];bar['quotes']+=1;bar.update(last_ms=stamp,last_source_row=source_row)
            for side,price in [('bid',bid),('ask',ask)]:
                bar[side+'_high']=str(max(Decimal(bar[side+'_high']),price))
                bar[side+'_low']=str(min(Decimal(bar[side+'_low']),price))
                bar[side+'_close']=str(price)
    return bars


def check():
    ledger_path=Path('reports/labels-017-ledger.json');ledger=json.loads(ledger_path.read_text())
    if sha(ledger_path)!=json.loads(Path('reports/labels-017-seal.json').read_text())['ledger_sha256']:
        raise ValueError('Independent label ledger seal differs')
    if sha('reports/labels-017-source.zip')!=ledger['archive_sha256']:raise ValueError('Source archive differs')
    for p,digest in ledger['file_bindings'].items():
        if sha(p)!=digest:raise ValueError('Bound input changed')
    review_path=Path('reports/labels-017-review.json');review=json.loads(review_path.read_text())
    if len(review['pairs'])!=12 or {(p['day'],p['tick_source']) for p in review['pairs']}!={(d,s) for d in DAYS for s in ('broker','histdata')}:
        raise ValueError('Independent scope differs')
    if any(review[k] for k in ('absolute_utc_certified','performance_evaluation_ready','demo_execution_ready','original_provider_bar_semantics_verified')):
        raise ValueError('Diagnostic evidence promoted')
    reference={}
    with Path('data/reference-016/diagnostic-minute-lineage.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            stamp=int(row['reference_time_msc'])
            if stamp in reference:raise ValueError('Reference overlap')
            reference[stamp]={k:row[k] for k in ('open','high','low','close')}
    minute_count=quotes=labels_checked=0;broker_pass=[]
    for summary in review['pairs']:
        path=Path(summary['report'])
        if sha(path)!=summary['report_sha256']:raise ValueError('Pair report changed')
        saved=json.loads(path.read_text());day,source=summary['day'],summary['tick_source']
        bars=reconstruct(day,source)
        if list(bars.values())!=saved['minute_bars']:raise ValueError('Independent minute aggregate differs')
        minute_count+=len(bars);quotes+=sum(b['quotes'] for b in bars.values())
        start,end=bounds(day);labels=list(range(start+60000,end-60000,60000))
        expected_rows=[];common={name:[] for name in SHIFTS};paired={name:0 for name in SHIFTS}
        for label in labels:
            ref=reference.get(label);interpretations={}
            for name,shift in SHIFTS.items():
                bar=bars.get(label+shift);delta=None
                if ref is not None and bar is not None:
                    delta={k:float(abs(Decimal(ref[k])-Decimal(bar['bid_'+k]))/Decimal('0.0001'))
                           for k in ('open','high','low','close')}
                    paired[name]+=1
                interpretations[name]={'interval_start_ms':label+shift,'interval_end_exclusive_ms':label+shift+60000,
                                        'tick_minute':bar,'absolute_ohlc_distance_pips':delta}
            complete=all(v['absolute_ohlc_distance_pips'] is not None for v in interpretations.values())
            if complete:
                for name in common:common[name].append(interpretations[name]['absolute_ohlc_distance_pips']['close'])
            expected_rows.append({'reference_label_ms':label,'reference':ref,'all_three_pairs_present':complete,
                                  'interpretations':interpretations})
        if expected_rows!=saved['labels']:raise ValueError('Independent interval/price comparison differs')
        labels_checked+=len(labels)
        medians={}
        for name,values in common.items():
            values.sort();n=len(values)
            medians[name]=(values[(n-1)//2]+values[n//2])/2 if n else None
        count=len(common['end_label'])
        passed=bool(count>=240 and medians['end_label']<=2 and
                    medians['literal_start']>=medians['end_label']+.25 and medians['future_control']>=medians['end_label']+.25)
        expected={'label_count':298,'common_triplets':count,'paired_labels_by_hypothesis':paired,
                  'common_close_median_pips':medians,'relative_end_label_screen_pass':passed}
        if any(saved[k]!=v or summary[k]!=v for k,v in expected.items()):raise ValueError('Independent summary differs')
        if source=='broker':broker_pass.append(passed)
        print(json.dumps({'day':day,'source':source,'minutes_checked':len(bars),'labels_checked':298}),flush=True)
    if all(broker_pass)!=review['all_six_broker_screens_pass']:raise ValueError('Broker inference differs')
    result={'kind':'independent_minute_label_check_017','review_sha256':sha(review_path),
        'ledger_sha256':sha(ledger_path),'pairs_checked':12,'minute_bars_checked':minute_count,
        'selected_quotes_checked':quotes,'reference_labels_checked':labels_checked,
        'interval_comparisons_checked':labels_checked*3,'all_arithmetic_matches':True,
        'absolute_utc_certified':False,'performance_evaluation_ready':False,'demo_execution_ready':False}
    with Path('reports/labels-017-independent.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':check()
