"""Replay automatic lifecycle over explicit invented163 publications only."""
import argparse
import json

from forex_demo_lab.trendline import data, engine, lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor");parser.add_argument("hours");parser.add_argument("new_output_directory")
    parser.add_argument("--profile",choices=lines.PROFILES,default="TRL_BRK3_E1")
    parser.add_argument("--as-of",type=int);parser.add_argument("--unlock-receipt")
    parser.add_argument("--restore-checkpoint")
    args = parser.parse_args()
    source,hours = data.load_dataset(args.descriptor,args.hours,args.unlock_receipt)
    frame = "D1" if args.profile == "D1_BRK3" else "H4"
    stream = data.BarStream(source)
    now = args.as_of if args.as_of is not None else hours[-1].available_at
    if not source.calendar.start <= now <= source.calendar.end+60000:raise ValueError("as-of outside invented scope")
    for hour in hours:
        if hour.available_at > now:break
        stream.observe(hour)
    stream.advance(now)
    bars = tuple(bar for bar in stream.bars() if bar.timeframe == frame)
    replay = engine.Engine(source,args.profile,frame)
    if args.restore_checkpoint:
        checkpoint,_ = data.read_json(data.no_links(args.restore_checkpoint),limit=engine.MAX_CHECKPOINT_BYTES)
        replay = engine.Engine.restore(source,checkpoint)
        if (replay.profile != args.profile or replay.timeframe != frame or replay.clock > now
                or replay.publications != bars[:len(replay.publications)]):
            raise ValueError("checkpoint must match the supplied prefix/profile/cursor")
    for bar in bars[len(replay.publications):]:replay.observe(bar)
    replay.advance(now)
    report,checkpoint = replay.report(),replay.checkpoint()
    output = data.no_links(args.new_output_directory);output.mkdir(exist_ok=False)
    data.write_new(output/"replay.json",report);data.write_new(output/"checkpoint.json",checkpoint)
    print(json.dumps({"kind":report["kind"],"publications":len(replay.publications),
                      "journal_events":len(report["journal"]["events"]),"orders_available":False}))


if __name__ == "__main__":main()
