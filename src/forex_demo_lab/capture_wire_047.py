"""Closed binary fixture protocol. No IPC, accounts, quotes or execution."""
import struct
from .capture_budget_047 import Policy,VERSION,receipt_valid,PermitRejected
REQUEST=struct.Struct('<8s16s32s')
RESPONSE=struct.Struct('<8s16s32sIQQQ')

def encode_request(policy):
    if type(policy) is not Policy:raise PermitRejected('wire_policy_rejected')
    return REQUEST.pack(b'FXDL047Q',bytes.fromhex(policy.phase),bytes.fromhex(policy.digest))

def decode_request(raw,policy):
    if type(raw) is not bytes or len(raw)!=REQUEST.size:raise PermitRejected('request_length_rejected')
    if raw!=encode_request(policy):raise PermitRejected('request_binding_rejected')
    return policy.phase,policy.digest

def encode_response(receipt):
    keys={'version','phase','policy_sha256','permission','issued_boot_ms','expires_boot_ms','expires_utc_ms'}
    try:
        if type(receipt) is not dict or set(receipt)!=keys or receipt['version']!=VERSION:raise ValueError()
        p=Policy(receipt['phase'],receipt['policy_sha256'])
        integers=[receipt[k] for k in ('permission','issued_boot_ms','expires_boot_ms','expires_utc_ms')]
        if any(type(x) is not int for x in integers) or integers[0]!=1:raise ValueError()
        return RESPONSE.pack(b'FXDL047R',bytes.fromhex(p.phase),bytes.fromhex(p.digest),*integers)
    except Exception:raise PermitRejected('response_schema_rejected') from None

def decode_response(raw,policy,utc_ms,boot_ms):
    if type(raw) is not bytes or len(raw)!=RESPONSE.size:raise PermitRejected('response_length_rejected')
    magic,phase,digest,permission,issued,expires,utc=RESPONSE.unpack(raw)
    if magic!=b'FXDL047R':raise PermitRejected('response_magic_rejected')
    r=dict(version=VERSION,phase=phase.hex(),policy_sha256=digest.hex(),permission=permission,
        issued_boot_ms=issued,expires_boot_ms=expires,expires_utc_ms=utc)
    if not receipt_valid(r,policy,utc_ms,boot_ms):raise PermitRejected('response_bounds_rejected')
    return r
