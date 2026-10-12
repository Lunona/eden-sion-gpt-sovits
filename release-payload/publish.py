"""Assemble the reviewed local package contents and publish only its new Release asset."""
from pathlib import Path
import os,json,hashlib,zipfile,urllib.request,urllib.parse

REPO='Lunona/eden-sion-gpt-sovits'
RELEASE_ID=409701082
NAME='sion-v1.0.1-full-15-references.zip'
API='https://api.github.com/repos/'+REPO
TOKEN=os.environ['RELEASE_TOKEN']
HEADERS={'Authorization':'Bearer '+TOKEN,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'sion-full-release-publisher'}
def api(path,method='GET',data=None):
    headers=dict(HEADERS)
    if data is not None:
        data=json.dumps(data).encode();headers['Content-Type']='application/json'
    req=urllib.request.Request(API+path,data=data,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=180) as response:return json.load(response)

payload=Path('payload.zip')
payload.write_bytes(b''.join(p.read_bytes() for p in sorted(Path('release-payload').glob('part-*.bin'))))
assert hashlib.sha256(payload.read_bytes()).hexdigest()=='5a88ffa91cadd48f62766132d93fd9da1f195a0fd35d9a3c4fc8aa98e480e9f3'
old=Path('no-reference-original.zip')
with urllib.request.urlopen('https://github.com/'+REPO+'/releases/download/v1.0.1/sion-v1.0.0-no-reference-audio.zip',timeout=180) as response,old.open('wb') as target:
    while chunk:=response.read(1024*1024):target.write(chunk)
assert hashlib.sha256(old.read_bytes()).hexdigest()=='8adf22f27f9f0aaf5aa4e07c6ae5660cfea727de778091cdc5f3276d00bfdae8'
out=Path(NAME)
with zipfile.ZipFile(payload) as p,zipfile.ZipFile(old) as original,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as result:
    assert p.testzip() is None and original.testzip() is None
    model_manifest=json.loads(p.read('model-manifest.json'))
    files={n:(p,p.getinfo(n)) for n in p.namelist()}
    for model in model_manifest['files']:
        matches=[n for n in original.namelist() if n==model['file'] or n.endswith('/'+model['file'])]
        assert len(matches)==1,matches
        info=original.getinfo(matches[0]);info.filename=model['file']
        data=original.read(matches[0])
        assert len(data)==model['size'] and hashlib.sha256(data).hexdigest()==model['sha256']
        files[model['file']]=(original,info)
    for name,(archive,info) in sorted(files.items()):
        data=archive.read(info.orig_filename)
        result.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    rows=json.loads(z.read('references.json'))
    assert len(rows)==15 and len({row['id'] for row in rows})==15
    assert len([n for n in z.namelist() if n.startswith('curated/')])==15
    for item in json.loads(z.read('reference-manifest.json'))['references']:
        assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
    assert all(row['audio'] in z.namelist() and not row['audio'].startswith(('F:', 'C:')) for row in rows)
    assert not any(n.startswith(('generated/','temp/','private-backup','client-temp/')) for n in z.namelist())
digest=hashlib.sha256(out.read_bytes()).hexdigest()
release=api('/releases/'+str(RELEASE_ID))
existing=next((a for a in release['assets'] if a['name']==NAME),None)
if existing:
    assert existing.get('digest')=='sha256:'+digest,'Existing different asset; refusing to overwrite'
    asset=existing
else:
    url=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(NAME)
    headers=dict(HEADERS);headers['Content-Type']='application/zip';headers['Content-Length']=str(out.stat().st_size)
    with out.open('rb') as file:
        req=urllib.request.Request(url,data=file,headers=headers,method='POST')
        with urllib.request.urlopen(req,timeout=600) as response:asset=json.load(response)
assert asset['state']=='uploaded' and asset['size']==out.stat().st_size
if asset.get('digest'):assert asset['digest']=='sha256:'+digest
body=Path('release-payload/release-notes.md').read_text(encoding='utf-8').replace('7d84af965dbadab58018221e2828ac86f928b5669fb6e43b19f19494ffc60e98',digest)
api('/releases/'+str(RELEASE_ID),'PATCH',{'body':body})
proof={'name':NAME,'size':out.stat().st_size,'sha256':digest,'asset_id':asset['id'],'url':asset['browser_download_url'],'reference_count':15,'models_verified':True,'references_verified':True}
print(json.dumps(proof,ensure_ascii=False))
with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as summary:
    summary.write('## Full package published\n\n'+json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
