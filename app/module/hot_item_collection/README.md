# 爆款采集模块

## 模块定位

`hot_item_collection` 用于承载爆款商品、爆款内容或爆款线索的采集相关能力。

当前模块提供 FastMoss 爆款商品采集、关联视频 URL 获取、TikTok 无水印视频下载和本地 Web 控制台。

## 当前能力

- 打开 FastMoss 并保存登录态。
- 按国家、类目、关键词和筛选条件采集商品及关联视频。
- 将采集结果写入 CSV。
- 读取最新 CSV 并通过 Kolsprite 下载 TikTok 视频。
- 通过 Web 控制台维护配置、触发任务、查看任务日志和预览输出文件。

## 快速启动

```bash
app/module/hot_item_collection/restart_server.command --foreground
```

默认访问地址为 `http://localhost:8091`。如需指定端口，可在命令前设置 `PORT`。

## 模块文件

| 文件 | 说明 |
| --- | --- |
| `server.py` | 本地 Web 控制台服务。 |
| `index.html` | Web 控制台页面。 |
| `collect_fastmoss_product_videos.py` | 采集 FastMoss 商品及关联视频。 |
| `download_tiktok_videos_kolsprite.py` | 下载 TikTok 无水印视频。 |
| `login_fastmoss_assisted.py` | 辅助刷新 FastMoss 登录态。 |
| `config_store.py` | 读取、兼容和保存模块配置。 |
| `project_assets.py` | 输出目录、运行态和文件命名工具。 |
| `config.json` | 当前本地配置文件。 |
| `config.example.json` | 可提交的配置示例，不包含账号密码。 |
| `function-parameter-response-standard.md` | 模块功能参数输入与响应规范。 |

## 输出与本地状态

- CSV 和视频默认写入 `app/result/hot_item_collection/`。
- 浏览器登录态、诊断截图和本地 profile 写入模块目录下的运行态目录，并已加入 `.gitignore`。
- `config.json` 支持旧字段 `fastmoss_username`、`fastmoss_password` 和 `filter—condition`，保存后会按新分组结构输出。
