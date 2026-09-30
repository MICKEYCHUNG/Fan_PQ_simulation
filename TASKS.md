# TASKS.md:分階段任務

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

### 0.5 安裝 ParaView `[ ]`
- 為什麼:用來目視檢查網格與流場,是判斷模擬是否合理的重要工具。此原生 Windows OpenFOAM 安裝包**不含** ParaView,需另外安裝。
- 到官網 paraview.org 下載 Windows 版安裝。
- 在 `D:\01_EC_Fan\Open_foam\run\pitzDaily` 資料夾建立空的 `pitzDaily.foam` 檔,用 ParaView 開啟,
  Apply 後能看到顏色分布即可。
- 完成標準:使用者能在 ParaView 看到 pitzDaily 的速度或壓力分布。

**階段 0 結束時向使用者報告:** 規格、OpenFOAM 版本號、範例是否成功、ParaView 是否可看。

---

## 後續階段(尚未展開,待階段 0 完成後逐一細化)
1. 幾何檢查與清理(STEP → STL)
2. 計算域設計(進口段、出口段、旋轉區)
3. 網格(blockMesh + snappyHexMesh)
4. MRF 與邊界條件
5. 湍流模型與求解設定
6. 單一流量點試算與收斂判斷
7. 後處理:壓差計算(注意乘以密度)
8. 多流量點掃描,畫 P-Q 曲線
9. 與實驗比對、網格獨立性驗證、參數校準
