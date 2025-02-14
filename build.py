# 打包成exe文件脚本
import os
import subprocess

def build_exe():
    # 确保输出目录存在
    if not os.path.exists('dist'):
        os.makedirs('dist')
    
    # 使用 PyInstaller 打包
    cmd = [
        'pyinstaller',
        '--noconfirm',
        '--onefile',
        '--console',
        '--name', '网易云音乐云盘导入工具1.0.3',
        'main.py'
    ]
    
    subprocess.run(cmd)
    
    print("打包完成！exe文件位于 dist 目录中")

if __name__ == "__main__":
    build_exe() 