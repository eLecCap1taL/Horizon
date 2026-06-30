import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import stats
import os

# 读取数据的函数
def read_data(filepath):
    """
    从文件中读取数据，格式为两组数据：Empty和AK47
    每组包含多份数据，每份数据以空行分隔
    """
    data_dict = {'Empty': [], 'AK47': []}
    current_group = None
    current_dataset = []
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:  # 空行
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
            
            # 解析数据行
            parts = line.split()
            if len(parts) == 2:
                t, v = float(parts[0]), float(parts[1])
                current_dataset.append([t, v])
        
        # 处理最后一组数据
        if current_dataset and current_group:
            data_dict[current_group].append(np.array(current_dataset))
    
    return data_dict

# 标准化时间
def normalize_time(data_list):
    """
    以每组数据的第一个时间点为基准，标准化时间
    第一个时间点设为0，速度保持初始值
    """
    normalized_list = []
    for data in data_list:
        t0 = data[0, 0]  # 初始时间
        v0 = data[0, 1]  # 初始速度
        
        normalized_data = data.copy()
        normalized_data[:, 0] = data[:, 0] - t0  # 时间标准化
        # 速度不需要除以v0，保持原始值以便观察衰减
        
        normalized_list.append(normalized_data)
    
    return normalized_list

# 定义拟合函数
def linear_func(t, a, b):
    """线性函数：v = a*t + b"""
    return a * t + b

def quadratic_func(t, a, b, c):
    """二次函数：v = a*t^2 + b*t + c"""
    return a * t**2 + b * t + c

def exponential_func(t, a, b, c):
    """指数衰减函数：v = a * exp(-b*t) + c"""
    return a * np.exp(-b * t) + c

# 执行拟合
def fit_data(t, v, func, p0=None):
    """对数据进行拟合并返回拟合参数和R²"""
    try:
        popt, pcov = curve_fit(func, t, v, p0=p0, maxfev=10000)
        
        # 计算R²
        residuals = v - func(t, *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((v - np.mean(v))**2)
        r_squared = 1 - (ss_res / ss_tot)
        
        return popt, r_squared
    except:
        return None, None

# 主程序
def main():
    # 设置中文字体（如果需要）
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    
    # 保存数据到临时文件
    temp_file = r'.\stop_data.txt'
    
    # 读取数据
    data = read_data(temp_file)

    # 添加这行调试代码
    print(f"Empty组数据数量: {len(data['Empty'])}")
    print(f"AK47组数据数量: {len(data['AK47'])}")
    if len(data['Empty']) > 0:
        print(f"第一组Empty数据形状: {data['Empty'][0].shape}")
    
    # 标准化时间
    for group in ['Empty', 'AK47']:
        data[group] = normalize_time(data[group])
    
    # 创建图形
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Velocity-Time Analysis and Fitting', fontsize=16, fontweight='bold')
    
    colors = ['blue', 'red', 'green', 'orange']
    group_colors = {'Empty': 'blue', 'AK47': 'red'}
    
    # 子图1: Empty组原始数据和拟合
    ax1 = axes[0, 0]
    ax1.set_title('Empty Group - All Trials with Linear Fit', fontsize=12)
    ax1.set_xlabel('Normalized Time (s)')
    ax1.set_ylabel('Velocity (m/s)')
    
    # 子图2: AK47组原始数据和拟合
    ax2 = axes[0, 1]
    ax2.set_title('AK47 Group - All Trials with Linear Fit', fontsize=12)
    ax2.set_xlabel('Normalized Time (s)')
    ax2.set_ylabel('Velocity (m/s)')
    
    # 子图3: 两组对比（平均值±标准差）
    ax3 = axes[0, 2]
    ax3.set_title('Group Comparison (Mean ± SD)', fontsize=12)
    ax3.set_xlabel('Normalized Time (s)')
    ax3.set_ylabel('Velocity (m/s)')
    
    # 子图4: Empty组拟合残差
    ax4 = axes[1, 0]
    ax4.set_title('Empty Group - Fitting Residuals', fontsize=12)
    ax4.set_xlabel('Normalized Time (s)')
    ax4.set_ylabel('Residuals (m/s)')
    ax4.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    # 子图5: AK47组拟合残差
    ax5 = axes[1, 1]
    ax5.set_title('AK47 Group - Fitting Residuals', fontsize=12)
    ax5.set_xlabel('Normalized Time (s)')
    ax5.set_ylabel('Residuals (m/s)')
    ax5.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    # 子图6: 拟合参数和统计信息
    ax6 = axes[1, 2]
    ax6.axis('off')
    ax6.set_title('Fitting Results Summary', fontsize=12)
    
    # 存储所有拟合结果
    all_fits = {'Empty': [], 'AK47': []}
    
    # 处理和拟合每组数据
    for group_idx, group_name in enumerate(['Empty', 'AK47']):
        datasets = data[group_name]
        
        # 用于计算平均值的数据结构
        all_times = []
        all_velocities = []
        
        for trial_idx, dataset in enumerate(datasets):
            t = dataset[:, 0]
            v = dataset[:, 1]
            
            all_times.append(t)
            all_velocities.append(v)
            
            # 线性拟合
            popt_linear, r2_linear = fit_data(t, v, linear_func)
            
            # 二次拟合
            popt_quad, r2_quad = fit_data(t, v, quadratic_func)
            
            # 指数拟合
            try:
                popt_exp, r2_exp = fit_data(t, v, exponential_func, p0=[250, 50, 0])
            except:
                popt_exp, r2_exp = None, None
            
            # 选择最佳拟合（基于R²）
            fits = {
                'Linear': (popt_linear, r2_linear),
                'Quadratic': (popt_quad, r2_quad),
                'Exponential': (popt_exp, r2_exp)
            }
            
            # 找出最佳拟合（排除None值）
            valid_fits = {k: v for k, v in fits.items() if v[0] is not None and v[1] is not None}
            if valid_fits:
                best_fit_name = max(valid_fits, key=lambda x: valid_fits[x][1])
                best_popt, best_r2 = valid_fits[best_fit_name]
                all_fits[group_name].append({
                    'trial': trial_idx + 1,
                    'best_fit': best_fit_name,
                    'params': best_popt,
                    'r2': best_r2
                })
            
            # 绘制到对应子图
            ax = ax1 if group_name == 'Empty' else ax2
            ax.scatter(t, v, color=colors[trial_idx], alpha=0.6, 
                      label=f'Trial {trial_idx+1}', s=30)
            
            # 绘制最佳拟合线
            if valid_fits:
                t_fit = np.linspace(0, max(t), 100)
                if best_fit_name == 'Linear':
                    v_fit = linear_func(t_fit, *best_popt)
                elif best_fit_name == 'Quadratic':
                    v_fit = quadratic_func(t_fit, *best_popt)
                else:
                    v_fit = exponential_func(t_fit, *best_popt)
                ax.plot(t_fit, v_fit, '--', color=colors[trial_idx], alpha=0.8)
        
        # 计算和绘制平均值
        if all_times:
            # 插值到公共时间网格
            max_t = max([max(t) for t in all_times])
            common_t = np.linspace(0, max_t, 100)
            
            interpolated_v = []
            for t_orig, v_orig in zip(all_times, all_velocities):
                v_interp = np.interp(common_t, t_orig, v_orig)
                interpolated_v.append(v_interp)
            
            interpolated_v = np.array(interpolated_v)
            mean_v = np.mean(interpolated_v, axis=0)
            std_v = np.std(interpolated_v, axis=0)
            
            # 绘制平均值±标准差
            ax3.fill_between(common_t, mean_v - std_v, mean_v + std_v, 
                           alpha=0.2, color=group_colors[group_name])
            ax3.plot(common_t, mean_v, color=group_colors[group_name], 
                    linewidth=2, label=f'{group_name} (mean)')
            
            # 绘制残差
            ax_res = ax4 if group_name == 'Empty' else ax5
            for trial_idx, (t_orig, v_orig) in enumerate(zip(all_times, all_velocities)):
                if trial_idx < len(all_fits[group_name]):
                    fit_info = all_fits[group_name][trial_idx]
                    popt = fit_info['params']
                    fit_name = fit_info['best_fit']
                    
                    if fit_name == 'Linear':
                        v_pred = linear_func(t_orig, *popt)
                    elif fit_name == 'Quadratic':
                        v_pred = quadratic_func(t_orig, *popt)
                    else:
                        v_pred = exponential_func(t_orig, *popt)
                    
                    residuals = v_orig - v_pred
                    ax_res.scatter(t_orig, residuals, color=colors[trial_idx], 
                                  alpha=0.6, s=20, label=f'Trial {trial_idx+1}')
        
        ax1.legend(loc='upper right', fontsize=8)
        ax2.legend(loc='upper right', fontsize=8)
        ax3.legend(loc='upper right', fontsize=8)
        ax4.legend(loc='upper right', fontsize=8)
        ax5.legend(loc='upper right', fontsize=8)
    
    # 在子图6中显示拟合结果
    summary_text = "Fitting Results Summary\n" + "="*40 + "\n\n"
    
    for group_name in ['Empty', 'AK47']:
        summary_text += f"{group_name} Group:\n" + "-"*30 + "\n"
        for fit in all_fits[group_name]:
            summary_text += f"Trial {fit['trial']}: {fit['best_fit']} fit\n"
            summary_text += f"  R² = {fit['r2']:.4f}\n"
            if fit['best_fit'] == 'Linear':
                summary_text += f"  v = {fit['params'][0]:.2f}t + {fit['params'][1]:.2f}\n"
            elif fit['best_fit'] == 'Quadratic':
                summary_text += f"  v = {fit['params'][0]:.2f}t² + {fit['params'][1]:.2f}t + {fit['params'][2]:.2f}\n"
            else:
                summary_text += f"  v = {fit['params'][0]:.2f}exp(-{fit['params'][1]:.2f}t) + {fit['params'][2]:.2f}\n"
            summary_text += "\n"
    
    ax6.text(0.1, 0.9, summary_text, transform=ax6.transAxes, 
            fontsize=9, verticalalignment='top', family='monospace')
    
    plt.tight_layout()
    plt.savefig('velocity_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 输出详细统计信息
    print("\n" + "="*50)
    print("ANALYSIS RESULTS")
    print("="*50)
    
    for group_name in ['Empty', 'AK47']:
        print(f"\n{group_name} Group Analysis:")
        print("-" * 30)
        
        for fit in all_fits[group_name]:
            print(f"\nTrial {fit['trial']}:")
            print(f"  Best fit type: {fit['best_fit']}")
            print(f"  R-squared: {fit['r2']:.4f}")
            print(f"  Parameters: {fit['params']}")
        
        # 计算平均R²
        if all_fits[group_name]:
            avg_r2 = np.mean([f['r2'] for f in all_fits[group_name]])
            std_r2 = np.std([f['r2'] for f in all_fits[group_name]])
            print(f"\n  Average R²: {avg_r2:.4f} ± {std_r2:.4f}")

if __name__ == "__main__":
    main()