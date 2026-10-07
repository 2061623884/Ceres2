"""Tester-owned bounded browser harness. Never launch against a personal runtime."""
import argparse
import hashlib
import shutil
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request


def refuse_dotenv(source):
    for path in (source/'.env', source/'backend/.env'):
        if path.exists() or path.is_symlink():
            raise ValueError('FIXTURE_REFUSES_PROJECT_DOTENV')


def stop_owned(process):
    if process is None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    if process.poll() is None:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--frontend-dist',type=Path,required=True)
    parser.add_argument('--lifetime',type=int,default=300)
    parser.add_argument('--artifacts',type=Path)
    parser.add_argument('--wait-for-cua',action='store_true')
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    source=args.source.resolve()
    try:
        refuse_dotenv(source)
    except ValueError as error:
        print(str(error),file=sys.stderr)
        return 2
    if not 1<=args.lifetime<=900:
        parser.error('lifetime must be 1..900 seconds')
    if not (args.frontend_dist/'index.html').is_file():
        parser.error('a Tester-built frontend-dist/index.html is required')
    command=args.command[1:] if args.command[:1]==['--'] else args.command
    if not command and not args.wait_for_cua:
        parser.error('pass the bounded browser command after -- or --wait-for-cua')
    if command and args.wait_for_cua:
        parser.error('choose one browser command or --wait-for-cua')
    # These paths carry Tester's preinstalled guards/toolchain, never credentials.
    preserve=('PATH','PYTHONPATH','CERES_NODE_GUARD_AUDIT','PLAYWRIGHT_BROWSERS_PATH')
    if not os.environ.get('CERES_NODE_GUARD_AUDIT'):
        parser.error('Tester Node guard audit configuration is required')
    base={key:os.environ[key] for key in preserve if key in os.environ}
    base.update(LANG='C.UTF-8',PYTHONUNBUFFERED='1',NO_PROXY='127.0.0.1,localhost,::1',no_proxy='127.0.0.1,localhost,::1')
    support=Path(__file__).parent
    files=('launch_browser_fixture.py','fixture_backend.py','test_launcher_contract.py','api_smoke.py','cua_http_contract.py','README.md')
    hashes=lambda:{name:hashlib.sha256((support/name).read_bytes()).hexdigest() for name in files}
    before=hashes()
    evidence_base=args.artifacts or Path(os.environ.get('TMPDIR',tempfile.gettempdir()))
    evidence_base.mkdir(parents=True,exist_ok=True)
    evidence=Path(tempfile.mkdtemp(prefix='browser-fixture-evidence-',dir=evidence_base))
    print(json.dumps({'fixture_support_sha256':before,'evidence_dir':str(evidence)}),flush=True)
    child=browser=None
    def terminate(_signum,_frame):
        raise KeyboardInterrupt
    for signum in (signal.SIGINT,signal.SIGTERM):
        signal.signal(signum,terminate)
    with tempfile.TemporaryDirectory(prefix='ceres-browser-',dir=os.environ.get('TMPDIR')) as temporary:
        runtime=Path(temporary)
        (runtime/'home').mkdir()
        env={**base,'HOME':str(runtime/'home'),'TMPDIR':str(runtime),
            'OPENAI_API_KEY':'browser-synthetic-provider-key','LLM_MODEL':'browser-controlled-model',
            'LLM_MODE':'live','BUSINESS_DATA_MODE':'demo','HUMAN_OPERATOR_TOKEN':'browser-synthetic-operator-token',
            'SHOPPING_WRITES_PAUSED':'false','DATABASE_URL':f'sqlite:///{runtime}/business.sqlite3',
            'MERCURY_CHECKPOINT_PATH':str(runtime/'checkpoints.sqlite3')}
        started=time.monotonic()
        ready=runtime/'ready.json'
        try:
            with (runtime/'backend.log').open('w') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).with_name('fixture_backend.py')),
                    '--source',str(source),'--frontend-dist',str(args.frontend_dist.resolve()),
                    '--runtime-dir',str(runtime)],env=env,stdout=log,stderr=log,start_new_session=True)
                while not ready.exists():
                    if child.poll() is not None:
                        raise RuntimeError('FIXTURE_BACKEND_START_FAILED\n'+(runtime/'backend.log').read_text()[-6000:])
                    if time.monotonic()-started>min(45,args.lifetime):
                        raise TimeoutError('FIXTURE_BACKEND_NOT_READY')
                    time.sleep(.1)
                manifest=json.loads(ready.read_text())
                with urllib.request.urlopen(manifest['base_url']+'/health',timeout=2) as response:
                    assert json.load(response)['status']=='ok'
                stop_file=evidence/'stop'
                manifest.update(entry_url=manifest['browser_url']+'/__fixture__/start',stop_file=str(stop_file),backend_pid=child.pid)
                ready.write_text(json.dumps(manifest,ensure_ascii=False))
                shutil.copyfile(ready,evidence/'ready.json')
                print(json.dumps({'fixture_ready':manifest},ensure_ascii=False),flush=True)
                if args.wait_for_cua:
                    while not stop_file.exists():
                        if child.poll() is not None:
                            raise RuntimeError('FIXTURE_BACKEND_EXITED_DURING_CUA')
                        if time.monotonic()-started>=args.lifetime:
                            raise TimeoutError('FIXTURE_LIFETIME_EXCEEDED')
                        time.sleep(.2)
                    return 0
                browser=subprocess.Popen(command,env={**env,'BROWSER_BASE_URL':manifest['base_url'],
                    'FIXTURE_MANIFEST':str(ready)},start_new_session=True)
                remaining=max(1,args.lifetime-(time.monotonic()-started))
                result=browser.wait(timeout=remaining)
                return result
        except KeyboardInterrupt:
            return 130
        except (TimeoutError,subprocess.TimeoutExpired):
            print('FIXTURE_LIFETIME_EXCEEDED',file=sys.stderr)
            return 124
        finally:
            for signum in (signal.SIGINT,signal.SIGTERM):
                signal.signal(signum,signal.SIG_IGN)
            stop_owned(browser)
            stop_owned(child)
            after=hashes()
            lifecycle={'fixture_stopped':True,'backend_returncode':child.returncode if child else None,
                'browser_returncode':browser.returncode if browser else None,'support_before_sha256':before,
                'support_after_sha256':after,'support_source_stable':before==after,'evidence_dir':str(evidence)}
            for name in ('backend.log','ready.json'):
                if (runtime/name).exists():
                    shutil.copyfile(runtime/name,evidence/name)
            (evidence/'lifecycle.json').write_text(json.dumps(lifecycle,indent=2))
            print(json.dumps(lifecycle),flush=True)
            if before!=after:
                return 70


if __name__=='__main__':
    raise SystemExit(main())
