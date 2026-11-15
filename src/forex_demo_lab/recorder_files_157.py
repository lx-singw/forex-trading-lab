"""Explicit regular-file IO for157. No discovery, overwrite, repair or resume."""
import os
import hashlib
from pathlib import Path
import stat
from .native_journal_157 import CAP, inspect_native, transport, require


def folder_check(folder,job):
    folder=Path(folder).absolute()
    require(folder.name=='Job156-'+job and folder.is_dir() and not any(p.is_symlink() for p in (folder,*folder.parents)))
    return folder


def read_file(path,cap):
    fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as file:
        require(stat.S_ISREG(os.fstat(file.fileno()).st_mode))
        raw=file.read(cap+1);require(len(raw)<=cap);return raw


def write_file(path,raw):
    require(type(raw) is bytes and 0<len(raw)<=CAP)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb',buffering=0) as file:
        require(file.write(raw)==len(raw));os.fsync(file.fileno())


def check_files(folder,expected_job):
    folder=folder_check(folder,expected_job)
    raw=read_file(folder/'NativePort156.txt',CAP)
    value=inspect_native(raw);value['native_sha256']=hashlib.sha256(raw).hexdigest();require(value['job']==expected_job)
    for lease in value['leases']:
        index=lease['ordinal'];stem=f'{index:04d}'
        req=transport(read_file(folder/f'Request{stem}.txt',512),'FXDL_REQUEST156_V1',4)
        reply=transport(read_file(folder/f'Reply{stem}.txt',512),'FXDL_REPLY156_V1',8)
        prefix=[expected_job,str(index),lease['challenge']]
        require(req[1:]==prefix and reply[1:4]==prefix)
        require(reply[4:]==[str(lease[k]) for k in ('sequence','tick','owner','flags')])
    return value
