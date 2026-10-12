"""Local reference library for the existing Sion GPT-SoVITS installation."""
import os,json,sys,time,uuid,shutil,threading,random
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ['GRADIO_TEMP_DIR']=str(ROOT/'temp')
import gradio as gr
import soundfile as sf
from translation import prepare_text, TranslationError, KANA
DB=ROOT/'references.json';LOCK=threading.Lock();ENGINE=None
CATEGORIES=['平静','温柔','悲伤','开心','疑惑','不满','疲惫','虚弱','怀念','认真']
MODEL=ROOT/'models/sion-pause-supplement-lr002-e2.ckpt'
SOVITS=ROOT/'models/sion-timbre-lr00002_e8_s1392.pth'
def read():return json.loads(DB.read_text(encoding='utf-8'))
def write(rows):
 tmp=DB.with_suffix('.tmp');tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(DB)
def initialize():
 if not DB.exists():write([])
def audio_path(row):
 p=Path(row['audio'])
 return str(p if p.is_absolute() else ROOT/p)

def choices(category):
 return [(r['name']+' · '+r['category'],r['id']) for r in read() if category=='全部' or r['category']==category]
def select(key):
 r=next((r for r in read() if r['id']==key),None)
 if not r:return None,'','平静',False,'',''
 note=r.get('classification_basis','用户提供分类')
 if r.get('context'):note+='\n\n剧情上下文：\n'+r['context']
 return audio_path(r),r['text'],r['category'],r['verified'],r['name'],note
def filter_list(category):
 opts=choices(category);key=opts[0][1] if opts else None
 return (gr.update(choices=opts,value=key),*select(key))
def category_update():
 return gr.update(choices=['全部']+[c for c in CATEGORIES if any(r['category']==c for r in read())],value='全部')
def save(key,name,text,category,verified):
 if not key or not name.strip() or not text.strip():raise gr.Error('请选择参考，并填写名称和准确的日文原文。')
 with LOCK:
  rows=read();r=next(r for r in rows if r['id']==key);r.update(name=name.strip(),text=text.strip(),category=category,verified=bool(verified));write(rows)
 return gr.update(choices=choices('全部'),value=key),category_update(),'参考信息已保存。'
def add(audio,name,text,category,verified):
 if not audio or not name.strip() or not text.strip():raise gr.Error('请上传音频，填写名称和准确的日文原文。')
 info=sf.info(audio)
 if not 3<=info.duration<=10:raise gr.Error('参考音频需为3–10秒，请准备完整、清晰的短句。')
 key=uuid.uuid4().hex;dest=ROOT/'imported'/f'{key}.wav';dest.parent.mkdir(exist_ok=True)
 x,sr=sf.read(audio);sf.write(dest,x,sr,subtype='FLOAT')
 with LOCK:
  rows=read();rows.append(dict(id=key,name=name.strip(),text=text.strip(),category=category,verified=bool(verified),audio=dest.relative_to(ROOT).as_posix()));write(rows)
 return (gr.update(choices=choices('全部'),value=key),category_update(),*select(key),'已加入参考库。')
def get_engine():
 global ENGINE
 if ENGINE is None:
  appdir=Path(os.environ.get('GPT_SOVITS_APP','')).expanduser().resolve()
  if not (appdir/'GPT_SoVITS/inference_webui.py').is_file():
   raise RuntimeError('请设置 GPT_SOVITS_APP 为已安装的 GPT-SoVITS 根目录。')
  os.chdir(appdir);sys.path[:0]=[str(appdir/'GPT_SoVITS'),str(appdir)]
  os.environ.update(version='v2ProPlus',hz='25hz',USE_LIBUV='0')
  if os.name=='nt':
   os.environ['PATH']=str(Path(sys.prefix)/'Lib/site-packages/torch/lib')+os.pathsep+str(appdir/'runtime')+os.pathsep+os.environ.get('PATH','')
   from tools.my_utils import load_cudnn
   load_cudnn()
  os.environ.update(language='zh_CN',gpt_path=str(MODEL),sovits_path=str(SOVITS),G2PW='1',is_half='True')
  import inference_webui as infer
  import torch;torch.set_num_threads(1)
  ENGINE=infer
 return ENGINE
def generate(key,text,split,seed):
 if not text.strip():raise gr.Error('请填写要生成的日文台词。')
 r=next((r for r in read() if r['id']==key),None)
 if not r:raise gr.Error('请选择一条参考音频。')
 if not Path(audio_path(r)).is_file():raise gr.Error('参考音频文件不存在。')
 with LOCK:
  infer=get_engine();import torch,numpy as np
  seed=int(seed);random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
  lang=next(k for k,v in infer.dict_language.items() if v=='all_ja');cut=infer.i18n('按中文句号。切' if split else '不切')
  for result in infer.get_tts_wav(audio_path(r),r['text'],lang,text,lang,how_to_cut=cut,speed=1,ref_free=False,if_freeze=False,use_cuda_graph=False,use_flash_attention=False):pass
  sr,wav=result
  if not len(wav) or not np.isfinite(wav).all():raise gr.Error('生成音频无效，请查看日志。')
  folder=ROOT/'generated';folder.mkdir(exist_ok=True);p=folder/(time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]+'.wav');sf.write(p,wav,sr)
  p.with_suffix('.json').write_text(json.dumps(dict(text=text,reference=r,gpt=str(MODEL),sovits=str(SOVITS),seed=seed,speed=1,natural_sentence_split=bool(split),postprocessing='none'),ensure_ascii=False,indent=2),encoding='utf-8')
 return str(p),f'已生成 {len(wav)/sr:.2f} 秒。原速，未调速或滤波。'
def prepare_preview(text,mode,endpoint,model,api_key):
 try:
  japanese,route,note=prepare_text(text,mode,endpoint,model,api_key)
  state=dict(source=text.strip(),mode=mode,endpoint=endpoint.strip(),model=model.strip(),japanese=japanese,route=route)
  return japanese,state,None,note
 except TranslationError as error:
  return '',None,None,str(error)

def generate_with_translation(key,text,split,seed,mode,endpoint,model,api_key,japanese,state):
 matches=bool(state and state.get('source')==text.strip() and state.get('mode')==mode and state.get('endpoint')==endpoint.strip() and state.get('model')==model.strip())
 if matches:
  route=state['route'];note='使用已查看的日文。';japanese=japanese.strip()
  if not japanese or len(japanese)>2000 or (route=='zh' and not KANA.search(japanese)):
   return None,japanese,None,'实际朗读的日文为空、过长或缺少日文假名，请修改后重试。'
 else:
  japanese,state,unused,note=prepare_preview(text,mode,endpoint,model,api_key)
  if state is None:return None,japanese,None,note
  route=state['route']
 try:
  audio,status=generate(key,japanese,split,seed)
  record=Path(audio).with_suffix('.json')
  if record.is_file():
   data=json.loads(record.read_text(encoding='utf-8'));data.update(source_text=text.strip(),input_language_mode=mode,input_route=route,japanese_text=japanese,translation_model=model.strip() if route=='zh' else None,translation_edited=japanese!=state['japanese'])
   record.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
  return audio,japanese,state,note+' '+status
 except Exception:
  return None,japanese,state,'日文已准备好，但语音生成失败。请检查参考音频、模型与运行环境后重试。'

def clear_prepared():return '',None,None,'输入或翻译设置已变更，请重新查看日文或直接生成。'

if __name__=='__main__':get_engine()
initialize();opts=choices('全部');default='baseline_warm' if any(r['id']=='baseline_warm' for r in read()) else (opts[0][1] if opts else None);audio,txt,cat,verified,name,note=select(default)
with gr.Blocks(title='诗音参考音频库') as app:
 gr.Markdown('# 诗音参考音频库\n'+(f'当前库中已有{len(opts)}条参考，可直接选择。' if opts else '当前参考库为空，请加入自己的参考。')+'支持日文直接生成，中文可通过单独配置的翻译服务转成日文后生成。最终输出为日语；分类不能保证相同情绪。\n\n模型：GPT 停顿补样第2轮＋SoVITS 0.00002第8轮。')
 with gr.Row():
  with gr.Column():
   category=gr.Dropdown(['全部']+[c for c in CATEGORIES if any(r['category']==c for r in read())],value='全部',label='按语气筛选')
   selected=gr.Dropdown(opts,value=default,label='选择参考音频'+(f'（已有{len(opts)}条）' if opts else '（请先自行导入）'))
   audition=gr.Audio(value=audio,type='filepath',label='试听当前参考',interactive=False)
   reference_text=gr.Textbox(value=txt,label='参考音频对应日文原文',lines=3)
   refname=gr.Textbox(value=name,label='参考名称')
   emotion=gr.Dropdown(CATEGORIES,value=cat,label='情绪分类（可修改）')
   confirmed=gr.Checkbox(value=verified,label='我已试听确认该语气')
   basis=gr.Textbox(value=note,label='分类依据与剧情上下文',interactive=False,lines=5)
   savebtn=gr.Button('保存参考信息')
  with gr.Column():
   target=gr.Textbox(label='要说的内容（中文或日文）',lines=4,value='')
   input_language=gr.Radio(['自动','中文','日文'],value='自动',label='输入语言')
   gr.Markdown('有日文假名时直接生成；纯汉字默认按中文翻译。纯汉字日文或混合语言请手动选择。最终输出始终是日语。')
   prepared=gr.State(None)
   with gr.Accordion('中文翻译设置（使用中文时配置）',open=False):
    gr.Markdown('填写你使用的翻译服务。支持兼容chat-completions的本地或在线服务；在线翻译会把输入文本发送给该服务。地址需包含服务要求的/v1；不附带或自动下载翻译模型。设置只用于当前运行，密钥不写入生成记录。')
    translation_endpoint=gr.Textbox(label='翻译服务地址',placeholder='例如本机服务：http://127.0.0.1:11434/v1',value='')
    translation_model=gr.Textbox(label='翻译模型名称',placeholder='填写该服务提供的模型名称',value='')
    translation_key=gr.Textbox(label='服务密钥（本地服务可留空）',type='password',value='')
   preview=gr.Button('查看／翻译日文')
   japanese_preview=gr.Textbox(label='实际朗读的日文（可修改）',lines=4,value='')
   split=gr.Checkbox(value=True,label='按自然句号分句（长句推荐）')
   seed=gr.Number(value=20261011,precision=0,label='随机种子（相同参数可复现）')
   run=gr.Button('用当前参考生成',variant='primary')
   result=gr.Audio(type='filepath',label='生成结果')
   message=gr.Textbox(label='状态',interactive=False)
 with gr.Accordion('加入新的参考音频（可选）',open=not bool(opts)):
  gr.Markdown('已有参考可以直接选择。如需新增，请仅导入你有权使用的音频，填写与录音一致的日文原文。原作：minori《eden*》。')
  upload=gr.Audio(type='filepath',label='上传3–10秒清晰参考音频')
  newname=gr.Textbox(label='名称');newtext=gr.Textbox(label='准确的日文原文',lines=2)
  newemotion=gr.Dropdown(CATEGORIES,value='平静',label='语气分类');newverified=gr.Checkbox(label='我已试听确认该语气')
  addbtn=gr.Button('加入参考库')
 category.input(filter_list,[category],[selected,audition,reference_text,emotion,confirmed,refname,basis],api_name='filter_references')
 selected.input(select,[selected],[audition,reference_text,emotion,confirmed,refname,basis],api_name='select_reference')
 savebtn.click(save,[selected,refname,reference_text,emotion,confirmed],[selected,category,message],api_name='save_reference')
 addbtn.click(add,[upload,newname,newtext,newemotion,newverified],[selected,category,audition,reference_text,emotion,confirmed,refname,basis,message],api_name='add_reference')
 preview.click(prepare_preview,[target,input_language,translation_endpoint,translation_model,translation_key],[japanese_preview,prepared,result,message],api_name='prepare_text',concurrency_limit=1)
 for control in [target,input_language,translation_endpoint,translation_model,translation_key]:
  control.input(clear_prepared,[],[japanese_preview,prepared,result,message],queue=False)
 run.click(generate_with_translation,[selected,target,split,seed,input_language,translation_endpoint,translation_model,translation_key,japanese_preview,prepared],[result,japanese_preview,prepared,message],api_name='generate',concurrency_limit=1)
if __name__=='__main__':
 app.queue(default_concurrency_limit=1).launch(server_name='127.0.0.1',server_port=9882,inbrowser=False,allowed_paths=[str(ROOT)])
