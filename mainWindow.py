import json

from PySide6 import QtCore, QtGui, QtWidgets
from pathlib import Path

from PathListModel import PathListModel
from firewall import FirewallManager
import toml


class ConfigManager:
    @staticmethod
    def import_config(file_path):
        try:
            with open(file_path, "r") as file:
                config = toml.load(file)
                return config.get("paths", [])
        except (FileNotFoundError, toml.TomlDecodeError):
            return []

    @staticmethod
    def export_config(file_path, paths):
        config = {"paths": paths}
        with open(file_path, "w") as file:
            toml.dump(config, file)


class BlockThread(QtCore.QThread):
    progress_update = QtCore.Signal(float)
    log_update = QtCore.Signal(str)

    def __init__(self, path_list, extensions):
        super().__init__()
        self.path_list = path_list
        self.extensions = extensions
        self.firewall_manager = FirewallManager()

    def run(self):
        self.process_files(self.path_list, self.extensions,
                           "添加禁止联网程序：",
                           self.firewall_manager.block_internet)

    def process_files(self, path_list, extensions, log_prefix,
                      firewall_action):
        blocked_paths = []
        total_files = 0
        processed_files = 0

        for path in path_list:
            path_obj = Path(path)
            for file_path in path_obj.glob("**/*"):
                if file_path.suffix.lower() in extensions and file_path.is_file():
                    total_files += 1
                    blocked_paths.append(file_path)
        for block_file_path in blocked_paths:
            # 更新进度和日志
            processed_files += 1
            progress_percentage = processed_files / total_files * 100
            self.progress_update.emit(progress_percentage)

            remaining_files = total_files - processed_files
            remaining_time = remaining_files * 0.5  # 假设每个文件处理时间为0.5秒
            remaining_time = round(remaining_time, 1)

            log_message = f"{log_prefix}{block_file_path}"
            self.log_update.emit(log_message)

            firewall_action(block_file_path)

        self.progress_update.emit(100)
        self.log_update.emit(f"{log_prefix[:-1]}操作完成")


class UnblockThread(BlockThread):
    def run(self):
        self.process_files(self.path_list, self.extensions,
                           "取消禁止联网程序：",
                           self.firewall_manager.unblock_internet)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "断网卫士，阻止文件夹内程序联网的工具，帮助你保护隐私。"
            "作者：吴会欢(hh.wu@connect.polyu.hk)")
        self.setFixedSize(800, 400)
        self.center_on_screen()

        self.path_list = []
        self.load_paths_from_config()

        self.path_list_view = QtWidgets.QListView(self)
        self.path_list_view.setGeometry(20, 20, 250, 360)

        self.path_list_model = PathListModel(self.path_list)
        self.path_list_view.setModel(self.path_list_model)

        self.path_list_view.doubleClicked.connect(self.edit_path)

        self.new_button = QtWidgets.QPushButton("添加文件夹", self)
        self.new_button.setGeometry(300, 20, 80, 30)
        self.new_button.clicked.connect(self.new_path)

        self.delete_button = QtWidgets.QPushButton("删除", self)
        self.delete_button.setGeometry(300, 60, 80, 30)
        self.delete_button.clicked.connect(self.delete_selected_path)

        self.move_up_button = QtWidgets.QPushButton("上移", self)
        self.move_up_button.setGeometry(300, 100, 80, 30)
        self.move_up_button.clicked.connect(self.move_selected_path_up)

        self.move_down_button = QtWidgets.QPushButton("下移", self)
        self.move_down_button.setGeometry(300, 140, 80, 30)
        self.move_down_button.clicked.connect(self.move_selected_path_down)

        self.import_button = QtWidgets.QPushButton("导入配置", self)
        self.import_button.setGeometry(300, 180, 80, 30)
        self.import_button.clicked.connect(self.import_config)

        self.export_button = QtWidgets.QPushButton("导出配置", self)
        self.export_button.setGeometry(300, 220, 80, 30)
        self.export_button.clicked.connect(self.export_config)

        self.group_box = QtWidgets.QGroupBox("阻止联网", self)
        self.group_box.setGeometry(400, 20, 350, 360)

        self.block_all_button = QtWidgets.QPushButton("阻止所有",
                                                      self.group_box)
        self.block_all_button.setGeometry(40, 60, 100, 30)
        self.block_all_button.clicked.connect(self.start_block_thread)

        self.unblock_all_button = QtWidgets.QPushButton("取消阻止",
                                                        self.group_box)
        self.unblock_all_button.setGeometry(200, 60, 100, 30)
        self.unblock_all_button.clicked.connect(self.start_unblock_thread)

        self.progress_label = QtWidgets.QLabel(self.group_box)
        self.progress_label.setGeometry(40, 100, 200, 30)
        self.progress_label.setText("进度：")
        self.progress_label.setAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.progress_bar = QtWidgets.QProgressBar(self.group_box)
        self.progress_bar.setGeometry(40, 140, 280, 30)
        self.progress_bar.setValue(0)

        self.log_label = QtWidgets.QLabel(self.group_box)
        self.log_label.setGeometry(40, 180, 200, 30)
        self.log_label.setText("日志：")
        self.log_label.setAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.log_text_edit = QtWidgets.QTextEdit(self.group_box)
        self.log_text_edit.setGeometry(40, 220, 280, 100)
        self.log_text_edit.setReadOnly(True)

        self.block_thread = None
        self.unblock_thread = None

    def center_on_screen(self):
        screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen_geometry.center().x() - self.width() / 2,
                         screen_geometry.center().y() - self.height() / 2,
                         self.width(), self.height())

    def load_paths_from_config(self):
        config_file = "config.json"
        if Path(config_file).is_file():
            with open(config_file, "r") as file:
                try:
                    config = json.load(file)
                    self.path_list = config.get("paths", [])
                except json.JSONDecodeError:
                    pass

    def import_config(self):
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dialog.setNameFilter("TOML 文件 (*.toml)")

        if dialog.exec_():
            selected_file = dialog.selectedFiles()[0]
            with open(selected_file, "r") as file:
                try:
                    config = toml.load(file)
                    self.path_list = config.get("paths", [])
                    self.path_list_model.setPaths(self.path_list)
                except json.JSONDecodeError:
                    pass

    def export_config(self):
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialog.setNameFilter("TOML 文件 (*.toml)")
        if dialog.exec_():
            selected_file = dialog.selectedFiles()[0]
            config = {"paths": self.path_list}
            with Path(f'{selected_file}.toml').open('w', encoding='utf8') as f:
                toml.dump(config, f)

    def save_paths_to_config(self):
        config = {"paths": self.path_list}
        config_file = "config.json"
        with open(config_file, "w") as file:
            json.dump(config, file)

    def update_path_list_view(self):
        self.path_list_model = PathListModel(self.path_list)
        self.path_list_view.setModel(self.path_list_model)

    def new_path(self):
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        if dialog.exec_():
            selected_path = dialog.selectedFiles()[0]
            self.path_list_model.insertPath(selected_path)
            self.save_paths_to_config()

    def edit_selected_path(self):
        selected_indexes = self.path_list_view.selectedIndexes()
        if selected_indexes:
            selected_index = selected_indexes[0]
            self.path_list_view.edit(selected_index)

    def browse_selected_path(self):
        selected_indexes = self.path_list_view.selectedIndexes()
        if selected_indexes:
            selected_index = selected_indexes[0]
            selected_path = self.path_list_model.data(selected_index,
                                                      QtCore.Qt.DisplayRole)
            if Path(selected_path).is_dir():
                QtGui.QDesktopServices.openUrl(
                    QtCore.QUrl.fromLocalFile(selected_path))

    def delete_selected_path(self):
        selected_indexes = self.path_list_view.selectedIndexes()
        if selected_indexes:
            selected_index = selected_indexes[0]
            self.path_list_model.removePath(selected_index.row())
            self.save_paths_to_config()

    def move_selected_path_up(self):
        selected_indexes = self.path_list_view.selectedIndexes()
        if selected_indexes:
            selected_index = selected_indexes[0]
            self.path_list_model.movePathUp(selected_index.row())
            self.save_paths_to_config()

    def move_selected_path_down(self):
        selected_indexes = self.path_list_view.selectedIndexes()
        if selected_indexes:
            selected_index = selected_indexes[0]
            self.path_list_model.movePathDown(selected_index.row())
            self.save_paths_to_config()

    def edit_path(self, index):
        self.path_list_view.edit(index)

    def start_block_thread(self):
        if self.block_thread is None or not self.block_thread.isRunning():
            extensions, ok = QtWidgets.QInputDialog.getText(
                self, "阻止操作",
                "输入要阻止的文件扩展名类型（用逗号分隔），默认为exe。\n"
                "例如输入“exe,dll,bat”,如果仅需要exe，直接输入exe即可:",
                text='exe')
            if ok:
                extensions = [f'.{ext.strip().lower()}' for ext in
                              extensions.split(",")]

                print(extensions)
                self.block_thread = BlockThread(self.path_list, extensions)
                self.block_thread.progress_update.connect(
                    self.update_block_progress)
                self.block_thread.log_update.connect(self.update_log)
                self.block_thread.start()

    def start_unblock_thread(self):
        if self.unblock_thread is None or not self.unblock_thread.isRunning():
            extensions, ok = QtWidgets.QInputDialog.getText(
                self, "取消阻止操作",
                "输入要取消阻止的文件扩展名类型（用逗号分隔），默认为exe。\n"
                "例如输入“exe,dll,bat”,如果仅需要exe，直接输入exe即可:",
                text='exe')
            if ok:
                extensions = [f'.{ext.strip().lower()}' for ext in
                              extensions.split(",")]
                print(extensions)
                self.unblock_thread = UnblockThread(self.path_list, extensions)
                self.unblock_thread.progress_update.connect(
                    self.update_unblock_progress)
                self.unblock_thread.log_update.connect(self.update_log)
                self.unblock_thread.start()

    def update_block_progress(self, progress):
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(f"进度：{progress:.2f}%")

    def update_unblock_progress(self, progress):
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(f"进度：{progress:.2f}%")

    def update_log(self, message):
        log_message = f"{message}"
        self.log_text_edit.append(log_message)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_()
