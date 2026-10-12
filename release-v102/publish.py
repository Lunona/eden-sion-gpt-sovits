from pathlib import Path
import os,json,hashlib,zipfile,urllib.request,urllib.parse,urllib.error,py_compile
REPO='Lunona/eden-sion-gpt-sovits';API='https://api.github.com/repos/'+REPO
HEADERS={'Authorization':'Bearer '+os.environ['RELEASE_TOKEN'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'sion-release-publisher'}
def api(path,method='GET',data=None):
    headers=dict(HEADERS)
    if data is not None:data=json.dumps(data).encode();headers['Content-Type']='application/json'
    req=urllib.request.Request(API+path,data=data,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=180) as response:return json.load(response)
def upload(release,file):
    digest=hashlib.sha256(file.read_bytes()).hexdigest()
    existing=next((a for a in release['assets'] if a['name']==file.name),None)
    if existing:
        assert existing.get('digest')=='sha256:'+digest,'Refusing to overwrite a different asset'
        asset=existing
    else:
        headers=dict(HEADERS);headers['Content-Type']='application/zip';headers['Content-Length']=str(file.stat().st_size)
        url=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(file.name)
        with file.open('rb') as data:
            with urllib.request.urlopen(urllib.request.Request(url,data=data,headers=headers,method='POST'),timeout=600) as response:asset=json.load(response)
    assert asset['state']=='uploaded' and asset['size']==file.stat().st_size
    assert asset.get('digest')=='sha256:'+digest
    return {'name':file.name,'size':file.stat().st_size,'sha256':digest,'url':asset['browser_download_url']}

old=Path('old-full.zip')
with urllib.request.urlopen('https://github.com/'+REPO+'/releases/download/v1.0.1/sion-v1.0.1-full-15-references.zip',timeout=180) as response,old.open('wb') as target:
    while chunk:=response.read(1024*1024):target.write(chunk)
assert hashlib.sha256(old.read_bytes()).hexdigest()=='baba7c6652b175d92d4bb12c5fcff847c66797a927209983efd3015ef4568384'
overlay=['app.py','translation.py','README.md','docs/TUTORIAL.md','docs/CHINESE_INPUT.md','docs/UPGRADE.md','tests/test_translation_flow.py','docs/images/06-language-input.png','docs/images/07-japanese-preview.png']
manifest=json.loads(Path('release-v102/overlay-manifest.json').read_text())
for name in overlay:
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==manifest[name]
for name in ['app.py','translation.py','tests/test_translation_flow.py']:py_compile.compile(name,doraise=True)
full=Path('sion-v1.0.2-full-15-references.zip');upgrade=Path('sion-v1.0.2-ui-update.zip')
with zipfile.ZipFile(old) as source,zipfile.ZipFile(full,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in sorted(set(source.namelist())|set(overlay)):
        if name in overlay:z.write(name,name)
        else:z.writestr(source.getinfo(name),source.read(name),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
with zipfile.ZipFile(upgrade,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in overlay:z.write(name,name)
with zipfile.ZipFile(full) as z:
    assert z.testzip() is None
    rows=json.loads(z.read('references.json'));assert len(rows)==15
    for item in json.loads(z.read('reference-manifest.json'))['references']:
        assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
    for item in json.loads(z.read('model-manifest.json'))['files']:
        assert hashlib.sha256(z.read(item['file'])).hexdigest()==item['sha256']
with zipfile.ZipFile(upgrade) as z:
    assert z.testzip() is None
    assert not any(n.startswith(('models/','curated/','imported/','generated/','temp/')) or n=='references.json' for n in z.namelist())
try:release=api('/releases/tags/v1.0.2')
except urllib.error.HTTPError as error:
    if error.code!=404:raise
    release=api('/releases','POST',{'tag_name':'v1.0.2','target_commitish':os.environ['TASK_SHA'],'name':'eden* 诗音 GPT-SoVITS v1.0.2｜中文输入、日语输出','body':'正在发布新版下载包；完成后将补充使用说明。','prerelease':True,'draft':False})
proof=[upload(release,full),upload(release,upgrade)]
body=Path('release-v102/release-notes.md').read_text(encoding='utf-8')
body+='\n\n## 下载包校验\n\n'+'\n'.join(f"- `{p['name']}`：SHA256 `{p['sha256']}`" for p in proof)
api('/releases/'+str(release['id']),'PATCH',{'body':body})
print(json.dumps({'release':release['html_url'],'assets':proof,'reference_count':15,'models_verified':True,'references_verified':True},ensure_ascii=False))
with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as summary:summary.write('## Published v1.0.2\n\n'+json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
