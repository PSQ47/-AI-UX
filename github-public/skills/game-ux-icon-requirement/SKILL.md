---
name: game-ux-icon-requirement
description: "接收设计师反馈并收尾：扫描 Figma 交互文档中 AI沟通控件的回复，同步修改设计稿与文档，并整理输出图标需求表。When the designer has replied in the doc and the workflow needs to consolidate feedback + generate an icon requirement sheet. Trigger phrases: '接收反馈收尾', '生成图标需求', 'game-ux-icon-requirement', '回收设计师反馈', 'gather feedback and output icon requirements'."
---

# game-ux-icon-requirement

## When to Use

流程第 7 步。设计师完成第 6 步接手后触发。做两件事：
1. **回收反馈**：扫描交互文档里 AI沟通控件的 reply 字段，据此同步修改设计稿 + 文档
2. **出图标需求**：整理界面所需图标，输出到在线表格

由主 Agent 触发，可派子 Agent 执行文档更新。

**不要用于**：初次画稿/写文档（用 designer / doc-builder）。

## Inputs / Outputs

| | |
|---|---|
| 输入 | 设计师已回复的 Figma 交互文档 + 红色定制控件的设计产出 |
| 输出 | ① 同步更新后的设计稿与文档 ② 图标需求表（在线表格 / md） |
| 依赖工具 | Vibma MCP + `icon_requirement_gen.py`（可选） |

## Prerequisites

`connection(method:"create")` → `connection(method:"get")` 确认 Figma 已连。

## Workflow

### 1. 回收 AI沟通控件反馈
- 用 `instances(method:"list", query:"AI沟通")` 找出全部沟通控件
- 逐个 `instances(method:"get")` 读 reply 字段
- 分流：
  - reply 有明确决策 → 记为待执行修改项
  - reply 为空 → 记为仍待确认，回写清单提醒设计师
  - reply 指向定制控件 → 检查设计师是否已交付红色标记控件

### 2. 同步修改
按回收到的决策，`frames/text/components/instances(method:"update")` 更新设计稿与文档，使三者（分析/稿/文档）一致。改动较大时派子 Agent 批量执行，保护主 Agent 上下文。

### 3. 整理图标需求
遍历设计稿中的图标占位与新增控件，整理成需求条目，每条含：

| 字段 | 说明 |
|------|------|
| 图标名 | 与设计稿节点名对齐 |
| 用途/位置 | 出现的页面与控件 |
| 尺寸 | 导出规格（如 48×48） |
| 风格说明 | 线性/面性、配色、状态（默认/点亮/置灰） |
| 优先级 | P0/P1/P2 |
| 备注 | 是否复用、是否需差异化避险 |

### 4. 输出表格
- 优先输出为在线表格（POPO / 飞书 / 石墨等，按团队约定）
- 无在线表格环境则输出 `图标需求.md` 表格 + 可选跑 `icon_requirement_gen.py` 生成结构化文件
- 用 `图标需求表模板.md`（若存在）统一列顺序

### 5. 收尾自检
- 确认所有非空 reply 都已落实
- `lint` 跑设计稿，无遗留硬编码/未绑 token
- 汇总"仍待设计师确认项"，交回第 8 步终审

## Conventions

- **反馈可追溯**：每条修改标注来源的 AI沟通控件，方便复查
- **自迭代**：把本轮沉淀的通用规则写入 `learned-rules.md`，供后续复用
- **图标需求与设计稿同源**：图标名/尺寸从设计稿节点直接取，避免手抄错漏

## Handoff

交给 **设计师**（第 8 步）做最终审核；审核通过即流程完成。
