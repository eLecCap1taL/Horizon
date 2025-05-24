import os
import shutil
import json
import yaml
from pathlib import Path

# 常量设置
SENSITIVITY = 2.52
YAW_PITCH_VALUE = 0.022


def backup_file_if_exists(filepath: Path):
    """
    如果文件存在，则重命名为 .backupN
    """
    if not filepath.exists():
        return
    index = 1
    while True:
        backup = filepath.with_name(f"{filepath.name}.backup{index}")
        if not backup.exists():
            break
        index += 1
    try:
        shutil.move(str(filepath), str(backup))
        print(f"已将原文件 '{filepath}' 备份为 '{backup}'")
    except Exception as e:
        print(f"备份失败: {e}")


def json_to_yaml(input_file: Path, output_file: Path):
    """
    将 list.json 转换为 Custom.yml
    """
    if not input_file.exists():
        print(f"输入文件不存在: {input_file}")
        return
    backup_file_if_exists(output_file)

    with input_file.open('r', encoding='utf-8') as f:
        data = json.load(f)

    root = {}
    for g in data.get('grenades', []):
        gid = g.get('id', '')
        zh = g.get('name_zh_cn', '')
        en = g.get('name_en_us', '')
        pitch = float(g.get('angle', {}).get('pitch', 0.0))
        yaw = float(g.get('angle', {}).get('yaw', 0.0))

        # 角度转换
        p_conv = pitch / (SENSITIVITY * YAW_PITCH_VALUE)
        y_conv = -yaw / (SENSITIVITY * YAW_PITCH_VALUE)

        cmd = g.get('throw_command', '')
        if cmd == 'hzNade_jumpthrow_L':
            mode = 'Jump'
        elif cmd == 'hzNade_Wjumpthrow_L':
            mode = 'ForwardJump'
        elif cmd == 'hzNade_throw_L':
            mode = 'Normal'
        else:
            mode = 'Custom'

        mapname = g.get('map', '')
        gtype = g.get('type', '')
        if gtype == 'HE':
            gtype = 'grenade'

        root[gid] = {
            'filename': f"{gid}.cfg",
            'displayname': f"{zh} {en}",
            'map': mapname,
            'sensitivity': SENSITIVITY,
            'yaw': y_conv,
            'pitch': p_conv,
            'type': gtype,
            'throwmode': mode,
            'extra': [g.get('pre_throw_command', ''), g.get('post_throw_command', '')],
            'select': [
                {'page': ''}, {'slot': ''}, {'command': ''}, {'bind': 'None'}
            ],
            'setpos': [
                {'x': float(g.get('position', {}).get('x', 0.0))},
                {'z': float(g.get('position', {}).get('y', 0.0))},
                {'y': 100}
            ]
        }

    with output_file.open('w', encoding='utf-8') as f:
        yaml.dump(root, f, allow_unicode=True, sort_keys=False)
    print(f"已将 JSON '{input_file}' 转换为 YAML '{output_file}'")


def yaml_to_json(input_file: Path, output_file: Path):
    """
    将 Custom.yml 转换为 list.json
    """
    if not input_file.exists():
        print(f"输入文件不存在: {input_file}")
        return
    backup_file_if_exists(output_file)

    with input_file.open('r', encoding='utf-8') as f:
        root = yaml.safe_load(f) or {}

    result = {'grenades': []}
    for gid, v in root.items():
        dsp = v.get('displayname', '')
        zh, en = (dsp.rsplit(' ', 1) if ' ' in dsp else (dsp, ''))

        # 确保 pitch/yaw 为数值
        p_val = float(v.get('pitch', 0.0)) * SENSITIVITY * YAW_PITCH_VALUE
        y_val = -float(v.get('yaw', 0.0)) * SENSITIVITY * YAW_PITCH_VALUE

        mode = v.get('throwmode', '')
        if mode == 'Jump':
            cmd = 'hzNade_jumpthrow_L'
        elif mode == 'ForwardJump':
            cmd = 'hzNade_Wjumpthrow_L'
        else:
            cmd = 'hzNade_throw_L'

        sp = v.get('setpos', [])
        x = float(sp[0].get('x', 0.0)) if len(sp) > 0 else 0.0
        z = float(sp[1].get('z', 0.0)) if len(sp) > 1 else 0.0

        g = {
            'id': gid,
            'name_zh_cn': zh,
            'name_en_us': en,
            'map': v.get('map', ''),
            'type': ('HE' if v.get('type') == 'grenade' else v.get('type', '')),
            'angle': {'pitch': p_val, 'yaw': y_val},
            'position': {'x': x, 'y': z},
            'pre_throw_command': v.get('extra', ['', ''])[0],
            'post_throw_command': v.get('extra', ['', ''])[1],
            'throw_command': cmd
        }
        result['grenades'].append(g)

    with output_file.open('w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"已将 YAML '{input_file}' 转换为 JSON '{output_file}'")


def main():
    print('1: Custom.yml → list.json')
    print('2: list.json → Custom.yml')
    choice = input('请选择 (1/2): ').strip()

    base = Path('.')
    if choice == '1':
        yaml_to_json(base / 'Custom.yml', base / 'list.json')
    elif choice == '2':
        json_to_yaml(base / 'list.json', base / 'Custom.yml')
    else:
        print('无效选择')

    # 等待用户按回车后退出
    input('转换完成，按回车退出...')


if __name__ == '__main__':
    main()