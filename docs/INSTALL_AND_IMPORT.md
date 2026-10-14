# 首次使用：完整整合包解压即用

当前 [Release](https://github.com/Lunona/eden-sion-gpt-sovits/releases/tag/v1.0.2) 已发布独立Windows完整整合包。**普通使用不需要先安装GPT-SoVITS、不需要手动导入模型、不需要填写外部环境路径。**

1. 下载全部 `.001`、`.002`、`.003` 三个分卷，放在同一文件夹。
2. 用7-Zip打开 `.001` 并完整解压。
3. 双击 **启动GPT-SoVITS.cmd**。无可用NVIDIA显卡时用 **CPU模式启动.cmd**。
4. 默认已加载诗音模型并选择参考，在页面中输入文字即可生成。

包内已包含Python、GPT-SoVITS主程序、生成依赖与15条参考。NVIDIA加速仍需兼容CUDA12.8的显卡驱动。本包是生成版，暂未打入完整训练环境。

![默认模型及参考已就绪](images/10-default-reference.png)

详见[从下载到生成的图文教程](TUTORIAL.md)。

**原项目与作者：RVC-Boss及GPT-SoVITS贡献者**，见[原项目](https://github.com/RVC-Boss/GPT-SoVITS)和[MIT许可](https://github.com/RVC-Boss/GPT-SoVITS/blob/main/LICENSE)。原作：minori《eden*》。诗音模型微调及个人整合包发布者：Lunona。各组件保留原版权和许可。

## 可选：把诗音权重导入自己已有的原版环境

下面仅供希望使用自己已有GPT-SoVITS环境的人参考，不是完整整合包的安装步骤。请按[原作者安装说明](https://github.com/RVC-Boss/GPT-SoVITS/blob/main/docs/cn/README.md)准备支持v2ProPlus的环境，再按下面的方法加载权重。

### 手动导入 v2ProPlus

这条路线只用原版软件，不要求使用本项目的参考库或启动器。

1. 下载并解压[诗音完整版](https://github.com/Lunona/eden-sion-gpt-sovits/releases/tag/v1.0.2)。进入诗音包的 `models` 文件夹，找到：
   - `eden_诗音_Sion_GPT.ckpt`
   - `eden_诗音_Sion_SoVITS.pth`
2. 找到完整环境的**程序目录**：即包含 `GPT_SoVITS` 与 `webui.py` 的目录。将两个文件分别复制到以下目录，不要放反：

|诗音权重文件|放进完整环境的目录|
|---|---|
|eden_诗音_Sion_GPT.ckpt|GPT_weights_v2ProPlus|
|eden_诗音_Sion_SoVITS.pth|SoVITS_weights_v2ProPlus|

目录不存在时在程序目录里新建。以示例目录为例，完成后是：

```text
D:\AI\GPT-SoVITS\
├─ webui.py
├─ GPT_SoVITS\
├─ GPT_weights_v2ProPlus\
│  └─ eden_诗音_Sion_GPT.ckpt
└─ SoVITS_weights_v2ProPlus\
   └─ eden_诗音_Sion_SoVITS.pth
```

3. 打开原版主页面，版本选择 **v2ProPlus**；进入 **1-GPT-SoVITS-TTS → 1C-推理**，点击开启 **TTS推理WebUI** 的按钮。不同版本文字稍有不同，以该环境实际界面为准。只停留在“0-前置数据集获取工具”不是生成页面。
4. 在推理页面点击 **刷新模型路径**。GPT模型列表选择文件名含 `eden_诗音_Sion_GPT.ckpt` 的那项；SoVITS模型列表选择含 `eden_诗音_Sion_SoVITS.pth` 的那项。没有出现时检查复制目录，并刷新或重启推理界面。不要用“不训练直接推……底模”代替已训练的诗音权重。
5. 上传3–10秒参考音频、填写这条参考的准确日文原文，参考语言选 **日文**。可用诗音包 `curated` 中的参考，并从 `references.json` 查对应原文；已有15条不等于程序会自动替你选参考。
6. 在目标文本栏输入**新日文台词**，目标语言选 **日文**，语速先保持1，再点击 **合成语音**。两份文件是训练好的模型，不需要先重训。

原版界面没有本项目新增的中文翻译API入口。若想中文输入后转日文生成，或在同一页使用15条参考库，请用下面路线B。


原版环境的生成页面仍需手动提供参考；本项目完整整合包已默认选好参考。原版页面没有本项目新增的中文翻译API入口。
