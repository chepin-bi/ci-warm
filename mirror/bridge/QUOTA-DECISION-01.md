# QUOTA-DECISION-01 · 计算面突围决策案（cisvr 主理首案）

dtag: QUOTA-DECISION-1 · 2026-08-16 · 主理：cisvr（依据 E1/E2：实测先行，重大事项上报）

## 裁决（特区/试点制，非拍脑袋）

**L1 即行（本轮已做）**：公域承接 —— 三虫+自省班+桥+poller+provision 全部跑在 ci-control/backup 公仓免费分钟。已实证（bridge 三班全绿）。

**L2 本周试点**：chepin-bi 暖备 —— **采纳 chepin 此前提案**（彼时我一口谢绝，理由记录为 App 安装面/凭证边界未厘清；现更正：谢绝不等于否决，按 E3 升 backlog 转试点）。
- 方案：精简版 CI 内核（poller+bridge 两班）镜像至 chepin-bi 私仓，吃那边未用的私域分钟；chepin-ai 侧保留热备语义（双跑互证，QUOTA-PACT L2 同构）。
- 需要 chepin 一次性动作（仅一次）：把 CI App 安装扩展到 chepin-bi 目标仓，或给我一枚 chepin-bi 侧最小权限 PAT（Contents+Actions，7 天，可撤销）。
- 杀条件：双跑 7 天内出现一次状态分叉不可调和 → 撤暖备，退回单极。

**L3 网格化（裁决通过，实施排队）**：多台闲置机组 runner 网格——
- GitHub self-hosted runner ×N（每台一条 Docker 命令，labels: grid）；qgl 已备双标签改造（runs-on: vars.RUNNER_LABEL || ubuntu-latest）——推而广之即全舰队可切。
- 风险条款：runner 机器=执行面非信任面——私仓 Secrets 不进 runner 环境（密钥只在公仓 workflows 经 App token 短暂落地内存）；机器被控最坏=任务伪造，由双跑互证+哈希链兜底。

**L4 公域加密空间（采纳但限界）**：chepin-ai 公仓可跑加密载荷 workflow（密文入、密文出、密钥在 Secrets、runner 内解密运算）。**红线**：公仓 Actions 日志公开——解密后的明文一旦进 stdout/log 即全球直播。故限界为：只承接「输入公开/过程敏感/输出可脱敏」的算力（如 LLM 批量调用的 prompt 不涉私货）；涉私域文件结构/持仓/密钥的一律不进公域解密。

**不采纳**：付费机密计算（机密 VM/SEV）——不免费，超出"免费解"约束，记 backlog 待资源变局。

## 免费线上解法清单（调研结论）
1. 公仓 Actions 无限分钟（已用）2. self-hosted runner 网格（L3）3. chepin-bi 私域余量（L2）4. Kaggle/Colab 沙箱班（usrm 已实证为 L3 外部位）5. Oracle 永久免费 ARM VM 作常驻 runner 宿主（归 L3）。


---

## v1.1 增补（2026-08-16 二班 · 应 chepin 细令）

### L2 细则落地
一次性授权操作书已出：`grid/README-GRID.md` 第一部分（路线 C 试点=chepin-bi 细粒度 PAT 直存 ci-control secret `WARM_BI_PAT`；路线 B 制度化=chepin-bi 名下第二 App）。我侧接收动作已备好：secret 就位即装 warm-sync 班。

### L3 细则落地
展开包四件已入 `ci-control/grid/`（README + macOS/Linux/Windows 三平台入网脚本）。**硬结论：Windows 7 不在官方 runner 支持面**（需 Win10+/.NET8）——Win7 机出路=升系统/装 Linux/转存储节点。macOS 11+ 一行脚本入网。私仓上网格=分钟计费归零（EYE-001 根治路径）。

### L4 精化：ENC-MIRROR 密文镜像制（采纳 chepin 令，升格为规矩）
- 公仓 Actions 明文**只放操作驱动记录**（op 名/哈希/时间戳/状态），**不涉具体内容**；
- 载荷一律 SealedBox 密文出入；明文只许活在私域；
- **镜像互译设在私域**：daemon/业务仓持有明文镜像，公域织面（ci-inbox/ci-library）只存密文+哈希投影——投影三元组（dtag+prev+body_sha256）不变，密文面亦满足全息可验。

### L5 复活：付费面准入准则（chepin 改判，收编）
付费机密 VM 从「不采纳」改为「**条件可选**」：当机密 VM 月费 < 私仓 CI 超支费时即划算。免费 VM 仍优先：Oracle Always Free（4 OCPU ARM/24GB 常驻）、GCP e2-micro 免费档。成本比较并入 QUOTA-91 月度仪式。

### COST-20260816-01 · LongCat 计费事件（录入观察账）
**规矩（即立）**：①包到期前 72h 提烧——重活前排，到期额度先用光（烧不光=浪费）；②月度 QUOTA-91 仪式加「密钥↔资源包绑定核查」查点；③用户侧动作：LongCat 控制台 API 密钥管理→确认各密钥计费方式/资源包绑定/扣费顺序。

> 账务明细属运营隐私（L2），已迁私域锚 full_sha256: 74fe62a40c104d95dcb6784bc007ece0affb913d1c245230c541c82e2e4e7f21
