"""Explicit next-day-midnight adapter; original date/time/row stay visible."""
import csv
from datetime import datetime, timedelta
import io

from .reference import parse as original_parse


def parse(lines, day):
    expected=datetime.strptime(day,'%Y-%m-%d')
    next_date=(expected+timedelta(days=1)).strftime('%Y%m%d')
    previous_date=expected.strftime('%Y%m%d')
    rewritten=io.StringIO(newline='')
    writer=csv.writer(rewritten)
    originals={}
    for number,fields in enumerate(csv.reader(lines),1):
        if len(fields)==7 and fields[0]=='EURUSD' and fields[1]==next_date and fields[2]=='000000':
            originals[number]=(fields[1],fields[2])
            fields[1],fields[2]=previous_date,'240000'
        writer.writerow(fields)
    rewritten.seek(0)
    rows=original_parse(rewritten,day)
    for row in rows:
        if row['source_row'] in originals:
            row['source_date'],row['source_time']=originals[row['source_row']]
    return rows
