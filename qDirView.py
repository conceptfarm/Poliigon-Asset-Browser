import sys
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QHBoxLayout, QListView, QTableView 
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QModelIndex, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QSize, QPersistentModelIndex, QDir, QDirIterator ,QVariant
import random


class viewerSystemModel(QFileSystemModel):
	def __init__(self):
		super().__init__()
		self.fileCount	= {}
		self.thumbFiles = {}
		
	def columnCount(self, parent = QModelIndex()):
		return super(viewerSystemModel, self).columnCount()+1

	def data(self, index, role):
		if index.column() == self.columnCount() - 1:
			if role == Qt.DisplayRole:
				return (self.getFileCount(index))
			#if role == Qt.TextAlignmentRole:
			#	return Qt.AlignHCenter

		return super(viewerSystemModel, self).data(index, role)
		
	def getFileCount(self, index):
		if index in self.fileCount:
			#print('present', (self.fileCount[index]))
			return str(self.fileCount[index])
		else:
			#print(self.filePath(index))
			i = 0
			fileList = []
			it = QDirIterator((self.filePath(index)), ['*_tn.jpg'],  QDir.Files, QDirIterator.Subdirectories)
			while it.hasNext():
				i+=1
				file = it.next()
				fileList.append(file)
				
			if i == 0:
				i = '-'
			#print('not present')
			self.fileCount[index] = i
			self.thumbFiles[(self.filePath(index))] = fileList
			return str(self.fileCount[index])
	
	
	def getFilesFromPath(self, path):
		if path in self.thumbFiles:
			return (self.thumbFiles[path])
		else:
			return None

'''
class viewerSystemModel(QFileSystemModel):
	def __init__(self):
		super().__init__()
		self.fileCount	= {}

		
	def columnCount(self, parent = QModelIndex()):
		return super(viewerSystemModel, self).columnCount()+1
	
	def data(self, index, role):
		if not index.isValid():
			return None
		
		if index.column() == self.columnCount() - 1:
			
			if role == Qt.DisplayRole:
				#return QVariant('string')
				return QString(self.getFileCount(index))
			else:
				return QString('string')
			
			#if role == Qt.TextAlignmentRole:
				#return Qt.AlignHCenter

		return super(viewerSystemModel, self).data(index, role)
	
	def setData(self, index, value, role):
		if (index.column() == 4):
			self.fileCount[index] = value
			self.dataChanged.emit(index, index)
			print('setData(): {}'.format(value), index)
			return 'something'
		return QtWidgets.QFileSystemModel.setData(self, index, value, role)
	
	def flags(self, index):
		if not index.isValid():
			return None
			
		if index.column() == 4:
			flags = Qt.NoItemFlags
		else:
			flags = super(viewerSystemModel, self).flags(index)
		return flags

	def getFileCount(self, index):
		if index in self.fileCount:
			#print('present', (self.fileCount[index]))
			return str(self.fileCount[index])
		else:
			i = 0
			it = QDirIterator((self.filePath(index)), ['*_tn.jpg'],  QDir.Files, QDirIterator.Subdirectories)
			while it.hasNext():
				i=i+1
				it.next()
			if i == 0:
				i = '-'
			#print(' not present')
			self.fileCount[index] = i
			#return QtCore.Qt.Checked
			return str(self.fileCount[index])
	'''	

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
		self.tree.setColumnWidth(0,280)
		
		self.dirModel.sort(0, Qt.AscendingOrder)
		
		self.fileList = QListView()
		self.fileList.setModel(self.fileModel)
		self.fileList.setRootIndex(self.fileModel.index(self.rootPath))
		self.fileList.setViewMode(1)
		self.fileList.setResizeMode(1)
		self.fileList.setWrapping(True)
		self.fileList.setWordWrap(True)
		self.fileList.setGridSize(QSize(180,180))
		self.fileList.setUniformItemSizes(True)
		
		self.tree.showColumn(4)
		
		self.tree.setWindowTitle("Dir View")
		self.tree.resize(640, 480)
		
		windowLayout = QHBoxLayout()
		windowLayout.addWidget(self.tree)
		windowLayout.addWidget(self.fileList)
		self.setLayout(windowLayout)
		#self.dirModel.directoryLoaded.connect(self.printDir)
		self.tree.selectionModel().currentChanged.connect(self.item_selection_changed_slot)
		#self.tree.doubleClicked.connect(self.test)
		self.show()
	
	def printDir(self, d):
		print(d)
	
	'''
	QModelIndex TreeModel::index(int row, int column, const QModelIndex &parent) const
{
    if (!hasIndex(row, column, parent))
        return QModelIndex();

    TreeItem *parentItem;

    if (!parent.isValid())
        parentItem = rootItem;
    else
        parentItem = static_cast<TreeItem*>(parent.internalPointer());

    TreeItem *childItem = parentItem->child(row);
    if (childItem)
        return createIndex(row, column, childItem);
    return QModelIndex();
}
	'''
	
	def item_selection_changed_slot(self, curr, prev):
		#print(e.row())
		#print(curr.row(),' x ', curr.column())
		#print('current ', curr)
		file_path=self.tree.model().filePath(curr)
		#print('index hash' , self.dirModel.index(file_path))
		
		self.fileList.setRootIndex(self.fileModel.setRootPath(file_path))
		print(self.dirModel.getFilesFromPath(file_path))
		#print('hash ', file_path, hash(file_path))
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