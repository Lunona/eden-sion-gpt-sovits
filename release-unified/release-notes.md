## 完整包已整合更新

重新下载下方 sion-v1.0.2-full-15-references.zip，解压到新目录，双击第一层的 **启动GPT-SoVITS.cmd**。首次指定已有 GPT-SoVITS 完整环境的目录，之后会记住；加载完成后自动打开 http://127.0.0.1:9872/ 。

- 同一个页面，用顶部大按钮切换 **直接生成** 与 **参考库**。
- 两页都有翻译 API 入口：日文直接生成，中文先通过配置的服务翻译成日文再生成日语。可查看和修改实际朗读的日文。
- 完整15条参考及文本、分类均已保留。参考库直接选择即可；直接生成可手动上传参考，无需先加入库。
- 模型名能看出是 **eden* 诗音**，默认使用 GPT 停顿补样第2轮＋SoVITS 0.00002第8轮，权重内容未变。
- 启动、停止脚本已整合；停止脚本仅停止本目录启动的服务。
- 本次直接替换完整版，不再另发升级补丁。

👉 [图文教程](https://github.com/Lunona/eden-sion-gpt-sovits/blob/main/docs/TUTORIAL.md) · [翻译设置](https://github.com/Lunona/eden-sion-gpt-sovits/blob/main/docs/CHINESE_INPUT.md) · [替换旧版与保留自己的参考](https://github.com/Lunona/eden-sion-gpt-sovits/blob/main/docs/UPGRADE.md)

本包需要已有的完整 GPT-SoVITS v2ProPlus 环境，Gradio 4.44.1；不包含 Python、CUDA、主程序或通用预训练依赖。GitHub Source code 不包含权重和参考音频。

## 已验证的流程

下载包实际启动及停止、模型默认选择、直接生成与参考库均已在 Windows 环境验证，两个入口均实际生成音频。中文转日文的衔接、未配置时停止、修改译文后生成，通过本机固定响应翻译接口验证；这不是实际翻译模型质量评测。另通过已有12项翻译流程测试。密钥未写入发布文件、启动设置或生成记录。

## 来源与使用范围

原作：minori《eden*》。非官方个人实验，无官方授权或代言关系。作者代码、模型和生成内容仅限非商业用途，对外传播须标明 AI 合成。原作音频、文本、角色及配音表演权利属于原权利人，本项目不转授或保证第三方素材权利，不表示已取得再分发授权。完整条款见仓库。
