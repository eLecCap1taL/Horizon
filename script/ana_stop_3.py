import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def read_data(filepath):
    """读取减速数据文件"""
    data_dict = {'Empty': []}
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
            
            if line == '[Empty]':
                current_group = 'Empty'
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

def poly2_func(t, a, b, c):
    """二次多项式：v = a*t² + b*t + c"""
    return a * t**2 + b * t + c

def poly3_func(t, a, b, c, d):
    """三次多项式：v = a*t³ + b*t² + c*t + d"""
    return a * t**3 + b * t**2 + c * t + d

def poly4_func(t, a, b, c, d, e):
    """四次多项式：v = a*t⁴ + b*t³ + c*t² + d*t + e"""
    return a * t**4 + b * t**3 + c * t**2 + d * t + e

def calculate_acceleration(t, v):
    """计算加速度"""
    a = np.gradient(v, t)
    return a

def analyze_empty_deceleration(filepath):
    """分析Empty减速过程 - 多项式拟合"""
    
    # 读取数据
    data = read_data(filepath)
    data['Empty'] = normalize_time(data['Empty'])
    
    print(f"读取到 {len(data['Empty'])} 组减速数据")
    
    # 创建图形
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Empty Deceleration Analysis - Polynomial Fitting', fontsize=16, fontweight='bold')
    
    v0_empty = 250.0  # 初始速度
    
    # ============================================
    # 拟合各组数据 - 2次、3次、4次多项式
    # ============================================
    popt_list_2 = []
    popt_list_3 = []
    popt_list_4 = []
    
    for i, dataset in enumerate(data['Empty']):
        t = dataset[:, 0]
        v = dataset[:, 1]
        
        # 二次多项式（固定c=250）
        try:
            popt_2, _ = curve_fit(
                lambda t, a, b: poly2_func(t, a, b, v0_empty),
                t, v,
                p0=[3000, -2500]
            )
            popt_list_2.append(popt_2)
        except Exception as e:
            print(f"Trial {i+1} 二次拟合失败: {e}")
        
        # 三次多项式（固定d=250）
        try:
            popt_3, _ = curve_fit(
                lambda t, a, b, c: poly3_func(t, a, b, c, v0_empty),
                t, v,
                p0=[5000, 2000, -2500],
                maxfev=10000
            )
            popt_list_3.append(popt_3)
        except Exception as e:
            print(f"Trial {i+1} 三次拟合失败: {e}")
        
        # 四次多项式（固定e=250）
        try:
            popt_4, _ = curve_fit(
                lambda t, a, b, c, d: poly4_func(t, a, b, c, d, v0_empty),
                t, v,
                p0=[10000, 5000, 3000, -2500],
                maxfev=10000
            )
            popt_list_4.append(popt_4)
        except Exception as e:
            print(f"Trial {i+1} 四次拟合失败: {e}")
    
    popt_list_2 = np.array(popt_list_2)
    popt_list_3 = np.array(popt_list_3)
    popt_list_4 = np.array(popt_list_4)
    
    popt_2_mean = np.mean(popt_list_2, axis=0)
    popt_2_std = np.std(popt_list_2, axis=0)
    
    popt_3_mean = np.mean(popt_list_3, axis=0)
    popt_3_std = np.std(popt_list_3, axis=0)
    
    popt_4_mean = np.mean(popt_list_4, axis=0)
    popt_4_std = np.std(popt_list_4, axis=0)
    
    # 生成模型曲线
    max_t_actual = max([max(dataset[:, 0]) for dataset in data['Empty']])
    t_range = np.linspace(0, max_t_actual * 1.1, 200)
    
    v_model_2 = poly2_func(t_range, popt_2_mean[0], popt_2_mean[1], v0_empty)
    v_model_3 = poly3_func(t_range, popt_3_mean[0], popt_3_mean[1], popt_3_mean[2], v0_empty)
    v_model_4 = poly4_func(t_range, popt_4_mean[0], popt_4_mean[1], popt_4_mean[2], popt_4_mean[3], v0_empty)
    
    a_model_2 = calculate_acceleration(t_range, v_model_2)
    a_model_3 = calculate_acceleration(t_range, v_model_3)
    a_model_4 = calculate_acceleration(t_range, v_model_4)
    
    # ============================================
    # 计算R²
    # ============================================
    r2_2_list, r2_3_list, r2_4_list = [], [], []
    
    for dataset in data['Empty']:
        t_actual = dataset[:, 0]
        v_actual = dataset[:, 1]
        v_mean = np.mean(v_actual)
        
        v_pred_2 = poly2_func(t_actual, popt_2_mean[0], popt_2_mean[1], v0_empty)
        v_pred_3 = poly3_func(t_actual, popt_3_mean[0], popt_3_mean[1], popt_3_mean[2], v0_empty)
        v_pred_4 = poly4_func(t_actual, popt_4_mean[0], popt_4_mean[1], popt_4_mean[2], popt_4_mean[3], v0_empty)
        
        ss_tot = np.sum((v_actual - v_mean)**2)
        r2_2_list.append(1 - np.sum((v_actual - v_pred_2)**2) / ss_tot)
        r2_3_list.append(1 - np.sum((v_actual - v_pred_3)**2) / ss_tot)
        r2_4_list.append(1 - np.sum((v_actual - v_pred_4)**2) / ss_tot)
    
    # ============================================
    # 归零时间
    # ============================================
    t_zero_2 = t_zero_3 = t_zero_4 = None
    
    mask_2 = v_model_2 <= 0.1
    if np.any(mask_2):
        t_zero_2 = t_range[mask_2][0]
    
    mask_3 = v_model_3 <= 0.1
    if np.any(mask_3):
        t_zero_3 = t_range[mask_3][0]
    
    mask_4 = v_model_4 <= 0.1
    if np.any(mask_4):
        t_zero_4 = t_range[mask_4][0]
    
    # 实际归零时间
    t_zero_actual = []
    for dataset in data['Empty']:
        mask_actual = dataset[:, 1] <= 0.1
        if np.any(mask_actual):
            t_zero_actual.append(dataset[mask_actual][0, 0])
    
    # ============================================
    # 绘图
    # ============================================# 动态生成足够多的颜色
    n_trials = len(data['Empty'])
    colors = plt.cm.tab10(np.linspace(0, 1, max(n_trials, 4)))
    
    # 子图1: 原始数据+二次拟合
    ax1 = axes[0, 0]
    ax1.set_title('Quadratic Fit (v = at² + bt + 250)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Normalized Time (s)')
    ax1.set_ylabel('Velocity (units/s)')
    ax1.grid(True, alpha=0.3)
    
    for i, dataset in enumerate(data['Empty']):
        ax1.scatter(dataset[:, 0], dataset[:, 1], color=colors[i], alpha=0.6, s=30, label=f'Trial {i+1}', zorder=3)
    
    ax1.plot(t_range, v_model_2, 'k-', linewidth=2.5, 
             label=f'v(t) = {popt_2_mean[0]:.0f}t² + {popt_2_mean[1]:.0f}t + 250', zorder=4)
    if t_zero_2:
        ax1.axvline(x=t_zero_2, color='red', linestyle=':', alpha=0.5, label=f't_zero = {t_zero_2:.4f}s')
    ax1.legend(loc='upper right', fontsize=8)
    
    # 子图2: 原始数据+三次拟合
    ax2 = axes[0, 1]
    ax2.set_title('Cubic Fit (v = at³ + bt² + ct + 250)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Normalized Time (s)')
    ax2.set_ylabel('Velocity (units/s)')
    ax2.grid(True, alpha=0.3)
    
    for i, dataset in enumerate(data['Empty']):
        ax2.scatter(dataset[:, 0], dataset[:, 1], color=colors[i], alpha=0.6, s=30, label=f'Trial {i+1}', zorder=3)
    
    ax2.plot(t_range, v_model_3, 'k-', linewidth=2.5, 
             label=f'v(t) = {popt_3_mean[0]:.0f}t³ + {popt_3_mean[1]:.0f}t² + {popt_3_mean[2]:.0f}t + 250', zorder=4)
    if t_zero_3:
        ax2.axvline(x=t_zero_3, color='red', linestyle=':', alpha=0.5, label=f't_zero = {t_zero_3:.4f}s')
    ax2.legend(loc='upper right', fontsize=7)
    
    # 子图3: 原始数据+四次拟合
    ax3 = axes[0, 2]
    ax3.set_title('Quartic Fit (v = at⁴ + bt³ + ct² + dt + 250)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Normalized Time (s)')
    ax3.set_ylabel('Velocity (units/s)')
    ax3.grid(True, alpha=0.3)
    
    for i, dataset in enumerate(data['Empty']):
        ax3.scatter(dataset[:, 0], dataset[:, 1], color=colors[i], alpha=0.6, s=30, label=f'Trial {i+1}', zorder=3)
    
    ax3.plot(t_range, v_model_4, 'k-', linewidth=2.5, 
             label=f'v(t) = {popt_4_mean[0]:.0f}t⁴ + {popt_4_mean[1]:.0f}t³\n       + {popt_4_mean[2]:.0f}t² + {popt_4_mean[3]:.0f}t + 250', zorder=4)
    if t_zero_4:
        ax3.axvline(x=t_zero_4, color='red', linestyle=':', alpha=0.5, label=f't_zero = {t_zero_4:.4f}s')
    ax3.legend(loc='upper right', fontsize=7)
    
    # 子图4: 三种模型对比
    ax4 = axes[1, 0]
    ax4.set_title('Model Comparison', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Normalized Time (s)')
    ax4.set_ylabel('Velocity (units/s)')
    ax4.grid(True, alpha=0.3)
    
    ax4.plot(t_range, v_model_2, 'b-', linewidth=2, label=f'Quadratic (R²={np.mean(r2_2_list):.4f})', alpha=0.8)
    ax4.plot(t_range, v_model_3, 'r--', linewidth=2, label=f'Cubic (R²={np.mean(r2_3_list):.4f})', alpha=0.8)
    ax4.plot(t_range, v_model_4, 'g:', linewidth=2, label=f'Quartic (R²={np.mean(r2_4_list):.4f})', alpha=0.8)
    ax4.legend(loc='upper right', fontsize=8)
    
    # 子图5: 加速度对比
    ax5 = axes[1, 1]
    ax5.set_title('Acceleration Comparison', fontsize=12, fontweight='bold')
    ax5.set_xlabel('Time (s)')
    ax5.set_ylabel('Acceleration (units/s²)')
    ax5.grid(True, alpha=0.3)
    
    ax5.plot(t_range, a_model_2, 'b-', linewidth=2, label=f'Quadratic', alpha=0.8)
    ax5.plot(t_range, a_model_3, 'r--', linewidth=2, label=f'Cubic', alpha=0.8)
    ax5.plot(t_range, a_model_4, 'g:', linewidth=2, label=f'Quartic', alpha=0.8)
    
    for i, dataset in enumerate(data['Empty']):
        a_actual = calculate_acceleration(dataset[:, 0], dataset[:, 1])
        ax5.scatter(dataset[:, 0], a_actual, s=10, color=colors[i], alpha=0.3, label=f'Actual Trial {i+1}')
    
    ax5.legend(loc='lower right', fontsize=7)
    
    # 子图6: 统计信息
    ax6 = axes[1, 2]
    ax6.axis('off')
    ax6.set_title('Statistical Summary', fontsize=12, fontweight='bold')
    
    # 确定最佳模型
    models = [
        ("Quadratic", np.mean(r2_2_list), popt_2_mean, t_zero_2),
        ("Cubic", np.mean(r2_3_list), popt_3_mean, t_zero_3),
        ("Quartic", np.mean(r2_4_list), popt_4_mean, t_zero_4)
    ]
    best_model = max(models, key=lambda x: x[1])
    
    summary_text = f"""
    MODEL COMPARISON (v₀ = 250)
    {'='*40}
    
    Quadratic: v(t) = at² + bt + 250
      a = {popt_2_mean[0]:.2f} ± {popt_2_std[0]:.2f}
      b = {popt_2_mean[1]:.2f} ± {popt_2_std[1]:.2f}
      R² = {np.mean(r2_2_list):.6f}
    
    Cubic: v(t) = at³ + bt² + ct + 250
      a = {popt_3_mean[0]:.2f} ± {popt_3_std[0]:.2f}
      b = {popt_3_mean[1]:.2f} ± {popt_3_std[1]:.2f}
      c = {popt_3_mean[2]:.2f} ± {popt_3_std[2]:.2f}
      R² = {np.mean(r2_3_list):.6f}
    
    Quartic: v(t) = at⁴ + bt³ + ct² + dt + 250
      a = {popt_4_mean[0]:.2f} ± {popt_4_std[0]:.2f}
      b = {popt_4_mean[1]:.2f} ± {popt_4_std[1]:.2f}
      c = {popt_4_mean[2]:.2f} ± {popt_4_std[2]:.2f}
      d = {popt_4_mean[3]:.2f} ± {popt_4_std[3]:.2f}
      R² = {np.mean(r2_4_list):.6f}
    
    BEST MODEL: {best_model[0]}
      R² = {best_model[1]:.6f}
    
    ZERO TIME:
    """
    
    if t_zero_2: summary_text += f"  Quadratic: {t_zero_2:.4f}s\n"
    if t_zero_3: summary_text += f"  Cubic: {t_zero_3:.4f}s\n"
    if t_zero_4: summary_text += f"  Quartic: {t_zero_4:.4f}s\n"
    
    if t_zero_actual:
        summary_text += f"\n  Actual mean: {np.mean(t_zero_actual):.4f}s\n"
        summary_text += f"  Actual range: [{np.min(t_zero_actual):.4f}, {np.max(t_zero_actual):.4f}]s\n"
    
    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
            fontsize=8.5, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig('empty_deceleration_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # ============================================
    # 输出完整结果
    # ============================================
    print("\n" + "="*60)
    print("FITTING RESULTS")
    print("="*60)
    
    print(f"\n二次多项式 R²:")
    for i, r2 in enumerate(r2_2_list): print(f"  Trial {i+1}: {r2:.6f}")
    print(f"  平均: {np.mean(r2_2_list):.6f} ± {np.std(r2_2_list):.6f}")
    
    print(f"\n三次多项式 R²:")
    for i, r2 in enumerate(r2_3_list): print(f"  Trial {i+1}: {r2:.6f}")
    print(f"  平均: {np.mean(r2_3_list):.6f} ± {np.std(r2_3_list):.6f}")
    
    print(f"\n四次多项式 R²:")
    for i, r2 in enumerate(r2_4_list): print(f"  Trial {i+1}: {r2:.6f}")
    print(f"  平均: {np.mean(r2_4_list):.6f} ± {np.std(r2_4_list):.6f}")
    
    print(f"\n最佳模型: {best_model[0]} (R² = {best_model[1]:.6f})")
    
    print(f"\n{'='*60}")
    print(f"BEST MODEL PARAMETERS ({best_model[0]})")
    print("="*60)
    
    if best_model[0] == "Quadratic":
        print(f"v(t) = {best_model[2][0]:.8f} * t² + {best_model[2][1]:.8f} * t + 250")
        print(f"a(t) = {2*best_model[2][0]:.8f} * t + {best_model[2][1]:.8f}")
    elif best_model[0] == "Cubic":
        print(f"v(t) = {best_model[2][0]:.8f} * t³ + {best_model[2][1]:.8f} * t² + {best_model[2][2]:.8f} * t + 250")
        print(f"a(t) = {3*best_model[2][0]:.8f} * t² + {2*best_model[2][1]:.8f} * t + {best_model[2][2]:.8f}")
    else:
        print(f"v(t) = {best_model[2][0]:.8f} * t⁴ + {best_model[2][1]:.8f} * t³ + {best_model[2][2]:.8f} * t² + {best_model[2][3]:.8f} * t + 250")
    
    if best_model[3]:
        print(f"\n归零时间: {best_model[3]:.6f}s")
    
    return best_model

if __name__ == "__main__":
    # 修改为你的数据文件路径
    filepath = r'./stop_data_empty.txt'
    
    best_model = analyze_empty_deceleration(filepath)