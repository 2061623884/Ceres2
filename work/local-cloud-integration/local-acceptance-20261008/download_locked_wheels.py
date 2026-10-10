"""Download exact locked wheels over direct IPv4 and verify publisher SHA-256."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
import hashlib
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

from packaging.tags import sys_tags
from packaging.utils import canonicalize_name, parse_wheel_filename
from packaging.version import Version


ROOT = Path(__file__).resolve().parents[3]
LOCK = ROOT / 'backend/knowledge-requirements.lock'
DEST = ROOT / 'work/local-cloud-integration/local-acceptance-20261008/tmp/knowledge-wheelhouse'
MANIFEST = DEST / 'verified-wheel-manifest.json'
PYTORCH_INDEX = 'https://download.pytorch.org/whl/cpu/torch/'


def curl_bytes(url: str) -> bytes:
    result = subprocess.run(
        ['curl', '-4', '--noproxy', '*', '--fail', '--location', '--silent', '--show-error',
         '--connect-timeout', '15', '--max-time', '90', url],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.stdout


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.hrefs.append(href)


def lock_rows() -> list[tuple[str, str]]:
    rows = []
    for line in LOCK.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        name, version = line.split('==', 1)
        rows.append((canonicalize_name(name), version.strip()))
    return rows


def best_wheel(files, name: str, version: str, ranks: dict, source: str):
    candidates = []
    for row in files:
        filename = row['filename']
        if not filename.endswith('.whl') or row.get('yanked'):
            continue
        try:
            wheel_name, wheel_version, _build, tags = parse_wheel_filename(filename)
        except Exception:
            continue
        if canonicalize_name(wheel_name) != name or wheel_version != Version(version):
            continue
        matching = [ranks[tag] for tag in tags if tag in ranks]
        if matching:
            candidates.append((min(matching), row))
    if not candidates:
        raise RuntimeError(f'no compatible official wheel: {name}=={version} ({source})')
    _rank, row = min(candidates, key=lambda item: item[0])
    return row


def package_plan(row: tuple[str, str], ranks: dict, torch_links: list[dict]) -> dict:
    name, version = row
    if name == 'torch':
        selected = best_wheel(torch_links, name, version, ranks, 'official-pytorch-cpu-index')
        source = 'official-pytorch-cpu-index'
        digest = selected['sha256']
    else:
        url = f'https://pypi.org/pypi/{name}/{version}/json'
        metadata = json.loads(curl_bytes(url))
        selected = best_wheel(metadata['urls'], name, version, ranks, 'PyPI')
        source = 'PyPI'
        digest = selected['digests']['sha256']
    return {**selected, 'name': name, 'version': version, 'source': source,
            'sha256': digest, 'size': selected.get('size', -1)}


def download_and_verify(plan: dict) -> dict:
    url = urlunsplit((*urlsplit(plan['url'])[:4], ''))
    filename = plan['filename']
    output = DEST / filename
    if output.exists():
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        if digest == plan['sha256']:
            return {key: plan[key] for key in ('name', 'version', 'filename', 'size', 'sha256', 'source')}
        output.unlink()
    subprocess.run(
        ['curl', '-4', '--noproxy', '*', '--fail', '--location', '--silent', '--show-error',
         '--connect-timeout', '15', '--max-time', '900', '--output', str(output), url],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    if digest != plan['sha256']:
        output.unlink(missing_ok=True)
        raise RuntimeError(f'publisher SHA-256 mismatch: {filename}')
    if plan['size'] >= 0 and output.stat().st_size != plan['size']:
        output.unlink(missing_ok=True)
        raise RuntimeError(f'publisher size mismatch: {filename}')
    return {key: plan[key] for key in ('name', 'version', 'filename', 'size', 'sha256', 'source')}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    ranks = {tag: index for index, tag in enumerate(sys_tags())}
    torch_html = curl_bytes(PYTORCH_INDEX).decode('utf-8')
    parser = Links()
    parser.feed(torch_html)
    torch_links = []
    for href in parser.hrefs:
        absolute = urljoin(PYTORCH_INDEX, href)
        parsed = urlsplit(absolute)
        filename = unquote(Path(parsed.path).name)
        if not filename.endswith('.whl'):
            continue
        sha256 = next((part.removeprefix('sha256=') for part in parsed.fragment.split('&')
                       if part.startswith('sha256=')), None)
        if not sha256:
            continue
        try:
            _name, _version, _build, tags = parse_wheel_filename(filename)
        except Exception:
            continue
        if any(tag in ranks for tag in tags):
            torch_links.append({'filename': filename, 'url': absolute, 'size': -1,
                                'sha256': sha256, 'tags': tags})

    rows = lock_rows()
    print(f'locked_packages={len(rows)} workers=8 metadata_source=official_pypi_json torch_source=official_pytorch_cpu_index', flush=True)
    plans = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(package_plan, row, ranks, torch_links): row for row in rows}
        for future in as_completed(futures):
            plan = future.result()
            plans.append(plan)
            print(f"resolved {plan['name']}=={plan['version']} {plan['filename']}", flush=True)
    if len(plans) != len(rows):
        raise RuntimeError(f'wheel plan count mismatch: {len(plans)} != {len(rows)}')

    # PyTorch's simple index does not publish file sizes; use the verified file's
    # actual size after download while retaining its index SHA-256.
    verified = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download_and_verify, plan): plan for plan in plans}
        for future in as_completed(futures):
            row = future.result()
            if row['size'] < 0:
                row['size'] = (DEST / row['filename']).stat().st_size
            verified.append(row)
            print(f"verified {row['name']}=={row['version']} size={row['size']} sha256={row['sha256']}", flush=True)
    verified.sort(key=lambda row: row['name'])
    MANIFEST.write_text(json.dumps({'lock_sha256': hashlib.sha256(LOCK.read_bytes()).hexdigest(),
                                    'wheel_count': len(verified), 'wheels': verified}, indent=2) + '\n')
    print(f'wheelhouse_complete count={len(verified)} bytes={sum(row["size"] for row in verified)} manifest={MANIFEST}', flush=True)


if __name__ == '__main__':
    main()
