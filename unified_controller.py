"""Portable launcher for the packaged Sion UI and its reference library."""
import os,sys,json,time,subprocess,urllib.request,importlib.util
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('mode',choices=['start','stop','serve-direct','serve-library'])
parser.add_argument('--app',required=True)
parser.add_argument('--no-browser',action='store_true')
options=parser.parse_args()
APP=Path(options.app).resolve()
if not (APP/'GPT_SoVITS/inference_webui.py').is_file():raise SystemExit('GPT-SoVITS程序目录不正确。')
MODELS=ROOT/'models'
GPT=MODELS/'eden_诗音_Sion_GPT.ckpt'
SOVITS=MODELS/'eden_诗音_Sion_SoVITS.pth'

def serve():
    os.chdir(APP)
    sys.path[:0]=[str(ROOT),str(APP/'GPT_SoVITS'),str(APP)]
    os.environ.update(PYTHONUTF8='1',language='zh_CN',is_share='False',G2PW='1',version='v2ProPlus',is_half='True',GPT_SOVITS_APP=str(APP),GRADIO_ANALYTICS_ENABLED='False',gpt_path=str(GPT),sovits_path=str(SOVITS),infer_ttswebui='9872')
    os.environ['PATH']=str(Path(sys.prefix)/'Lib/site-packages/torch/lib')+os.pathsep+str(APP/'runtime')+os.pathsep+os.environ.get('PATH','')
    import gradio as gr
    original_launch=gr.Blocks.launch
    def local_launch(self,*args,**kwargs):
        kwargs.update(server_name='127.0.0.1',inbrowser=False,share=False)
        return original_launch(self,*args,**kwargs)
    gr.Blocks.launch=local_launch
    if options.mode=='serve-direct':
        import config
        config.GPT_weight_root=[];config.SoVITS_weight_root=[]
        config.name2gpt_path['eden* 诗音 · GPT']=str(GPT)
        config.name2sovits_path['eden* 诗音 · SoVITS']=str(SOVITS)
        from integrated_ui import integrated_source
        entry=APP/'GPT_SoVITS/inference_webui.py'
        source=integrated_source(entry)
        source=source.replace('if "！" in gpt_path or "!" in gpt_path:', 'if gpt_path in name2gpt_path:')
        source=source.replace('if "！" in sovits_path or "!" in sovits_path:', 'if sovits_path in name2sovits_path:')
        sys.argv=['inference_webui.py','zh_CN']
        exec(compile(source,str(entry),'exec'),{'__name__':'__main__','__file__':str(entry)})
    else:
        spec=importlib.util.spec_from_file_location('sion_library',ROOT/'app.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        settings=APP/'weight.json';saved=settings.read_bytes() if settings.exists() else None
        try:module.get_engine()
        finally:
            if saved is not None:settings.write_bytes(saved)
        module.app.queue().launch(server_port=9882,allowed_paths=[str(ROOT)])

def owned_process(pid):
    import psutil
    process=psutil.Process(int(pid))
    args=process.cmdline()
    if str(ROOT/'unified_controller.py') not in args or not any(x in args for x in ['serve-direct','serve-library']):
        raise RuntimeError('进程不属于本目录，未操作该进程。')
    return process

def start():
    import psutil
    logs=ROOT/'launcher-logs';logs.mkdir(exist_ok=True)
    for name,port in [('library',9882),('direct',9872)]:
        pidfile=logs/(name+'.pid')
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/config',timeout=2).close()
            if not pidfile.exists():raise RuntimeError(f'端口{port}被其他程序占用，请先停止旧版。')
            owned_process(pidfile.read_text())
            print(('参考库' if name=='library' else '诗音语音页面')+'已在运行。',flush=True)
            continue
        except (OSError,psutil.NoSuchProcess):pass
        with (logs/(name+'.stdout.log')).open('ab') as out,(logs/(name+'.stderr.log')).open('ab') as err:
            process=subprocess.Popen([sys.executable,'-X','utf8','-u',str(ROOT/'unified_controller.py'),'serve-'+name,'--app',str(APP)],cwd=ROOT,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        pidfile.write_text(str(process.pid))
        print(('参考库' if name=='library' else '诗音语音页面')+'正在加载……',flush=True)
    print('正在等待服务，加载完成后自动打开 http://127.0.0.1:9872/ 。',flush=True)
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        try:
            for port in [9872,9882]:urllib.request.urlopen(f'http://127.0.0.1:{port}/config',timeout=2).close()
            break
        except OSError:time.sleep(1)
    else:raise RuntimeError('加载超时，请检查 launcher-logs 文件夹。')
    print('页面已就绪：顶部可切换“直接生成”和“参考库”，两页都支持翻译 API。',flush=True)
    if not options.no_browser:
        try:os.startfile('http://127.0.0.1:9872/')
        except OSError:print('浏览器未能自动打开，请复制 http://127.0.0.1:9872/ 到浏览器。')

def stop():
    import psutil
    for name in ['direct','library']:
        pidfile=ROOT/'launcher-logs'/(name+'.pid')
        if not pidfile.exists():continue
        try:
            process=owned_process(pidfile.read_text());targets=process.children(recursive=True)+[process]
            for target in targets:
                try:target.terminate()
                except psutil.NoSuchProcess:pass
            gone,alive=psutil.wait_procs(targets,timeout=5)
            for target in alive:target.kill()
            print(('参考库' if name=='library' else '诗音语音页面')+'已停止。',flush=True)
        except psutil.NoSuchProcess:pass

if options.mode.startswith('serve-'):serve()
elif options.mode=='start':start()
else:stop()
