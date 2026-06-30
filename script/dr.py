#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算急停所需时间关于起步时间的函数。

起步函数 p(x): 速度从 0 到 250  (x 为起步时间)
停止函数 q(t): 速度从 250 到 0  (t 为从制动开始的时间)
给定步长 delta，输出 (起步时间, 当前速度, 急停所需时间)。
"""

import sys
import csv
import argparse
from pathlib import Path

# ==================== 拟合函数 ====================
def p(x):
    """起步 v-t 函数，速度从 0 到 250 (单调递增)"""
    return (719.39225811 * x**3
            - 1541.72021432 * x**2
            + 1081.13530258 * x)


def q(t):
    """停止 v-t 函数，速度从 250 到 0 (单调递减)"""
    return (90245.67797464 * t**3
            - 15483.41749524 * t**2
            - 1389.11586978 * t
            + 250.0)


# ==================== 通用二分求根 ====================
def bisect(f, target, a, b, tol=1e-12):
    """
    在区间 [a, b] 上求解 f(x) == target。
    要求 f 在 [a, b] 上单调，且 target 严格介于 f(a) 与 f(b) 之间。
    返回满足条件的 x。
    """
    fa, fb = f(a), f(b)
    if (fa - target) * (fb - target) > 0:
        raise ValueError(
            f"根不在区间 [{a}, {b}] 内: f(a)={fa}, f(b)={fb}, target={target}"
        )

    # 递增函数
    if fa <= fb:
        while (b - a) > tol:
            m = (a + b) / 2.0
            if f(m) < target:
                a = m
            else:
                b = m
    # 递减函数
    else:
        while (b - a) > tol:
            m = (a + b) / 2.0
            if f(m) > target:
                a = m
            else:
                b = m
    return (a + b) / 2.0


# ==================== 主程序 ====================
def main():
    parser = argparse.ArgumentParser(
        description="根据起步与停止 v-t 函数，计算急停所需时间随起步时间的变化。"
    )
    parser.add_argument(
        "delta",
        type=float,
        help="起步时间步长"
    )
    parser.add_argument(
        "--T_end",
        type=float,
        default=None,
        help="停止过程总时间（从 250 到 0），若不指定则自动计算"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="stop_time_vs_start_time.csv",
        help="输出 CSV 文件路径 (默认: stop_time_vs_start_time.csv)"
    )
    args = parser.parse_args()

    # 1. 确定停止总时间 T_end (q(T_end) = 0)
    if args.T_end is not None:
        T_end = args.T_end
        print(f"使用给定的停止总时间 T_end = {T_end:.8f}")
    else:
        # 搜索区间 [0, 0.2]，因为 q(0)=250，q(0.2) < 0
        T_end = bisect(q, 0.0, 0.0, 0.2)
        print(f"自动计算停止总时间 T_end = {T_end:.8f}")

    # 2. 确定起步终止时间 (p(t) = 250)
    # p(0)=0, p(1)≈258.8，所以根在 (0, 1) 内
    T_start_end = 0.577
    print(f"起步达到 250 的时间 T_start_end = {T_start_end:.8f}")

    # 3. 步进计算
    outpath = Path(args.output)
    with outpath.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(["起步时间", "当前速度", "急停所需时间"])

        t = 0.0
        step = args.delta
        # 最后一次可能略超过 T_start_end，我们包含终点
        while t <= T_start_end + 1e-12:
            v = p(t)
            if v > 250.0:
                v = 250.0  # 截断

            # 在停止函数上二分求 t'，使得 q(t') = v
            # 搜索区间硬编码为 [0, T_end] （q 在此区间单调递减）
            try:
                t_prime = bisect(q, v, 0.0, T_end)
            except ValueError:
                # 由于数值误差 v 可能略超出 [q(T_end), q(0)]
                if v >= 250.0:
                    t_prime = 0.0
                elif v <= 0.0:
                    t_prime = T_end
                else:
                    raise

            t_stop_needed = T_end - t_prime
            writer.writerow([
                f"{t:.10f}",
                f"{v:.10f}",
                f"{t_stop_needed:.10f}"
            ])

            t += step
            # 处理浮点误差，确保终点包含在内
            if t > T_start_end and (t - T_start_end) < step / 2:
                t = T_start_end

    print(f"结果已保存至: {outpath.resolve()}")


if __name__ == "__main__":
    main()