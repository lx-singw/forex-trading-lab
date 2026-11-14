"""Relative minute-label evidence; no clock certification or trading inputs."""
from decimal import Decimal
from statistics import median

MINUTE=60000
HYPOTHESES={'end_label':-MINUTE,'literal_start':0,'future_control':MINUTE}


def aggregate(ticks):
    bars={}; previous_time=previous_row=None
    for tick in ticks:
        stamp,source_row=tick['time_msc'],tick['source_row']
        if type(stamp) is not int or type(source_row) is not int or source_row<0:
            raise ValueError('Invalid tick timestamp/row')
        if previous_time is not None and (stamp<previous_time or source_row<=previous_row):
            raise ValueError('Tick reversal or repeated source row')
        bid,ask=Decimal(tick['bid']),Decimal(tick['ask'])
        if not bid.is_finite() or not ask.is_finite() or not 0<bid<=ask:
            raise ValueError('Invalid bid/ask quote')
        previous_time,previous_row=stamp,source_row
        minute=stamp//MINUTE*MINUTE
        if minute not in bars:
            bars[minute]={'minute_start_ms':minute,'quotes':0,'first_ms':stamp,
                'first_source_row':source_row,
                **{side+'_'+key:str(price) for side,price in [('bid',bid),('ask',ask)]
                   for key in ('open','high','low')}}
        bar=bars[minute];bar['quotes']+=1
        bar.update(last_ms=stamp,last_source_row=source_row)
        for side,price in [('bid',bid),('ask',ask)]:
            bar[side+'_high']=str(max(Decimal(bar[side+'_high']),price))
            bar[side+'_low']=str(min(Decimal(bar[side+'_low']),price))
            bar[side+'_close']=str(price)
    return bars


def distance(reference,bar):
    if reference is None or bar is None:return None
    return {key:float(abs(Decimal(reference[key])-Decimal(bar['bid_'+key]))*10000)
            for key in ('open','high','low','close')}


def compare(labels,reference,bars):
    labels=list(labels)
    if not labels or any(type(t) is not int or t%MINUTE for t in labels):
        raise ValueError('Invalid reference label grid')
    if labels!=sorted(set(labels)):raise ValueError('Duplicated or reversed label grid')
    rows=[];common={name:[] for name in HYPOTHESES};present={name:0 for name in HYPOTHESES}
    for stamp in labels:
        ref=reference.get(stamp)
        if ref is not None:
            prices=[Decimal(ref[k]) for k in ('open','high','low','close')]
            if not all(p.is_finite() and p>0 for p in prices) or not prices[2]<=min(prices[0],prices[3])<=max(prices[0],prices[3])<=prices[1]:
                raise ValueError('Invalid reference OHLC')
        interpretations={}
        for name,shift in HYPOTHESES.items():
            bar=bars.get(stamp+shift);delta=distance(ref,bar)
            interpretations[name]={'interval_start_ms':stamp+shift,'interval_end_exclusive_ms':stamp+shift+MINUTE,
                                   'tick_minute':bar,'absolute_ohlc_distance_pips':delta}
            present[name]+=delta is not None
        complete=all(v['absolute_ohlc_distance_pips'] is not None for v in interpretations.values())
        if complete:
            for name in common:common[name].append(interpretations[name]['absolute_ohlc_distance_pips']['close'])
        rows.append({'reference_label_ms':stamp,'reference':ref,'all_three_pairs_present':complete,
                     'interpretations':interpretations})
    medians={name:median(values) if values else None for name,values in common.items()}
    count=len(common['end_label'])
    passed=bool(count>=240 and medians['end_label']<=2
                and all(medians[name]>=medians['end_label']+.25 for name in ('literal_start','future_control')))
    return {'label_count':len(labels),'common_triplets':count,'paired_labels_by_hypothesis':present,
            'common_close_median_pips':medians,'relative_end_label_screen_pass':passed,'labels':rows}
