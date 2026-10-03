"""Scan source/index and frontend bundles without printing matched credentials."""
import os
import re
import subprocess
from pathlib import Path
from app import config

def main():
    root=config.ROOT
    names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root).decode().split('\0')
    secrets=[os.environ[key].encode() for key in ['GNANI_API_KEY','HF_TOKEN','EVON_API_KEY'] if len(os.getenv(key,''))>=8]
    pattern=re.compile(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
    findings=[]
    def inspect(label,content):
        if any(value in content for value in secrets) or pattern.search(content): findings.append(label)
    for name in names:
        if not name: continue
        path=root/name
        if path.name.startswith('.env') and path.name!='.env.example': findings.append(name)
        if path.is_file(): inspect(name,path.read_bytes())
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
    for name in tracked:
        if name:
            blob=subprocess.run(['git','show',':'+name],cwd=root,capture_output=True,check=True).stdout
            inspect('index:'+name,blob)
    inspect('Git history',subprocess.check_output(['git','log','--all','--format=','--patch'],cwd=root))
    bundles=list((root/'app/web/.next/static').rglob('*'))
    for path in bundles:
        if path.is_file(): inspect(str(path.relative_to(root)),path.read_bytes())
    print({'source_files':len([name for name in names if name]),'bundle_files':sum(path.is_file() for path in bundles),'findings':sorted(set(findings))})
    if findings: raise SystemExit(1)

if __name__=='__main__': main()
