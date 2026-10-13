from pathlib import Path
import os,json,hashlib,zipfile,urllib.request,urllib.parse

REPO='Lunona/eden-sion-gpt-sovits'
API='https://api.github.com/repos/'+REPO
HEADERS={'Authorization':'Bearer '+os.environ['RELEASE_TOKEN'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'sion-reviewed-replacement'}
def api(path,method='GET',data=None):
    headers=HEADERS.copy()
    if data is not None:data=json.dumps(data).encode();headers['Content-Type']='application/json'
    with urllib.request.urlopen(urllib.request.Request(API+path,data=data,headers=headers,method=method),timeout=180) as response:
        return json.load(response) if response.status!=204 else None

manifest=json.loads(Path('release-install/manifest.json').read_text())
name='sion-v1.0.2-full-15-references.zip'
release=api('/releases/tags/v1.0.2')
canonical=next(a for a in release['assets'] if a['name']==name)
expected='sha256:'+manifest['zip_sha256']
if canonical.get('digest')!=expected:
    assert canonical['digest']=='sha256:dac4229d5e08018ebc9918fac395035e71bbd24639590208bca64095dea131c0','Old release changed; refusing replacement.'
    old=Path('old-v102.zip')
    with urllib.request.urlopen(canonical['browser_download_url'],timeout=180) as response,old.open('wb') as target:
        while chunk:=response.read(1024*1024):target.write(chunk)
    assert hashlib.sha256(old.read_bytes()).hexdigest()==canonical['digest'].split(':')[1]
    entries={}
    with zipfile.ZipFile(old) as base:
        for path,info in manifest['files'].items():
            data=Path(info['source']).read_bytes() if info['source'] is not None else base.read(info['base'])
            assert hashlib.sha256(data).hexdigest()==info['sha256'],path
            if path.endswith('.py'):compile(data.decode('utf-8'),path,'exec')
            entries[path]=data
    rows=json.loads(entries['references.json']);assert len(rows)==15
    for item in json.loads(entries['reference-manifest.json'])['references']:
        assert hashlib.sha256(entries[item['path']]).hexdigest()==item['sha256']
    for item in json.loads(entries['model-manifest.json'])['files']:
        assert hashlib.sha256(entries[item['file']]).hexdigest()==item['sha256']
    package=Path(name)
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path,data in sorted(entries.items()):
            info=zipfile.ZipInfo(path,(2026,10,13,0,0,0));info.create_system=3;info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
    assert hashlib.sha256(package.read_bytes()).hexdigest()==manifest['zip_sha256']
    with zipfile.ZipFile(package) as archive:assert archive.testzip() is None
    temporary=name+'.replacement'
    assert not any(a['name'] in [temporary,name+'.previous'] for a in release['assets']),'Unfinished earlier replacement needs inspection.'
    headers=HEADERS.copy();headers.update({'Content-Type':'application/zip','Content-Length':str(package.stat().st_size)})
    url=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(temporary)
    with package.open('rb') as data,urllib.request.urlopen(urllib.request.Request(url,data=data,headers=headers,method='POST'),timeout=600) as response:
        uploaded=json.load(response)
    assert uploaded['state']=='uploaded' and uploaded['size']==package.stat().st_size and uploaded['digest']==expected
    api('/releases/assets/'+str(canonical['id']),'PATCH',{'name':name+'.previous'})
    try:
        api('/releases/assets/'+str(uploaded['id']),'PATCH',{'name':name})
        refreshed=api('/releases/tags/v1.0.2')
        current=next(a for a in refreshed['assets'] if a['name']==name)
        assert current['digest']==expected and current['state']=='uploaded'
    except Exception:
        api('/releases/assets/'+str(canonical['id']),'PATCH',{'name':name})
        raise
    api('/releases/assets/'+str(canonical['id']),'DELETE')
else:current=canonical
release=api('/releases/tags/v1.0.2')
for asset in release['assets']:
    if asset['name']=='sion-v1.0.2-ui-update.zip':api('/releases/assets/'+str(asset['id']),'DELETE')
body=Path('release-install/release-notes.md').read_text(encoding='utf-8')
body+='\n\n完整包 SHA256：`'+manifest['zip_sha256']+'`\n'
api('/releases/'+str(release['id']),'PATCH',{'name':'eden* 诗音 v1.0.2｜统一页面、双页翻译API、完整15条参考','body':body})
proof={'release':release['html_url'],'asset':current['browser_download_url'],'sha256':manifest['zip_sha256'],'size':current['size'],'references_verified':15,'models_verified':True,'replaced_existing_full_package':True,'upgrade_patch_removed':True}
print(json.dumps(proof,ensure_ascii=False))
with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as summary:summary.write('## Full package replaced\n\n'+json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
