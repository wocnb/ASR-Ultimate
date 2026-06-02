"""打包脚本 - 使用 PyInstaller 打包成 exe"""

import subprocess
import sys
from pathlib import Path


def build():
    """执行打包"""
    root = Path(__file__).parent
    spec_file = root / "build.spec"

    if not spec_file.exists():
        print("错误: 找不到 build.spec 文件")
        sys.exit(1)

    print("=" * 50)
    print("ASR-Ultimate 打包工具")
    print("=" * 50)
    print()

    # 检查 PyInstaller 是否安装
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    print()
    print("开始打包...")
    print()

    # 执行打包
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file),
    ]

    result = subprocess.run(cmd, cwd=str(root))

    if result.returncode == 0:
        print()
        print("=" * 50)
        print("打包完成!")
        print(f"输出目录: {root / 'dist'}")
        print("=" * 50)
    else:
        print()
        print("打包失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    build()
