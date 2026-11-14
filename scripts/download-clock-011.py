"""One bounded public legacy archive request; no retries or paid access."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request


def download(hour, folder):
    if hour.tzinfo != timezone.utc or any((hour.minute, hour.second, hour.microsecond)):
        raise ValueError('Use a whole explicit UTC hour')
    if folder.exists():
        raise FileExistsError('Capture destination exists')
    url = (f'https://datafeed.dukascopy.com/datafeed/EURUSD/{hour.year}/'
           f'{hour.month - 1:02d}/{hour.day:02d}/{hour.hour:02d}h_ticks.bi5')
    meta = {'url': url, 'requested_hour_utc': hour.isoformat(),
        'requested_utc': datetime.now(timezone.utc).isoformat(),
        'plan_sha256': hashlib.sha256(Path('docs/CLOCK-011-PLAN.md').read_bytes()).hexdigest(),
        'transport_plan_sha256': hashlib.sha256(Path('docs/CLOCK-011-TRANSPORT.md').read_bytes()).hexdigest(),
        'provider': 'Dukascopy public legacy hourly archive', 'performance_evaluation_ready': False}
    folder.mkdir(parents=True, exist_ok=False)
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            meta['status'] = response.status
            if urllib.parse.urlparse(response.geturl()).netloc != 'datafeed.dukascopy.com':
                raise ValueError('Unexpected redirect origin')
            data = response.read(10_000_001)
            if len(data) > 10_000_000:
                raise ValueError('Oversized archive')
            meta.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            with (folder / 'original.bi5').open('xb') as stream:
                stream.write(data)
    except urllib.error.HTTPError as exc:
        meta['status'] = exc.code
    except urllib.error.URLError as exc:
        meta['error_type'] = 'URLError'
        meta['transport_reason_type'] = type(exc.reason).__name__
    except Exception as exc:
        meta['error_type'] = type(exc).__name__
    with (folder / 'download.json').open('x', encoding='utf-8') as stream:
        json.dump(meta, stream, indent=2, allow_nan=False)
        stream.write('\n')
    return meta


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hour', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = download(datetime.fromisoformat(args.hour.replace('Z', '+00:00')), args.output)
    print(json.dumps(result, indent=2))
    if result.get('status') != 200 or 'error_type' in result:
        parser.exit(2, 'Acquisition stopped; failure preserved.\n')
