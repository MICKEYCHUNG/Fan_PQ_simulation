﻿# TASKS.md:分階段任務

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

---

## 後續階段(尚未展開,待階段 1 完成後逐一細化)
1. 計算域設計(進口段、出口段、旋轉區)
2. 網格(blockMesh + snappyHexMesh)
3. MRF 與邊界條件
4. 湍流模型與求解設定
5. 單一流量點試算與收斂判斷
6. 後處理:壓差計算(注意乘以密度)
7. 多流量點掃描,畫 P-Q 曲線
8. 與實驗比對、網格獨立性驗證、參數校準
