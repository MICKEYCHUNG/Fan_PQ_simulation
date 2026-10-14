# openfoam_case_template

這是 Fan_PQ_simulation 專案實際跑過的 OpenFOAM v2106 案例設定檔範本,
依 `CLAUDE.md` 的資料安全規則,所有數值都已替換成**假值**(佔位數字),
並在每個被替換的地方加上註解說明:這個數字原本代表什麼、怎麼從真實幾何/
轉速/壓力點算出來。真實數值依規則只存在本機的 `config.local.yaml` 或
計算過程,不會出現在這個 repo 裡。

## 怎麼使用這份範本

1. 先讀 `MESH_RULES.md`、`BC_RULES.md`、`SOLVER_RULES.md`、`TASKS.md`,理解規則本身。
2. 對照這裡的檔案,看規則怎麼變成實際的 OpenFOAM dictionary 語法。
3. 每個檔案開頭的註解區塊會列出「這個檔案裡哪些數字是假的、要怎麼算出真的」。
4. 真的要跑案例時,把假值換成你自己量測/計算出來的真實值,存在本機,不要回填進這個範本。

## 檔案對應關係

| 檔案 | 對應規則 | 階段 |
|---|---|---|
| `system/blockMeshDict` | MESH_RULES.md 1 | 背景網格 |
| `system/snappyHexMeshDict` | MESH_RULES.md 1.0 / 1.1 / 2 / 2.1 / 4 / 5 | 主網格(castellate+snap+layers) |
| `system/topoSetDict` | MESH_RULES.md 1.0(端面 patch)、BC_RULES.md 4(MRF cellZone) | 切出 inlet/outlet 面、建立旋轉區 |
| `system/createPatchDict` | MESH_RULES.md 1.0 | 把 topoSet 選到的面變成正式 patch |
| `system/controlDict` | SOLVER_RULES.md 3 | 求解流程、監控函式 |
| `system/fvSchemes` / `fvSolution` | BC_RULES.md 3.2(kOmegaSST 的 wallDist 坑)、BC_RULES.md 6(收斂門檻) | 數值離散與求解器設定 |
| `system/decomposeParDict` | SOLVER_RULES.md 1 | 平行運算切分 |
| `constant/MRFProperties` | BC_RULES.md 4 | 轉速與旋轉軸 |
| `constant/turbulenceProperties` | BC_RULES.md 0 / 3.2 | k-ω SST 模型 |
| `constant/transportProperties` | — | 空氣物性 |
| `0/U` `0/p` `0/k` `0/omega` `0/nut` | BC_RULES.md 3.1 / 3.2 / 5.1 | 邊界條件(壓力驅動 + 失速區固定流量備案) |

## 學習重點(給新手的導讀)

- **為什麼要先 blockMesh 再 snappyHexMesh**:blockMesh 只產生一個粗的背景網格盒子,
  snappyHexMesh 才真的把這個盒子「雕」出風扇/管道的形狀。背景盒子邊長見 `MESH_RULES.md` 5。
- **為什麼要先 castellate+snap、再單獨做 addLayers**:在這個專案的硬體上,一次做完三件事
  (castellate+snap+addLayers)在網格數大的時候容易把記憶體吃光,分成兩次 snappyHexMesh
  呼叫(第一次只開 castellatedMesh/snap,第二次只開 addLayers)比較穩。這是本專案實際
  遇到記憶體問題後的解法,不是 OpenFOAM 官方規定,但是個實用技巧。
- **為什麼 0/ 資料夾要先搬開、網格做完才搬回來**:0/ 邊界條件檔案裡寫的 patch 名稱
  (`inlet`、`fanSurface`…)要等 snappyHexMesh/createPatch 真的建立這些 patch 之後才存在。
  網格階段的背景網格只有一個 `allBoundary` patch,这時候 decomposePar 讀到 0/ 檔案會因為
  找不到 patch 對應而報錯。解法:網格完成、patch 都確定之後,再把 0/ 放回去、decomposePar
  一次帶 `-fields`。
- **壓力驅動 vs 固定流量**:正常用壓力邊界條件(`totalPressure` 進口、`fixedValue` 出口)
  由低壓力往高壓力逐點算,每點跳動小、好收斂。但接近風扇的失速區(流量-壓力曲線斜率
  平緩甚至反轉)時,給定壓力可能對應不到唯一的流量解,殘差會震盪不收斂。這時改用
  固定流量(`flowRateInletVelocity`)由高流量往低流量算,流量是邊界條件本身不會跳動,
  反過來把壓力當「算出來的結果」讀出來。兩種方法算同一個流量點,結果要互相對得上
  (本專案驗證誤差 < 1%),才能放心把兩段曲線接在一起。見 `BC_RULES.md` 5.1。
