# TASKS.md:分階段任務

狀態標記:`[ ]` 未做、`[x]` 完成。一次只做一個階段,完成後向使用者報告並等確認。

---

## 階段 0:安裝環境

**目的:** OpenFOAM 原生是 Linux 軟體。Windows 上透過 WSL2(Windows 內建的 Linux 子系統)執行,
不需要雙系統,也不需要虛擬機。ParaView 是看結果的工具,裝在 Windows 即可。

### 0.1 確認電腦規格 `[ ]`
- 為什麼:核心數與記憶體決定網格能做多大、要開幾個平行處理。
- 在 Windows 工作管理員 → 效能,記下 CPU 核心數與記憶體(GB)。
- 完成標準:使用者回報兩個數字。

### 0.2 安裝 WSL2 與 Ubuntu `[ ]`
- 為什麼:提供 OpenFOAM 所需的 Linux 環境。
- 以「系統管理員身分」開啟 PowerShell,執行:
  ```powershell
  wsl --install -d Ubuntu-24.04
  ```
  完成後依提示重新開機,再開啟「Ubuntu」,設定 Linux 使用者名稱與密碼(密碼輸入時畫面不會顯示,這是正常的)。
- 完成標準:在 Ubuntu 視窗輸入 `lsb_release -a` 能看到 Ubuntu 版本。
- 常見問題:若顯示虛擬化未啟用,需進 BIOS 開啟 Virtualization(VT-x / SVM)。

### 0.3 確認 WSL 資源 `[ ]`
- 為什麼:確認 Linux 端看得到的核心與記憶體。
- 在 Ubuntu 輸入 `nproc`(核心數)與 `free -h`(記憶體)。
- 預設 WSL 只使用約一半記憶體。網格變大時再到 Windows 使用者資料夾建立 `.wslconfig` 調整,現階段不用動。

### 0.4 安裝 OpenFOAM `[ ]`
- 為什麼:這是求解器本體。本專案使用 ESI 版(openfoam.com)。
- 先加入官方套件庫,並查詢目前可安裝的版本名稱:
  ```bash
  curl https://dl.openfoam.com/add-debian-repo.sh | sudo bash
  sudo apt-get update
  apt-cache search openfoam | grep default
  ```
- 從查詢結果挑選最新版的 `openfoamXXXX-default` 套件安裝(XXXX 是版本號),例如:
  ```bash
  sudo apt-get install openfoamXXXX-default
  ```
- 完成標準:安裝過程沒有錯誤訊息。

### 0.5 載入 OpenFOAM 環境 `[ ]`
- 為什麼:OpenFOAM 的指令(simpleFoam 等)要先載入環境檔才找得到。
- 執行(XXXX 換成實際版本號):
  ```bash
  source /usr/lib/openfoam/openfoamXXXX/etc/bashrc
  ```
  確認可用後,把同一行加到 `~/.bashrc` 最後,之後開啟終端機就會自動載入。
- 完成標準:輸入 `simpleFoam -help` 會顯示說明文字。

### 0.6 用內建範例驗證安裝 `[ ]`
- 為什麼:確認整條工具鏈能跑,把「安裝問題」和「之後風扇設定問題」分開。
- 複製並執行 pitzDaily 範例(一個簡單的 simpleFoam 算例):
  ```bash
  mkdir -p ~/run && cd ~/run
  cp -r $FOAM_TUTORIALS/incompressible/simpleFoam/pitzDaily .
  cd pitzDaily
  blockMesh
  simpleFoam | tee log.simpleFoam
  ```
  - `blockMesh`:產生網格。
  - `simpleFoam`:求解。畫面會滾動出現殘差,最後看到 `End` 表示結束。
- 完成標準:log 最後一行出現 `End`,且沒有 `FOAM FATAL ERROR`。

### 0.7 安裝 ParaView `[ ]`
- 為什麼:用來目視檢查網格與流場,是判斷模擬是否合理的重要工具。
- 到官網 paraview.org 下載 Windows 版安裝。
- 在 pitzDaily 資料夾建立空的 `pitzDaily.foam` 檔(`touch pitzDaily.foam`),用 ParaView 開啟,
  Apply 後能看到顏色分布即可。WSL 的檔案可在 Windows 檔案總管網址列輸入 `\\wsl$` 存取。
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
