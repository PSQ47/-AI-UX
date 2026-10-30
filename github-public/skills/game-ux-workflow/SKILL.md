---
name: game-ux-workflow
description: "游戏交互设计 AI 工作流的总编排 skill。统一接收策划文档输入，按序调度各执行 skill 与子 Agent，管理人机反馈回收，跑通『策划文档 → 交互分析 → Figma 设计稿 + 交互文档 → 设计师反馈 → 收尾出图标需求 → 终审』全链路。When the user drops a 策划文档 (.xlsx/.md) and wants the full game UX design workflow. Trigger phrases: '激活工作流', '跑游戏交互工作流', 'game-ux-workflow', '开始做交互设计', '从策划文档做设计稿'."
---

# game-ux-workflow（总编排）

## 角色

全流程的**总编排器**。本身不干具体活，只负责：识别输入 → 按序触发下游 skill → 在人机交接点暂停/恢复 → 保证上下文与产物一致。

重活分派给子 Agent（第 4/5 步），保护主 Agent 上下文。

## 触发

输入一份**策划文档**（`.xlsx` 或已转好的 `.md`），本 skill 被激活，开始按流程干活。

## 前期准备（每次开工前的环境连接）

需操作 Figma 时（4b/5/7 步），先确保链路三段全通：
`AI(MCP) → tunnel(3055) → Vibma插件 → Figma`

> 使用前需自行安装并配置 Vibma 插件和 MCP 服务，确认有权限访问目标 Figma 文件。具体安装方式以所用版本的官方说明为准。

| 步 | 谁做 | 操作 |
|---|---|---|
| 1. 启动 tunnel | AI 可代跑 | 终端 `npx -y @ufira/vibma-tunnel`，见 `running on ...:3055`，**勿关此终端** |
| 2. 打开插件并连接 | 🟡 **你手动** | Figma 桌面版 → 运行 Vibma 插件 → Port `3055` / Channel `vibma` → 点 **Connect** |
| 3. MCP 接入 | AI | `connection(method:"create", channel:"vibma")` → `connection(method:"get")` 收到 `pong` |

**报错对照：**
- `Relay not reachable on port 3055` → tunnel 没跑 → 做步骤 1
- `Waiting for MCP connection…` → 插件已连 tunnel，但 MCP 未 join → 做步骤 3
- `connection get` 超时(5s) → 插件没运行 / 端口或 channel 不一致 → 回步骤 2

## 流程编排

```
[输入] 策划文档.xlsx
   │
1. game-ux-workflow  激活工作流（本 skill）
   │
2. xlsx-to-markdown  策划文档 → 交互分析可用的 .md        [主]
   │   ↳ 先 python xlsx2md.py <file> --detect 判类型
   │   ↳ document/mixed 才转；data 型走 xlsx skill
   │
3. 按《游戏交互需求分析》方法将 .md 转为交互分析.md [主]
   │        （参见 `../../方法/游戏交互需求分析.md`；不是可自动调用的独立 Skill）
   │
4a. game-ux-wireframe  低保真 ASCII 草图（快/省token）  [主]
   │   ↳ 只表达布局+控件位置+状态，不碰 Figma、不建 token
   │
🔶【人工核对门】用户核对草图 → 反馈改哪里/选哪方案 → 便宜迭代
   │   ↳ 方案未确认，不得进入 4b
   │
   ├─ → 已确认草图 + 交互分析.md，派子 Agent 分派 ─┐
   │                                              │
4b. game-ux-designer      5. game-ux-doc-builder
   团队库组件组装高保真 [子]    Figma 交互文档初稿  [子]
   （用现成控件，不自画;         （绿色 AI沟通控件=待回复）
    库无→红色待接手）           │
   │                            │
   └──────── 设计稿 + 交互文档 ──┘
   │
6. 设计师接手和反馈  [人]
   ↳ 审核文档、回复 AI沟通控件 reply 字段、设计红色定制控件
   │
7. game-ux-icon-requirement  接收反馈并收尾  [主+子]
   ↳ 扫 reply 回收反馈 → 同步改稿/文档 → 输出图标需求表
   │
8. 设计师最终审核  [人]
   ↳ 无误即完成
```

## 编排规则

### 顺序与门控
- 2→3 串行：转换产物是分析输入
- 3→4a：分析后**先出低保真草图**，不直接高保真
- 🔶 **4a 后人工核对门**：用户确认草图方案前，禁止进入 4b（省 token、防返工）
- 4b、5 可在草图确认后并行准备；文档引用实际设计稿控件名之前，需等待设计稿对应部分完成。
- 6、8 是**人类门控点**：到此暂停，等设计师完成后由用户/信号恢复
- 7 依赖 6 完成（有 reply 才回收）

### 子 skill 清单

| 步 | skill | 角色 | 职责 |
|---|---|---|---|
| 1 | `game-ux-workflow` | 🔵主编排 | 调度全局（本 skill） |
| 2 | `xlsx-to-markdown` | 🔵主 | xlsx→md |
| 3 | 游戏交互需求分析方法 | 🔵主 | 交互分析（方法文档，非独立 Skill） |
| 4a | `game-ux-wireframe` | 🔵主 | 低保真 ASCII 草图（省token，供人工核对） |
| — | 🔶 人工核对门 | 🟡人 | 确认草图方案 / 反馈修改 |
| 4b | `game-ux-designer` | 🟣子 | **团队库组件组装**高保真（不自画） |
| 5 | `game-ux-doc-builder` | 🟣子 | Figma 交互文档 |
| 6 | —（设计师） | 🟡人 | 接手反馈 |
| 7 | `game-ux-icon-requirement` | 🔵主 | 收尾+图标需求 |
| 8 | —（设计师） | 🟡人 | 终审 |

### 前置检查
- 第 2 步前：确认本机 Python + openpyxl 可用（`xlsx-to-markdown`）
- 第 4b/5 步前：确认 Vibma MCP 已连（`connection(method:"get")` 收到 `pong`）
- 第 4b 前：确认**团队库可用**（`library(method:"list")` 能列组件；或打开库文件用 `components(method:"list")`）。不通则停下问用户，勿自画。

### 交接信号约定（全流程统一）
- 🔴 **红色描边** = AI 画不了的定制控件，待设计师接手（第 4 步埋，第 6 步接）
- 🟢 **AI沟通控件** = 待设计师回复的决策点（第 5 步埋，第 7 步回收）

## 设计理念

- **草图先行、低保真门控**：先出 ASCII 草图给人核对，方案定了再投入高保真，省 token、防推倒重来
- **库优先、不自画**：4b 一律用团队库现成控件组装，保持与游戏设计系统一致；库无才 🔴 标红交设计师
- **项目知识外置**：按需提供项目规则、模板与脚本；本公开目录不包含 `控件决策规则.md`、`figma-mcp-best-practices.md` 或 `icon_requirement_gen.py`，使用前须自行准备。
- **子 Agent 干重活**：画稿/写文档放子 Agent，省主 Agent 上下文
- **人只做关键决策**：AI沟通控件把需拍板处收敛，人回复即可，不逐句改
- **自迭代**：每轮把通用经验沉淀进 `learned-rules.md`

## 恢复

到人类门控点（第 6/8 步）后，用户示意"反馈已完成/审核通过"时，从对应下一步继续编排。
