# 爆款采集模块功能参数输入与响应规范

## 适用范围

本文档用于定义 `app/module/hot_item_collection` 模块 Web 控制台与脚本入口的参数输入和响应格式。

本文档只描述数据结构、字段类型、必填规则和填写约束，不描述具体业务流程或代码实现。

## 基本约定

- 脚本入口不接收命令行输入参数，运行参数从模块 `config.json` 读取。
- Web 控制台接口统一使用 JSON 请求与 JSON 响应。
- 响应必须符合调用方约定的数据格式或文档格式。
- 字段名使用英文驼峰命名，并与本规范保持一致。
- 说明性文本必须使用简体中文。
- 可选数组字段没有数据时使用空数组 `[]`，不使用 `null`。
- 可选字符串字段没有数据时使用空字符串 `""`，不使用 `null`。
- 时间字段统一使用 `yyyy-MM-dd HH:mm:ss` 格式。

## 输入规范

### 脚本输入参数

采集、下载、登录和流水线脚本不接收位置参数。FastMoss 账号来自模块 `config.json` 中的 `login_params.phone` 和 `login_params.password`。

### Web 配置参数

`POST /api/config` 与 `POST /api/actions/{actionId}/run` 的 `config` 字段允许传入以下结构：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `show_browser` | `boolean` | 否 | `false` | 是否显示浏览器窗口。 |
| `category_config_path` | `string` | 否 | `"app/tools/fastmoss_category_config.json"` | FastMoss 分类数据源 JSON 文件路径，支持绝对路径和相对项目根目录路径。 |
| `login_params.phone` | `string` | 否 | `""` | FastMoss 手机号。 |
| `login_params.password` | `string` | 否 | `""` | FastMoss 密码。 |
| `filter_condition.category_path` | `array` | 否 | `[]` | FastMoss 类目路径，最多保留三级。 |
| `filter_condition.keyword` | `string` | 否 | `""` | 商品搜索关键词。 |
| `filter_condition.country` | `string` | 否 | `"马来西亚"` | 国家或地区筛选。 |
| `filter_condition.product_limit` | `number` | 否 | `3` | 采集商品数量。 |
| `filter_condition.videos_per_product` | `number` | 否 | `20` | 每个商品采集的视频数量。 |
| `result_path.csv_output_dir` | `string` | 否 | `""` | CSV 输出目录；空值使用默认目录。 |
| `result_path.video_output_dir` | `string` | 否 | `""` | 视频输出目录；空值使用默认目录。 |

### 输入校验规则

1. 脚本入口不需要传入请求体或命令行位置参数。
2. Web 接口如无参数，请传入空 JSON object：`{}`。
3. `category_path` 如传入数组，只保留非空字符串且最多三级。

## 响应规范

### Web 响应类型

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `actions` | `array` | 否 | `[]` | 可执行动作列表。 |
| `tasks` | `array` | 否 | `[]` | 当前服务生命周期内的任务列表。 |
| `taskId` | `string` | 否 | `""` | 异步任务 ID。 |
| `status` | `string` | 否 | `""` | 任务状态，可能为 `running`、`completed` 或 `failed`。 |
| `logs` | `array` | 否 | `[]` | 任务输出日志。 |
| `files` | `array` | 否 | `[]` | 可预览或下载的产物文件列表。 |
| `error` | `string` | 否 | `""` | 请求失败时的错误信息。 |

### 响应校验规则

1. 响应内容必须符合本文档定义的响应格式。
2. 响应内容不得虚构输入或采集来源中不存在的数据。
3. 响应内容中如需保留无法确认的信息，应使用 `待确认`。
