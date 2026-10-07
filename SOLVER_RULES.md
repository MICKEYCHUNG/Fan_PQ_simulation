# SOLVER_RULES.md:求解器、平行運算與 P_set 掃描流程(階段 5~6 專用)

本文件自足,只含規則與流程,不含任何計算結果。核心數、P_set 數值、路徑寫在 `config.local.yaml`(不上傳)。
定案日期:2026-10-06。

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

## 3. Warm-up 與結果堆疊(P_set 掃描)

**概念:** 每個 P_set 點都從零開始算會很慢,且高背壓點從靜止流場起算容易發散。改為「先算最好收斂的點,再用前一點的收斂流場當下一點的初始值」。

| 順序 | 內容 | 說明 |
|---|---|---|
| 1. Warm-up | P_set = 0(無背壓,自由送風點),從靜止流場起算至完全收斂 | 無背壓時流動最順、最容易收斂,用來建立完整的風扇流場 |
| 2. 堆疊 | 下一點 P_set₂ 以 P_set = 0 的收斂流場為初始值 | 流場只需小幅調整,疊代次數大幅減少 |
| 3. 遞推 | P_set₃ 用 P_set₂ 的結果,依此類推,壓力由低往高 | 每次只改出口壓力值,其他設定不變 |
| 4. 失速區 | P_set 不收斂時,依 `BC_RULES.md` 5.1 改用固定流量法,同樣以最後一個收斂點的流場為初始值 | — |

### 3.1 每點的操作步驟

| 步驟 | 動作 |
|---|---|
| 1 | 前一點收斂後,`reconstructPar -latestTime` |
| 2 | 建立新案例資料夾(每個 P_set 一個資料夾,保留每點結果可回查) |
| 3 | 把前一點最後時間步的場檔(U、p、k、omega、nut)複製到新案例的 `0/` |
| 4 | 用 `foamDictionary` 只修改 `0/p` 的 outlet 值為新的 P_set/ρ |
| 5 | `decomposePar` → `mpiexec -n N simpleFoam -parallel` |
| 6 | 依 `BC_RULES.md` 第 6 節判斷收斂,收斂才進下一點 |

### 3.2 P_set 步長

| 區段 | 規則 |
|---|---|
| 一般區段 | 依實驗 P-Q 數據的壓力點設定(`config.local.yaml`) |
| 接近失速 | 步長減半;連續 2 點收斂困難即觸發 `BC_RULES.md` 5.1 |
| 收斂監控 | 每點的 Q、入口壓力、殘差歷史只在對話內回報,不寫入 repo |

## 4. 確認紀錄

| # | 問題 | 定案 |
|---|---|---|
| 1 | 總核心數取實體核心或邏輯核心 | ✅ 實體核心(10/06) |
| 2 | 電腦是否已有 MS-MPI | ✅ 已確認可用(10/06) |
