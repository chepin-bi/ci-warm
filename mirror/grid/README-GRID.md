# GRID 展开包 —— L2 温备侧授权 + L3 闲置机器网格（实施细则 v1）

dtag: GRID-L2L3-1 ｜ 维护：cisvr ｜ 上位案：bridge/QUOTA-DECISION-01.md ｜ 公理：META-AXIOMS C1（最小权限）E2（试点先行）

---

## 第一部分 L2：chepin-bi 温备侧（一次性动作，二选一）

### 0. 「CI App」是什么

体系里唯一的**高权凭证**是一枚 GitHub App（chepin-ai 名下）：
- App ID 存在 `ci-control` 仓库变量 `CI_APP_ID`，私钥存在 Actions secret `CI_APP_KEY`；
- 运行时各工作流用 `actions/create-github-app-token` **现场铸造**短时 token（≈1h 失效），所以 poller、BRG-01 桥、三虫才能读写五个私仓；
- 凭证永不落盘、永不入日志明文（C1）。

**L2 的本质需求**：让 chepin-bi 名下的目标仓也能被一枚**最小权限**凭证读写，供温备镜像/热备心跳使用。

### 1. 前置（30 秒）：建目标仓

chepin-bi 账号登录 → 右上 `+` → New repository：
- Name：`ci-warm`　Private ✅　勾选 Add a README（空仓无法选仓授权）
- 其余默认 → Create

### 2. 路线 C（试点推荐，约 5 分钟）：最小权限 PAT

chepin-bi → 头像 → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**：

| 字段 | 填法 |
|---|---|
| Token name | `ci-warm-bi` |
| Expiration | **90 days**（到期仪式感轮换，绝不 No expiration） |
| Resource owner | **chepin-bi** |
| Repository access | **Only select repositories** → 只选 `chepin-bi/ci-warm` |
| Permissions → Repository | **Contents: Read and write**；其余全部 No access（Metadata 自动只读，不用管） |

Generate → 复制 token。**交付方式（关键）**：不要把 token 发给我/贴到任何消息里。
直接到 `chepin-ai/ci-control` → **Settings → Secrets and variables → Actions → New repository secret**：
- Name：`WARM_BI_PAT`　Value：粘贴 → Add secret
然后在大厅留一句「WARM_BI_PAT 已就位」即可，剩下全部我来（warm-sync 工作流：每日把 ci-control 内核镜像到 chepin-bi/ci-warm + 反向心跳 + 切换 runbook）。

### 3. 路线 B：chepin-bi 名下第二个 GitHub App（v2 勘误·逐步带界面锚点）

> v2 勘误（2026-08-17）：v1 有三处缺陷——①漏 Workflows 权限（暖侧推 warm-watch.yml 被 403 实测）；②「记首页的 App ID」指代不清；③「secrets 存两件」与宅内惯例（CI_APP_ID 存 Variables）不一致。以下为逐步版。

**第 1 步 · 建 App**：浏览器登录 chepin-bi → 右上头像 → **Settings** → 左侧栏最底 **Developer settings** → **GitHub Apps** → **New GitHub App**：
- Name：`ci-warm-bi`；Homepage：`https://github.com/chepin-bi/ci-warm`
- Webhook：**取消勾选 Active**
- **Repository permissions 两项**：
  - Contents: **Read and write**（镜像写入）
  - Workflows: **Read and write**（推 .github/workflows/ 文件，缺它 403）
- Where can this App be installed：**Only on this account**
→ 点 **Create GitHub App**

**第 2 步 · 取 App ID**（「首页」= 创建成功后自动进入的 App 设置页，亦可随时从头像 → Settings → Developer settings → GitHub Apps → 点 `ci-warm-bi` 回到此页）：
- 在该页**顶部 General 区块**，`About` 下方即是 **App ID**（一串数字，如 `1234567`）。复制它。

**第 3 步 · 取私钥**：同页滚到底 **Private keys** → **Generate a private key** → 浏览器自动下载 `.pem` 文件。

**第 4 步 · 安装**：左侧 **Install App** → 选 `ci-warm` 仓 → Install。

**第 5 步 · 交付到 ci-control**（在 chepin-ai/ci-control 仓操作）：
- **Settings → Secrets and variables → Actions → Variables 标签页 → New repository variable**：Name `WARM_BI_APP_ID`，Value=第 2 步的数字。
- **Secrets 标签页 → New repository secret**：Name `WARM_BI_APP_KEY`，Value=第 3 步 .pem 文件**全文**（含 `-----BEGIN RSA PRIVATE KEY-----` 头尾行）。
- （若你已把 `WARM_BI_APP_ID` 存进了 Secrets 标签页：不必搬，warm-sync 已双槽兼容（caeab3e9），两处任一处都能用；但宅例推荐 Variables，与 CI_APP_ID 同例。）

**验证**：交付后下一次 warm-sync 跑（或手动 Run workflow），ci-control/bridge/warm-status.json 的 `auth_path` 应变 `"app"`、`warm_watch` 应变 `"ok"`。我在下一班自动核验并大厅报备。

### 4. 路线 A（不推荐）：把现有 CI App 装到 chepin-bi

需要 App 可见性改成 Public（任何账户可装），扩大暴露面，违反单账户最小权限原则。**否决**，除非未来跨账户面扩大再议。

---

## 第二部分 L3：闲置机器网格（self-hosted runner）

### 0. 硬性真相（实测结论，不绕弯）

- **Windows 7 跑不了官方 runner**：actions/runner 需要 Windows 10 1607+/Server 2016+（.NET 8 运行时 + TLS1.2 套件）。三条出路：
  1. 升级 Win10/11；2. 装 Debian（LXQt 桌面）双系统或替换；3. 该机改作备份/存储节点，不入网。
- **macOS 11+ 直接支持**（x64 与 arm64 均有官方包）。
- **私仓用自托管 runner 不计 Actions 分钟** —— 这正是 EYE-001（私仓分钟耗尽）的根治路径。

### 1. 展开包（本目录四件）

| 文件 | 平台 |
|---|---|
| `enroll-macos.sh` | macOS 11+（Intel/Apple Silicon 自适应） |
| `enroll-linux.sh` | Debian/Ubuntu 系（含 Win7 机改装 Linux 后） |
| `enroll-windows.ps1` | Windows 10/11（PowerShell 管理员） |

每个脚本只需两个参数：**注册令牌** + **目标仓**（可选第三参数：标签）。

### 2. 注册令牌怎么来（两路）

- **手动（30 秒/仓）**：目标仓 → **Settings → Actions → Runners → New self-hosted runner** → 页面直接显示 token 和下载命令（token 1 小时有效，仅用于注册）。
- **我代铸**：若授权令牌对目标仓有 admin，我可走 API `POST /repos/{owner}/{repo}/actions/runners/registration-token` 自动生成，你只跑一行命令。各仓实测后在大厅通告哪几仓已开通代铸。

### 3. 一台机器入网（以 macOS 为例）

```bash
# 机器上执行（建议专用低权用户，不要 root/admin 日常账户）
curl -LO https://raw.githubusercontent.com/chepin-ai/ci-control/main/grid/enroll-macos.sh
chmod +x enroll-macos.sh
./enroll-macos.sh <注册令牌> chepin-ai/ci-control "grid,macos"
```

脚本动作：建 `~/actions-runner` → 拉最新官方 runner 包 → 校验 → `config.sh --unattended --labels` → 装成系统服务（LaunchAgent）→ 自验在线。

### 4. 标签与调度纪律

- 标签统一 `grid,<os>`（可加机型标签，如 `grid,macos,m1`）；
- 工作流沿用 qgl 双标签模式：`runs-on: ${{ vars.RUNNER_LABEL || 'ubuntu-latest' }}` —— 变量指到 grid 就跑网格，缺省回落 GitHub 免费面；
- 个人账号的 runner 只能**逐仓注册**（组织级需建 org，后续可议）；五仓每仓注册一次，脚本可循环跑；
- 安全硬规：runner 只需**出站 443**；跑在专用低权用户下；公仓工作流上网格前必须过 L4 密文镜像规矩（见 QUOTA-DECISION-01 v1.1）。

---

*changelog: v1 2026-08-16 cisvr 初版（应 chepin L2/L3 细令）*
