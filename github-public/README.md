# AI 辅助游戏 UX 设计

这里整理游戏交互设计中可复用的方法、知识库建设说明、AI Skills 和一个 Excel 转 Markdown 工具，帮助设计师从需求分析推进到草图、Figma 设计与交付。内容是工作方法与辅助工具，不是自动完成设计的成品；业务规则、视觉质量和交付结果仍需人工确认。

## 目录

```text
.
├─ README.md                    使用入口和公开边界
├─ .gitignore                   排除本地配置、密钥和临时文件
├─ 方法/
│  └─ 游戏交互需求分析.md       需求分析方法与输出模板
├─ 知识库/
│  └─ README.md                 游戏 UX 知识库建设与使用说明
└─ skills/
   ├─ game-ux-workflow/         工作流总编排
   ├─ game-ux-wireframe/        文字低保真草图
   ├─ game-ux-designer/         基于现有组件库组装设计稿
   ├─ game-ux-doc-builder/      整理 Figma 交互说明
   ├─ game-ux-icon-requirement/ 回收反馈、整理图标需求
   └─ xlsx-to-markdown/         Excel 文档检测与转换
```

## 从哪里开始

1. 阅读 [游戏 UX 知识库说明](知识库/README.md)，准备项目背景、规则和组件依据。
2. 阅读 [游戏交互需求分析方法](方法/游戏交互需求分析.md)，明确功能、流程、控件、状态和验收标准。
3. 按 [工作流说明](skills/game-ux-workflow/SKILL.md)选择需要的阶段：先分析和核对草图，再考虑 Figma 设计与交付。
4. 使用兼容 Skill 的 AI 环境时，按该环境的安装说明导入 `skills/` 下需要的目录。各 Skill 的 `SKILL.md` 是执行说明，并不是单独运行的程序。
5. 分析方法目前是一份文档，**不包含**可自动调用的 `game-ux-analyzer` Skill。

## 工作流程

1. **准备资料**：整理项目知识和策划文档；Excel 文档可先检测并转换为 Markdown。
2. **分析需求**：梳理玩家目标、操作流程、界面控件和状态边界。
3. **确认草图**：生成低保真草图，由设计师审核并确认方案。
4. **制作设计与文档**：连接 Figma，使用现有组件库组装设计稿，并整理交互说明和待确认事项。
5. **反馈与交付**：设计师回复问题，AI 协助同步修改、整理图标需求；最终由设计师检查画面和图层结构。

以上是人机协作流程，不代表全程自动化。详细步骤见 [工作流说明](skills/game-ux-workflow/SKILL.md)。

## 转换 Excel 文档

适用于以排版为主的 `.xlsx` 策划文档，不适合用作复杂公式或数据模型的计算工具。需安装 Python 和 `openpyxl`：

```bash
python -m pip install openpyxl
python skills/xlsx-to-markdown/xlsx2md.py 输入文件.xlsx --detect
python skills/xlsx-to-markdown/xlsx2md.py 输入文件.xlsx 输出文件.md
```

先检查检测结果，再核对转换后的内容、表格和图片。更多参数见 [转换工具说明](skills/xlsx-to-markdown/SKILL.md)。

## 使用 Figma 工作流

Figma 相关 Skill 需要自行准备有权限的 Figma 文件、组件库、Vibma 插件、MCP 服务和本地 tunnel。它们不包含在本目录中；安装方式及 API 以实际使用版本为准。详细连接流程见 [工作流说明](skills/game-ux-workflow/SKILL.md)。

先确认草图，再使用现有组件组装。AI 对 Figma 的修改必须由设计师检查，包括画面、图层结构与开发导出要求。流程中的部分工具能力和并行协作依赖运行环境，不保证所有环境均可自动执行。

## 发布前检查

- 本目录是从本地工作区复制整理的公开候选版本，不与原文件自动同步。
- 包含通用知识库建设说明，不包含具体项目知识库、项目需求、截图、历史产出、第三方海报 Skill、Vibma 插件源码或本地 MCP 配置。
- 发布前由内容负责人确认每个文件及示例可公开，核对来源、版权及授权；本目录暂未指定开源许可证。
- 检查提交清单、文件内容和 Git 历史，不提交令牌、账号信息、内部链接或未经授权的资料。`.gitignore` 只影响未被 Git 跟踪的文件，不能清理已提交历史，也不能替代人工检查。
