---
name: game-ux-doc-builder
description: "把交互分析文档转化为可供设计师审核和反馈的 Figma 交互文档，用固定的『AI沟通控件』搭建人机沟通桥梁。When the user wants a Figma interaction/spec doc from 交互分析.md for designer review. Trigger phrases: '制作交互文档', '出交互文档初稿', 'game-ux-doc-builder', '生成figma交互说明', 'build figma interaction doc'."
---

# game-ux-doc-builder

## When to Use

流程第 5 步。输入 **交互分析.md**，输出 **Figma 交互文档初稿**——供设计师审核、反馈的规格说明页。

由子 Agent 执行，与 game-ux-designer（第 4 步）并行。

**不要用于**：画界面设计稿（用 game-ux-designer）、图标需求（用 game-ux-icon-requirement）。

## Inputs / Outputs

| | |
|---|---|
| 输入 | `交互分析.md` + game-ux-designer 产出的设计稿（引用其 frame/控件名） |
| 输出 | Figma 交互文档页（结构化说明 + AI沟通控件） |
| 依赖工具 | Vibma MCP（Figma 插件需 Connected） |

## Prerequisites

同 game-ux-designer：先 `connection(method:"create")` → `connection(method:"get")` 收到 `pong` 再开工。

## Workflow

### 1. 搭文档骨架
用 `frames` 建一页文档 frame（竖向 auto-layout），分区块：
- 概述（设计目的 / 系统设计）
- 逐控件交互说明（触发 → 反馈 → 状态流转）
- 极端状态说明
- 待确认清单

### 2. 逐控件写交互说明
按交互分析的控件树，每个控件一个说明块：
- 控件名（与设计稿 frame 名一致，可交叉引用）
- 交互行为：点击/滑动/切换 → 结果
- 状态：默认 / 空 / 锁定 / 极端
- 用 `text` 写，标题绑 text style，正文分级

### 3. 埋『AI沟通控件』🟢 —— 人机桥梁核心
凡是 AI 拿不准、需要设计师拍板的点，插入**固定格式的沟通控件**（统一样式的问答块）：

```
┌─ [AI沟通] ─────────────────────┐
│ 问题：<AI 的疑问/待确认项>       │
│ AI 建议：<默认方案>              │
│ 设计师回复：▢（留空待填）        │
└────────────────────────────────┘
```

实现：用 `components` 建一个可复用的「AI沟通控件」组件（带 TEXT 属性：question / suggestion / reply），全文档 `instances` 复用。设计师第 6 步只需在 reply 字段回复，AI 第 7 步据此扫描回收。

### 4. 待确认清单
文档末尾汇总所有 AI沟通控件的问题，做成一张 checklist，方便设计师快速过一遍。

### 5. 自检
`lint` / `components(method:"audit")` 跑一遍，确保文字绑 style、布局用 auto-layout、沟通控件命名统一。

## Conventions

- **AI沟通控件是固定资产**：统一命名（如 `AI沟通/待确认`）+ 统一结构，第 7 步靠它自动回收反馈
- **引用而非重复**：控件名与设计稿对齐，文档只写行为逻辑，不重绘界面
- **绿色 = 人机沟通**：AI沟通控件用统一的绿色标识，区别于第 4 步的红色"待接手定制控件"
- **子 Agent 边界**：只写文档，不改设计稿、不出图标需求

## Handoff

交给 **设计师**（第 6 步）：审核文档、在 AI沟通控件的 reply 字段回复、设计红色定制控件。
回收由 **game-ux-icon-requirement**（第 7 步）扫描 reply 字段完成。
