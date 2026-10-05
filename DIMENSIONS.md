# DIMENSIONS.md:模擬尺寸設定

本檔集中定義**所有與模擬尺寸有關的符號、公式、規則與檢查條件**。流程檔(`TASKS.md`)與 `CLAUDE.md` 只引用本檔,不重複尺寸內容。

## 0. 使用規則

| 規則 | 說明 |
|---|---|
| 只放定義,不放數值 | 本檔是公開 repo 的一部分,只寫符號、公式、規則。真實尺寸一律寫在 `config.local.yaml`(不上傳) |
| 設定檔範本 | `config.example.yaml` 的 `geometry`、`domain`、`mrf_zone`、`mesh` 區塊對應本檔各節,範本內為假值 |
| 數值回報 | 量到的數值、算出的 R_mrf 等結果只在對話內回報,不寫進 repo |
| 修改尺寸規則 | 修改本檔的任何公式或規則,視為流程變更,需在對應 Gate 取得使用者同意 |
| 單位 | 幾何與 config 一律 mm;OpenFOAM 內部為 m(見第 7 節) |

## 1. 符號與量測方式

| 符號 | 名稱 | 量測方式(在本機用 PyVista 讀 STL,數值只在對話內回報) | config 對應鍵 |
|---|---|---|---|
| 旋轉軸 | 風扇旋轉軸方向與通過點 | 由幾何對稱性判定;確認軸是 x、y 或 z,以及軸是否通過原點 | `geometry.axis`、`geometry.axis_origin_mm` |
| R_blade | 葉尖半徑(= 葉輪外徑 / 2) | 風扇 STL 所有頂點到旋轉軸的最大距離 | `geometry.r_blade_mm` |
| R_hub | 輪轂半徑 | 風扇 STL 輪轂圓柱的半徑(輪轂簡化見 `TASKS.md` 1.7) | `geometry.r_hub_mm` |
| R_ring | wall ring 內壁半徑(= Frame 內徑 / 2) | wall ring STL 內圓柱面頂點到旋轉軸的距離;取半徑最小的那一群頂點 | `geometry.r_ring_mm` |
| z_fan_min、z_fan_max | 風扇(葉片加輪轂)軸向最小、最大座標 | 風扇 STL 沿旋轉軸方向的邊界 | `geometry.z_fan_min_mm`、`geometry.z_fan_max_mm` |
| z_ring_min、z_ring_max | wall ring 內壁軸向範圍 | wall ring STL 內壁面頂點沿軸向的邊界 | `geometry.z_ring_min_mm`、`geometry.z_ring_max_mm` |
| g | 葉尖間隙(tip gap) | g = R_ring − R_blade | 由前述算出,不另存 |
| D | 風扇外徑 | D = 2 × R_blade | `fan.outer_diameter_mm` |

軸向座標在本檔以 `min` / `max` 表示兩端,**入風側與出風側的對應要等 G5b 驗證流向後才定案**(見 `TASKS.md` 1.6)。

## 2. 幾何關係

| 方向 | 關係 |
|---|---|
| 徑向由內到外 | R_hub < 葉片範圍 < R_blade < 間隙 g < R_ring |
| 必要條件 | R_ring > R_blade(g > 0) |
| 軸向 | wall ring 內壁軸向範圍通常涵蓋或接近風扇葉片軸向範圍 |
| 靜止與旋轉 | wall ring 靜止,風扇旋轉,兩者之間只隔一圈流體間隙 |
| ring 的軸對稱性 | 內壁需為旋轉曲面(螺絲孔填補見 `TASKS.md` 1.8),旋轉區才能放在間隙中央 |

## 3. 旋轉區(MRF cellZone)定義

| 項目 | 定義 |
|---|---|
| 形狀 | 與風扇同軸的圓柱 |
| 外半徑 | R_mrf = (R_blade + R_ring) / 2 = R_blade + g / 2,即葉尖與 ring 內壁的中點(注意是**半徑**,不是直徑) |
| 軸向範圍 | 由風扇範圍兩端各加餘量:[z_fan_min − δ_a, z_fan_max + δ_b] |
| 內含零件 | 只含扇葉與輪轂;wall ring 與其他靜止件排除在外 |
| 輪轂內部 | 實心,不算流體,網格階段挖除;旋轉區圓柱涵蓋輪轂,是否含內部不影響 |

### 3.1 餘量 δ

| 情況 | 取法 |
|---|---|
| 流向已定案(G5b 之後) | 入風側 δ 約 0.05 × D,出風側 δ 約 0 至 0.02 × D(入風側略微超出風扇) |
| 流向未定案(階段 2 到 G5b 之前) | 兩端暫時都取較大的入風側餘量,G5b 確認流向後視需要再調整 |
| 性質 | 以上是工程經驗值,不是規範;於 G2b 確認,config 鍵為 `mrf_zone.delta_in_ratio`、`mrf_zone.delta_out_ratio` |

### 3.2 必須通過的三個檢查條件

| 編號 | 條件 | 不符合的後果 |
|---|---|---|
| C1 | 在旋轉區軸向範圍內,R_mrf 小於 ring 內壁的**最小**半徑(若 ring 有內凸唇緣,以最小值為準),即側面不碰實體 | 旋轉區切到靜止壁,MRF 邊界出錯 |
| C2 | 兩個端面所在平面落在流體中,不穿過 ring 或其他實體 | 旋轉區邊界與固體重疊 |
| C3 | 葉片與輪轂的軸向範圍完全落在旋轉區內 | 部分葉片沒受到旋轉效應 |

## 4. 計算域尺寸

| 項目 | 規則(初步值,依實驗設置於 G2b 調整) | config 對應鍵 |
|---|---|---|
| 進口段長度 | 約 2–3 × D | `domain.inlet_length_ratio` |
| 出口段長度 | 約 5 × D 以上 | `domain.outlet_length_ratio` |
| 出入口位置 | 必須對應實驗量測設置(風室、管路或自由出流)與壓力取點位置 | 於 G2a 確認 |
| 邊界命名 | inlet / outlet / wall / ring / fan | — |

## 5. 網格尺寸要求

| 項目 | 規則 | config 對應鍵 |
|---|---|---|
| 葉尖間隙解析度 | 間隙 g 沿徑向至少 6 層網格,旋轉區邊界兩側各約 3 層 | `mesh.gap_cells_min` |
| 旋轉區邊界 | 邊界兩側網格大小接近,避免劇烈尺寸跳變 | — |
| 邊界層 | 先用壁面函數,目標 y+ 約 30–100 | `mesh.yplus_target` |
| 網格套數 | 粗、中、細三套 | — |
| 加密比 | 線性加密比約 √2;實際規模依階段 0.1 的核心數與記憶體決定 | `mesh.refinement_ratio` |

## 6. 旋轉參數

| 項目 | 公式 |
|---|---|
| 角速度 | ω = rpm × 2π / 60(rad/s),rpm 取自 `fan.rpm` |
| 旋轉方向 | 依 `TASKS.md` 1.6 的結論,於 G4a 確認 |
| 進出風方向 | 於 G5b 以兩案試算驗證 |

## 7. 單位換算(OpenFOAM)

| 項目 | 規則 |
|---|---|
| STL 與 config | mm |
| blockMesh / snappyHexMesh | 搭配 `convertToMeters 0.001` |
| `topoSet` 的 `cylinderToCell` | 軸向兩端點座標與半徑要換成 m |
| `MRFProperties` | `origin` 以 m 表示,`omega` 以 rad/s 表示 |

## 8. 與流程的對應

| Gate | 使用本檔的哪些節 |
|---|---|
| G1.8a、G1.8b | 第 2 節(ring 軸對稱性) |
| G2a | 第 1 節(量測符號與方式)、第 4 節(出入口位置) |
| G2b | 第 3 節(旋轉區、餘量、C1–C3)、第 4 節 |
| G3a、G3b、G3c | 第 5 節、第 7 節 |
| G4a、G4b | 第 3 節、第 6 節、第 7 節 |
| G5b | 第 3.1 節(流向定案後調整餘量) |
