﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿# TASKS.md:分階段任務

狀態標記:`[ ]` 未做、`[x]` 完成。一次只做一個階段,完成後向使用者報告並等確認。

---

## 階段 0:安裝環境(原生 Windows,不使用 WSL)

**背景變更:** 原規劃使用 WSL2 + Ubuntu,但使用者電腦受公司 IT 政策限制,虛擬化(Hyper-V/WSL2/Docker)全數禁用。
改為使用**原生 Windows 編譯版 OpenFOAM**(ESI v2106,cross-compiled with MinGW,包在 MSYS2 環境裡),
執行時完全不需要虛擬化技術,以一般 Windows 程式的方式直接執行。

### 0.1 確認電腦規格 `[x]`
- 為什麼:核心數與記憶體決定網格能做多大、要開幾個平行處理。
- 完成標準:已取得 CPU 核心數與記憶體大小(細節見對話紀錄,不寫入 repo)。

### 0.2 確認虛擬化限制,改用原生 Windows 方案 `[x]`
- 原因:WSL2 因公司 IT 政策(虛擬化/Hyper-V 被鎖)無法使用。
- 改用 blueCFD 系列的原生 Windows OpenFOAM 編譯版,不需虛擬化。
- 完成標準:已確認並改用下方 0.3 的既有安裝。

### 0.3 OpenFOAM 原生 Windows 安裝 `[x]`
- 使用者電腦已預先安裝 OpenFOAM v2106(原生 Windows 版),路徑:`D:\01_EC_Fan\Open_foam\v2106`。
- 啟動方式:在 `cmd.exe` 執行 `call D:\01_EC_Fan\Open_foam\v2106\setEnvVariables-v2106.bat` 載入環境變數,
  之後即可在同一個 cmd session 使用 `blockMesh`、`simpleFoam` 等指令,如同一般 Windows 程式。
- 完成標準:`simpleFoam -help` 能正常顯示說明文字並回報版本 `OpenFOAM-com (2106)`。✅ 已驗證。

### 0.4 用內建範例驗證安裝 `[x]`
- 為什麼:確認整條工具鏈能跑,把「安裝問題」和「之後風扇設定問題」分開。
- 案例工作目錄:`D:\01_EC_Fan\Open_foam\run`(對應原規劃的 `~/run`)。
- 複製並執行 pitzDaily 範例(OpenFOAM 內建的 simpleFoam 教學案例):
  ```
  call D:\01_EC_Fan\Open_foam\v2106\setEnvVariables-v2106.bat
  cd /d D:\01_EC_Fan\Open_foam\run\pitzDaily
  blockMesh
  simpleFoam
  ```
- 完成標準:`blockMesh` 與 `simpleFoam` 皆執行完畢並顯示 `End`,無 `FOAM FATAL ERROR`。✅ 已驗證(SIMPLE solution 已收斂)。

### 0.5 後處理方案:改用 PyVista(取代 ParaView) `[x]`
- 背景變更:公司政策規定軟體只能透過內部軟體商店(Software Center)安裝,ParaView 不在清單內,且無法自行下載安裝檔。
- 改用 **PyVista**(Python 套件,底層也是 VTK,與 ParaView 同源),透過 `pip install pyvista` 安裝,不需要另外的安裝程式或管理員權限。
- 讀取方式:在案例資料夾建立空的 `<case>.foam` 檔,用 `pyvista.POpenFOAMReader` 讀取,可離屏(off-screen)渲染輸出 PNG 截圖,或需要互動視窗時用 `plotter.show()`。
- 完成標準:成功讀取 pitzDaily 範例的網格與 U/p/k/epsilon/nut 欄位,並離屏渲染出速度場截圖,畫面與預期流場一致。✅ 已驗證。

**階段 0 結束時向使用者報告:** 規格、OpenFOAM 版本號、範例是否成功、後處理工具是否可看。

---

## 階段 1:幾何檢查與清理(STEP → STL)

### 1.1 確認 STEP 單位 `[x]`
- 從 STEP 檔頭 `SI_UNIT` 定義確認為毫米(mm)。之後所有 blockMesh/snappyHexMesh 設定須搭配 `convertToMeters 0.001`。

### 1.2 STEP → STL 轉換工具 `[x]`
- 背景:公司政策不可自行下載安裝檔,且 Software Center 無 CAD 軟體。改用 **cadquery**(內建 OpenCASCADE 幾何引擎)透過 `pip install cadquery` 安裝,不需另外的安裝程式。
- 完成標準:`import cadquery` 成功,能讀取 STEP 並輸出 STL。✅ 已驗證。

### 1.3 幾何拆解與轉檔 `[x]`
- 幾何內含 2 個獨立實體(外環 + 風扇本體),已分別匯出成獨立 STL(供後續指定不同邊界/MRF 區域使用),另有合併版供整體檢視。
- tessellation 誤差設定:linear 0.1mm / angular 8.6°(初步設定,如網格階段面品質不足會再加密)。
- 完成標準:兩個零件皆轉出 STL。✅ 已完成。

### 1.4 密封性(watertight)檢查 `[x]`
- 用 PyVista 讀取 STL,檢查開放邊(open edges)數量,0 代表沒有破面/縫隙。
- 完成標準:兩個零件 open_edges 皆為 0。✅ 已驗證。

### 1.5 視覺確認 `[x]`
- 離屏渲染兩個零件疊圖,確認形狀為「外環法蘭 + 3 片扇葉風扇本體(含軸孔)」,與預期一致。
- 完成標準:使用者確認渲染結果形狀正確。✅ 已確認。

**階段 1 結束時向使用者報告:** 單位、實體數量、密封性檢查結果、視覺確認結果。STL 檔僅存於本機 `D:\01_EC_Fan\Open_foam\run\geometry\`,未上傳。

### 1.6 旋轉方向推算(幾何分析,無實體/規格書可對照) `[x]`
- 背景:無法取得實體或規格書確認真實旋轉方向,使用者同意改用幾何推算並接受風險。
- 方法一:扇葉隨半徑的角度偏移趨勢(假設後掠扇葉)。方法二:前緣(圓鈍)/後緣(尖薄)厚度分布直接判斷。兩種獨立方法交叉驗證,結論一致。
- 完成標準:兩個獨立幾何方法結論一致。✅ 已完成(結論與假設前提記錄在對話中,不寫入 repo)。
- **進出風方向(軸向流向)未定案**:純幾何推算風險較高,決議改用後續「單一流量點快速試算」的方式做經驗驗證,而非繼續用幾何猜測。

### 1.7 Hub 簡化為實心 `[x]`
- 原因:原始幾何 hub 內部有軸孔、5 個螺絲孔與多層階梯機構細節(軸承座等),這些屬於機構安裝細節,對氣動性能無影響,但會造成網格困難,且空心軸孔若不處理會被誤判為流體可通過的通道。
- 方法:挖除 hub 半徑 80mm 以內的全部複雜細節,換成單一乾淨實心圓柱(半徑 82mm,涵蓋原 hub 軸向範圍),直接與 3 片扇葉熔接(boolean fuse)。
- 完成標準:修正後幾何 watertight(open_edges = 0),視覺確認 hub 為完整實心圓柱、扇葉連接正常。✅ 已驗證。

### 1.8 Wall ring 法蘭螺絲孔填補 `[ ]`(進行中,暫停)
- 背景:wall ring 法蘭盤上有 16 個貫穿螺絲孔(半徑 4.5mm,位於法蘭厚度區域),同樣需要填平,原因與 hub 相同(避免網格困難與不實際的洩漏通道)。
- 已知問題:用 16 次連續 boolean fuse 處理會讓 OCCT 幾何引擎卡死(曾經跑超過 4 小時沒有結果,已強制終止程序)。改用「先把 16 個填補圓柱合併成一個 compound,再跟 ring 本體做一次性 fuse」的方法,仍在測試是否能在合理時間內完成。
- **目前狀態:尚未完成,已全部停止執行,等待下一步決定替代方案**(例如:降低布林運算精度容忍度、改用網格層級工具如 PyVista/VTK 做孔洞填補而非 CAD 層級的精確布林運算、或分批處理)。
- `fan_solid_hub.stl`(風扇,已完成修正)不受影響,問題只在 `wall_ring.stl` 的螺絲孔填補。

**階段 1 目前結論:** 風扇幾何(STL 轉換、密封性驗證、旋轉方向、hub 簡化)已完成。

### 1.8 Wall ring 法蘭螺絲孔填補 `[x]`(改由來源檔案更新解決)
- 來源檔案已更新為 `Fan_with_Wallring.stp`(取代舊的 `Fan_with_ring.stp`)。新設計的 wall ring 已移除原本帶 16 個螺絲孔的法蘭盤,只保留圓筒狀段,掃描確認無任何殘留孔洞。此問題不再需要處理。
- Fan 本體尺寸在新舊檔案中完全相同(僅整體座標平移),所有幾何分析結論沿用。

### 1.9 Fan 修改標準流程(5 片葉片可行性驗證) `[x]`
- 已驗證可行:用「角度楔塊隔離單一葉片 + 繞軸旋轉複製 + 與精確尺寸 hub 熔接」的方法,把 3 片扇葉改成 5 片,符合「hub 尺寸不變、總高度與最大直徑不超過原始值、轉軸不平移」的規則。
- **標準流程(日後修改 fan 皆依此進行,不需重跑這次的驗證過程)**:
  1. 確認來源 STEP 含一個 fan + 一個 wall ring
  2. 分別存檔 fan / wall ring
  3. 需要修改 fan 時,直接修改 fan(例如改葉片數),遵守規則:轉軸不平移、hub 精確尺寸不變、總高度/最大直徑不超過原始值
  4. 修改後與 wall ring 重新組裝,輸出新的 STEP
- 已知技術限制:STL 轉三角網格在扇葉-hub 熔接的過渡帶可能殘留少量開放邊(非幾何錯誤,BRepCheck 驗證拓撲有效,STEP 為正式交付成果;STL 留待實際網格階段再處理)。

---

## 階段 2:計算域設計(圓柱坐標系)

**背景:** 風扇實際測試為 ducted(裝在管道內,進出口皆接管)。計算域由三部分組成,皆為同軸圓柱,圓心軸與 fan/ring 轉軸相同:

### 2.1 尺寸規則 `[x]`(已確認,待實作)
令 `D` = fan 最大外徑(真實離軸半徑量測,非 bounding box)。

| 區域 | 直徑 | 長度 | 說明 |
|---|---|---|---|
| Inlet(進口段) | `3D` | `2D` | 風扇上游,讓氣流穩定後再進風扇 |
| Outlet(出口段) | `5D` | `10D` | 風扇下游,讓尾流/旋流充分發展 |
| MRF 旋轉區 | 葉尖半徑 + (葉尖與 ring 內壁間隙)/2 | fan 軸長 × 1.3(前後各 +15% 餘量) | 半徑需落在葉尖與靜止 ring 內壁之間,避免把靜止壁面誤判為旋轉面;長度留餘量讓旋轉座標系流場在扇葉前後有緩衝 |

- 完成標準:三個區域尺寸公式確認,下一步用 cadquery 建立對應的圓柱幾何(本機),供使用者在 CAD 視覺確認。✅ 已完成。
- 進出口實際對應方向(哪一端接 inlet/outlet)待後續單一流量點試算經驗驗證後確定,目前先以暫定方向建立幾何,方向錯誤只需對調兩個管段位置,不需重建。

### 2.2 計算域外殼與布林運算(產生流體域) `[x]`
- 背景:inlet(3D×2D)與 outlet(5D×10D)直徑差異大,兩者之間直接相接會在風扇/ring 所在區段留下空隙。改為三段式外殼:inlet → 中段(對齊 ring 外徑,涵蓋 ring 完整軸向範圍)→ outlet,三段先 fuse 成一個連續外殼,再扣除 fan(hub 實心化)與 wall ring 兩個固體,產生流體域。
- MRF 旋轉區(參照 2.1 規則)不參與布林減除,獨立輸出作為後續 snappyHexMesh cellZone 設定用的標記幾何。
- 完成標準:布林運算後單一連通實體、BRepCheck 拓撲驗證有效、剖面視覺確認風扇/ring 區域正確扣除。✅ 已驗證。
- STL 網格殘留少量開放邊(局部過渡帶,非幾何錯誤,STEP 為正式交付成果,與階段 1 的已知技術限制同類)。

**階段 2 結論:** 流體域幾何(`fluid_domain.step`)已產生,可做為網格階段輸入。進出風方向仍待經驗驗證。

---

## 階段 3:網格(blockMesh + snappyHexMesh)

所有尺寸、分區、加密區與邊界層規則都寫在 `MESH_RULES.md`,網格階段必須照該文件執行。

### 3.1 網格規則定案 `[x]`
- `MESH_RULES.md` 第 8 節的 5 個項目已由使用者全部確認。

### 3.2 背景網格(blockMesh)與 snappyHexMesh 設定檔 `[x]`
- 依 `MESH_RULES.md` 第 1、2、5 節產生設定檔。
- **重要修正**:Fluid3(出口後段,5D~10D)要求純六面體結構網格,snappyHexMesh 無法保證此限制。改為該段**獨立建立圓柱 O-grid 結構網格**(中心方塊 + 4 片弧形外圍區塊,案例目錄 `fluid3_case`),完全不經過 snappyHexMesh。Fluid1+Fluid2+旋轉區(含風扇/ring 細節)仍用 blockMesh 背景 + snappyHexMesh(案例目錄 `fan_case`)。
- 兩個案例用 `mergeMeshes` 合併成一個 polyMesh。介面銜接原本計畫用 `stitchMesh`(把兩個 patch 縫成內部面),但 `stitchMesh` 的滑動介面演算法在「不規則 snappyHexMesh 網格」對「規則 O-grid 網格」的交界處丟出 fatal error(`Created illegal face`)。改用更穩健的標準做法:兩個交界 patch(`fluid2_outlet` / `fluid3_inlet`)設為 **`cyclicAMI`** 配對(非一致性介面,求解時用內插方式傳遞通量),不需要兩側網格拓撲完全一致。✅ 已完成,視覺確認兩個介面完全對齊同心同徑。

### 3.3 中網格試跑與 `checkMesh` `[x]`
- **Fluid3 O-grid**:`Mesh OK`,100% 六面體(22048/22048),non-orthogonality 最大 33°、skewness 最大 0.97,完全符合第 7 節標準。
- **Fluid1+Fluid2+旋轉區**(snappyHexMesh):1,334,831 cells,MRF cellZone(`rotatingZone`,用 topoSet 建立,955,877 cells)已建立。checkMesh 僅 1 項未過:skewness 最大 5.94(標準 <4),**僅 2 個面**,位置在扇葉後緣尖端(該處幾何厚度本身趨近於零,標準差僅 0.16mm,配合規則要求的 level 5 面網格已達自動網格演算法極限)。已嘗試 3 組不同的 `nCellsBetweenLevels`/snap 參數(3/6/10),結果在 4.6~5.9 間震盪未能穩定壓低,判斷非網格引擎調校可解,改善需局部修改幾何(後緣微增厚),會改變外形尺寸。使用者確認:**接受為已知例外,繼續後續流程**,不修改幾何。
- **整體合併後**(cyclicAMI 拼接):總計 1,356,879 cells,總體積 18.69 m³。checkMesh 確認 cyclicAMI 介面拓撲正確,除上述已知的 2 個 skewness 例外面外,其餘全部通過(非正交度最大 52.67°、長寬比、體積、邊界開放性皆 OK)。✅ 階段 3 中網格完成。

### 3.4 粗 / 細網格 `[x]`
- 依 `MESH_RULES.md` 第 6 節(第 2、3 節尺寸分別 ×1.3 / ÷1.3,區域位置與邊界層設定不變)建立,流程與中網格相同(blockMesh 背景 + snappyHexMesh + Fluid3 O-grid + cyclicAMI 拼接)。
- 粗網格:653,489 cells,總體積 18.66 m³,checkMesh 僅 skewness 未過(11 個例外面,同一已知原因:葉片後緣極限幾何,網格越粗此例外越明顯,符合預期)。
- 細網格:2,698,223 cells,總體積 18.71 m³,**`Mesh OK`,全部檢查通過,無任何例外**(skewness 降到 3.73,首次低於 4.0 門檻,代表網格夠細時能完整捕捉葉片後緣的薄邊幾何)。
- 三套網格體積一致(18.66~18.71 m³,誤差 <0.3%),格數依規則比例正確縮放,為網格獨立性驗證備妥。
- ✅ 階段 3(網格)全部完成。

---

## 階段 4:MRF 與邊界條件、求解設定

### 4.1 轉速與 MRF 設定 `[x]`
- 額定轉速 1400 RPM = 146.607657 rad/s。
- 這個 OpenFOAM 版本(v2106)的 `simpleFoam` **不支援把 MRF 寫在 `fvOptions`**(型別 `MRFSource` 不存在,無獨立的 `MRFSimpleFoam` 執行檔)。改用傳統的 `constant/MRFProperties` 檔案(`cellZone rotatingZone`,`origin`/`axis`/`omega`),這是 `simpleFoam` 原生支援的機制。
- 旋轉方向沿用階段 1.6 的幾何交叉驗證結論(+Y 軸右手定則正轉),與進出風方向無關,不受本階段調整影響。

### 4.2 邊界條件與湍流模型 `[x]`
- 紊流模型:standard k-epsilon + 標準壁面函數(`kqRWallFunction`/`epsilonWallFunction`/`nutkWallFunction`),邊界層目前關閉(依 `MESH_RULES.md` 第4節預設),y+ 待邊界層開啟後再檢視。
- `fanSurface` 用 `rotatingWallVelocity`(葉片隨旋轉區實際轉動);`ductEnvelope`/`ringSurface`/`fluid3_wall` 為 `noSlip` 固定壁面。

### 4.3 進出風方向經驗驗證 `[x]`
- 背景:幾何推算無法可靠判斷進出風方向(階段 1.6 已說明),改用單一流量點試算的壓力正負號經驗判斷,比純幾何猜測風險低。
- **第一次測試(2026-10-05)**:Fluid1 端(小管徑,3D)當 inlet、Fluid3 端(大管徑,5D)當 outlet。結果壓力持續下降,不符風扇做功預期,判斷進出風端設反。
- **第二次測試(2026-10-06,對調後)**:Fluid3 端(大管徑)當 inlet、Fluid1 端(小管徑)當 outlet,同流量 Q=2.822 m³/s。300 次疊代後:**風扇上游 → 下游壓力從 -37.96 升至 -7.75 m²/s²(壓差 +30.20 m²/s² = +36.24 Pa),壓力在流動方向上通過風扇時正確上升**,符合風扇做正功的預期。整體壓力沿流道因管徑收縮(動壓效應)持續下降,但風扇區段本身明確貢獻一段升壓,訊號清楚。
- **✅ 結論確認:Fluid3 端(大管徑,5D)= inlet,Fluid1 端(小管徑,3D)= outlet。** 此結果已寫入 `fan_case` 的邊界條件(`0/U`、`0/p`、`0/k`、`0/epsilon`),後續所有流量點計算沿用此方向設定。
- 完成標準:對調後重跑,風扇前後壓力呈現上升。✅ 已達成。

---

## 階段 5:單一流量點完整收斂試算(待展開)

**目前狀態:** 階段 4.3 用的兩次測試(含方向確認那次)都只跑 300 次疊代、殘差約 1e-3,**未達 `fvSolution` 設定的 1e-4 收斂門檻**,且用的是任意設定的保守測試流量(非真實實驗流量點),僅供方向判斷使用,不是正式結果。

**待辦:**
1. 取得真實實驗流量點數值(`config.local.yaml`,不上傳),取代目前的測試流量。
2. 用確認過的進出風方向(Fluid3=inlet、Fluid1=outlet)+ 真實流量點,重跑至真正收斂(殘差達 1e-4 門檻或更嚴格)。
3. 收斂後才進入後處理:壓差計算(注意乘以密度,見 `CLAUDE.md` 技術注意事項)。

## 後續階段(尚未展開)
1. 多流量點掃描,畫 P-Q 曲線
2. 與實驗比對、網格獨立性驗證、參數校準
