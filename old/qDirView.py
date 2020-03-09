import sys
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QHBoxLayout, QListView, QTableView 
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QModelIndex, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QSize, QPersistentModelIndex, QDir, QDirIterator 
import random

class viewerSystemModel(QFileSystemModel):
	def __init__(self):
		super().__init__()

		
	def columnCount(self, parent = QModelIndex()):
		return super(viewerSystemModel, self).columnCount()+1
	'''
	def data(self, index, role):
		self.n = len(QDir(self.filePath(index)).entryInfoList())
		#it = QDirIterator((self.filePath(index)), ['*_tn.jpg'],  QDir.Files, QDirIterator.Subdirectories)
		#while it.hasNext():
		#	print (it.next())
		
		#print(self.n.filePath())
		print('display role' + str(random.randint(0, 10000)))
		# if index.column() == self.columnCount() - 1:
			# if role == Qt.DisplayRole:
				# if self.n > 0:
					# return (self.n - 2)		
				# else:
					# return('-')
			# if role == Qt.TextAlignmentRole:
				# return Qt.AlignHCenter

		return super(viewerSystemModel, self).data(index, role)
	'''
	def setData(self, index, value, role):
		print(self.filePath(index))
		i = 0
		it = QDirIterator((self.filePath(index)), ['*_tn.jpg'],  QDir.Files, QDirIterator.Subdirectories)
		while it.hasNext():
			i=i+1
		#print(i)
		if index.column() == self.columnCount() - 1:
			self.layoutAboutToBeChanged.emit()
			value = str(i)
			self[index]=str(i)
			self.layoutChanged.emit()
			return True
		
		return super(viewerSystemModel, self).setData( index, i, role)
		


class App(QWidget):

	def __init__(self):
		super().__init__()
		self.title = 'PyQt5 file system view - pythonspot.com'
		self.left = 150
		self.top = 150
		self.width = 960
		self.height = 480
		self.initUI()
	
	def initUI(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)
		
		#self.model = QFileSystemModel()
		self.rootPath = 'C:/poliigon/'
		
		self.dirModel = viewerSystemModel()
		self.dirModel.setRootPath(self.rootPath)
		
		self.fileModel = QFileSystemModel()
		self.fileModel.setRootPath(self.rootPath)
		
		self.tree = QTreeView()
		self.tree.setModel(self.dirModel)
		self.tree.setRootIndex(self.dirModel.index(self.rootPath))
		
		self.tree.setAnimated(False)
		self.tree.setIndentation(20)
		self.tree.setSortingEnabled(True)
		self.tree.hideColumn(1)
		self.tree.hideColumn(2)
		self.tree.hideColumn(3)
		self.tree.setColumnWidth(0,480)
		
		self.dirModel.sort(0, Qt.AscendingOrder)
		
		self.fileList = QListView()
		self.fileList.setModel(self.fileModel)
		self.fileList.setRootIndex(self.fileModel.index(self.rootPath))
		self.fileList.setViewMode(1)
		self.fileList.setWordWrap(True)
		self.fileList.setGridSize(QSize(80,80))
		
		#self.tree.showColumn(4)
		
		self.tree.setWindowTitle("Dir View")
		self.tree.resize(640, 480)
		
		windowLayout = QHBoxLayout()
		windowLayout.addWidget(self.tree)
		windowLayout.addWidget(self.fileList)
		self.setLayout(windowLayout)
		#self.dirModel.directoryLoaded.connect(self.printDir)
		self.tree.selectionModel().currentChanged.connect(self.item_selection_changed_slot)
		self.tree.doubleClicked.connect(self.test)
		self.show()
	
	def printDir(self, d):
		print(d)
	
	def item_selection_changed_slot(self, curr, prev):
		#print(e.row())
		print(curr.row())
		#file_path=QDir(self.tree.model().filePath(curr)).entryInfoList()
		#for f in file_path:
		#	print(f.filePath())

	def test(self, signal):

		#print(signal)
		file_path=self.tree.model().filePath(signal)
		#print(file_path)
		it = QDirIterator(file_path, ['*_tn.jpg'],  QDir.Files, QDirIterator.Subdirectories)
		while it.hasNext():
			print (it.next())
		#self.fileList.setRootIndex(self.fileModel.setRootPath(file_path))
	
	def selectionChanged(self):
		print(e)
	
if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = App()
	sys.exit(app.exec_())
