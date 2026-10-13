import textwrap

def integrated_source(path):
    source=path.read_text(encoding="utf-8")
    source=source.replace('value=i18n("中文"),','value=i18n("日文"),')
    source=source.replace('label=i18n("需要合成的语种") + i18n(".限制范围越小判别效果越好。"),','label="输出语言（日语）",\n                    interactive=False,')
    source=source.replace('text = gr.Textbox(label=i18n("需要合成的文本"), value="", lines=26, max_lines=26)', '''text = gr.Textbox(label="要说的内容（中文或日文）", value="", lines=6, max_lines=12)
                direct_mode=gr.Radio(['自动','中文','日文'],value='自动',label='输入语言')
                gr.Markdown('日文直接生成；中文先翻译成日文。最终朗读日语。纯汉字日文请手动选择日文。')
                with gr.Accordion('翻译 API 设置（中文输入时配置）',open=True):
                    direct_endpoint=gr.Textbox(label='翻译服务地址',placeholder='https://api.deepseek.com',value='')
                    direct_model=gr.Textbox(label='翻译模型名称',placeholder='deepseek-flash',value='')
                    direct_key=gr.Textbox(label='API 密钥',type='password',value='')
                direct_preview_button=gr.Button('查看／翻译日文')
                direct_japanese=gr.Textbox(label='实际朗读的日文（可修改）',lines=4,value='')
                direct_state=gr.State(None)
                direct_status=gr.Textbox(label='翻译与生成状态',interactive=False)''')
    source=source.replace('            get_tts_wav,\n            [','            direct_generate,\n            [',1)
    source=source.replace('                cfg_rate,\n            ],\n            [output],','''                cfg_rate,
                direct_mode,direct_endpoint,direct_model,direct_key,direct_japanese,direct_state,
            ],
            [output,direct_japanese,direct_state,direct_status],
            api_name='direct_generate',''',1)
    source=source.replace('        inference_button.click(','''        direct_generate=synthesis_adapter(get_tts_wav,i18n('日文'))
        direct_preview_button.click(prepare_preview,[text,direct_mode,direct_endpoint,direct_model,direct_key],[direct_japanese,direct_state,output,direct_status],api_name='direct_prepare_text')
        for field in [text,direct_mode,direct_endpoint,direct_model,direct_key]:
            field.input(clear_preview,[],[direct_japanese,direct_state,output,direct_status],queue=False)
        inference_button.click(''',1)
    marker='with gr.Blocks(title="GPT-SoVITS WebUI"'
    start=source.index(marker)
    body_start=source.index("\n",start)+1
    end=source.index('\nif __name__ == "__main__":',body_start)
    body=source[body_start:end]
    navigation_css='''
#sion-navigation > .tab-nav {display:flex!important;gap:12px!important;padding:12px!important;background:#eef6ff!important;border-radius:14px!important;border:1px solid #b9d7fa!important;}
#sion-navigation > .tab-nav > button {flex:1!important;min-height:58px!important;margin:0!important;padding:14px 24px!important;font-size:22px!important;font-weight:700!important;color:#1954a0!important;background:white!important;border:2px solid #b9d7fa!important;border-radius:10px!important;opacity:1!important;}
#sion-navigation > .tab-nav > button.selected, #sion-navigation > .tab-nav > button[aria-selected="true"] {background:#2169d5!important;color:white!important;border-color:#2169d5!important;box-shadow:0 3px 10px #2169d533!important;}
#sion-navigation > .tab-nav > button:hover {border-color:#2169d5!important;}
@media(max-width:600px){#sion-navigation > .tab-nav > button{font-size:18px!important;padding:12px 8px!important;}}
'''
    prefix=source[:start]+'\nfrom direct_translation import synthesis_adapter,prepare_preview,clear_preview\ncss += '+repr(navigation_css)+'\n'
    tabs='    gr.Markdown("# eden* 诗音语音生成\\n请选择下方入口：手动上传参考，或直接使用参考库中的15条。")\n    with gr.Tabs(elem_id="sion-navigation"):\n        with gr.Tab("直接生成"):\n'
    library='''
        with gr.Tab("参考库"):
            gr.Markdown("完整版已预置15条参考，可直接选择生成。中文翻译设置在下方页面内展开。")
            gr.HTML('<iframe title="诗音参考库" src="http://127.0.0.1:9882/" style="width:100%;height:2200px;border:0" loading="eager"></iframe>')
'''
    return prefix+source[start:body_start]+tabs+textwrap.indent(body,"        ")+library+source[end:]
