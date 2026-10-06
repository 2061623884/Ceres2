"""Capture exact new-repository source hashes and a scoped test command."""
import datetime, hashlib, json, os, pathlib, subprocess, sys, time
root=pathlib.Path(__file__).resolve().parents[4]
label=sys.argv[1]; command=sys.argv[2:]
out=root/'work/ceres2-runtime-upgrade'/label
out.mkdir(parents=True,exist_ok=True)
def snapshot():
    hashes={}
    for area in ('backend','runtime','frontend','data','scripts'):
        for p in sorted((root/area).rglob('*')):
            if p.is_file() and not any(x in p.parts for x in ('node_modules','.venv','__pycache__','.pytest_cache','dist')) and p.suffix not in ('.sqlite','.sqlite3','.db','.pyc') and not p.name.startswith('.env'):
                hashes[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (root/'work/clean-rebuild').glob('*/*'):
        if p.is_file() and p.suffix in ('.cjs','.mjs','.tsx'):
            hashes[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted((root/'runtime/pi/dist').rglob('*')):
        if p.is_file():
            hashes[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes
meta={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'command':command,'cwd':str(root),'source_sha256_before':snapshot(),'scope':'fresh source only; no archive runtime/data reuse'}
start=time.monotonic()
env={**os.environ,'PYTHONPATH':str(root/'backend'),'PYTHONDONTWRITEBYTECODE':'1'}
with (out/'output.txt').open('w') as log:
    result=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
meta.update(exit_code=result.returncode,elapsed_seconds=time.monotonic()-start,source_sha256_after=snapshot())
meta['source_changed_during_run']=meta['source_sha256_before']!=meta['source_sha256_after']
(out/'evidence.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print((out/'output.txt').read_text());print(json.dumps({k:meta[k] for k in ('exit_code','elapsed_seconds','source_changed_during_run')}));sys.exit(result.returncode)
