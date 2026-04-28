# stock-agent-lab 项目现状

## 1. 项目目标

这是一个用于练手的多 Agent 股票分析系统，当前目标是：

- 以 A 股为主
- 用 CLI 作为第一入口
- 用 LangGraph 编排多 Agent 工作流
- 输出 Markdown 和 JSON 报告
- 逐步参考 `TradingAgents-CN`，但保持轻量、自主可控和容易理解

## 2. 当前已实现能力

### 2.1 工作流

当前 graph 已经是 LangGraph 实现，并包含两类回路：

- 工具回路
  - `Technical Analyst -> tools_technical -> Technical Analyst`
  - `News Analyst -> tools_news -> News Analyst`
- 多空辩论回路
  - `Bull Researcher <-> Bear Researcher`

之后再进入：

- `Research Manager`
- `Trader`
- `Risk Manager`

### 2.2 数据获取

当前数据层以 AkShare 为核心，已实现：

- A 股历史日线行情
- 个股新闻
- 技术指标输入数据整理

并已补强：

- 东方财富请求头 patch
- 代理失败重试
- AkShare 内部双通路 fallback
  - `stock_zh_a_hist`
  - `stock_zh_a_daily`

### 2.3 LLM

当前支持：

- `MockLLMClient`
- `OpenAICompatibleClient`
- DeepSeek OpenAI-compatible 接入

已验证：

- DeepSeek 最小真实调用成功
- 完整 CLI 可用 DeepSeek 真实模型跑通

### 2.4 报告输出

当前输出：

- `report.md`
- `result.json`

支持可选开关：

- `--include-node-trace`

开启后会在 Markdown 和 JSON 中输出 graph 的执行轨迹。

## 3. 外部链路现状

### 3.1 AkShare

当前状态：**可用**

已经能在当前机器上成功抓到：

- `600519` 最近 N 天日线
- 个股新闻

但仍需注意：

- 东财接口在某些网络环境下仍可能断连
- 当前虽然有新浪 fallback，但还没有更丰富的 AkShare 内部 fallback 链

### 3.2 DeepSeek

当前状态：**可用**

使用方式：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`

已完成真实调用和完整 CLI 联调。

## 4. 与原项目相比还缺什么

当前项目相对 `TradingAgents-CN` 还缺以下关键能力：

### 4.1 分析层能力缺口

- `Fundamentals Analyst`
- `Social Analyst`
- 风险辩论回路
  - `Risky Analyst`
  - `Safe Analyst`
  - `Neutral Analyst`
  - `Risk Judge`

### 4.2 数据层能力缺口

- 基本面/财务数据
- 实时行情快照
- 股票基础信息
- 更强的新闻预处理
  - 去重
  - 时间标准化
  - 重要性筛选
  - 事件分类

### 4.3 工程层能力缺口

- 本地缓存
- 数据源来源标记
- 更细粒度日志
- 更强的失败诊断信息
- 文档持续维护机制

## 5. 当前技术债

### 5.1 编码与中文字符串

部分文件在历史迁移过程中出现过编码混乱，虽然功能已经恢复，但仍需要持续清理，避免：

- 注释难读
- 字段名误判
- PowerShell 查看文件时出现乱码困扰

### 5.2 工具回路仍是轻量实现

虽然 graph 已经有 `tools_technical` / `tools_news` 回路，但还不是原项目那种标准：

- `ToolNode`
- `tool_calls`
- LangChain message 流

### 5.3 数据层还不是平台级 Provider

现在的数据层是“为当前项目服务”的轻量 Provider，不是原项目那种可复用、多资产、多接口、多阶段 fallback 的平台级实现。

## 6. 已识别的可简化点

当前代码适合继续做的低风险 simplify 方向：

- 收拢 `data/akshare_provider.py` 的小辅助逻辑
- 保持 `pipeline.py` 只做“state -> report”转换
- 保持 `reports/writer.py` 只做格式输出，不混入业务判断
- 逐步清理历史迁移留下的重复描述和过渡性结构

## 7. 后续优化优先级

### P1

- 补 `Fundamentals Analyst`
- 补财务数据获取入口
- 给数据层增加 `data_source_meta`

### P2

- 补实时行情快照
- 增强新闻预处理
- 增加本地缓存

### P3

- 把轻量工具节点升级成真正的 `ToolNode`
- 继续向原项目靠近，补风险辩论回路

## 8. 维护约定

后续每次做以下类型改动时，都应同步更新本文件：

- graph 结构变化
- 新增或删除 Agent
- 数据源调整
- 外部工具可用性变化
- 重要技术债被消除
- 优先级发生变化
