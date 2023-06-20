from PySide6 import QtCore

class PathListModel(QtCore.QAbstractListModel):
    def __init__(self, paths=[], parent=None):
        super().__init__(parent)
        self.paths = paths

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.paths)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        if 0 <= row < len(self.paths):
            path = self.paths[row]
            if role == QtCore.Qt.DisplayRole:
                return path
            elif role == QtCore.Qt.EditRole:
                return path

        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid() and 0 <= index.row() < len(self.paths):
            if role == QtCore.Qt.EditRole:
                self.paths[index.row()] = value
                self.dataChanged.emit(index, index)
                return True

        return False

    def insertPath(self, path):
        self.beginInsertRows(QtCore.QModelIndex(), len(self.paths), len(self.paths))
        self.paths.append(path)
        self.endInsertRows()

    def removePath(self, row):
        if 0 <= row < len(self.paths):
            self.beginRemoveRows(QtCore.QModelIndex(), row, row)
            del self.paths[row]
            self.endRemoveRows()

    def movePathUp(self, row):
        if 0 < row < len(self.paths):
            self.beginMoveRows(QtCore.QModelIndex(), row, row, QtCore.QModelIndex(), row - 1)
            self.paths[row], self.paths[row - 1] = self.paths[row - 1], self.paths[row]
            self.endMoveRows()

    def movePathDown(self, row):
        if 0 <= row < len(self.paths) - 1:
            self.beginMoveRows(QtCore.QModelIndex(), row, row, QtCore.QModelIndex(), row + 2)
            self.paths[row], self.paths[row + 1] = self.paths[row + 1], self.paths[row]
            self.endMoveRows()

    def setPaths(self, paths):
        self.beginResetModel()
        self.paths = paths
        self.endResetModel()