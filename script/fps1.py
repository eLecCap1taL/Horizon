import math

def predict_wait(single_wait: float, target_delay: float, fps: float) -> tuple:
    """
    基于 "Test_Wait 向上取整为帧时间整数倍" 的假设，
    计算 N 次相同参数 Test_Wait 的理论总耗时和误差。

    参数:
        single_wait: 单次 Test_Wait 的参数（秒）
        target_delay: 期望的总延时（秒）
        fps: 实时帧率
    返回:
        (actual_total, error)  单位秒
    """
    # 需要多少次 Test_Wait 才能达到目标总延时
    n = round(target_delay / single_wait)   # 或直接用 target_delay // single_wait，但浮点除法取整
    frame_time = 1.0 / fps

    # 单次实际等待帧数（向上取整）
    frames_per_wait = math.ceil(single_wait * fps)

    # 单次实际耗时
    actual_per_wait = frames_per_wait * frame_time

    # 总耗时
    actual_total = n * actual_per_wait

    # 绝对误差
    error = actual_total - target_delay

    return actual_total, error


# ---------- 使用示例 ----------
if __name__ == "__main__":
    # 例 1：20 次 Test_Wait 0.05，目标 1 秒，帧率 64
    single = 0.05
    target = 1.0
    fps = 64.0
    total, err = predict_wait(single, target, fps)
    print(f"64fps: 理论总耗时 = {total:.6f}s, 误差 = {err:.6f}s (应为 ~1.25s)")

    # 例 2：20 次 Test_Wait 0.05，目标 1 秒，帧率 200
    fps = 200.0
    total, err = predict_wait(single, target, fps)
    print(f"200fps: 理论总耗时 = {total:.6f}s, 误差 = {err:.6f}s (应为 ~1.00s)")

    # 例 3：混合参数（不同数值） —— 如果你需要，可以用下面这个版本