﻿﻿﻿# TASKS.md:分階段任務

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

**階段 1 目前結論:** 風扇幾何(STL 轉換、密封性驗證、旋轉方向、hub 簡化)已完成。Wall ring 的螺絲孔填補卡在 CAD 布林運算效能問題,暫停處理中。

---

## 後續階段(尚未展開,待階段 1 完成後逐一細化)
1. 計算域設計(進口段、出口段、旋轉區)
2. 網格(blockMesh + snappyHexMesh)
3. MRF 與邊界條件(含旋轉方向、進出風方向設定)
4. 湍流模型與求解設定
5. 單一流量點試算與收斂判斷(含進出風方向經驗驗證)
6. 後處理:壓差計算(注意乘以密度)
7. 多流量點掃描,畫 P-Q 曲線
8. 與實驗比對、網格獨立性驗證、參數校準
