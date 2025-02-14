# 网易云音乐云盘导入工具

将歌曲批量导入到网易云音乐云盘的工具。

## 功能特点

- 支持批量导入歌曲到网易云音乐云盘
- 支持扫码登录（网盘容量获取有问题）和手动输入 cookie（推荐App或客户端抓包） 两种登录方式
- 自动去重，避免重复上传
- 支持自定义接口频繁重试等待时间（默认40秒）
- 支持自定义上传延迟时间（默认0秒）
- 详细的操作日志，包含时间戳显示

## 交流群

- 群人数已超过200人，添加微信 `Br00wn` 邀请进群
- 欢迎加入交流, 获取最新的exe打包文件

## 使用前提

本程序需要配合 NeteaseCloudMusicApi 使用，你可以：

1. 下载完整包：
   - [完整包下载(含API接口和Node.js)](https://luqiao.lanzouw.com/iFYep2nqmbmh)
   - 解压后直接使用，无需其他配置

2. 或者自行配置：
   - 从 [NeteaseCloudMusicApi GitLab 仓库](https://gitlab.com/Binaryify/neteasecloudmusicapi) 获取并运行 API 服务
   - 确保 API 服务运行在 3000 端口

## Windows一键运行版本：

1. 下载可执行文件：
   - [exe可执行文件(含node服务和脚本文件)](https://luqiao.lanzouw.com/icaWx2nrnfij)

## 使用说明

1. **准备工作**
   - 确保 NeteaseCloudMusicApi 服务已启动（wind版可运行 NeteaseCloudMusicApi-win.exe）
   - 准备要导入的歌曲数据（JSON 格式）

2. **登录方式**
   - 方式一：手动输入 cookie（推荐）
     - 一定要从app或者客户端抓网易云音乐的 cookie
     - 推荐使用 [Reqable](https://reqable.com/zh-CN/) 抓包工具获取 cookie
     - 将 cookie 保存到 cookies.txt 文件或通过程序输入
   - 方式二：扫码登录
     - 直接运行程序选择扫码登录即可
     - 注意：扫码登录可能无法正确识别云盘容量

3. **参数设置**
   - 接口频繁重试等待时间
     - 默认为40秒
     - 可在程序启动时自定义设置
     - 用于处理接口频繁访问的等待时间
   - 上传延迟时间
     - 默认为0秒
     - 可在程序启动时自定义设置
     - 支持小数点，精确控制上传间隔

4. **运行程序**
   ```bash
   python main.py
   ```

5. **后续操作**
   - 按提示输入歌曲 JSON 文件路径
   - 程序会自动处理歌曲导入
   - 导入失败的歌曲 ID 会记录在 failed_ids.txt 中

## 注意事项

1. 确保你的网易云音乐账号有足够的云盘空间
2. 建议使用手动输入 cookie 的方式登录，可以更准确地获取云盘信息
3. 如遇到频繁操作提示，程序会自动等待后重试
4. 程序会自动去重，避免重复上传相同歌曲
5. 获取 cookie 时推荐使用 Reqable 抓包工具，它是一个强大的跨平台抓包工具，支持 Windows/macOS/Linux
6. 可以通过调整上传延迟时间来控制上传速度，避免接口频繁访问

## 依赖项

```bash
pip install -r requirements.txt
```

## 问题反馈

如果遇到问题，请检查：
1. NeteaseCloudMusicApi 服务是否正常运行
2. 网络连接是否正常
3. Cookie 是否有效（建议使用 Reqable 抓包工具获取最新 cookie）
4. JSON 文件格式是否正确
5. 是否需要调整重试等待时间或上传延迟时间

## 免责声明

本工具仅供学习交流使用，请勿用于商业用途。使用本工具时请遵守相关法律法规，尊重版权。
