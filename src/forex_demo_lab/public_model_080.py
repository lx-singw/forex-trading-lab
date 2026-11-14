"""Offline Windows lexical-path/metadata models; never Windows identity proof."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import stat
import time
from types import SimpleNamespace
from unittest.mock import patch

from . import public_preflight_080 as reader080

WINDOWS_ROOT080=PureWindowsPath('//wsl.localhost/Ubuntu/home/lx_singw/projects/forex-demo-lab')
DATE_CLOCK080=(int(datetime(2026,10,8,16,tzinfo=timezone.utc).timestamp()*1000),1000000)
RECORDS080=(('ledger','reports/native-timing-078-ledger.json'),
    ('checks','reports/native-timing-078-checks.json'),
    ('final','reports/native-timing-078-final-source.json'),
    ('review','reports/native-timing-078-completion-review.json'),
    ('helper_profile','reports/helper-profile-068.json'),
    ('authorization','reports/native-timing-078-authorization.json'))


def original_class080(source):
    """Extract only the bound pure078 class AST; no entry/module execution."""
    tree=ast.parse(source)
    nodes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PublicInputs078']
    if len(nodes)!=1:raise ValueError('public_class_missing')
    namespace=dict(datetime=datetime,timezone=timezone,time=time,hashlib=hashlib,
        json=json,os=os,Path=Path,stat=stat,DATE=reader080.DATE080,
        ProbeRejected=reader080.PublicInputRejected080,unique_pairs=reader080.unique_pairs080)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<bound-public-class>','exec'),namespace)
    return namespace['PublicInputs078'],namespace


def unchanged_methods080(old_source,new_source):
    """Independent AST comparison of all four unchanged integrity methods."""
    def methods(text,name):
        cls=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef) and n.name==name)
        return {n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
    old=methods(old_source,'PublicInputs078');new=methods(new_source,'PublicInputs080')
    class Normalize(ast.NodeTransformer):
        def visit_Name(self,node):
            names={'DATE':'DATE080','ProbeRejected':'PublicInputRejected080'}
            if node.id in names:node.id=names[node.id]
            return node
    names=('__init__','check','properties','raw')
    for n in names:
        if ast.dump(Normalize().visit(old[n]),include_attributes=False)!=ast.dump(new[n],include_attributes=False):
            raise ValueError('public_integrity_method_changed')
    return names


def model_paths080(mapping, parent_directory, overrides=None):
    """Use Windows parent counts with actual local descriptor identity/bytes.

    Attributes default to non-reparse; optional overrides inject failures.
    This does not measure the attributes/link/descriptor behavior of Windows.
    """
    mapping={str(PureWindowsPath(k)):Path(v) for k,v in mapping.items()}
    overrides={} if overrides is None else overrides
    class ModelPath:
        def __init__(self,value):self.value=PureWindowsPath(str(value))
        def __str__(self):return str(self.value)
        @property
        def parents(self):return tuple(ModelPath(p) for p in self.value.parents)
        def with_suffix(self,suffix):return ModelPath(self.value.with_suffix(suffix))
        def lstat(self):
            s=(mapping.get(str(self.value),Path(parent_directory))).lstat()
            fields={n:getattr(s,n) for n in ('st_mode','st_dev','st_ino','st_size','st_mtime_ns','st_nlink')}
            fields['st_file_attributes']=0
            fields.update(overrides.get(str(self.value),{}))
            return SimpleNamespace(**fields)
        def open(self,mode):
            if mode!='rb':raise ValueError('model_write_forbidden')
            return mapping[str(self.value)].open(mode)
    return ModelPath


def model_case080(root,legacy=False,launcher='launcher',overrides=None):
    root=Path(root)
    ledger=json.loads((root/'reports/native-timing-078-ledger.json').read_text())
    mapping={}
    for label,name in RECORDS080:
        p=WINDOWS_ROOT080/name;mapping[str(p)]=root/name
        mapping[str(p.with_suffix('.sha256'))]=(root/name).with_suffix('.sha256')
    for n in ledger['runtime_sources']:mapping[str(WINDOWS_ROOT080/n)]=root/n
    chain=ledger['helper_chain'];chosen=chain['launcher'] if launcher=='launcher' else chain['images'][0]
    selected=PureWindowsPath('C:/')/chosen[7:]
    mapping[str(selected)]=Path('/mnt/c')/chosen[7:]
    PathModel=model_paths080(mapping,root,overrides)
    if legacy:
        cls,namespace=original_class080((root/'scripts/runtime-native-timing-078.py').read_text())
        namespace['Path']=PathModel
        manager=patch.dict(namespace,{'Path':PathModel})
    else:
        cls=reader080.PublicInputs080;manager=patch.object(reader080,'Path',PathModel)
    stop=None;completed=False;public_done=False;sources_done=False
    reader=cls(lambda:DATE_CLOCK080)
    with manager:
        try:
            for label,name in RECORDS080:
                stop=label;reader.record(str(WINDOWS_ROOT080/name))
            public_done=True
            for n in ledger['runtime_sources']:
                stop='source'
                raw=reader.raw(str(WINDOWS_ROOT080/n),262144,source=True)
                if hashlib.sha256(raw).hexdigest()!=ledger['runtime_bindings'][n]:
                    raise reader080.PublicInputRejected080('timing_source_rejected')
            sources_done=True;stop='launcher'
            raw=reader.raw(str(selected),1048576,source=True)
            if hashlib.sha256(raw).hexdigest()!=ledger['runtime_bindings'][chain['launcher']]:
                raise reader080.PublicInputRejected080('timing_launcher_rejected')
            completed=True;stop=None;reason=None
        except reader080.PublicInputRejected080 as error:
            reason=str(error)
    return dict(completed=completed,stopped_label=stop,stop_reason=reason,
        public_records_complete=public_done,source_bindings_complete=sources_done,
        public_reads=reader.reads,public_bytes=reader.bytes,public_stats=reader.stats,
        source_reads=reader.source_reads,source_bytes=reader.source_bytes,source_stats=reader.source_stats,
        dependencies_injected=True,windows_metadata_measured=False,sdk_connections=0,orders_available=False)
