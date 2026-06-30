import numpy as np

def evaluate_T(D, T, f_list, delta_f_ratio=0.2):
    """返回全局最坏误差(ms)和策略字典 {f0: (N, max_err_ms)}"""
    worst_global = 0
    strategy = {}
    for f0 in f_list:
        f_low = f0 * (1 - delta_f_ratio)
        f_high = f0 * (1 + delta_f_ratio)
        w_typical = np.ceil(T * f0) / f0
        N_typical = int(round(D / w_typical))
        best_worst = float('inf')
        best_N = None
        for N in range(max(1, N_typical - 5), N_typical + 6):
            fs = np.linspace(f_low, f_high, 200)  # 更密的采样
            delays = N * np.ceil(T * fs) / fs
            errors = np.abs(delays - D)
            max_err = np.max(errors)
            if max_err < best_worst:
                best_worst = max_err
                best_N = N
        strategy[f0] = (best_N, best_worst * 1000)
        if best_worst > worst_global:
            worst_global = best_worst
    return worst_global * 1000, strategy

# ---------- 参数设置 ----------
D = 0.150            # 目标延迟 150ms
delta_ratio = 0.2    # 假设实际 fps 在标称值的 ±20% 内波动

# 关注的标称 fps 列表（包含常见值和步长扫描）
f_common = [64, 100, 120, 144, 165, 200, 240, 300, 400, 500]
f_extra = np.arange(60, 501, 10).tolist()   # 用于精细搜索 T
f_all = sorted(set(f_common + f_extra))

# ---------- 扫描 T ----------
T_candidates = np.arange(0.001, 0.101, 0.0005)  # 步长 0.5ms
best_T = None
best_error = float('inf')
best_strat = None

for T in T_candidates:
    err, strat = evaluate_T(D, T, f_all, delta_ratio)
    if err < best_error:
        best_error = err
        best_T = T
        best_strat = strat

print(f"最优 T = {best_T:.4f}s, 全局最坏误差 = {best_error:.2f}ms\n")

# ---------- 输出常见 fps 的推荐 N ----------
print("标称fps | 推荐N | 波动区间内最大误差(ms)")
print("-" * 45)
for f in f_common:
    N, max_err = best_strat[f]
    print(f"{f:5d}   | {N:5d} | {max_err:19.1f}")