import sys
from PyQt5 import QtWidgets, QtCore, QtGui


class FileTreeSelectorModel(QtWidgets.QFileSystemModel):
	def __init__(self, parent=None, rootpath='/'):
		QtWidgets.QFileSystemModel.__init__(self, None)
		self.root_path	  = rootpath
		self.checks		 = {}
		self.nodestack	  = []
		self.parent_index   = self.setRootPath(self.root_path)
		self.root_index	 = self.index(self.root_path)

		self.setFilter(QtCore.QDir.AllEntries | QtCore.QDir.Hidden | QtCore.QDir.NoDot)
		self.directoryLoaded.connect(self._loaded)

	def _loaded(self, path):
		print('_loaded', self.root_path, self.rowCount(self.parent_index))

	def data(self, index, role=QtCore.Qt.DisplayRole):
		if role != QtCore.Qt.CheckStateRole:
			return QtWidgets.QFileSystemModel.data(self, index, role)
		else:
			if index.column() == 0:
				return self.checkState(index)

	def flags(self, index):
		return QtWidgets.QFileSystemModel.flags(self, index) | QtCore.Qt.ItemIsUserCheckable

	def checkState(self, index):
		if index in self.checks:
			return self.checks[index]
		else:
			return QtCore.Qt.Checked

	def setData(self, index, value, role):
		if (role == QtCore.Qt.CheckStateRole and index.column() == 0):
			self.checks[index] = value
			print('setData(): {}'.format(value))
			return True
		return QtWidgets.QFileSystemModel.setData(self, index, value, role)

	def traverseDirectory(self, parentindex, callback=None):
		print('traverseDirectory():')
		self.setTo = (self.checkState(parentindex))
		callback(parentindex)
		self.layoutAboutToBeChanged.emit()
		if self.hasChildren(parentindex):
			path = self.filePath(parentindex)
			print('path in trav is', path)
			it = QtCore.QDirIterator(path, QtCore.QDir.NoFilter, QtCore.QDirIterator.Subdirectories)
			#it = QtCore.QDirIterator(path, self.filter()  | QtCore.QDir.NoDotAndDotDot)
			while it.hasNext():
				print('printing next ',it.next())
				childIndex =  self.index(it.next())
				self.setData(childIndex, self.setTo, QtCore.Qt.CheckStateRole)
				#self.traverseDirectory(childIndex, callback=callback)
		else:
			print('no children')
		#self.changePersistentIndex(parentindex, parentindex)
		self.layoutChanged.emit()
		
	def printIndex(self, index):
		print('model printIndex(): {}'.format(self.filePath(index)))


class FileTreeSelectorDialog(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()

		self.root_path	  = 'c:/python37/'

		# Widget
		self.title		  = "Application Window"
		self.left		   = 100
		self.top			= 100
		self.width		  = 1080
		self.height		 = 640

		self.setWindowTitle(self.title)		 #TODO:  Whilch title?
		self.setGeometry(self.left, self.top, self.width, self.height)

		# Model
		self.model		  = FileTreeSelectorModel(rootpath=self.root_path)
		# self.model		  = QtWidgets.QFileSystemModel()

		# View
		self.view		   = QtWidgets.QTreeView()

		self.view.setObjectName('treeView_fileTreeSelector')
		self.view.setWindowTitle("Dir View")	#TODO:  Which title?
		self.view.setAnimated(False)
		self.view.setIndentation(20)
		self.view.setSortingEnabled(True)
		self.view.setColumnWidth(0,150)
		self.view.resize(1080, 640)

		# Attach Model to View
		self.view.setModel(self.model)
		self.view.setRootIndex(self.model.parent_index)

		# Misc
		self.node_stack	 = []

		# GUI
		windowlayout = QtWidgets.QVBoxLayout()
		windowlayout.addWidget(self.view)
		self.setLayout(windowlayout)

		QtCore.QMetaObject.connectSlotsByName(self)

		self.show()

	@QtCore.pyqtSlot(QtCore.QModelIndex)
	def on_treeView_fileTreeSelector_clicked(self, index):
		print('tree clicked: {}'.format(self.model.filePath(index)))
		self.model.traverseDirectory(index, callback=self.model.printIndex)


if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	ex = FileTreeSelectorDialog()
	sys.exit(app.exec_())
