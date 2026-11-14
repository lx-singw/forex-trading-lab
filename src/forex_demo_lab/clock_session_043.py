"""Interactive-session and already-deployed artifact ownership checks."""
from pathlib import PureWindowsPath
import re

def require_interactive(stream):
    if not getattr(stream,'isatty',lambda:False)():raise ValueError('interactive_session_required')

def reuse_path(data_root,deployment,artifact_sha):
    root=PureWindowsPath(data_root)
    if not root.is_absolute() or len(root.drive)!=2 or root.drive[1]!=':':raise ValueError('terminal_data_root_invalid')
    if set(deployment)!={'folder','artifact_binding'} or re.fullmatch('ForexDemoLab042-[0-9a-f]{32}',deployment['folder']) is None:
        raise ValueError('reuse_deployment_invalid')
    expected=root/'MQL5'/'Scripts'/deployment['folder']/'ForexDemoClockObserver042.ex5'
    name='/mnt/'+expected.drive[0].lower()+expected.as_posix()[2:]
    if deployment['artifact_binding']!={name:artifact_sha}:raise ValueError('reuse_deployment_hash_or_root_invalid')
    return expected
