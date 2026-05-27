# 产品信息模块功能参数输入与响应规范

## 适用范围

本文档用于定义 `app/module/product_info` 模块统一的功能参数输入与响应格式。

本文档只描述数据结构、字段类型、必填规则和填写约束，不描述具体功能能力、业务流程或代码实现。

## 基本约定

- 输入使用 JSON object 作为根节点。
- 响应为 Markdown 文档，必须符合 `app/standard/knowledge-md-format-standard.md`。
- 字段名使用英文驼峰命名，并与本规范保持一致。
- 说明性文本必须使用简体中文。
- 可选数组字段没有数据时使用空数组 `[]`，不使用 `null`。
- 可选字符串字段没有数据时使用空字符串 `""`，不使用 `null`。
- 时间字段统一使用 `yyyy-MM-dd HH:mm:ss` 格式。
- 价格字段统一使用字符串，避免金额精度丢失。
- 价格字符串不包含货币符号、千分位分隔符或单位。

## SQLite 数据库规范

### 数据库职责

产品信息模块必须维护一个 SQLite 数据库，用于记录产品信息 Markdown 文档与产品报告 Markdown 文档之间的关系。

数据库只保存索引关系和文件定位信息，不保存完整产品详情。完整产品详情仍以产品信息 Markdown 文档和原始输入数据为准。

### 数据库配置

| 配置项 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `sqlite_database_path` | `str` | 是 | `app/module/product_info/product_info.sqlite3` | 产品信息模块 SQLite 数据库路径。相对路径以项目根目录为基准解析。 |

### 初始化脚本

项目初始化或首次使用产品信息模块前，必须执行数据库初始化脚本：

```bash
python3 -m app.module.product_info.init_database
```

初始化脚本必须具备幂等性；重复执行不得删除已有产品信息和产品报告记录。

### `product_info_document`

产品信息文档索引表用于记录每个 `productCode` 对应的产品信息 Markdown 文件。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | `INTEGER` | 主键，自增 | 产品信息数据库内部 ID。 |
| `product_code` | `TEXT` | 必填，唯一 | 商品编码，对应输入字段 `productCode`。 |
| `product_name_zh` | `TEXT` | 必填 | 中文产品名，对应输入字段 `productNameZh`。 |
| `info_file_name` | `TEXT` | 必填 | 产品信息 Markdown 文件名。 |
| `info_file_path` | `TEXT` | 必填，唯一 | 产品信息 Markdown 文件路径，建议使用项目相对路径。 |
| `product_created_at` | `TEXT` | 必填 | 产品信息创建时间，对应输入字段 `createdAt`。 |
| `created_at` | `TEXT` | 必填 | 数据库记录创建时间。 |
| `updated_at` | `TEXT` | 必填 | 数据库记录更新时间。 |

### `product_report_document`

产品报告索引表用于记录每个产品信息下已经生成的产品报告。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | `INTEGER` | 主键，自增 | 产品报告数据库内部 ID。 |
| `product_info_id` | `INTEGER` | 必填，外键 | 关联 `product_info_document.id`，删除产品信息记录时级联删除报告索引。 |
| `product_code` | `TEXT` | 必填 | 冗余商品编码，便于通过 `productCode` 查询报告。 |
| `report_no` | `INTEGER` | 必填，大于 0 | 产品报告序号，对应文件名中的 `{序号}`。 |
| `product_name_zh_snapshot` | `TEXT` | 必填 | 报告生成时的中文产品名快照。 |
| `report_file_name` | `TEXT` | 必填 | 产品报告 Markdown 文件名。 |
| `report_file_path` | `TEXT` | 必填，唯一 | 产品报告 Markdown 文件路径，建议使用项目相对路径。 |
| `created_at` | `TEXT` | 必填 | 数据库记录创建时间。 |
| `updated_at` | `TEXT` | 必填 | 数据库记录更新时间。 |

### 关系约束

1. `product_info_document.product_code` 必须唯一。
2. `product_report_document.product_info_id` 必须关联已存在的产品信息记录。
3. 同一个 `product_info_id` 下的 `report_no` 必须唯一。
4. `product_report_document.report_file_path` 必须唯一。
5. 创建产品报告前，必须先通过 `productCode` 匹配到产品信息记录；匹配失败时不得生成产品报告。

## 产品信息文档输入规范

### 输入根对象

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `productCode` | `str` | 是 | 无 | 商品编码，用于唯一标识一个产品。 |
| `productNameZh` | `str` | 是 | 无 | 产品中文名称。 |
| `productNameLocal` | `str` | 否 | `""` | 产品在目标国家或地区使用的本地语言名称。 |
| `country` | `str` | 是 | 无 | 目标国家或地区名称，使用简体中文填写。 |
| `categories` | `list[str]` | 是 | 无 | 产品所属类目，至少 1 项，按从大到小或从主到辅的顺序填写。 |
| `createdAt` | `str` | 是 | 无 | 产品信息创建时间，格式为 `yyyy-MM-dd HH:mm:ss`。 |
| `extendedAttributes` | `list[NameValueItem]` | 否 | `[]` | 产品扩展属性，用于描述非规格类卖点或参数。 |
| `extendedInfo` | `list[NameValueItem]` | 否 | `[]` | 产品扩展信息，用于存放店铺链接、渠道链接等补充信息。 |
| `specifications` | `list[NameValueItem]` | 否 | `[]` | 产品规格项，同一个 `name` 可以出现多次，用于表达多个可选值。 |
| `skus` | `list[SkuItem]` | 否 | `[]` | SKU 列表，多规格商品应填写。 |
| `keySellingPoints` | `list[KeySellingPoint]` | 否 | `[]` | 核心卖点列表，按推荐展示顺序填写。 |
| `price` | `PriceInfo` | 是 | 无 | 产品默认价格或主推价格。 |

### `NameValueItem`

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `name` | `str` | 是 | 无 | 属性名称、信息名称或规格名称。 |
| `value` | `str` | 是 | 无 | 属性值、信息值或规格值。 |

### `SkuItem`

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `skuId` | `str` | 是 | 无 | SKU 编码，同一产品内必须唯一。 |
| `attributes` | `dict[str, str]` | 是 | 无 | SKU 规格组合，键为规格名，值为规格值。 |
| `price` | `PriceInfo` | 是 | 无 | SKU 价格信息。 |

### `PriceInfo`

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `originalPrice` | `str` | 是 | 无 | 原价，不包含货币符号。 |
| `promotionalPrice` | `str` | 否 | `""` | 促销价，不包含货币符号；没有促销价时填写空字符串。 |

### `KeySellingPoint`

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `str` | 是 | 无 | 卖点标题，适合直接用于展示或生成文案。 |
| `description` | `str` | 是 | 无 | 卖点描述，说明具体价值、场景或差异化优势。 |

### 输入校验规则

1. 根对象必须是 JSON object，不允许使用数组作为根节点。
2. 所有字段名必须与本规范保持一致，区分大小写。
3. `createdAt` 必须使用 `yyyy-MM-dd HH:mm:ss` 格式。
4. `productCode` 和 `skuId` 应使用稳定编码，不应使用展示文案作为编码。
5. `specifications` 允许同名多值，用于表达颜色、尺寸、孔位等可选规格。
6. `skus.attributes` 中的规格名应能在 `specifications.name` 中找到对应项。
7. `skus.attributes` 中的规格值应能在 `specifications.value` 中找到对应项。
8. 同一产品内不允许出现重复的 `skuId`。
9. `price` 表示产品默认价格，`skus[].price` 表示具体 SKU 价格。

### 输入示例

```json
{
  "productCode": "SHG-001",
  "productNameZh": "智能桌面种植机",
  "productNameLocal": "スマートハーブガーデン",
  "country": "日本",
  "categories": ["家居", "智能设备", "园艺"],
  "createdAt": "2026-05-23 13:52:00",
  "extendedAttributes": [
    { "name": "光照功率", "value": "24W 全光谱 LED" },
    { "name": "水泵噪音", "value": "≤35dB" },
    { "name": "水箱续航", "value": "7-10天" },
    { "name": "适用种子", "value": "罗勒、薄荷、香菜、小番茄、草莓" },
    { "name": "连接方式", "value": "Wi-Fi 2.4G / 蓝牙 5.0" },
    { "name": "App 支持", "value": "iOS 14+ / Android 10+" }
  ],
  "extendedInfo": [
    { "name": "TK 店铺", "value": "https://www.tiktok.com/@simchair" }
  ],
  "specifications": [
    { "name": "颜色", "value": "奶油白" },
    { "name": "颜色", "value": "薄荷绿" },
    { "name": "颜色", "value": "珊瑚粉" },
    { "name": "水槽容量", "value": "1.2L" },
    { "name": "种植孔位", "value": "3孔" },
    { "name": "种植孔位", "value": "6孔" }
  ],
  "skus": [
    {
      "skuId": "SHG-3-W",
      "attributes": { "孔位": "3孔", "颜色": "奶油白" },
      "price": { "originalPrice": "249", "promotionalPrice": "199" }
    },
    {
      "skuId": "SHG-3-G",
      "attributes": { "孔位": "3孔", "颜色": "薄荷绿" },
      "price": { "originalPrice": "249", "promotionalPrice": "199" }
    },
    {
      "skuId": "SHG-3-P",
      "attributes": { "孔位": "3孔", "颜色": "珊瑚粉" },
      "price": { "originalPrice": "249", "promotionalPrice": "199" }
    },
    {
      "skuId": "SHG-6-W",
      "attributes": { "孔位": "6孔", "颜色": "奶油白" },
      "price": { "originalPrice": "299", "promotionalPrice": "249" }
    },
    {
      "skuId": "SHG-6-G",
      "attributes": { "孔位": "6孔", "颜色": "薄荷绿" },
      "price": { "originalPrice": "299", "promotionalPrice": "249" }
    },
    {
      "skuId": "SHG-6-P",
      "attributes": { "孔位": "6孔", "颜色": "珊瑚粉" },
      "price": { "originalPrice": "299", "promotionalPrice": "249" }
    }
  ],
  "keySellingPoints": [
    {
      "title": "全自动托管，忘了浇水也不怕",
      "description": "内置水位传感器 + 智能补光系统，缺水自动提醒、光照不足自动补偿。出差一周回来，你的罗勒比你活得还好。"
    },
    {
      "title": "6倍生长速度，看得见的成长",
      "description": "全光谱 LED 模拟最佳日照，配合定时营养液循环，从种子到餐桌比土培快 6 倍。App 每日推送生长日记，每一片新叶都有记录。"
    },
    {
      "title": "摆哪都好看，像一件家居艺术品",
      "description": "三种莫兰迪配色 + 哑光磨砂机身，放在厨房是工具，放在书桌是装饰，放在客厅是话题。"
    }
  ],
  "price": {
    "originalPrice": "299",
    "promotionalPrice": "249"
  }
}
```

## 产品信息文档响应规范

### 响应类型

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `markdown` | `str` | 是 | 无 | 符合 `app/standard/knowledge-md-format-standard.md` 的 Markdown 文档内容。 |
| `fileName` | `str` | 是 | 无 | Markdown 文档文件名，必须使用输入字段 `productNameZh` 的值，并以 `.md` 结尾。 |

### Markdown 响应规则

1. 输出文件必须是 `.md` 文件。
2. Markdown 内容必须符合 `app/standard/knowledge-md-format-standard.md`。
3. 文档内容必须使用简体中文，代码标识符、文件路径、协议字段名除外。
4. 一个 Markdown 文档只表达一个产品主题。
5. 输出文件名必须使用输入字段 `productNameZh` 的值，例如 `智能桌面种植机.md`。
6. 本模块的文件命名规则以中文产品名称为准，覆盖通用 Markdown 规范中的英文文件名建议。
7. 正文只允许使用标题、段落、代码块、无序列表、有序列表、嵌套列表、表格、链接引用定义、引用、Frontmatter、任务列表等规范支持的 Markdown 块。
8. 标题、段落、列表、代码块、表格、引用之间必须使用一个空行分隔。
9. 一级标题用于文档主标题，每个文档建议只出现一次。
10. 表格必须包含表头行和分隔行，每一行的列数必须与表头保持一致。
11. 列表项内容应保持为单行文本，不在列表项内部嵌套代码块、引用、表格或段落。

### 响应校验规则

1. Markdown 文档必须能够被 `app/tools/json_to_md/json_to_md.py` 支持的块级结构稳定解析。
2. Markdown 文档主标题应优先使用输入中的 `productNameZh`。
3. 文档中的商品编码、产品名称、目标国家、类目、价格、SKU 信息应与输入保持一致。
4. 输入中不存在的数据不应在输出文档中虚构。
5. 输出文档中如需保留无法确认的信息，应使用 `待确认`。
6. 输出文件名必须为 `{productNameZh}.md`。
7. 产品信息 Markdown 文件创建成功后，必须向 `product_info_document` 写入或更新记录。
8. 数据库记录中的 `product_code`、`product_name_zh`、`info_file_name`、`info_file_path`、`product_created_at` 必须与本次创建结果保持一致。

## 产品报告输入规范

### 输入根对象

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `productCode` | `str` | 是 | 无 | 商品编码，用于定位需要生成产品报告的产品。 |

### 输入校验规则

1. 根对象必须是 JSON object，不允许使用数组作为根节点。
2. `productCode` 必须是非空字符串。
3. `productCode` 必须能匹配到已存在的产品信息。
4. 无法通过 `productCode` 解析中文产品名称时，不生成产品报告文档。

### 输入示例

```json
{
  "productCode": "SYY-001"
}
```

## 产品报告响应规范

### 响应类型

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `markdown` | `str` | 是 | 无 | 符合 `app/standard/knowledge-md-format-standard.md` 的产品报告 Markdown 文档内容。 |
| `fileName` | `str` | 是 | 无 | Markdown 文档文件名，格式为 `{中文产品名称}-信息报告-{序号}.md`。 |

### Markdown 响应规则

1. 输出文件必须是 `.md` 文件。
2. Markdown 内容必须符合 `app/standard/knowledge-md-format-standard.md`。
3. 文档内容必须使用简体中文，代码标识符、文件路径、协议字段名除外。
4. 一个 Markdown 文档只表达一个产品报告主题。
5. 输出文件名必须使用通过 `productCode` 解析得到的中文产品名称。
6. 输出文件名格式必须为 `{中文产品名称}-信息报告-{序号}.md`，例如 `智能桌面种植机-信息报告-1.md`。
7. `序号` 使用正整数；同一产品已有报告时，取 `product_report_document` 中当前最大 `report_no` 加 1；没有已有报告时使用 `1`。
8. 本模块的文件命名规则以中文产品名称和报告序号为准，覆盖通用 Markdown 规范中的英文文件名建议。
9. 正文只允许使用标题、段落、代码块、无序列表、有序列表、嵌套列表、表格、链接引用定义、引用、Frontmatter、任务列表等规范支持的 Markdown 块。
10. 标题、段落、列表、代码块、表格、引用之间必须使用一个空行分隔。
11. 一级标题用于文档主标题，每个文档建议只出现一次。
12. 表格必须包含表头行和分隔行，每一行的列数必须与表头保持一致。
13. 列表项内容应保持为单行文本，不在列表项内部嵌套代码块、引用、表格或段落。

### 响应校验规则

1. Markdown 文档必须能够被 `app/tools/json_to_md/json_to_md.py` 支持的块级结构稳定解析。
2. Markdown 文档主标题应包含中文产品名称和报告类型。
3. 文档中的商品编码必须与输入 `productCode` 保持一致。
4. 文档中的中文产品名称必须与 `productCode` 对应产品信息保持一致。
5. 输入或产品信息中不存在的数据不应在输出文档中虚构。
6. 输出文档中如需保留无法确认的信息，应使用 `待确认`。
7. 输出文件名必须为 `{中文产品名称}-信息报告-{序号}.md`。
8. 产品报告 Markdown 文件创建成功后，必须向 `product_report_document` 写入记录。
9. 数据库记录中的 `product_code`、`report_no`、`report_file_name`、`report_file_path` 必须与本次创建结果保持一致。
