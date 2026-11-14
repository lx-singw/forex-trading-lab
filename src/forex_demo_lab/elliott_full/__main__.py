import argparse
import json
from .replay import write_report


def main():
    parser = argparse.ArgumentParser(description="Invented Elliott research replay; no broker access")
    parser.add_argument("fixture")
    parser.add_argument("output")
    parser.add_argument("--profile", choices=("base", "adverse"), default="base")
    args = parser.parse_args()
    def pairs(items):
        result = {}
        for key,value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    with open(args.fixture, encoding="utf-8") as stream:
        value = json.load(stream, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    result = write_report(value,args.output,args.profile)
    print(json.dumps({k:result[k] for k in ("version","kind","market_validation","orders_available")}))


if __name__ == "__main__":
    main()
