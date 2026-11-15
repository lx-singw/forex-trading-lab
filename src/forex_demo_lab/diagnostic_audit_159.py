"""Independent159 source/three-journal/acknowledged-prefix reconciliation."""
import re
from pathlib import Path
from .diagnostic_source_159 import capture,sha
from .paired_replay_133 import canonical,strict_json,DENIED
from .segment_journal_138 import inspect_segments
from .supervision_140 import inspect_ledger
from .recorder_files_157 import read_file

ZERO='0'*64
HASH=re.compile('[a-f0-9]{64}')


def need(condition):
    if not condition:raise ValueError('bridge159_rejected')


def inspect(output,source_folder):
    try:return _inspect(Path(output),source_folder)
    except (OSError,ValueError,KeyError,TypeError,IndexError,AttributeError):raise ValueError('bridge159_rejected') from None


def _inspect(root,source_folder):
    need(root.is_dir() and not any(p.is_symlink() for p in (root,*root.absolute().parents)))
    source_raw=read_file(root/'Source159.json',1024*1024);source=strict_json(source_raw,1024*1024)
    need(canonical(source)+b'\n'==source_raw and capture(source_folder,source['source_job'])==source)
    source_hash=sha(canonical(source));raw=read_file(root/'Binding159.journal',131072)
    lines=raw.split(b'\n');tail=lines.pop();need(len(tail)<8192 and len(lines)<=16 and lines)
    rows=[];heads={ZERO:0};head=ZERO;last=0;job=None
    fields={'schema','job','sequence','previous','event','at_us','source_sha256','source_ref','context_binding','life_head','segment','slot'}
    for index,line in enumerate(lines,1):
        need(0<len(line)<8192);body,digest=line.rsplit(b'\t',1);row=strict_json(body,8192)
        need(set(row)==fields and canonical(row)==body and sha(body).encode()==digest and row['previous']==head and row['sequence']==index)
        need(row['schema']=='invented_diagnostic_bridge159_v1' and row['source_sha256']==source_hash)
        need(type(row['job']) is str and re.fullmatch('[a-f0-9]{32}',row['job']) is not None and row['job']!=source['source_job'])
        if job is None:job=row['job']
        need(row['job']==job)
        for key in ('sequence','at_us','segment','slot'):need(type(row[key]) is int and 0<=row[key]<2**64)
        need(row['at_us']>=last and type(row['life_head']) is str and HASH.fullmatch(row['life_head']) is not None)
        head=digest.decode();heads[head]=index;row['_head']=head;rows.append(row);last=row['at_us']
    directory=root/('InventedJob138-'+job);segments=[]
    if directory.exists():
        need(not directory.is_symlink());entries=[]
        for entry in directory.iterdir():entries.append(entry);need(len(entries)<=64)
        need(all(re.fullmatch('Segment[0-9]{4}\\.journal',p.name) for p in entries))
        for index,entry in enumerate(sorted(entries),1):
            need(entry.name==f'Segment{index:04d}.journal');segments.append(read_file(entry,65536))
    life=inspect_segments(segments) if segments else None
    supervisor_raw=read_file(root/('Supervisor140-'+job+'.journal'),65536)
    supervision=inspect_ledger(supervisor_raw)
    refs={ZERO:dict(segment=0,committed_sequence=0,event=None,at_us=0)}
    for segment in segments:
        for line in segment.split(b'\n')[:-1]:
            body,digest=line.rsplit(b'\t',1);value=strict_json(body,1024);need(value['job']==job);refs[digest.decode()]=value
    super_heads={ZERO};last_super=None
    for line in supervisor_raw.split(b'\n')[:-1]:
        body,digest=line.rsplit(b'\t',1);value=strict_json(body,2048)
        need(value['job']==job and value['life_head'] in refs and refs[value['life_head']]['committed_sequence']==value['life_committed'])
        super_heads.add(digest.decode());last_super=value
    if supervision['stopped_record_present'] and not last_super['life_poisoned']:need(last_super['life_head']==next(reversed(refs)))
    state=None;context_head=None;context_segment=None;begin_head=None;physical=0
    allowed={None:{'open'},'open':{'context','end'},'context':{'begin','end'},'begin':{'prepared','abort'},'prepared':{'commit','abort'},'commit':{'end'},'abort':{'end'},'end':set()}
    for row in rows:
        event=row['event'];need(event in allowed[state]);ref=refs[row['life_head']]
        need(row['segment']==ref['segment'] and row['at_us']>=ref['at_us'])
        if event=='open':need(row['life_head']==ZERO and row['slot']==0 and row['source_ref'] is None and row['context_binding'] is None)
        elif event=='context':
            need(ref['event']=='context' and ref['committed_sequence']==0 and row['slot']==0 and row['context_binding'] is None and row['source_ref']==source['context_sha256'])
            context_head=row['_head'];context_segment=row['segment']
        elif event in ('begin','prepared','commit','abort'):
            need(context_head is not None and row['context_binding']==context_head and row['segment']==context_segment and row['slot']==1 and row['source_ref']==source['triple_sha256'])
            if event=='begin':need(ref['event']=='triple_begin' and ref['sequence']==1);begin_head=row['life_head']
            if event=='prepared':need(row['life_head']==begin_head)
            if event=='commit':need(ref['event']=='triple_commit' and ref['sequence']==1 and ref['committed_sequence']==1);physical+=1
            if event=='abort':need(ref['committed_sequence']==0)
        elif event=='end':need(row['slot']==0 and row['source_ref'] is None and row['context_binding']==context_head)
        state=event
    receipt_path=root/'Receipt159.json';receipt=None;ack_count=None;published=0
    if receipt_path.exists() or receipt_path.is_symlink():
        receipt_raw=read_file(receipt_path,1024*1024);receipt=strict_json(receipt_raw,1024*1024)
        need(set(receipt)=={'schema','job','source_sha256','binding_ack_head','life_ack_head','supervision_ack_head','binding_commit_acks','binding_close_ack','publishable','fault','market_eligible','caller_acknowledgement_known'})
        need(canonical(receipt)+b'\n'==receipt_raw and receipt['schema']=='invented_bridge159_receipt_v1' and receipt['job']==job and receipt['source_sha256']==source_hash)
        for key in ('binding_close_ack','publishable','market_eligible','caller_acknowledgement_known'):need(type(receipt[key]) is bool)
        need(not receipt['market_eligible'] and not receipt['caller_acknowledgement_known'])
        need(receipt['binding_ack_head'] in heads and receipt['life_ack_head'] in refs and receipt['supervision_ack_head'] in super_heads)
        ack_index=heads[receipt['binding_ack_head']];ack_count=sum(r['event']=='commit' for r in rows[:ack_index])
        need(type(receipt['binding_commit_acks']) is int and receipt['binding_commit_acks']==ack_count)
        faults={'start_guard','start_storage','context_guard','context_lifecycle','context_storage','begin_guard','begin_storage','prepare_guard','prepare_storage','source_changed','commit_guard','commit_storage','finish_guard','finish_storage','explicit_abort','receipt_write'}
        need(receipt['fault'] is None or receipt['fault'] in faults)
        if receipt['publishable']:
            need(receipt['fault'] is None and receipt['binding_close_ack'] and ack_count==1 and not tail and ack_index==len(rows) and state=='end')
            need(life is not None and life['final_close_present'] and not life['pending_triple'] and supervision['stopped_record_present'] and supervision['cancel_ack'] is True and supervision['exit_ack'] is True)
            need(life['trailing_partial_bytes']==0 and supervision['trailing_partial_bytes']==0)
            need(receipt['life_ack_head']==next(reversed(refs)) and receipt['supervision_ack_head']==supervisor_raw.splitlines()[-1].rsplit(b'\t',1)[1].decode())
            published=1
    lifecycle_commits=0 if life is None else life['committed_sequence_present']
    return dict(schema='invented_bridge159_inspection_v1',profile=source['profile'],source_manifest_matched=True,physical_binding_commits=physical,
                acknowledged_binding_commits=ack_count,published_diagnostic_triples=published,unpublished_lifecycle_commits=lifecycle_commits-published,
                lifecycle_pending=False if life is None else life['pending_triple'],binding_partial_bytes=len(tail),receipt_present=receipt is not None,
                ended=state=='end',supervision_unobserved_lifecycle_suffix=last_super['life_head']!=next(reversed(refs)),
                caller_acknowledgement_known=False,resume_available=False,replay_clock_only=True,invented_payload_profile_only=True,
                replay_checks_are_invented=True,live_source_admission_available=False,market_eligible=False,**DENIED)


def main(argv=None):
    import argparse,json
    parser=argparse.ArgumentParser(description='Inspect one offline invented159 bridge; no native activity.')
    parser.add_argument('--output',required=True);parser.add_argument('--source',required=True);args=parser.parse_args(argv)
    try:value=inspect(args.output,args.source)
    except ValueError:print(json.dumps(dict(error='bridge159_rejected',market_eligible=False)));return 2
    print(json.dumps(value,sort_keys=True));return 0
