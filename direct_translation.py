"""Chinese/Japanese input adapter for the existing inference engine."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from translation import prepare_text, TranslationError, KANA

def prepare_preview(text,mode,endpoint,model,key):
    try:
        japanese,route,note=prepare_text(text,mode,endpoint,model,key)
        state=dict(source=text.strip(),mode=mode,endpoint=endpoint.strip(),model=model.strip(),japanese=japanese,route=route)
        return japanese,state,None,note
    except TranslationError as error:
        return '',None,None,str(error)

def clear_preview():
    return '',None,None,'输入或翻译设置已变更，请重新查看日文或直接生成。'

def resolve_text(text,mode,endpoint,model,key,japanese,state):
    matches=bool(state and state.get('source')==text.strip() and state.get('mode')==mode and state.get('endpoint')==endpoint.strip() and state.get('model')==model.strip())
    if matches:
        japanese=japanese.strip()
        if not japanese or len(japanese)>2000 or (state['route']=='zh' and not KANA.search(japanese)):
            raise TranslationError('实际朗读的日文为空、过长或缺少日文假名，请修改后重试。')
        return japanese,state,'使用已查看的日文。'
    japanese,route,note=prepare_text(text,mode,endpoint,model,key)
    state=dict(source=text.strip(),mode=mode,endpoint=endpoint.strip(),model=model.strip(),japanese=japanese,route=route)
    return japanese,state,note

def synthesis_adapter(engine,language):
    def generate(*values):
        import gradio as gr
        args=list(values[:-6])
        mode,endpoint,model,key,japanese,state=values[-6:]
        try:
            japanese,state,note=resolve_text(args[3],mode,endpoint,model,key,japanese,state)
        except TranslationError as error:
            raise gr.Error(str(error)) from None
        args[3]=japanese
        args[4]=language
        for audio in engine(*args):
            yield audio,japanese,state,note+' 已生成日语语音。'
    return generate
