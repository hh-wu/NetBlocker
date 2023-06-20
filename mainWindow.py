import json

from PySide6 import QtCore, QtGui, QtWidgets
from pathlib import Path

from PathListModel import PathListModel
from firwall import FirewallManager


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("断网卫士")
        self.resize(800, 400)
        self.center_on_screen()

        self.path_list = []
        self.load_paths_from_config()

        self.path_list_view = QtWidgets.QListView(self)
        self.path_list_view.setGeometry(20, 20, 250, 360)

        self.path_list_model = PathListModel(self.path_list)
        self.path_list_view.setModel(self.path_list_model)

        self.path_list_view.doubleClicked.connect(self.edit_path)

        self.new_button = QtWidgets.QPushButton("新建", self)
        self.new_button.setGeometry(300, 20, 80, 30)
        self.new_button.clicked.connect(self.new_path)

        self.edit_button = QtWidgets.QPushButton("编辑", self)
        self.edit_button.setGeometry(300, 60, 80, 30)
        self.edit_button.clicked.connect(self.edit_selected_path)

        self.browse_button = QtWidgets.QPushButton("浏览", self)
        self.browse_button.setGeometry(300, 100, 80, 30)
        self.browse_button.clicked.connect(self.browse_selected_path)

        self.delete_button = QtWidgets.QPushButton("删除", self)
        self.delete_button.setGeometry(300, 140, 80, 30)
        self.delete_button.clicked.connect(self.delete_selected_path)

        self.move_up_button = QtWidgets.QPushButton("上移", self)
        self.move_up_button.setGeometry(300, 180, 80, 30)
        self.move_up_button.clicked.connect(self.move_selected_path_up)

        self.move_down_button = QtWidgets.QPushButton("下移", self)
        self.move_down_button.setGeometry(300, 220, 80, 30)
        self.move_down_button.clicked.connect(self.move_selected_path_down)

        self.group_box = QtWidgets.QGroupBox("阻止操作", self)
        self.group_box.setGeometry(400, 20, 350, 360)

        self.block_all_button = QtWidgets.QPushButton("阻止所有",
                                                      self.group_box)
        self.block_all_button.setGeometry(40, 60, 100, 30)
        self.block_all_button.clicked.connect(self.block_all)

        self.unblock_all_button = QtWidgets.QPushButton("取消阻止",
                                                        self.group_box)
        self.unblock_all_button.setGeometry(200, 60, 100, 30)
        self.unblock_all_button.clicked.connect(self.unblock_all)

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

    def block_all(self):
        extensions = [".exe", ".dll"]  # 特定文件扩展名列表
        blocked_paths = []

        for path in self.path_list:
            path_obj = Path(path)
            for file_path in path_obj.glob("**/*"):
                if file_path.suffix.lower() in extensions and file_path.is_file():
                    blocked_paths.append(file_path)

        firewall_manager = FirewallManager()
        for file_path in blocked_paths:
            firewall_manager.block_internet(file_path)

    def unblock_all(self):
        extensions = [".exe", ".dll"]  # 特定文件扩展名列表
        blocked_paths = []

        for path in self.path_list:
            path_obj = Path(path)
            for file_path in path_obj.glob("**/*"):
                if file_path.suffix.lower() in extensions and file_path.is_file():
                    blocked_paths.append(file_path)

        firewall_manager = FirewallManager()
        for file_path in blocked_paths:
            firewall_manager.unblock_internet(file_path)
