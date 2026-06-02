"""ASR-Ultimate 入口"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    # 切换到项目根目录
    root = Path(__file__).parent
    import os
    os.chdir(root)

    # 启动 Qt 应用
    app = QApplication(sys.argv)
    app.setApplicationName("ASR-Ultimate")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
