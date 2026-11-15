"""Independent final receipt/file reconciliation. Self-consistency is not trust."""
import hashlib
import json
import re
from .native_journal_157 import CAP, IDENT, require
from .recorder_files_157 import check_files, read_file, folder_check

STATUS={'schema','token','challenge','operation','contained','running','sample_valid','sample_sequence','sample_tick_ms','owner_tick_ms','create_ack','set_ack','ready_signal','mains','helper_running_marker','cancel_ack'}
BOOLS=STATUS-{'schema','token','challenge','operation','sample_sequence','sample_tick_ms','owner_tick_ms'}


def pairs(items):
    result={}
    for key,value in items:require(key not in result);result[key]=value
    return result


def decode(raw,cap=CAP):
    require(type(raw) is bytes and 0<len(raw)<=cap)
    def constant(_):raise ValueError('relay157_constant')
    try:return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
    except (ValueError,UnicodeError,RecursionError):raise ValueError('relay157_json') from None


def uint(value,maximum=2**63-1):require(type(value) is int and 0<=value<=maximum);return value


def status(text,job,challenge,operation='POLL'):
    require(type(text) is str and IDENT.fullmatch(challenge) is not None)
    value=decode(text.encode('ascii'),2048)
    require(type(value) is dict and set(value)==STATUS and value['schema']=='native_health142_status_v1'
            and value['token']==job and value['challenge']==challenge and value['operation']==operation)
    for key in BOOLS:require(type(value[key]) is bool)
    for key in ('sample_sequence','sample_tick_ms','owner_tick_ms'):uint(value[key])
    require(value['contained'] and value['cancel_ack']==(operation=='CANCEL'));return value


def bind_responses(folder,native,responses):
    require(type(responses) is list and len(responses)==native['requests'] and len(responses)<=256)
    for index,(proof,lease) in enumerate(zip(responses,native['leases']),1):
        require(type(proof) is dict and set(proof)=={'ordinal','challenge','request_sha256','reply_sha256','published','sent_us','received_us','packet'})
        require(type(proof['ordinal']) is int and proof['ordinal']==index and proof['challenge']==lease['challenge'] and proof['published'] is True)
        value=status(proof['packet'],native['job'],proof['challenge'])
        require([value[k] for k in ('sample_sequence','sample_tick_ms','owner_tick_ms')]==[lease[k] for k in ('sequence','tick','owner')])
        for kind,key in (('Request','request_sha256'),('Reply','reply_sha256')):
            require(type(proof[key]) is str and re.fullmatch('[0-9a-f]{64}',proof[key]) is not None)
            require(hashlib.sha256(read_file(folder/f'{kind}{index:04d}.txt',512)).hexdigest()==proof[key])


def inspect_job(folder,job):
    """Reject incomplete receipts; report no caller ACK or native certification."""
    try:
        folder=folder_check(folder,job);require(read_file(folder/'Owner157.claim',64)==b'FXDL157_NO_RESUME\n')
        native=check_files(folder,job);receipt=decode(read_file(folder/'Relay157.json',CAP))
        require(type(receipt) is dict and set(receipt)=={'schema','job','cause','origin_us','active_end_us','last_us','budget_us','start_packet','probes','responses','cancel','exit','cleanup_complete','writer_complete','owner_exit_observed','native_sha256'})
        require(receipt['schema']=='relay157_receipt_v1' and receipt['job']==job and receipt['cause']=='complete'
                and receipt['cleanup_complete'] is True and receipt['writer_complete'] is True and receipt['owner_exit_observed'] is True)
        require(receipt['native_sha256']==native['native_sha256'])
        origin=uint(receipt['origin_us']);end=uint(receipt['active_end_us']);last=uint(receipt['last_us']);budget=uint(receipt['budget_us'],30_000_000)
        require(budget>0 and origin<=end<=last and end-origin<budget)
        start=decode(receipt['start_packet'].encode('ascii'),2048)
        require(set(start)=={'schema','token','contained','resumed','helper_pid'} and start['schema']=='native_health142_start_v1'
                and start['token']==job and start['contained'] is True and start['resumed'] is True
                and type(start['helper_pid']) is int and 0<start['helper_pid']<2**31)
        probes=receipt['probes'];require(type(probes) is list and 1<=len(probes)<=32)
        bind_responses(folder,native,receipt['responses'])
        previous=None;sample=None;observed=None;marker=origin;challenges=set();was_ready=False
        for probe,record in [(True,p) for p in probes]+[(False,p) for p in receipt['responses']]:
            if probe:require(type(record) is dict and set(record)=={'challenge','healthy','sent_us','received_us','packet'} and type(record['healthy']) is bool and not was_ready)
            challenge=record['challenge'];require(challenge not in challenges);challenges.add(challenge)
            sent=uint(record['sent_us']);received=uint(record['received_us'])
            require(marker<=sent<=received<=end and received-sent<=1_000_000);marker=received
            value=status(record['packet'],job,challenge);require(value['running'] and value['mains'])
            seq,tick,owner=[value[k] for k in ('sample_sequence','sample_tick_ms','owner_tick_ms')]
            if previous:require(owner>=previous[2])
            healthy=False
            if value['sample_valid']:
                require(seq>0 and tick<=owner)
                current=tuple(value[k] for k in ('sample_tick_ms','create_ack','set_ack','ready_signal','mains','helper_running_marker'))
                require(not value['ready_signal'] or all(value[k] for k in ('create_ack','set_ack','helper_running_marker')))
                at=sent-(owner-tick)*1000;require(at>=0)
                if previous:
                    require(seq>=previous[0] and tick>=previous[1])
                    if seq==previous[0]:require(current==sample);at=observed
                    else:require(at>=observed)
                previous=(seq,tick,owner);sample=current;observed=at
                healthy=all(value[k] for k in ('create_ack','set_ack','ready_signal','helper_running_marker'))
                if healthy:require(received-at<=1_000_000)
            else:require(previous is None)
            if probe:require(record['healthy']==healthy);was_ready=healthy
            else:require(was_ready and healthy)
        require(was_ready)
        cancel=receipt['cancel'];require(type(cancel) is dict and set(cancel)=={'challenge','packet'})
        status(cancel['packet'],job,cancel['challenge'],'CANCEL')
        exit_proof=receipt['exit'];require(type(exit_proof) is dict and set(exit_proof)=={'challenge','packet'} and IDENT.fullmatch(exit_proof['challenge']) is not None)
        exit_value=decode(exit_proof['packet'].encode('ascii'),2048)
        require(set(exit_value)=={'schema','token','challenge','exit_observed','cancel_ack','job_closed','clear_ack','close_ack','forced'}
                and exit_value['schema']=='native_health142_exit_v1' and exit_value['token']==job and exit_value['challenge']==exit_proof['challenge']
                and all(exit_value[k] is True for k in ('exit_observed','cancel_ack','job_closed','clear_ack','close_ack')) and exit_value['forced'] is False)
        result={k:v for k,v in native.items() if k!='leases'}
        result.update(relay_receipt_consistent=True,caller_acknowledgement_known=False,cleanup_claim_consistent=True)
        return result
    except (OSError,ValueError,TypeError,KeyError,AttributeError):raise ValueError('relay157_rejected') from None


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description='Check one explicit diagnostic job; no process launch or market admission.')
    parser.add_argument('--folder',required=True);parser.add_argument('--job',required=True)
    args=parser.parse_args(argv)
    try:result=inspect_job(args.folder,args.job)
    except ValueError:
        print(json.dumps(dict(error='relay157_rejected',market_eligible=False)));return 2
    print(json.dumps(result,sort_keys=True));return 0
