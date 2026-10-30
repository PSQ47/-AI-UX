---
name: game-ux-designer
description: "在草图方案确认后，用 Vibma MCP 调团队库(Team Library)现有控件组装高保真 Figma 设计稿，保持与游戏设计系统一致——不自己画控件。When a wireframe is approved and the user wants a high-fi Figma draft assembled from the game's existing library components. Trigger phrases: '组装设计稿', '用团队库控件出稿', 'game-ux-designer', '按草图做高保真', 'assemble figma from library'."
---

# game-ux-designer（团队库组装 · 4b）

## When to Use

流程第 **4b** 步，在 game-ux-wireframe 草图**已被用户确认后**执行。
输入已确认的草图 + `交互分析.md`，输出高保真 Figma 设计稿。

**铁律：用团队库现成控件组装，不自己画控件。** 库里没有的才 🔴 标红交设计师。

**不要**：在草图未确认前动手；用 `frames.create`/`text.create` 手搓已存在于团队库的控件。

## Inputs / Outputs

| | |
|---|---|
| 输入 | 已确认草图 `草图_<模块>.md` + `交互分析.md` |
| 输出 | Figma 高保真设计稿（团队库 instances 组装）+ 🔴定制控件标记 |
| 依赖 | Vibma MCP + **团队库访问**（`library` 工具，需 FIGMA_API_TOKEN） |

## Prerequisites

1. Vibma 已连：`connection(method:"create")` → `connection(method:"get")` 收到 `pong`
2. **团队库可用**：`library(method:"list")` 能列出发布组件
   - ⚠️ 若 `library` 工具无法激活/调用（曾遇按需检索激活不了），先解决：
     - 确认 `.mcp.json` 里 `FIGMA_API_TOKEN` + `FIGMA_TEAM_ID` 已配并重载
     - 或退路：在 Figma 直接打开团队库源文件，用 `components(method:"list")` 读本地组件
   - **团队库不通 = 无法保证一致性**，此时应停下告知用户，不要自己画替代。

## Workflow

### 1. 发现团队库组件（建立 name→key 注册表）
```
library(method:"list")            // 一次性，填充 name→key 注册表
library(method:"get", query:...)  // 取目标组件的属性/变体/用法
```
把草图控件清单里的"复用组件名"逐一对应到真实库组件名。对不上的 → 记为候选缺口。

### 2. 用 instances 组装（核心）
- 放置库组件：`instances(method:"create", items:[{componentName:"...", variantProperties:{...}, properties:{...}, parentId, ...}])`
- 布局容器用 `frames(type:"auto_layout")` 承载，但**内容控件一律用库组件 instance**
- 变体/文本通过 `variantProperties` / `properties` 设置，不 detach、不重画
- 复用库的样式/变量：`fillStyleName`/`textStyleName`/`fillVariableName` 用库里已有名，本地不再造

### 3. 按已确认草图布局
严格照草图的区块与层级组装；草图没定的不擅自加。auto-layout + FILL/HUG 保证响应式。

### 4. 极端状态出图
草图标注的空态/锁定/超长文本，各出一版——仍用库组件的对应变体/状态。

### 5. 标记真正的定制控件 🔴
仅当团队库**确实没有**对应控件（原创视觉/特效）时，才用红色描边 frame + `annotations` 标"需设计师接手：<原因>"。**能复用绝不新画。**

### 6. 自检
`lint` / `components(method:"audit")`：确认无 detach 的库组件、无手搓的重复控件、无硬编码色值。

## Conventions

- **库优先级**：团队库组件 > 本地组件 > （极少数）新建。新建只发生在 🔴 定制控件占位。
- **不 detach**：instance 保持与库链接，设计系统更新可同步。
- **命名对齐**：frame/实例名与草图、交互分析、交互文档一致，便于交叉引用。
- **缺口即停**：库里找不到关键控件时，停下问用户，别用自绘糊弄一致性。

## Handoff

交给 **game-ux-doc-builder（5）** 并行做文档；红色定制控件交 **设计师（6）**。
