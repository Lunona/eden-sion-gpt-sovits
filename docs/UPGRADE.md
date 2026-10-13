# 用新版完整包替换旧版

本次替换 v1.0.2 的完整下载包，不再另外发布补丁。

1. 停止旧版服务。
2. 重新下载发布页中的 sion-v1.0.2-full-15-references.zip，解压到新目录。
3. 双击新目录的 启动GPT-SoVITS.cmd，首次指定已有完整环境的目录。以后会记住安装路径。
4. 浏览器在同一页面切换直接生成、参考库；两页均有翻译 API 设置。

新包的模型名称为 eden_诗音_Sion_GPT.ckpt 与 eden_诗音_Sion_SoVITS.pth，权重内容与旧版相同，参考仍是完整15条。旧版模型清单位置变化不会影响旧目录中的文件。

如旧版加入过自己的参考，请先备份 references.json 与对应 imported、curated 文件，再迁移到新目录。相对音频路径需保持对应目录；generated 中的结果可按需保留。不要用新包的 references.json 覆盖自己的修改。API 密钥不保存，请重新填写。
