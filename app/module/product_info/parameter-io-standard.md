# 产品信息模块参数输入输出规范

## 适用范围

本文档用于定义 `app/module/product_info` 模块统一的参数输入与输出格式。

本文档只描述数据结构、字段类型、必填规则和填写约束，不描述具体功能能力、业务流程或代码实现。

## 基本约定

- 输入使用 JSON object 作为根节点。
- 输出为 Markdown 文档，必须符合 `app/standard/knowledge-md-format-standard.md`。
- 字段名使用英文驼峰命名，并与本规范保持一致。
- 说明性文本必须使用简体中文。
- 可选数组字段没有数据时使用空数组 `[]`，不使用 `null`。
- 可选字符串字段没有数据时使用空字符串 `""`，不使用 `null`。
- 时间字段统一使用 `yyyy-MM-dd HH:mm:ss` 格式。
- 价格字段统一使用字符串，避免金额精度丢失。
- 价格字符串不包含货币符号、千分位分隔符或单位。

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

## 产品信息文档输出规范

### 输出类型

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `markdown` | `str` | 是 | 无 | 符合 `app/standard/knowledge-md-format-standard.md` 的 Markdown 文档内容。 |
| `fileName` | `str` | 是 | 无 | Markdown 文档文件名，必须使用输入字段 `productNameZh` 的值，并以 `.md` 结尾。 |

### Markdown 输出规则

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

### 输出校验规则

1. Markdown 文档必须能够被 `app/tools/json_to_md/json_to_md.py` 支持的块级结构稳定解析。
2. Markdown 文档主标题应优先使用输入中的 `productNameZh`。
3. 文档中的商品编码、产品名称、目标国家、类目、价格、SKU 信息应与输入保持一致。
4. 输入中不存在的数据不应在输出文档中虚构。
5. 输出文档中如需保留无法确认的信息，应使用 `待确认`。
6. 输出文件名必须为 `{productNameZh}.md`。

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

## 产品报告输出规范

### 输出类型

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `markdown` | `str` | 是 | 无 | 符合 `app/standard/knowledge-md-format-standard.md` 的产品报告 Markdown 文档内容。 |
| `fileName` | `str` | 是 | 无 | Markdown 文档文件名，格式为 `{中文产品名称}-信息报告-{序号}.md`。 |

### Markdown 输出规则

1. 输出文件必须是 `.md` 文件。
2. Markdown 内容必须符合 `app/standard/knowledge-md-format-standard.md`。
3. 文档内容必须使用简体中文，代码标识符、文件路径、协议字段名除外。
4. 一个 Markdown 文档只表达一个产品报告主题。
5. 输出文件名必须使用通过 `productCode` 解析得到的中文产品名称。
6. 输出文件名格式必须为 `{中文产品名称}-信息报告-{序号}.md`，例如 `智能桌面种植机-信息报告-1.md`。
7. `序号` 使用正整数；同一中文产品名称已有报告时，取当前最大序号加 1；没有已有报告时使用 `1`。
8. 本模块的文件命名规则以中文产品名称和报告序号为准，覆盖通用 Markdown 规范中的英文文件名建议。
9. 正文只允许使用标题、段落、代码块、无序列表、有序列表、嵌套列表、表格、链接引用定义、引用、Frontmatter、任务列表等规范支持的 Markdown 块。
10. 标题、段落、列表、代码块、表格、引用之间必须使用一个空行分隔。
11. 一级标题用于文档主标题，每个文档建议只出现一次。
12. 表格必须包含表头行和分隔行，每一行的列数必须与表头保持一致。
13. 列表项内容应保持为单行文本，不在列表项内部嵌套代码块、引用、表格或段落。

### 输出校验规则

1. Markdown 文档必须能够被 `app/tools/json_to_md/json_to_md.py` 支持的块级结构稳定解析。
2. Markdown 文档主标题应包含中文产品名称和报告类型。
3. 文档中的商品编码必须与输入 `productCode` 保持一致。
4. 文档中的中文产品名称必须与 `productCode` 对应产品信息保持一致。
5. 输入或产品信息中不存在的数据不应在输出文档中虚构。
6. 输出文档中如需保留无法确认的信息，应使用 `待确认`。
7. 输出文件名必须为 `{中文产品名称}-信息报告-{序号}.md`。
