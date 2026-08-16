# WORM-SPEC v1 —— 三虫（+应答虫）运行机制白皮书

dtag: WORM-SPEC-1 ｜ 维护：cisvr（中枢值班制）｜ 上位：META-AXIOMS.md（D3 自转律）｜ 工程形态：ci-control/.github/workflows/worm-*.yml + worms/*.py

> 本体论定位（chepin 正典）：三虫自动机 = ontological autonomous entity/agent/engines + 米田共识实现。
> 蚕→茧（自包含/自洽/自指），蜘蛛→网（耦合/嵌入/关联/统一），爬虫→穴（分形/节点/局部-整体）。

## 1. 运行机制（怎么跑）

| 班 | 周期（UTC cron） | 职责 | 数据面产出（ci-library weave/） |
|---|---|---|---|
| crawl 爬虫班 | `17 */2 * * *` | 采料：大厅/提交/织面/outbox 注册表/邮箱/指令轨 → 原料 | `crawl/raw-<ts>.md` + `latest.md` |
| weave 蚕班 | `41 */4 * * *` | 织层：四层图谱（料→谱→实体→共识） | `layers.md` |
| spider 蜘蛛班 | `11 */6 * * *` | 断边检测 → 报告 + **自动出工单**（SPIDER-WO-1） | `spider/report-<ts>.md` + `state.json` |
| audit 宪兵班 | `29 */6 * * *` | 泄密指纹/op 词表漂移/别名一致性/[CMD] 滞留 | `audit/last.md` |
| respond 应答班 | `53 */2 * * *` | 新言分级分诊 → 路由/登记/回响（RESPOND-1） | `respond/log-<ts>.md` + `state.json` |

公共件 `worms/common.py`：零凭证脚本本体，App token 由 `actions/create-github-app-token` 现场铸造（CI_APP_ID/CI_APP_KEY），班后即焚——**私钥永不落盘**。
成本：全部跑在 `ci-control`（公仓）= GitHub 免费分钟面；写面仅限 ci-library/ci-control 公开件，业务私仓只读（经指令轨）。

## 2. 实测/验证（怎么证它活着、活着对）

1. **绿运行核查**：ci-control → Actions，各 worm-* 应有周期运行且 success；产物 `weave/*/latest.md` 时间戳应新于上个周期。
2. **合成故障注入（spider 压测法）**：往 `bridge/backlog.json` 埋一件 `due=昨天` 的假件 → 下一班 spider 必报且大厅出 `thr: SPIDER-工单` → 撤假件 → 再下一班**不得重复报**（指纹去重）。BRG-01 曾用同法全绿（见 BRG-01-压测记录）。
3. **金丝雀（audit 压测法）**：在临时路径投假密钥模式串 → 下一班 audit 必报 → 清除 → 再班无报。
4. **分诊演练（respond 压测法）**：大厅留一条无 dtag 测试言 → 下一班 respond 必出 `thr: RESPOND-分诊` 且 `mailbox/cisvr.json` 出现 RESP- 工单。
5. **实战即压测**：E911（隐私卫士误私有化 ci-inbox/ci-library）= 免费的真实故障注入，修复全程已入谱。

## 3. 跟踪（怎么看它）

- **稳定契约**：每个班都有 `latest.md`（永远是最新快照），外部只需盯契约不看流水；
- **报警面**：大厅 `thr: SPIDER-工单` / `thr: RESPOND-分诊`，**仅新发现才发言**（防刷屏）；
- **系统记录**：`bridge/backlog.json` 是一切工单/截止/状态的 system of record；
- **四层视图**：`weave/layers.md` = 米田共识实体的读面。

## 4. 演化（怎么长大）

- 新虫 = 复制任一 worm 脚本骨架 + 一条 workflow + 在 worms/REGISTRY 登记一行（crawl 班会自动采到）；
- **D3 自转律**：任何手动动作做满两次，第三次必须变成机班——respond 班就是本案（人工分诊两次后制度化）；
- 版本即 commit sha，改动即审计线索（链/哈希无处不在）。

## 5. 融合/嵌入（怎么与体系一体）

虫只读写体系已有的五个面：mailbox（指令）/backlog（工单）/outbox（出件）/lobby（通报）/bridge（桥）。不造新面、不设私道——因此链/哈希绑定（iid 去重、prev 前驱、body_sha256 投影三元组）天然贯通。

## 6. 评价/改进（怎么变好）

| 指标 | 定义 | 目标 |
|---|---|---|
| MTTD | 断边发生→工单落 mailbox 的时延 | < 一个 spider 周期+调度抖动 |
| 误报率 | 新发现中被判无效的占比 | 月度 < 10% |
| 去重正确率 | 同断边不重复出工单 | 100%（指纹级） |
| 分钟耗 | 单班 Actions 分钟 | < 2 min/班 |
| 覆盖面 | 已采面 / 体系总面 | 只增不减 |

改进走 backlog，月度并入 QUOTA-91 仪式复盘。评价权：cisvr 主评，TOP5 参议，chepin 裁决重大事项。

## 7. 授权矩阵（respond 专章）

respond 虫**只分级、只路由、只登记**：写面=weave/respond/* + mailbox/cisvr.json；**执行权仍独占于 [CMD] HMAC 密封轨**。灭活开关：`bridge/RESPOND_OFF` 一落即全线静默。分级：应急→prio:fast 工单即刻回响；指令→当班会签；提案→72h 裁决；问询→24h 作答；备录→入谱。

---
*changelog: v1 2026-08-16 cisvr（应 chepin「机制/实测/跟踪/演化/融合/评价」六问）*
