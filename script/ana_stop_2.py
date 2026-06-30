import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import stats
import os

def read_data(filepath):
    """读取数据文件"""
    data_dict = {'Empty': [], 'AK47': []}
    current_group = None
    current_dataset = []
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                if current_dataset and current_group:
                    data_dict[current_group].append(np.array(current_dataset))
                    current_dataset = []
                continue
            
            if line == '[Empty]':
                current_group = 'Empty'
                continue
            elif line == '[AK47]':
                current_group = 'AK47'
                continue
            
            parts = line.split()
            if len(parts) == 2:
                t, v = float(parts[0]), float(parts[1])
                current_dataset.append([t, v])
        
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

def quadratic_func(t, a, b, c):
    """二次函数：v = a*t^2 + b*t + c"""
    return a * t**2 + b * t + c

def quadratic_func_fixed_v0(t, a, b, v0):
    """二次函数，固定初始速度 v0"""
    return a * t**2 + b * t + v0

def linear_func(t, a, b):
    """线性函数：v = a*t + b"""
    return a * t + b

def exponential_func(t, a, b, c):
    """指数衰减：v = a * exp(-b*t) + c"""
    return a * np.exp(-b * t) + c

def calculate_acceleration(t, v):
    """计算加速度（速度对时间的导数）"""
    a = np.gradient(v, t)
    return a

def analyze_velocity_scaling(filepath):
    """
    分析Empty组的速度曲线，验证是否可以等比缩放到AK47
    """
    # 读取数据
    data = read_data(filepath)
    data['Empty'] = normalize_time(data['Empty'])
    data['AK47'] = normalize_time(data['AK47'])
    
    # 创建图形
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Velocity Scaling Analysis - Empty Model Applied to AK47', fontsize=16, fontweight='bold')
    
    # ============================================
    # 1. 拟合Empty组数据（固定初始速度为250）
    # ============================================
    v0_empty = 250.0
    
    # 分别拟合每组Empty数据，然后平均参数
    popt_list = []
    for dataset in data['Empty']:
        t = dataset[:, 0]
        v = dataset[:, 1]
        
        # 拟合 a 和 b，固定 c=v0_empty
        popt, _ = curve_fit(
            lambda t, a, b: quadratic_func_fixed_v0(t, a, b, v0_empty),
            t, v,
            p0=[3000, -2000]  # 初始猜测值
        )
        popt_list.append(popt)
    
    popt_list = np.array(popt_list)
    popt_empty = np.mean(popt_list, axis=0)
    std_empty = np.std(popt_list, axis=0)
    
    print("="*60)
    print("EMPTY GROUP FITTING (Fixed v0 = 250)")
    print("="*60)
    print(f"平均参数: a = {popt_empty[0]:.2f} ± {std_empty[0]:.2f}")
    print(f"           b = {popt_empty[1]:.2f} ± {std_empty[1]:.2f}")
    print(f"           c = {v0_empty} (fixed)")
    print(f"\n各试验参数:")
    for i, params in enumerate(popt_list):
        print(f"  Trial {i+1}: a = {params[0]:.2f}, b = {params[1]:.2f}")
    
    # 生成Empty模型曲线
    t_range = np.linspace(0, 0.2, 100)
    v_empty_model = quadratic_func_fixed_v0(t_range, popt_empty[0], popt_empty[1], v0_empty)
    
    # ============================================
    # 2. 验证AK47是否符合缩放假设
    # ============================================
    v0_ak47 = 215.0
    scaling_factor = v0_ak47 / v0_empty
    
    print(f"\n缩放因子 (AK47/Empty): {scaling_factor:.4f}")
    
    # 预测AK47的速度曲线
    v_ak47_predicted = quadratic_func_fixed_v0(t_range, popt_empty[0], popt_empty[1], v0_ak47)
    
    # ============================================
    # 3. 绘图
    # ============================================
    
    # 子图1: Empty组原始数据和拟合
    ax1 = axes[0, 0]
    ax1.set_title('Empty Group - All Trials with Model', fontsize=12)
    ax1.set_xlabel('Normalized Time (s)')
    ax1.set_ylabel('Velocity (units/s)')
    ax1.grid(True, alpha=0.3)
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, dataset in enumerate(data['Empty']):
        ax1.scatter(dataset[:, 0], dataset[:, 1], 
                   color=colors[i], alpha=0.6, s=30, 
                   label=f'Trial {i+1}', zorder=3)
        # 绘制各组自己的拟合线
        t_trial = np.linspace(0, max(dataset[:, 0]), 100)
        v_trial_fit = quadratic_func_fixed_v0(t_trial, popt_list[i][0], popt_list[i][1], v0_empty)
        ax1.plot(t_trial, v_trial_fit, '--', color=colors[i], alpha=0.5, linewidth=1)
    
    ax1.plot(t_range, v_empty_model, 'k-', linewidth=2.5, label='Average Model', zorder=4)
    ax1.legend(loc='upper right', fontsize=8)
    
    # 子图2: AK47组原始数据和缩放预测
    ax2 = axes[0, 1]
    ax2.set_title('AK47 Group - Scaled Empty Model Prediction', fontsize=12)
    ax2.set_xlabel('Normalized Time (s)')
    ax2.set_ylabel('Velocity (units/s)')
    ax2.grid(True, alpha=0.3)
    
    for i, dataset in enumerate(data['AK47']):
        ax2.scatter(dataset[:, 0], dataset[:, 1], 
                   color=colors[i], alpha=0.6, s=30, 
                   label=f'Trial {i+1}', zorder=3)
    
    ax2.plot(t_range, v_ak47_predicted, 'k-', linewidth=2.5, 
             label=f'Scaled Model (×{scaling_factor:.3f})', zorder=4)
    
    # 添加置信区间
    v_upper = quadratic_func_fixed_v0(t_range, 
                                       popt_empty[0] + std_empty[0], 
                                       popt_empty[1] + std_empty[1], 
                                       v0_ak47)
    v_lower = quadratic_func_fixed_v0(t_range, 
                                       popt_empty[0] - std_empty[0], 
                                       popt_empty[1] - std_empty[1], 
                                       v0_ak47)
    ax2.fill_between(t_range, v_lower, v_upper, alpha=0.2, color='gray', 
                     label='±1σ confidence')
    ax2.legend(loc='upper right', fontsize=8)
    
    # 子图3: 标准化速度曲线对比
    ax3 = axes[0, 2]
    ax3.set_title('Normalized Velocity Comparison', fontsize=12)
    ax3.set_xlabel('Normalized Time (s)')
    ax3.set_ylabel('v(t)/v₀')
    ax3.grid(True, alpha=0.3)
    
    # Empty标准化
    v_empty_normalized = v_empty_model / v0_empty
    ax3.plot(t_range, v_empty_normalized, 'b-', linewidth=2.5, 
             label='Empty Model (normalized)')
    
    # AK47各试验标准化
    for i, dataset in enumerate(data['AK47']):
        v_ak47_normalized = dataset[:, 1] / v0_ak47
        ax3.scatter(dataset[:, 0], v_ak47_normalized, 
                   color=colors[i], alpha=0.6, s=20, 
                   label=f'AK47 Trial {i+1}')
    
    ax3.legend(loc='upper right', fontsize=8)
    
    # 子图4: 预测误差分析
    ax4 = axes[1, 0]
    ax4.set_title('Prediction Error Analysis (AK47)', fontsize=12)
    ax4.set_xlabel('Normalized Time (s)')
    ax4.set_ylabel('Error (Actual - Predicted) [units/s]')
    ax4.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax4.grid(True, alpha=0.3)
    
    all_errors = []
    for i, dataset in enumerate(data['AK47']):
        t_actual = dataset[:, 0]
        v_actual = dataset[:, 1]
        v_predicted = quadratic_func_fixed_v0(t_actual, popt_empty[0], popt_empty[1], v0_ak47)
        errors = v_actual - v_predicted
        all_errors.extend(errors)
        
        ax4.scatter(t_actual, errors, color=colors[i], alpha=0.6, s=25, 
                   label=f'Trial {i+1}')
        ax4.plot(t_actual, errors, '-', color=colors[i], alpha=0.3, linewidth=1)
    
    # 添加误差统计线
    all_errors = np.array(all_errors)
    mean_error = np.mean(all_errors)
    std_error = np.std(all_errors)
    ax4.axhline(y=mean_error, color='red', linestyle='-', alpha=0.7, 
                label=f'Mean error: {mean_error:.2f}')
    ax4.axhline(y=mean_error + std_error, color='red', linestyle=':', alpha=0.5)
    ax4.axhline(y=mean_error - std_error, color='red', linestyle=':', alpha=0.5)
    ax4.legend(loc='upper right', fontsize=8)
    
    # 子图5: 加速度-速度关系
    ax5 = axes[1, 1]
    ax5.set_title('Acceleration-Velocity Relationship', fontsize=12)
    ax5.set_xlabel('Velocity (units/s)')
    ax5.set_ylabel('Acceleration (units/s²)')
    ax5.grid(True, alpha=0.3)
    
    # Empty模型加速度
    a_empty_model = calculate_acceleration(t_range, v_empty_model)
    ax5.plot(v_empty_model, a_empty_model, 'b-', linewidth=2.5, 
             label='Empty Model', zorder=4)
    
    # AK47各试验实际加速度
    for i, dataset in enumerate(data['AK47']):
        t_ak47 = dataset[:, 0]
        v_ak47 = dataset[:, 1]
        a_ak47 = calculate_acceleration(t_ak47, v_ak47)
        ax5.scatter(v_ak47, a_ak47, s=15, color=colors[i], 
                   alpha=0.5, label=f'AK47 Trial {i+1}')
    
    ax5.legend(loc='lower left', fontsize=8)
    
    # 子图6: 统计信息
    ax6 = axes[1, 2]
    ax6.axis('off')
    ax6.set_title('Statistical Summary', fontsize=12, fontweight='bold')
    
    # 计算各试验的R²
    r2_list = []
    for i, dataset in enumerate(data['AK47']):
        t_actual = dataset[:, 0]
        v_actual = dataset[:, 1]
        v_predicted = quadratic_func_fixed_v0(t_actual, popt_empty[0], popt_empty[1], v0_ak47)
        
        ss_res = np.sum((v_actual - v_predicted)**2)
        ss_tot = np.sum((v_actual - np.mean(v_actual))**2)
        r2 = 1 - (ss_res / ss_tot)
        r2_list.append(r2)
    
    # 计算归零时间
    a, b = popt_empty
    discriminant = b**2 - 4*a*v0_empty
    t_zero_empty = (-b - np.sqrt(discriminant)) / (2*a) if discriminant >= 0 else None
    
    discriminant_ak47 = b**2 - 4*a*v0_ak47
    t_zero_ak47 = (-b - np.sqrt(discriminant_ak47)) / (2*a) if discriminant_ak47 >= 0 else None
    
    summary_text = f"""
    MODEL PARAMETERS
    {'='*35}
    Empty Model (v₀=250):
      v(t) = {popt_empty[0]:.1f}t² + {popt_empty[1]:.1f}t + 250
    
    Scaled to AK47 (v₀=215):
      v(t) = {popt_empty[0]:.1f}t² + {popt_empty[1]:.1f}t + 215
    
    SCALING VALIDATION
    {'='*35}
    Scaling Factor: {scaling_factor:.4f}
    
    Prediction R²:
    """
    
    for i, r2 in enumerate(r2_list):
        summary_text += f"  AK47 Trial {i+1}: {r2:.4f}\n"
    
    summary_text += f"""
    Mean R²: {np.mean(r2_list):.4f} ± {np.std(r2_list):.4f}
    
    ERROR STATISTICS
    {'='*35}
    Mean Error: {mean_error:.2f} units/s
    Std Error:  {std_error:.2f} units/s
    Max |Error|: {np.max(np.abs(all_errors)):.2f} units/s
    
    ZERO-VELOCITY TIME
    {'='*35}
    Empty (predicted): {t_zero_empty:.4f}s
    AK47 (predicted):  {t_zero_ak47:.4f}s
    Time difference:   {abs(t_zero_empty - t_zero_ak47) if t_zero_empty and t_zero_ak47 else 'N/A'}
    """
    
    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
            fontsize=9, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('velocity_scaling_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # ============================================
    # 4. 输出结论
    # ============================================

    print(f"\n平均模型函数:")
    print(f"v(t) = {popt_empty[0]:.6f} * t^2 + {popt_empty[1]:.6f} * t + {v0_empty}")
    print(f"\n即: v(t) = {popt_empty[0]:.2f}t² + {popt_empty[1]:.2f}t + {v0_empty}")

    # 输出用于验证的数据点
    print(f"\n模型曲线数据点 (前10个):")
    print(f"{'Time(s)':<12} {'Velocity':<12}")
    print("-" * 24)
    for i in range(0, len(t_range), 10):
        print(f"{t_range[i]:<12.6f} {v_empty_model[i]:<12.2f}")

    # 输出关键特征值
    print(f"\n关键特征:")
    print(f"初始速度: {v0_empty}")
    print(f"初始加速度 (t=0): {popt_empty[1]:.2f} units/s²")
    print(f"加速度变化率: {2*popt_empty[0]:.2f} units/s³")

    # 计算归零时间
    a, b = popt_empty
    discriminant = b**2 - 4*a*v0_empty
    if discriminant >= 0:
        t_zero = (-b - np.sqrt(discriminant)) / (2*a)
        print(f"速度归零时间: {t_zero:.6f}s")
        
        # 归零时的加速度
        a_at_zero = 2*a*t_zero + b
        print(f"归零时加速度: {a_at_zero:.2f} units/s²")

    # 输出完整的模型参数用于外部使用
    print(f"\n{'='*50}")
    print(f"MODEL PARAMETERS FOR EXTERNAL USE:")
    print(f"a = {popt_empty[0]:.8f}")
    print(f"b = {popt_empty[1]:.8f}")
    print(f"c = {v0_empty}")
    print(f"{'='*50}")


    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    
    print(f"""
缩放因子分析:
  Empty初始速度: {v0_empty}
  AK47初始速度:  {v0_ak47}
  缩放因子:      {scaling_factor:.4f}
  理论缩放因子:  {v0_ak47/v0_empty:.4f}

预测准确度:
  平均R²:        {np.mean(r2_list):.4f}
  平均误差:      {mean_error:.2f} units/s
  标准差:        {std_error:.2f} units/s

速度归零时间:
  Empty模型:     {t_zero_empty:.4f}s
  AK47预测:      {t_zero_ak47:.4f}s
""")
    
    if np.mean(r2_list) > 0.95 and np.abs(mean_error) < 5:
        print("✓ 结论: 缩放假设成立！")
        print("  不同武器的减速机制相同，只是初始速度按比例缩放")
        print(f"  通用模型: v(t) = {popt_empty[0]:.1f}t² + {popt_empty[1]:.1f}t + v₀")
        print("  其中v₀为该武器的初始速度")
    else:
        print("✗ 结论: 缩放假设不完全成立，需要进一步分析")
    
    return popt_empty, v0_empty, scaling_factor

if __name__ == "__main__":
    # 修改为你的数据文件路径
    filepath = r'./stop_data.txt'
    
    popt_empty, v0_empty, scaling_factor = analyze_velocity_scaling(filepath)