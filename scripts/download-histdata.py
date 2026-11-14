"""Download one free public EURUSD tick archive using its published web form."""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile


class DownloadForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.fields = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.active = attrs.get("id") == "file_down" and attrs.get("action") == "/get.php"
        if self.active and tag == "input" and "name" in attrs and "value" in attrs:
            self.fields[attrs["name"]] = attrs["value"]

    def handle_endtag(self, tag):
        if tag == "form":
            self.active = False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", required=True, help="YYYYMM")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    month = datetime.strptime(args.month, "%Y%m")
    if month >= datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0):
        parser.error("Use a completed historical month")
    if args.output.exists():
        parser.error("Destination exists")
    page = f"https://www.histdata.com/download-free-forex-historical-data/?/ascii/tick-data-quotes/eurusd/{month.year}/{month.month}"
    with urllib.request.urlopen(page, timeout=30) as response:
        form = DownloadForm()
        form.feed(response.read(1_000_000).decode("utf-8"))
    expected = dict(date=str(month.year), datemonth=args.month, platform="ASCII", timeframe="T", fxpair="EURUSD")
    if any(form.fields.get(k) != v for k,v in expected.items()) or not form.fields.get("tk"):
        parser.error("Provider form does not match requested archive")
    request = urllib.request.Request("https://www.histdata.com/get.php",
                                     data=urllib.parse.urlencode(form.fields).encode(), headers={"Referer": page})
    # No automatic retries; respect rate limits or other access failures.
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read(100_000_001)
    if len(data) > 100_000_000:
        parser.error("Archive exceeds bounded download size")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if f"DAT_ASCII_EURUSD_T_{args.month}.csv" not in archive.namelist():
            parser.error("Downloaded archive does not contain expected EURUSD ticks")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/"original.zip").write_bytes(data)
    metadata = {"source": "HistData", "page": page, "captured_utc": datetime.now(timezone.utc).isoformat(),
                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                "timezone": "EST fixed UTC-05:00 per provider FAQ"}
    (args.output/"download.json").write_text(json.dumps(metadata, indent=2)+"\n", encoding="utf-8")
    print(f"Saved {args.month} EURUSD archive: {len(data)} bytes")


if __name__ == "__main__":
    main()
