import sys
import os
import json
import ctypes
import subprocess
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from mainWindow import MainWindow


def run_as_admin():
    if sys.platform.startswith("win"):
        # 获取当前脚本的路径
        script_path = os.path.abspath(sys.argv[0])

        # 使用 ShellExecute 提升权限运行当前脚本
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, script_path, None, 1
        )
        sys.exit()


if __name__ == "__main__":

    # 检查是否以管理员权限运行，如果不是则重新启动以获取管理员权限
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        run_as_admin()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
