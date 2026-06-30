import numpy as np

# ---------- 权重函数（不变） ----------
def weight_D(delay):
    if delay <= 0.03:
        return 1.0
    elif delay <= 0.05:
        return 1.5
    elif delay <= 0.07:
        return 2.0
    elif delay <= 0.10:
        return 3.0
    elif delay <= 0.12:
        return 10.0
    else:  # 0.14
        return 100.0

def weight_f(fps):
    if 100 <= fps <= 240:
        return 3.0
    else:
        return 1.0

def combined_weight(delay, fps):
    return weight_D(delay) * weight_f(fps)

# ---------- 改进的误差评估函数 ----------
def evaluate_T_weighted(T, D_set, f_list, delta_ratio=0.1, N_max=200):
    global_weighted_worst = 0.0
    strategy = {}
    for D in D_set:
        wD = weight_D(D)
        for f0 in f_list:
            wF = weight_f(f0)
            weight = wD * wF

            f_low = f0 * (1 - delta_ratio)
            f_high = f0 * (1 + delta_ratio)
            fs = np.linspace(f_low, f_high, 600)

            best_N = None
            best_max_delay = -float('inf')   # 用于安全N的选择
            best_range = float('inf')        # 延迟范围（max-min），越小越好
            best_over_min = float('inf')     # 超限情况下的最小最大延迟
            best_over_N = None

            for N in range(1, N_max + 1):
                delays = N * np.ceil(T * fs) / fs
                max_d = np.max(delays)
                min_d = np.min(delays)
                delay_range = max_d - min_d

                if max_d <= D:
                    # 安全 N：优先选波动最小的；波动相同时选最大延迟最接近 D 的
                    if delay_range < best_range - 1e-15:
                        best_range = delay_range
                        best_max_delay = max_d
                        best_N = N
                    elif abs(delay_range - best_range) < 1e-15:
                        if max_d > best_max_delay:
                            best_max_delay = max_d
                            best_N = N
                else:
                    # 超限情况：只记录最大延迟最小的那个作为回退
                    if max_d < best_over_min:
                        best_over_min = max_d
                        best_over_N = N

            if best_N is not None:
                # 找到了满足 max_d <= D 的 N
                used_N = best_N
                # 这里我们以最大延迟与目标的偏差作为误差（负或零），但加权时取绝对值
                raw_err = best_max_delay - D   # ≤ 0
                # 同时可输出波动信息（调试用）
                # delay_range = best_range
            else:
                # 没有满足条件的 N，使用超限最小的 N
                used_N = best_over_N
                raw_err = best_over_min - D   # > 0

            strategy[(D, f0)] = (used_N, raw_err)
            weighted_err = weight * abs(raw_err)
            if weighted_err > global_weighted_worst:
                global_weighted_worst = weighted_err

    return global_weighted_worst, strategy

# ---------- 参数 ----------
D_set = [0.03, 0.05, 0.07, 0.10, 0.11, 0.12, 0.13, 0.139]
f_list = [64, 80, 100, 120, 144, 165, 180, 200, 240, 300, 320, 400, 450, 500, 550]
delta = 0.2

# ---------- 扫描 T ----------
T_candidates = np.arange(0.001, 0.03, 0.002)
best_T = None
best_weighted_err = float('inf')
best_strat = None

for T in T_candidates:
    weighted_err, strat = evaluate_T_weighted(T, D_set, f_list, delta)
    if weighted_err < best_weighted_err:
        best_weighted_err = weighted_err
        best_T = T
        best_strat = strat

print(f"最优固定 T = {best_T:.4f}s")
print(f"加权最大误差 = {best_weighted_err:.4f}\n")

# ---------- 输出策略表 ----------
print("目标(ms) | fps | N | 原始误差(ms) | 权重")
print("-" * 60)
for D in D_set:
    for f0 in f_list:
        N, raw_err = best_strat[(D, f0)]
        w = combined_weight(D, f0)
        print(f"  {D*1000:4.0f}   | {f0:4d} | {N:3d} |       {raw_err*1000:+6.1f}       |  {w:4.1f}")
    print("")