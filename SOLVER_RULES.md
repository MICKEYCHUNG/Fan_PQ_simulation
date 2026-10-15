# SOLVER_RULES.md:求解器、平行運算與 P-Q 掃描流程(階段 5~6 專用)

本文件自足,只含規則與流程,不含任何計算結果。核心數、流量比例、路徑寫在 `config.local.yaml`(不上傳)。
定案日期:2026-10-06。2026-10-15 修訂:第 3 節掃描流程改為「先求 Qmax,再固定流量掃描」。

## 1. 平行運算核心數

| 步驟 | 內容 |
|---|---|
| 查詢 | PowerShell:`Get-CimInstance Win32_Processor \| Select-Object NumberOfCores, NumberOfLogicalProcessors` |
| 使用核心數 N | **N = 總核心數 − 1**(保留 1 核給作業系統與 VS Code,避免電腦卡死) |
| 總核心數取哪一個 | 取實體核心(`NumberOfCores`,✅ 10/06 定案)。CFD 是記憶體頻寬密集運算,超執行緒(邏輯核心)通常沒有加速,甚至變慢 |
| 記錄 | N 寫入 `config.local.yaml`,不寫入 repo |

## 2. 平行運算流程(原生 Windows v2106)

名詞:**平行運算** = 把網格切成 N 塊(subdomain),每個核心算一塊,邊界資料透過 MPI(訊息傳遞介面)交換。

| 步驟 | 指令 / 設定 | 說明 |
|---|---|---|
| 0. 確認 MPI | `mpiexec -help` | ✅ 10/06 使用者確認 MS-MPI 可用 |
| 1. 切分設定 | `system/decomposeParDict`:`numberOfSubdomains N;`、`method scotch;` | scotch 自動切分,讓每塊格數平均、交界面最少,不需手動指定方向 |
| 2. 切分網格 | `decomposePar` | 產生 `processor0` ~ `processor(N-1)` 資料夾 |
| 3. 平行求解 | `mpiexec -n N simpleFoam -parallel > log.simpleFoam 2>&1` | `-parallel` 必加,否則 N 個程序會各自重複算整個網格 |
| 4. 合併結果 | `reconstructPar -latestTime` | 只合併最後一個時間步,節省時間與空間 |

**注意事項:**

| 項目 | 規則 |
|---|---|
| 網格介面 | 10/07 起全計算域為單一 snappyHexMesh 網格,沒有 cyclicAMI 介面(`MESH_RULES.md` 1.0),`decomposeParDict` 不需要 `preservePatches` |
| MRF | 平行運算不需額外設定,cellZone 會隨網格自動切分 |
| 驗證平行正確性 | 第一次平行運算時,與單核跑相同疊代次數的結果比對,Q 差異應 < 0.1% |
| 每格數建議 | 每核心至少約 5 萬格才有效率;中網格約 136 萬格,N 在 27 以下都在合理範圍 |

## 3. Warm-up 與結果堆疊(2026-10-15 改版:Qmax + 固定流量掃描)

**概念:** 每個點都從零開始算會很慢,且小流量點(失速區)從靜止流場起算容易發散。改為「先算最好收斂的點(Qmax),再用前一點的收斂流場當下一點的初始值,由大流量往小流量推進」。從好收斂的區域慢慢推進到失速區,比每點從零開始穩定得多。

| 順序 | 內容 | 說明 |
|---|---|---|
| 1. Warm-up(步驟 A) | P_set = 0(無背壓,自由送風點),從靜止流場起算至完全收斂,得到 Qmax | 無背壓時流動最順、最容易收斂;邊界見 `BC_RULES.md` 5.1 |
| 2. 算流量點 | Q_set = f × Qmax,f = 0.9、0.8 … 0.1、0(`BC_RULES.md` 5.2) | 比例寫在 `config.local.yaml` 的 `flow_fractions` |
| 3. 堆疊 | f = 0.9 以步驟 A 的收斂流場為初始值;f = 0.8 用 f = 0.9 的結果,依此類推,流量由大到小 | 每點只改入口流量值,其他設定不變;換成固定流量邊界時要重寫 `0/U`、`0/p` 的 inlet 型別 |
| 4. 關死點 | f = 0 用 f = 0.1 的結果為初始值,邊界改為入口封死(`BC_RULES.md` 5.4) | 最深失速,最容易不收斂 |
| 5. 不收斂 | 不收斂的點標示「未收斂」,後續點改用最後一個收斂點的流場;連續 2 點未收斂即停止並回報(`BC_RULES.md` 5.5) | — |

### 3.1 每點的操作步驟

| 步驟 | 動作 |
|---|---|
| 1 | 前一點收斂後,`reconstructPar -latestTime` |
| 2 | 建立新案例資料夾(每個流量點一個資料夾,保留每點結果可回查) |
| 3 | 把前一點最後時間步的場檔(U、p、k、omega、nut)複製到新案例的 `0/` |
| 4 | 用 `foamDictionary` 修改 `0/U` 的 inlet `volumetricFlowRate` 為新的 Q_set(m³/s);其他邊界依 `BC_RULES.md` 5.3 確認。f = 0 的點改用 5.4 節的邊界 |
| 5 | `decomposePar`(切分前先刪除 `cellLevel`、`pointLevel`、`level0Edge`,見 `TASKS.md` 5.0 已知坑)→ `mpiexec -n N simpleFoam -parallel` |
| 6 | 依 `BC_RULES.md` 第 6 節判斷收斂,取最後 N 次疊代的入口總壓平均,算出風扇靜壓(乘 ρ) |
| 7 | 結果在對話內向使用者報告;**每個流量點完成後等使用者確認再算下一點**(`CLAUDE.md` 工作方式) |

### 3.2 疊代與監控

| 項目 | 規則 |
|---|---|
| 疊代上限 | 3000 次(10/06 定案) |
| 監控量 | 入口面積平均總壓、進口與出風口流量、出口回流面積比例、殘差 |
| 平均次數 N | 寫在 `config.local.yaml` 的 `averaging_iterations`(暫定 200,首次試跑後確認) |
| 回報 | 每點的 Q、壓力、殘差歷史只在對話內回報,不寫入 repo |

## 4. 確認紀錄

| # | 問題 | 定案 |
|---|---|---|
| 1 | 總核心數取實體核心或邏輯核心 | ✅ 實體核心(10/06) |
| 2 | 電腦是否已有 MS-MPI | ✅ 已確認可用(10/06) |
| 3 | 掃描方式 | ✅ 10/15 改版:先求 Qmax,再對 Q 切 10 點固定流量由大到小計算(取代給壓力 P_set 掃描) |
