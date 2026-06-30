import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import stats

def read_acceleration_data(filepath):
    """读取加速数据文件"""
    data_dict = {'emp_st': []}
    current_group = None
    current_dataset = []
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            
            if not line:
                if current_dataset and current_group:
                    data_dict[current_group].append(np.array(current_dataset))
                    current_dataset = []
                continue
            
            if line == '[emp_st]':
                current_group = 'emp_st'
                continue
            
            if line.startswith('#') or line.startswith('//') or line.startswith('import'):
                continue
            
            parts = line.split()
            if len(parts) == 2:
                try:
                    t, v = float(parts[0]), float(parts[1])
                    current_dataset.append([t, v])
                except ValueError:
                    continue
    
    if current_dataset and current_group:
        data_dict[current_group].append(np.array(current_dataset))
    
    return data_dict

def normalize_time(data_list):
    """标准化时间"""
    normalized_list = []
    for data in data_list:
        t0 = data[0, 0]
        normalized_data = data.copy()
        normalized_data[:, 0] = data[:, 0] - t0
        normalized_list.append(normalized_data)
    return normalized_list

def cubic_func(t, a, b, c, d):
    """三次函数：v = a*t^3 + b*t^2 + c*t + d"""
    return a * t**3 + b * t**2 + c * t + d

def calculate_acceleration(t, v):
    """计算加速度"""
    a = np.gradient(v, t)
    return a

def analyze_acceleration(filepath):
    """分析加速过程数据 - 仅使用三次函数拟合"""
    
    # 读取数据
    data = read_acceleration_data(filepath)
    data['emp_st'] = normalize_time(data['emp_st'])
    
    print(f"读取到 {len(data['emp_st'])} 组加速数据")
    
    # 创建图形
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('emp_st Acceleration Analysis - Cubic Function Fit', fontsize=16, fontweight='bold')
    
    v_max = 250.0
    
    # ============================================
    # 拟合各组数据 - 三次函数
    # ============================================
    popt_list_cubic = []
    
    for i, dataset in enumerate(data['emp_st']):
        t = dataset[:, 0]
        v = dataset[:, 1]
        
        # 三次函数拟合（固定起点为0）
        try:
            popt_cubic, _ = curve_fit(
                lambda t, a, b, c: cubic_func(t, a, b, c, 0),
                t, v,
                p0=[-500, -500, 1000],
                maxfev=10000
            )
            popt_list_cubic.append(popt_cubic)
            print(f"Trial {i+1} 拟合成功: a={popt_cubic[0]:.2f}, b={popt_cubic[1]:.2f}, c={popt_cubic[2]:.2f}")
        except Exception as e:
            print(f"Trial {i+1} 拟合失败: {e}")
    
    popt_list_cubic = np.array(popt_list_cubic)
    popt_cubic_mean = np.mean(popt_list_cubic, axis=0)
    popt_cubic_std = np.std(popt_list_cubic, axis=0)
    
    # 生成模型曲线
    max_t_actual = max([max(dataset[:, 0]) for dataset in data['emp_st']])
    t_range = np.linspace(0, max_t_actual * 1.1, 200)
    v_cubic_model = cubic_func(t_range, popt_cubic_mean[0], popt_cubic_mean[1], 
                               popt_cubic_mean[2], 0)
    a_cubic_model = calculate_acceleration(t_range, v_cubic_model)
    
    # ============================================
    # 计算R²
    # ============================================
    r2_cubic_list = []
    
    for dataset in data['emp_st']:
        t_actual = dataset[:, 0]
        v_actual = dataset[:, 1]
        v_mean = np.mean(v_actual)
        
        v_pred_cubic = cubic_func(t_actual, popt_cubic_mean[0], popt_cubic_mean[1], 
                                  popt_cubic_mean[2], 0)
        ss_res_cubic = np.sum((v_actual - v_pred_cubic)**2)
        ss_tot = np.sum((v_actual - v_mean)**2)
        r2_cubic_list.append(1 - ss_res_cubic/ss_tot)
    
    # ============================================
    # 达到最大速度时间
    # ============================================
    t_to_max_cubic = None
    mask_cubic = v_cubic_model >= 249.9
    if np.any(mask_cubic):
        t_to_max_cubic = t_range[mask_cubic][0]
    
    t_to_max_actual = []
    for dataset in data['emp_st']:
        mask_actual = dataset[:, 1] >= 249.9
        if np.any(mask_actual):
            t_to_max_actual.append(dataset[mask_actual][0, 0])
    
    # ============================================
    # 绘图
    # ============================================
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # 子图1: 原始数据与三次拟合
    ax1 = axes[0, 0]
    ax1.set_title('Velocity-Time: Cubic Fit', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Normalized Time (s)')
    ax1.set_ylabel('Velocity (units/s)')
    ax1.grid(True, alpha=0.3)
    
    for i, dataset in enumerate(data['emp_st']):
        ax1.scatter(dataset[:, 0], dataset[:, 1], 
                   color=colors[i], alpha=0.6, s=30, 
                   label=f'Trial {i+1}', zorder=3)
        # 各组自己的拟合线
        t_trial = np.linspace(0, max(dataset[:, 0]), 100)
        v_trial_fit = cubic_func(t_trial, popt_list_cubic[i][0], popt_list_cubic[i][1], 
                                 popt_list_cubic[i][2], 0)
        ax1.plot(t_trial, v_trial_fit, '--', color=colors[i], alpha=0.5, linewidth=1)
    
    ax1.plot(t_range, v_cubic_model, 'k-', linewidth=2.5, 
             label=f'Average: {popt_cubic_mean[0]:.0f}t³ + {popt_cubic_mean[1]:.0f}t² + {popt_cubic_mean[2]:.0f}t', 
             zorder=4)
    ax1.axhline(y=250, color='gray', linestyle='--', alpha=0.5, label='v_max = 250')
    if t_to_max_cubic:
        ax1.axvline(x=t_to_max_cubic, color='green', linestyle=':', alpha=0.5, 
                   label=f't_max = {t_to_max_cubic:.4f}s')
    ax1.legend(loc='lower right', fontsize=8)
    
    # 子图2: 拟合残差分析
    ax2 = axes[0, 1]
    ax2.set_title('Residuals Analysis', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Normalized Time (s)')
    ax2.set_ylabel('Residuals (units/s)')
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax2.grid(True, alpha=0.3)
    
    all_residuals = []
    for i, dataset in enumerate(data['emp_st']):
        t_actual = dataset[:, 0]
        v_actual = dataset[:, 1]
        v_pred = cubic_func(t_actual, popt_cubic_mean[0], popt_cubic_mean[1], 
                           popt_cubic_mean[2], 0)
        residuals = v_actual - v_pred
        all_residuals.extend(residuals)
        
        ax2.scatter(t_actual, residuals, color=colors[i], alpha=0.5, s=20, 
                   label=f'Trial {i+1}')
    
    all_residuals = np.array(all_residuals)
    ax2.axhline(y=np.mean(all_residuals), color='red', linestyle='-', alpha=0.7, 
                label=f'Mean: {np.mean(all_residuals):.2f}')
    ax2.axhline(y=np.mean(all_residuals) + np.std(all_residuals), color='red', 
                linestyle=':', alpha=0.5)
    ax2.axhline(y=np.mean(all_residuals) - np.std(all_residuals), color='red', 
                linestyle=':', alpha=0.5)
    ax2.legend(loc='upper right', fontsize=8)
    
    # 子图3: 速度导数（加速度-时间）
    ax3 = axes[0, 2]
    ax3.set_title('Acceleration-Time Analysis', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Normalized Time (s)')
    ax3.set_ylabel('Acceleration (units/s²)')
    ax3.grid(True, alpha=0.3)
    
    # 模型加速度
    ax3.plot(t_range, a_cubic_model, 'k-', linewidth=2.5, 
             label=f'Model: a(t) = {3*popt_cubic_mean[0]:.0f}t² + {2*popt_cubic_mean[1]:.0f}t + {popt_cubic_mean[2]:.0f}')
    
    # 实际数据加速度
    for i, dataset in enumerate(data['emp_st']):
        t_actual = dataset[:, 0]
        v_actual = dataset[:, 1]
        a_actual = calculate_acceleration(t_actual, v_actual)
        ax3.scatter(t_actual, a_actual, s=15, color=colors[i], 
                   alpha=0.5, label=f'Actual Trial {i+1}')
    
    ax3.legend(loc='upper right', fontsize=7)
    
    # 子图4: 加速度-速度关系
    ax4 = axes[1, 0]
    ax4.set_title('Acceleration-Velocity Relationship', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Velocity (units/s)')
    ax4.set_ylabel('Acceleration (units/s²)')
    ax4.grid(True, alpha=0.3)
    
    ax4.plot(v_cubic_model, a_cubic_model, 'k-', linewidth=2.5, label='Cubic Model')
    
    for i, dataset in enumerate(data['emp_st']):
        v_actual = dataset[:, 1]
        a_actual = calculate_acceleration(dataset[:, 0], v_actual)
        ax4.scatter(v_actual, a_actual, s=15, color=colors[i], 
                   alpha=0.5, label=f'Actual Trial {i+1}')
    
    ax4.legend(loc='upper right', fontsize=8)
    
    # 子图5: 速度归一化分析
    ax5 = axes[1, 1]
    ax5.set_title('Normalized Velocity Analysis', fontsize=12, fontweight='bold')
    ax5.set_xlabel('Normalized Time (s)')
    ax5.set_ylabel('v(t)/v_max')
    ax5.grid(True, alpha=0.3)
    
    v_normalized_model = v_cubic_model / 250
    ax5.plot(t_range, v_normalized_model, 'k-', linewidth=2.5, label='Normalized Model')
    
    for i, dataset in enumerate(data['emp_st']):
        v_normalized_actual = dataset[:, 1] / 250
        ax5.scatter(dataset[:, 0], v_normalized_actual, 
                   color=colors[i], alpha=0.6, s=20, label=f'Trial {i+1}')
    
    # 添加关键百分比线
    for pct in [0.5, 0.9, 0.95]:
        ax5.axhline(y=pct, color='gray', linestyle=':', alpha=0.3)
        # 找到达到该百分比的时间
        mask = v_normalized_model >= pct
        if np.any(mask):
            t_pct = t_range[mask][0]
            ax5.axvline(x=t_pct, color='gray', linestyle=':', alpha=0.3)
            ax5.text(t_pct, pct, f' t={t_pct:.3f}s', fontsize=8, alpha=0.7)
    
    ax5.legend(loc='lower right', fontsize=8)
    
    # 子图6: 统计信息
    ax6 = axes[1, 2]
    ax6.axis('off')
    ax6.set_title('Statistical Summary', fontsize=12, fontweight='bold')
    
    # 计算关键时间点
    t_50 = t_90 = t_95 = t_99 = None
    for pct, target in [(0.5, 125), (0.9, 225), (0.95, 237.5), (0.99, 247.5)]:
        mask = v_cubic_model >= target
        if np.any(mask):
            t_val = t_range[mask][0]
            if pct == 0.5: t_50 = t_val
            elif pct == 0.9: t_90 = t_val
            elif pct == 0.95: t_95 = t_val
            elif pct == 0.99: t_99 = t_val
    
    summary_text = f"""
    CUBIC MODEL FIT RESULTS
    {'='*40}
    
    Model: v(t) = at³ + bt² + ct
    Parameters:
      a = {popt_cubic_mean[0]:.2f} ± {popt_cubic_std[0]:.2f}
      b = {popt_cubic_mean[1]:.2f} ± {popt_cubic_std[1]:.2f}
      c = {popt_cubic_mean[2]:.2f} ± {popt_cubic_std[2]:.2f}
    
    Acceleration: a(t) = 3at² + 2bt + c
      a(t) = {3*popt_cubic_mean[0]:.0f}t² + {2*popt_cubic_mean[1]:.0f}t + {popt_cubic_mean[2]:.0f}
    
    FIT QUALITY
    {'='*40}
    """
    
    for i, r2 in enumerate(r2_cubic_list):
        summary_text += f"Trial {i+1}: R² = {r2:.6f}\n"
    
    summary_text += f"""
    Mean R²: {np.mean(r2_cubic_list):.6f}
    Std R²:  {np.std(r2_cubic_list):.6f}
    
    RESIDUALS
    {'='*40}
    Mean: {np.mean(all_residuals):.3f} units/s
    Std:  {np.std(all_residuals):.3f} units/s
    Max:  {np.max(np.abs(all_residuals)):.3f} units/s
    
    KEY TIME POINTS
    {'='*40}
    """
    if t_50: summary_text += f"50% speed: {t_50:.4f}s\n"
    if t_90: summary_text += f"90% speed: {t_90:.4f}s\n"
    if t_95: summary_text += f"95% speed: {t_95:.4f}s\n"
    if t_99: summary_text += f"99% speed: {t_99:.4f}s\n"
    if t_to_max_cubic: summary_text += f"Max speed:  {t_to_max_cubic:.4f}s\n"
    
    if t_to_max_actual:
        summary_text += f"""
    ACTUAL MAX TIME
    {'='*40}
    Mean: {np.mean(t_to_max_actual):.4f}s
    Range: {np.min(t_to_max_actual):.4f}s - {np.max(t_to_max_actual):.4f}s
    """
    
    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
            fontsize=9, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig('emp_st_cubic_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # ============================================
    # 输出完整结果
    # ============================================
    print("\n" + "="*60)
    print("FINAL CUBIC MODEL")
    print("="*60)
    print(f"\n速度函数:")
    print(f"  v(t) = {popt_cubic_mean[0]:.6f} * t³ + {popt_cubic_mean[1]:.6f} * t² + {popt_cubic_mean[2]:.6f} * t")
    print(f"\n加速度函数:")
    print(f"  a(t) = {3*popt_cubic_mean[0]:.6f} * t² + {2*popt_cubic_mean[1]:.6f} * t + {popt_cubic_mean[2]:.6f}")
    print(f"\n拟合优度:")
    print(f"  R² = {np.mean(r2_cubic_list):.6f} ± {np.std(r2_cubic_list):.6f}")
    print(f"\n关键参数 (可直接用于代码):")
    print(f"  a = {popt_cubic_mean[0]:.8f}")
    print(f"  b = {popt_cubic_mean[1]:.8f}")
    print(f"  c = {popt_cubic_mean[2]:.8f}")
    
    return popt_cubic_mean, r2_cubic_list

if __name__ == "__main__":
    # 修改为你的数据文件路径
    filepath = r'./start_data.txt'
    
    popt_cubic, r2_list = analyze_acceleration(filepath)