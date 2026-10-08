# BC_RULES.md:邊界條件與 MRF 設定規則(階段 4 專用)

本文件自足,照表格逐項設定即可。只含規則與設定邏輯,不含任何實驗數據、幾何檔或計算結果。
定案日期:2026-10-06(取代 TASKS.md 4.2 的 k-epsilon / 固定流量設定)。

## 0. 與先前設定的差異(10/06 修訂)

| 項目 | 舊設定(TASKS.md 4.2) | 新設定(本文件) | 原因 |
|---|---|---|---|
| 湍流模型 | standard k-epsilon | **k-ω SST** | 對葉片表面逆壓梯度、分離流的預測較好 |
| 驅動方式 | 給流量 Q,算壓力 | **給壓力 P_set,算流量 Q** | 使用者決定 |
| 出口段側面 | 固定壁面(noSlip) | ~~free~~ → **wall**(10/08) | 方向翻轉後使用者決定所有側面維持 wall |
| 進出風方向 | Fluid3 = inlet、Fluid1 = outlet | **Fluid1 = inlet、Fluid3 = outlet;MRF omega 為負**(10/08) | TASKS.md 5.4 方向判斷:第 1 層幾何三項一致 + 第 3 層計算支持;4.3 的結論作廢 |

## 1. 流程中的位置

| 階段 | 內容 |
|---|---|
| 1~3 | 幾何、計算域、網格(已完成) |
| **4** | **邊界條件與 MRF 設定(本文件)** |
| 5 | 數值設定(求解器參數、離散格式、收斂監控) |
| 6 | 掃描 P_set,逐點計算 |
| 7 | 後處理:Q、靜壓、與實驗比對 |

## 2. 邊界分區

計算域方向依 TASKS.md 5.4(10/08 定案,取代 4.3):**小管徑端(Fluid1,前緣與喇叭口所在的 −Y 側)為進口,大管徑端(Fluid3 末端)為出口**,回到原始 `MESH_RULES.md` 的設計。

| 區域 | 對應網格分區 | 端面 | 側面(圓柱面) |
|---|---|---|---|
| 進口圓柱 | Fluid1(3D 管徑) | **inlet** | **wall** |
| 管徑台階 / 安裝隔板 | — | — | wall |
| 出口圓柱 | Fluid2 + Fluid3(5D 管徑) | **outlet**(Fluid3 末端端面) | **wall** |

**實作注意:** Fluid1 側面的 patch(`outletSideFree`,名稱沿用舊稱)型別要改為 `wall`;Fluid3 末端端面 patch 名稱為 `fluid3_outlet`,Fluid1 端面為 `inlet`(名稱與角色一致)。

## 3. 各場量設定

### 3.1 U(速度)與 p(壓力)

simpleFoam 的 p 是 kinematic 壓力 p/ρ(m²/s²),P_set 以 Pa 給定時要先除以 ρ(1.2 kg/m³)。

| 邊界 | U | p | 理由 |
|---|---|---|---|
| inlet(Fluid1 端面 `inlet`) | `pressureInletVelocity` | `totalPressure`,p0 = 0 | 給壓力,速度由壓差決定 |
| 所有側面(Fluid1 側面、Fluid2/3 側面)、台階、ring | `noSlip` | `zeroGradient` | 靜止壁面 |
| 安裝隔板 `sealPlate` / `sealPlate_slave`(兩面,10/06 追加) | `noSlip` | `zeroGradient` | 封住 ring 外側旁通道,見 `MESH_RULES.md` 1.1 節 |
| outlet(Fluid3 末端端面 `fluid3_outlet`) | `inletOutlet`,inletValue = (0 0 0) | `fixedValue`,值 = P_set / ρ | 允許局部回流而不發散 |
| 葉片 `fanSurface` | `rotatingWallVelocity`(沿用現有)或 `noSlip` | `zeroGradient` | 位於 MRF 區內,兩者等效 |

**靜壓定義:** 入口總壓 0、出口靜壓 P_set,等同標準「風扇靜壓 = 出口靜壓 − 入口總壓」,可直接與實驗比對(前提:實驗的壓力定義也是靜壓,見 `config.local.yaml` 的 `pressure_definition`)。

### 3.2 k、ω、nut(k-ω SST)

| 邊界 | k | omega | nut |
|---|---|---|---|
| inlet | `turbulentIntensityKineticEnergyInlet`,強度 0.05 | `turbulentMixingLengthFrequencyInlet`,長度 ≈ 0.07 × 進口管徑(Fluid1,3D) | `calculated` |
| outlet | `inletOutlet` | `inletOutlet` | `calculated` |
| 所有壁面(含 `sealPlate` 兩面) | `kqRWallFunction` | `omegaWallFunction` | `nutkWallFunction` |

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
| omega | 1400 RPM,**−146.607657 rad/s**(10/08) | 負號 = 繞 +Y 軸右手定則反轉,依 TASKS.md 5.4 方向判斷(前緣領先方向);`fanSurface` 的 `rotatingWallVelocity` omega 必須同號。舊的正號(TASKS 1.6 / 4.1)作廢 |
| nonRotatingPatches | MRF 區內若有靜止壁面則列入 | 避免靜止零件被當成轉動 |

## 5. P_set 掃描邏輯

| 項目 | 規則 |
|---|---|
| 掃描順序 | P_set = 0(自由送風點)起,逐點加大到接近最大靜壓 |
| 每點 | 獨立一次穩態計算;可用前一點的收斂結果當初始場加速收斂 |
| 流量輸出 | **評斷用的 Q 一律取出風口**(出口 patch 的淨流出量,`phi` 加總;10/07 使用者定案)。進口流量只當參考,單一網格下兩者應相同,差異過大代表質量不守恆 |
| 失速區 | 低流量區 P-Q 可能不單調,給壓力法可能不收斂 → 先縮小 P_set 步長;仍不收斂則**改用固定流量法驗證**(見第 5.1 節,10/06 定案) |
| 實際 P_set 數值 | 寫在 `config.local.yaml`,不上傳 |

### 5.1 失速區備案:改用固定流量法(10/06 定案)

**觸發條件(何謂「無法收斂」):** 某個 P_set 點在疊代上限內,未達第 6 節任一收斂標準,或 Q 持續週期性震盪不衰減。疊代上限 3000 次(10/06 定案)。

| 邊界 | U | p |
|---|---|---|
| inlet | `flowRateInletVelocity`,`volumetricFlowRate` = Q_set | `zeroGradient` |
| outlet(Fluid3 末端端面) | `inletOutlet` | `fixedValue` 0 |
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

**物理合理性(10/06 追加):** 收斂之外,P_set 堆疊時每一點還要檢查:
- 流量 Q 隨 P_set 升高而遞減;
- 低背壓點(接近 0 Pa)的 Q 應與 P_set = 0 接近;
- 不得出現整體倒流(進口端面變成流出)。

任一項不符就停止掃描、先找原因,不要往高壓力繼續堆疊。這類異常通常是計算域或邊界問題(例如 ring 外側旁通道,見 `MESH_RULES.md` 1.1),不是收斂監控能解決的。

## 7. 確認紀錄

| # | 問題 | 狀態 |
|---|---|---|
| 1 | 葉片近壁處理 | ✅ 10/06 定案:開啟葉片邊界層 5 層(見 `MESH_RULES.md` 第 4 節),壁面函數維持 `omegaWallFunction` / `nutkWallFunction`;收斂後檢查 y+ |
| 2 | 入口湍流強度 | ✅ 10/06 定案:5% |
| 3 | 失速區備案 | ✅ 10/06 定案:無法收斂時改用固定流量法驗證(見第 5.1 節) |
| 4 | 失速判定的疊代上限 | ✅ 10/06 定案:3000 次 |
| 5 | 進出風方向與轉向 | ✅ 10/08 定案:Fluid1 進口、Fluid3 出口、omega 為負(TASKS.md 5.4 設定 B) |
| 6 | 側面邊界 | ✅ 10/08 定案:所有側面維持 wall |
