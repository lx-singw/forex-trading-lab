"""Supplemental diagnostic serialization; original observer stays byte intact."""
import csv
import io

from .observer_parity import check_runtime

NAMES = {-99: 'GUARD', 0: 'INIT_SUCCEEDED', 1: 'INIT_FAILED', 2: 'INIT_PARAMETERS_INCORRECT'}
CONSTANT_ROWS = [('constant_success', 'INIT_SUCCEEDED'),
                 ('constant_failed', 'INIT_FAILED'),
                 ('constant_parameters', 'INIT_PARAMETERS_INCORRECT')]


def supplemental_harness(source):
    old = 'FileWrite(handle,gName,gGuard ? "guard" : "observation",init,gObservations,gSide,'
    new = ('FileWrite(native,gName,init,init==-99 ? "GUARD" : EnumToString((ENUM_INIT_RETCODE)init));\n'
           '      FileWrite(handle,gName,gGuard ? "guard" : "observation",Canonical018Init(init),gObservations,gSide,')
    if source.count(old) != 1: raise ValueError('Serialization site not unique')
    source = source.replace(old, new)
    old = '   FileWrite(handle,"case_id","kind","init","observations","side","stop","removed",'
    new = ('   string nativePath=OutputFile+".native.csv";\n'
           '   if(FileIsExist(nativePath,FILE_COMMON)) { FileClose(handle); return -1; }\n'
           "   int native=FileOpen(nativePath,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');\n"
           '   if(native==INVALID_HANDLE) { FileClose(handle); return -1; }\n'
           '   FileWrite(native,"case_id","raw_init","init_name");\n' + old)
    if source.count(old) != 1: raise ValueError('Header site not unique')
    source = source.replace(old, new)
    old = '   FileFlush(handle); FileClose(handle);'
    new = ('   FileWrite(native,"constant_success",INIT_SUCCEEDED,EnumToString((ENUM_INIT_RETCODE)INIT_SUCCEEDED));\n'
           '   FileWrite(native,"constant_failed",INIT_FAILED,EnumToString((ENUM_INIT_RETCODE)INIT_FAILED));\n'
           '   FileWrite(native,"constant_parameters",INIT_PARAMETERS_INCORRECT,EnumToString((ENUM_INIT_RETCODE)INIT_PARAMETERS_INCORRECT));\n'
           '   FileFlush(native); FileClose(native);\n' + old)
    if source.count(old) != 1: raise ValueError('Close site not unique')
    source = source.replace(old, new)
    prefix = ('// Supplemental 018B: diagnostic enum serialization only.\n'
              'int Canonical018Init(int code)\n{\n'
              '   if(code==INIT_SUCCEEDED) return 0;\n'
              '   if(code==INIT_FAILED) return 1;\n'
              '   if(code==INIT_PARAMETERS_INCORRECT) return 2;\n'
              '   return code;\n}\n')
    return prefix + source


def check_symbols(runtime_text, native_text, cases):
    reader = csv.DictReader(io.StringIO(native_text.lstrip('\ufeff')))
    if reader.fieldnames != ['case_id', 'raw_init', 'init_name']:
        raise ValueError('Native enum schema differs')
    rows = list(reader)
    inventory = [c['case_id'] for c in cases] + [name for name, _ in CONSTANT_ROWS]
    if [r['case_id'] for r in rows] != inventory:
        raise ValueError('Native enum inventory/order differs')
    constants = {}
    for row, (_, expected_name) in zip(rows[-3:], CONSTANT_ROWS):
        if row['init_name'] != expected_name or None in row:
            raise ValueError('Native enum constant name differs')
        constants[expected_name] = int(row['raw_init'])
    if constants['INIT_SUCCEEDED'] != 0 or constants['INIT_FAILED'] != 1 or len(set(constants.values())) != 3:
        raise ValueError('Native enum categories are inconsistent')
    for row, case in zip(rows[:-3], cases):
        name = NAMES[case['expected']['init']]
        if None in row or row['init_name'] != name:
            raise ValueError('Native initialization name differs: ' + case['case_id'])
        if int(row['raw_init']) != (-99 if name == 'GUARD' else constants[name]):
            raise ValueError('Native initialization value differs: ' + case['case_id'])
    review = check_runtime(runtime_text, cases)
    review.update(kind='synthetic_observer_symbolic_runtime_review_018b',
                  native_enum_rows=len(rows), native_enum_checks=len(rows)*2,
                  native_constants=constants, original_018_strict_review_passed=False)
    return review
