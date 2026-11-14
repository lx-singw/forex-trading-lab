"""Create separately versioned sources; preserve every038/041 byte."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for old,new in (('mt5/Scripts/ForexDemoClockObserver038.mq5','mt5/Scripts/ForexDemoClockObserver042.mq5'),
                ('mt5/Scripts/ClockGuard038.mqh','mt5/Scripts/ClockGuard042.mqh'),
                ('mt5/Tests/ClockGuard038.cpp','mt5/Tests/ClockGuard042.cpp')):
    text=(ROOT/old).read_text().replace('038','042')
    if new.endswith('.mq5'):text=text.replace('#property strict\n','#property strict\n#property script_show_inputs\n')
    with (ROOT/new).open('x',encoding='utf-8') as out:out.write(text)
print('New042 sources created, capture=false, fixed2026.10.06; originals unchanged')
