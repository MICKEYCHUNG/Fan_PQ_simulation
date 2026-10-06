# BC_RULES.md:邊界條件與 MRF 設定規則(階段 4 專用)

本文件自足,照表格逐項設定即可。只含規則與設定邏輯,不含任何實驗數據、幾何檔或計算結果。
定案日期:2026-10-06(取代 TASKS.md 4.2 的 k-epsilon / 固定流量設定)。

## 0. 與先前設定的差異(10/06 修訂)

| 項目 | 舊設定(TASKS.md 4.2) | 新設定(本文件) | 原因 |
|---|---|---|---|
| 湍流模型 | standard k-epsilon | **k-ω SST** | 對葉片表面逆壓梯度、分離流的預測較好 |
| 驅動方式 | 給流量 Q,算壓力 | **給壓力 P_set,算流量 Q** | 使用者決定 |
| 出口段側面 | 固定壁面(noSlip) | **free(壓力開放邊界)** | 使用者決定 |
| 進出風方向 | Fluid3 = inlet、Fluid1 = outlet | **不變** | 沿用 TASKS.md 4.3 經驗驗證結論 |

## 1. 流程中的位置

| 階段 | 內容 |
|---|---|
| 1~3 | 幾何、計算域、網格(已完成) |
| **4** | **邊界條件與 MRF 設定(本文件)** |
| 5 | 數值設定(求解器參數、離散格式、收斂監控) |
| 6 | 掃描 P_set,逐點計算 |
| 7 | 後處理:Q、靜壓、與實驗比對 |

## 2. 邊界分區

計算域方向沿用 TASKS.md 4.3:大管徑端為進口、小管徑端為出口。

| 區域 | 對應網格分區 | 端面 | 側面(圓柱面) |
|---|---|---|---|
| 進口圓柱 | Fluid3 + Fluid2(5D 管徑) | **inlet** | **wall** |
| 中段(對齊 ring 外徑) | — | — | wall(不變) |
| 出口圓柱 | Fluid1(3D 管徑) | **free** | **free** |

**實作注意:** 目前 Fluid1 與 Fluid2 的側面可能同屬 `ductEnvelope` 一個 patch。出口圓柱側面要改成 free,需先在本機把該 patch 拆開(例如用 `topoSet` + `createPatch` 依軸向座標切分),Fluid2 側面維持 wall、Fluid1 側面改為 outlet 群組。拆分後要重跑 `checkMesh` 確認 patch 名稱與面數。

## 3. 各場量設定

### 3.1 U(速度)與 p(壓力)

simpleFoam 的 p 是 kinematic 壓力 p/ρ(m²/s²),P_set 以 Pa 給定時要先除以 ρ(1.2 kg/m³)。

| 邊界 | U | p | 理由 |
|---|---|---|---|
| inlet(進口端面) | `pressureInletVelocity` | `totalPressure`,p0 = 0 | 給壓力,速度由壓差決定 |
| 進口圓柱側面 / 中段 / ring | `noSlip` | `zeroGradient` | 靜止壁面 |
| outlet(出口端面 + 側面) | `inletOutlet`,inletValue = (0 0 0) | `fixedValue`,值 = P_set / ρ | 允許局部回流而不發散 |
| 葉片 `fanSurface` | `rotatingWallVelocity`(沿用現有)或 `noSlip` | `zeroGradient` | 位於 MRF 區內,兩者等效 |

**靜壓定義:** 入口總壓 0、出口靜壓 P_set,等同標準「風扇靜壓 = 出口靜壓 − 入口總壓」,可直接與實驗比對(前提:實驗的壓力定義也是靜壓,見 `config.local.yaml` 的 `pressure_definition`)。

### 3.2 k、ω、nut(k-ω SST)

| 邊界 | k | omega | nut |
|---|---|---|---|
| inlet | `turbulentIntensityKineticEnergyInlet`,強度 0.05(待確認) | `turbulentMixingLengthFrequencyInlet`,長度 ≈ 0.07 × 進口管徑 | `calculated` |
| outlet | `inletOutlet` | `inletOutlet` | `calculated` |
| 所有壁面 | `kqRWallFunction` | `omegaWallFunction` | `nutkWallFunction` |

入口用「強度 + 長度尺度」而非固定數值,因為入口速度是計算結果,這兩種邊界條件會隨流量自動調整。

**改模型連帶要改的檔案(實作時):**
- 刪除 `0/epsilon`,新增 `0/omega`
- `constant/momentumTransport`(或 v2106 的 `turbulenceProperties`):`RASModel kOmegaSST;`
- `system/fvSchemes`:新增 `div(phi,omega)`
- `system/fvSolution`:solver 與 relaxationFactors 加入 `omega`(把原本的 `epsilon` 換成 `omega`)

## 4. MRF(`constant/MRFProperties`)

| 參數 | 設定 | 說明 |
|---|---|---|
| cellZone | `rotatingZone` | 沿用階段 3 已建立的區域 |
| origin / axis | 風扇轉軸中心線(+Y 軸) | 沿用 TASKS.md 4.1 |
| omega | 1400 RPM = 146.607657 rad/s | 正負號沿用 TASKS.md 4.1(+Y 右手定則正轉) |
| nonRotatingPatches | MRF 區內若有靜止壁面則列入 | 避免靜止零件被當成轉動 |

## 5. P_set 掃描邏輯

| 項目 | 規則 |
|---|---|
| 掃描順序 | P_set = 0(自由送風點)起,逐點加大到接近最大靜壓 |
| 每點 | 獨立一次穩態計算;可用前一點的收斂結果當初始場加速收斂 |
| 流量輸出 | 在 inlet 用 function object(`surfaceFieldValue`,operation `sum`,field `phi`)取得 Q |
| 失速區 | 低流量區 P-Q 可能不單調,給壓力法可能不收斂 → 先縮小 P_set 步長;仍不收斂則**改用固定流量法驗證**(見第 5.1 節,10/06 定案) |
| 實際 P_set 數值 | 寫在 `config.local.yaml`,不上傳 |

### 5.1 失速區備案:改用固定流量法(10/06 定案)

**觸發條件(何謂「無法收斂」):** 某個 P_set 點在疊代上限內,未達第 6 節任一收斂標準,或 Q 持續週期性震盪不衰減。疊代上限預設 3000 次(待確認,實際數值寫在 `config.local.yaml`)。

| 邊界 | U | p |
|---|---|---|
| inlet | `flowRateInletVelocity`,`volumetricFlowRate` = Q_set | `zeroGradient` |
| outlet(端面 + 側面) | `inletOutlet` | `fixedValue` 0 |
| 其他壁面、k、omega、MRF | 與第 3、4 節相同 | 與第 3、4 節相同 |

| 項目 | 規則 |
|---|---|
| Q_set 怎麼選 | 取最後一個收斂的 P_set 點流量,往低流量方向逐點遞減 |
| 輸出的壓力 | 風扇靜壓 = 出口靜壓(0)− 入口面積平均總壓(p + ½\|U\|²),與第 3.1 節定義一致,兩種方法的點可畫在同一條 P-Q 曲線上 |
| 驗證 | 失速區前後至少重疊 1 個點(兩種方法都算),兩者靜壓差 < 1%,證明兩種方法的定義一致 |

## 6. 收斂判斷

| 指標 | 標準 |
|---|---|
| 殘差 | 達 `fvSolution` 設定門檻(1e-4) |
| 流量 Q | 最後一段疊代波動 < 0.5% |
| 入口 / 出口壓力 | 最後一段疊代波動 < 0.5% |

只看殘差不夠,三者都達標才算收斂。

## 7. 確認紀錄

| # | 問題 | 狀態 |
|---|---|---|
| 1 | 葉片近壁處理 | ✅ 10/06 定案:開啟葉片邊界層 5 層(見 `MESH_RULES.md` 第 4 節),壁面函數維持 `omegaWallFunction` / `nutkWallFunction`;收斂後檢查 y+ |
| 2 | 入口湍流強度 5% 是否接受 | ⏳ 待確認 |
| 3 | 失速區備案 | ✅ 10/06 定案:無法收斂時改用固定流量法驗證(見第 5.1 節) |
| 4 | 失速判定的疊代上限(預設 3000) | ⏳ 待確認 |
