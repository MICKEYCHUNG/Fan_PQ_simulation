"""
fan_pressure.py - 範本：用 PyVista 讀 OpenFOAM 結果，算風扇靜壓

用途：壓力驅動法可以直接從 0/p 的 outlet 邊界值讀到 P_set，但固定流量法
（BC_RULES.md 5.1）的壓力是算出來的結果，不是邊界條件，需要後處理。

公式：風扇靜壓 = 出口靜壓(面積平均) - 入口總壓(面積平均)
     入口總壓 = p + 1/2 * |U|^2（動壓，kinematic）
     最後乘以空氣密度 rho 轉成 Pa

用法：
    python fan_pressure.py <case目錄> <時間步>
    python fan_pressure.py <case目錄>              # 不給時間步，用最後一個

這支程式不含任何真實幾何/實驗數值，case 目錄與時間步都由呼叫時指定。
"""
import pyvista as pv
import numpy as np
import sys
import os

RHO = 1.2  # 空氣密度 kg/m^3，見 config.example.yaml


def compute_fan_static_pressure(case_dir: str, time_value: float | None = None) -> dict:
    foam_file = os.path.join(case_dir, "case.foam")
    if not os.path.exists(foam_file):
        # pyvista 的 OpenFOAM reader 需要一個空的 .foam 檔當入口點
        open(foam_file, "w").close()

    reader = pv.POpenFOAMReader(foam_file)
    reader.cell_to_point_creation = False
    times = reader.time_values

    if time_value is None:
        time_value = times[-1]
    elif time_value not in times:
        raise ValueError(f"time {time_value} not in available times: {times}")

    reader.set_active_time_value(time_value)
    mesh = reader.read()
    patches = mesh["boundary"]

    inlet = patches["inlet"]
    p_in = inlet.cell_data["p"]
    U_in = inlet.cell_data["U"]
    area_in = inlet.compute_cell_sizes(length=False, area=True, volume=False)["Area"]
    p_total_in = p_in + 0.5 * np.sum(U_in**2, axis=1)
    avg_p_total_in = float(np.sum(p_total_in * area_in) / area_in.sum())

    outlet = patches["fluid3_outlet"]
    p_out = outlet.cell_data["p"]
    area_out = outlet.compute_cell_sizes(length=False, area=True, volume=False)["Area"]
    avg_p_static_out = float(np.sum(p_out * area_out) / area_out.sum())

    fan_static_pressure_pa = (avg_p_static_out - avg_p_total_in) * RHO

    return {
        "time": time_value,
        "inlet_area_m2": float(area_in.sum()),
        "inlet_avg_total_p_kinematic": avg_p_total_in,
        "outlet_avg_static_p_kinematic": avg_p_static_out,
        "fan_static_pressure_pa": fan_static_pressure_pa,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    case_dir = sys.argv[1]
    t = float(sys.argv[2]) if len(sys.argv) > 2 else None
    result = compute_fan_static_pressure(case_dir, t)
    for k, v in result.items():
        print(f"{k:32s}: {v}")
