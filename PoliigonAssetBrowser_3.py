'''
sources:
	multithreading:
	https://www.learnpyqt.com/courses/concurrent-execution/multithreading-pyqt-applications-qthreadpool/
	
	thumbnail framework:
	https://stackoverflow.com/questions/26829754/how-to-use-the-threads-to-create-the-images-thumbnail

	transparent icon:
	https://forum.qt.io/topic/64597/qpixmap-and-opacity-and-transparency

TODO:
	- convert to pyside to be usable in 3dsmax
	- double click thumb -> build material
	- double click thumb -> if asset not purchased -> take to the poliigon website
	- scale thumbs to fit nicely
	- search bar
	- root folder display
	- dark theme would be nice
	- large size thumbnail preview

DONE:
	- file count merge from previous
	- grayed out material thumbnails for not purchased materials - needs testing
'''

import os
import traceback, sys
import platform
from pathlib import PurePath

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

from PyQt5.QtWidgets import (QWidget, QProgressDialog, QMessageBox ,QMainWindow ,QSplitter, QHBoxLayout, QFileSystemModel,QTreeView,QListView, QStyle,QLabel, QLineEdit, QComboBox, QPushButton, QApplication, QStyleFactory, QGridLayout, QVBoxLayout, QLayout, QSizePolicy, QProgressBar, QPlainTextEdit, QButtonGroup, QRadioButton, QCheckBox, QFrame, QSpacerItem ,QMenuBar, QMenu,QStatusBar,QAction)
from PyQt5.QtCore import Qt, QCoreApplication, QRect, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QSize,QModelIndex,QMetaObject,QDir,QDirIterator
from PyQt5.QtGui import QIcon,QPixmap,QStandardItemModel,QStandardItem,QImage, QPainter


class WorkerSignals(QObject):
	finished = pyqtSignal()
	error = pyqtSignal(tuple)
	result = pyqtSignal(object)
	progressTuple = pyqtSignal(tuple)
	progressInt = pyqtSignal(int)



class Worker(QRunnable):
	#def __init__(self, fn, fileList, size, i, *args, **kwargs):
	def __init__(self, fn, progressType='tuple', *args, **kwargs):
		super(Worker, self).__init__()

		# Store constructor arguments (re-used for processing)
		self.fn = fn
		self.args = args
		self.kwargs = kwargs
		self.signals = WorkerSignals()
		#self.fileList = fileList
		#self.size = size
		#self.i = i


		# Add the callback to our kwargs
		self.kwargs['progress_callback'] = None
		if progressType == 'tuple':
			self.kwargs['progress_callback'] = self.signals.progressTuple
		elif progressType == 'int':
			self.kwargs['progress_callback'] = self.signals.progressInt
	@pyqtSlot()
	def run(self):
		'''
		Initialise the runner function with passed args, kwargs.
		'''
		
		# Retrieve args/kwargs here; and fire processing using them
		try:
			#result = self.fn(self.fileList, self.size, self.i, *self.args, **self.kwargs)
			result = self.fn(*self.args, **self.kwargs)
		except:
			traceback.print_exc()
			exctype, value = sys.exc_info()[:2]
			self.signals.error.emit((exctype, value, traceback.format_exc()))
		else:
			self.signals.result.emit(result)  # Return the result of the processing
		finally:
			self.signals.finished.emit()  # Done
		
class viewerSystemModel(QFileSystemModel):
	def __init__(self):
		super().__init__()
		self.fileCount	= {}
		self.thumbFiles = {}
		self.totalFileCount = 0
		self.allThumbFiles = []
		
		
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

	def getTotalFiles(self):
		fileList = []
		it = QDirIterator((self.rootPath()), ['*_tn.jpg'],  QDir.Files, QDirIterator.Subdirectories)
		while it.hasNext():
			file = it.next()
			fileList.append(file)

		self.totalFileCount = len(fileList)
		self.allThumbFiles = fileList


class MainWindow(QMainWindow):
	
	def __init__(self):
		super().__init__()
		self.left = 150
		self.top = 150
		self.width = 960
		self.height = 480
		self.rootPath = 'C:/poliigon/'
		#self.searchPath = 'Y:/Maps/Poliigon/'
		self.searchPath = 'Y:/Maps/Poliigon_com/'
		self.dbPath = 'poliigon.json'
		self.db = TinyDB(self.dbPath, storage=CachingMiddleware(JSONStorage))
		self.letRun = False
		self.dbQuery = Query()
		self.setupUi(self)

	def setupUi(self, MainWindow):
		self.setGeometry(self.left, self.top, self.width, self.height)
		self.threadpool = QThreadPool()
		#self.threadpool.setMaxThreadCount(1)
		self.threadpool.maxThreadCount()
		
		self.centralwidget = QWidget(MainWindow)		
		self.verticalLayout = QVBoxLayout(self.centralwidget)
		self.verticalLayout.setContentsMargins(11, 11, 11, 11)
		self.verticalLayout.setSpacing(11)

		self.gridLayoutControlls = QGridLayout()
		self.codecLabel = QPushButton('Test 1', self)
		self.codecLabel.setMinimumSize(80,23)
		self.codecLabel.setObjectName('Test1')
		self.alphaLabel = QPushButton('Test 2' , self)
		self.alphaLabel.setMinimumSize(80,23)
		self.frameRateLabel = QLineEdit('Search' , self)
		self.frameRateLabel.setMinimumHeight(23)
		self.gridLayoutControlls.addWidget(self.codecLabel, 0, 0, 1, 1, Qt.AlignTop)
		self.gridLayoutControlls.addWidget(self.alphaLabel, 0, 1, 1, 1, Qt.AlignTop)
		self.gridLayoutControlls.addWidget(self.frameRateLabel, 0, 2, 1, 1, Qt.AlignTop)
		
		self.dirModel = viewerSystemModel()
		self.dirModel.setRootPath(self.rootPath)
		self.dirModel.getTotalFiles()

		self.filesmodel = QStandardItemModel()

		self.treeView = QTreeView()
		self.treeView.setModel(self.dirModel)
		self.treeView.setObjectName('treeView')
		#homeIndex = self.dirModel.parent(self.dirModel.index(self.rootPath))
		#self.treeView.setRootIndex(homeIndex)
		self.treeView.setRootIndex(self.dirModel.index(self.rootPath))
		self.treeView.resizeColumnToContents(0)
		self.treeView.setRootIsDecorated(True)
		self.treeView.setHeaderHidden(False)
		self.treeView.hideColumn(1)
		self.treeView.hideColumn(2)
		self.treeView.hideColumn(3)
		self.treeView.setColumnWidth(0,280)
		
		self.listView = QListView()
		self.listView.setModel(self.filesmodel)
		self.listView.setObjectName('listView')
		self.listView.setViewMode(1)
		self.listView.setResizeMode(1)
		self.listView.setWrapping(True)
		self.listView.setWordWrap(True)
		self.listView.setGridSize(QSize(180,180))
		self.listView.setUniformItemSizes(True)
		self.listView.setIconSize(QSize(150,150))

		self.splitterLayout = QSplitter()
		self.splitterLayout.setOrientation(Qt.Horizontal)
		self.splitterLayout.addWidget(self.treeView)
		self.splitterLayout.addWidget(self.listView)
		
		self.windowLayout = QGridLayout()
		self.windowLayout.addWidget(self.splitterLayout)

		self.verticalLayout.addLayout(self.gridLayoutControlls, stretch=0)
		self.verticalLayout.addLayout(self.windowLayout)
		self.verticalLayout.setStretch(0,0)
		self.verticalLayout.setStretch(1,1)
		
		MainWindow.setCentralWidget(self.centralwidget)
		
		self.menubar = QMenuBar(MainWindow)
		self.menubar.setGeometry(0, 0, self.width, 21)
		self.menubar.setObjectName("menubar")
		
		self.menuFile = QMenu('Preferences', self.menubar)
		self.menuFile.setObjectName("menuFile")
		
		MainWindow.setMenuBar(self.menubar)
		self.statusbar = QStatusBar(MainWindow)
		self.statusbar.setObjectName("statusbar")
		MainWindow.setStatusBar(self.statusbar)
		
		self.actionReBuildDB = QAction('Re-Build DB', MainWindow)
		self.actionReBuildDB.setObjectName("actionReBuildDB")

		self.actionUpdateDB = QAction('Update DB', MainWindow)
		self.actionUpdateDB.setObjectName("actionUpdateDB")

		self.menuFile.addAction(self.actionReBuildDB)
		self.menuFile.addAction(self.actionUpdateDB)
		self.menubar.addAction(self.menuFile.menuAction())

		#self.listView.doubleClicked.connect(self.test)
		QMetaObject.connectSlotsByName(self) # auto connects defs on_Object_signal to object signal !use setObjectName, won't work with var name

		self.show()
	
	
	@pyqtSlot()
	def on_Test1_clicked(self):
		print('test1 clicked')
		print(self.dirModel.totalFileCount)

	@pyqtSlot()
	def on_actionUpdateDB_triggered(self):
		print('clicked update')

	
	def updatePorgressWindow(self,tup):
		#print('thread end')
		self.progressWindow.setValue(self.progressWindow.value() + 1)

	def endProgressWindow(self):
		print('ended')
		self.threadpool.clear()
		self.threadpool.maxThreadCount()
		self.progressWindow.close()
		self.db.close()
		self.db = TinyDB(self.dbPath, storage=CachingMiddleware(JSONStorage))

	@pyqtSlot()
	def on_actionReBuildDB_triggered(self):
		
		doUpdateDB = False
		try:
			print('in try')
			self.db.close()
			os.remove(self.dbPath)
			self.db = TinyDB(self.dbPath, storage=(CachingMiddleware(JSONStorage)))
			doUpdateDB = True
		except:
			self.messageBox = QMessageBox.critical(self.centralwidget, 'DB Update Error', 'The database is currently in use elsewhere.\nPlease close all other asset browsers and try again.')

		
		if doUpdateDB:
			allFiles = self.collectPurchasedFiles()
			
			#QProgressDialog(const QString &labelText, const QString &cancelButtonText, int minimum, int maximum, QWidget *parent = nullptr, Qt::WindowFlags f = Qt::WindowFlags())
			self.progressWindow = QProgressDialog('Updating Database...', '', 0, self.dirModel.totalFileCount, self.centralwidget, Qt.Popup)
			self.progressWindow.setObjectName('progressWindow')
			self.progressWindow.setWindowModality(Qt.WindowModal)
			self.progressWindow.setCancelButton(None)
			self.progressWindow.show()

			
			self.threadpool.setMaxThreadCount(1)
			worker = Worker(self.updateDB,'int', allFiles)
			worker.signals.progressInt.connect(self.progressWindow.setValue)
			worker.signals.finished.connect(self.endProgressWindow)
			self.threadpool.start(worker)
		

	#update db should have all instances of the asset folder 3K 1K HiRes, add those types to db as well
	#error in matching such as tiles04 matches to tiles042 and tiles043, need to do exact match
	def updateDB(self, searchInFiles, progress_callback):
		for i in range(self.dirModel.totalFileCount):
			file = self.dirModel.allThumbFiles[i]
			filename, file_extension = os.path.splitext(file)
			assetsList = []
			assetsResList = []
			#Get filename from path, remove spaces and remove the '_tn' from name
			searchName = (((PurePath(filename).stem).replace(' ',''))[:-3])
			for j in range(len(searchInFiles)):
				thisFile = searchInFiles[j]
				if searchName == (os.path.basename(thisFile).split('_'))[0]:
					assetsList.append(thisFile)
					assetRes = os.path.basename(thisFile).split('_')
					if len(assetRes) > 1:
						assetsResList.append(assetRes[-1])
					else:
						assetsResList.append('HIRES')

			if len(assetsList) > 0:
				self.db.insert({'thumb': file, 'assets': assetsList, 'assetsRes': assetsResList})
			
			#need this here, update every 20th otherwise buffer overrun error
			if i%20==0:
				try:
					progress_callback.emit(i)
				except:
					print('error')


	def collectPurchasedFiles(self):
		filesDir = []
		it = QDirIterator(self.searchPath, (QDir.Dirs | QDir.NoDotAndDotDot ),  QDirIterator.Subdirectories)
		while it.hasNext():
			thisDir = it.next()
			filesInDir = [f.path for f in os.scandir(thisDir) if f.is_file()]
			if len(filesInDir) > 0:
				filesDir.append(thisDir)
		return filesDir


	@pyqtSlot(QModelIndex)
	def on_listView_doubleClicked(self, index):
	#def test(self, index):
		thisItem = (self.filesmodel.itemFromIndex(self.listView.currentIndex()))
		print(thisItem.toolTip())
		self.getFileNumber(thisItem.toolTip())
	
	
	@pyqtSlot(QModelIndex)
	def on_treeView_clicked(self,index):
		self.filesmodel.clear()
		thisDir = (self.dirModel.filePath(self.treeView.currentIndex()))
		fileList = self.dirModel.getFilesFromPath(thisDir)

		#placeholder thumbnail, gray box
		placeholder = QPixmap(self.listView.iconSize())
		placeholder.fill(Qt.gray)

		#fill all items with placeholder thumbnail which is a gray box
		for i in range(len(fileList)):
			newItem = QStandardItem(QIcon(placeholder), os.path.basename(fileList[i]))
			newItem.setToolTip(fileList[i])
			newItem.setEditable(False)
			#self.filesmodel.setItem(i, QStandardItem(QIcon(placeholder), os.path.basename(fileList[i])))
			self.filesmodel.setItem(i, newItem)

		#start workers for each thumbnail to generate
		self.threadpool.clear()
		self.threadpool.maxThreadCount()
		for i in range(len(fileList)):
			worker = Worker(self.List,'tuple', fileList[i], self.listView.iconSize(), i)
			worker.signals.progressTuple.connect(self.setThumbs)
			self.threadpool.start(worker)


	def List(self, file, size, i, progress_callback):
		originalImage = QImage(file)
		if originalImage.isNull() == False:
			scaledImage = QImage(originalImage.scaled(size))
			if scaledImage.isNull() == False:
				progress_callback.emit((i, scaledImage))

	
	def setThumbs(self, tup):
		index, img = tup
		item = self.filesmodel.item(index)
		if item != None:
			
			if self.db.contains(self.dbQuery.thumb == item.toolTip()):
				icon = QIcon(QPixmap.fromImage(img))
			else:
				transImg = self.transparentIcon(img)
				icon = QIcon(QPixmap.fromImage(transImg))
				
			item.setIcon(icon)


	def getFileNumber(self, path):
		def getExt(path):
			filename, file_extension = os.path.splitext(path)
			return(file_extension)
		DIR =  os.path.dirname(os.path.abspath(path))
		#print (len([name for name in os.listdir(DIR) if os.path.isfile(name) and getExt(path)!='.txt']))
		return (len([name for name in os.listdir(DIR) if os.path.isfile(name) and getExt(path)!='.txt']))


	def transparentIcon (self, input):
		input = QPixmap.fromImage(input)
		image = QImage(input.size(),QImage.Format_ARGB32_Premultiplied)
		image.fill(Qt.transparent)
		p = QPainter(image)
		p.setOpacity(0.5)
		p.drawPixmap(0,0,input)
		p.end()
		return image
	
	
	#expects full file path	
	def getStemFromPath(self, path):
		return PurePath(os.path.dirname(os.path.abspath(path))).stem

if __name__ == '__main__':
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	ex = MainWindow()
	sys.exit(app.exec_())
