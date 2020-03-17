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
	- scale thumbs to fit nicely
	- root folder display
	- large size thumbnail preview
	- semi transparent thumbs don't work well, may need another way to dif purchased and not
	- scroll to top
	- config on startup (build database, thumbs folder, assets folder)

DONE:
	- file count merge from previous
	- grayed out material thumbnails for not purchased materials - needs testing
	- double click thumb -> if asset not purchased -> take to the poliigon website
	- search bar
	- dark theme would be nice
'''

import os
import traceback, sys
import platform
from pathlib import PurePath
import webbrowser

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

from PyQt5.QtWidgets import (QWidget, QProgressDialog, QMessageBox ,QMainWindow ,QSplitter, QHBoxLayout, QFileSystemModel,QTreeView,QListView, QStyle,QLabel, QLineEdit, QComboBox, QPushButton, QApplication, QStyleFactory, QGridLayout, QVBoxLayout, QLayout, QSizePolicy, QProgressBar, QPlainTextEdit, QButtonGroup, QRadioButton, QCheckBox, QFrame, QSpacerItem ,QMenuBar, QMenu,QStatusBar,QAction)
from PyQt5.QtCore import Qt, QCoreApplication, QRect, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QSize,QModelIndex,QMetaObject,QDir,QDirIterator,QByteArray
from PyQt5.QtGui import QIcon,QPixmap,QStandardItemModel,QStandardItem,QImage, QPainter, QPalette, QColor


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
		
class IconListItem(QStandardItem):
	def __init__(self,*args, **kwargs):
		super().__init__(*args,**kwargs)
		self.thumbPath = ''
		self.purchased = False
		self.webSource = ''
		self.dimensions = None

	def setThumbPath(self, inPut):
		self.thumbPath = inPut

	def setPurchased(self, inPut):
		self.purchased = inPut

	def setWebSource(self):
		fLocation = os.path.dirname(self.thumbPath) + '/webSource.txt'
		try:
			f = open(fLocation, 'r')
			self.webSource = f.readline()
			f.close()
		except:
			pass

	def setDimensions(self):
		fLocation = os.path.dirname(self.thumbPath) + '/dimensions.txt'
		try:
			f = open(fLocation, 'r')
			self.dimensions = (f.readline()).strip('][').split(', ') 
			f.close()
		except:
			pass

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
	
	iconBase64 = b'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAIAAADYYG7QAAAABnRSTlMAAAAAAABupgeRAAAEYUlEQVRYhd2ZzW8bRRiHn9nvXX/E+SAFEkCqygVVolJBoFZCVIJKlUBccuGWK/8Afw4CAUVwgBsttIC49JBDewFVQsCptGkS7Di2d73r3RkOcRLbya7Xa/vCe9zdeeeZmd+88867ghmYwPIAos70vvSpHdiUVyitYFfQTJIeKpnGnyjeVNNxarg1dPPkYRIR7BM0C2MVAxLYFbxFDAdxyoNSxF38OmEb1PyBTBdvCauE0LI+U5KwjV8n7s4NSDdxF3GqaEbeJjImaBLsI3szBRI6ThV3EcPKi3JsSpFEBA26Byg5PZDAKuEtYbpnyGUirJ6PXyfys4WV2Yfh4C1iVdAy5SITwhaAXUHLjCMyIWwT1InDCYE0A7eGU0PPlIuSRD5+nZ4PHM2lN2Yukx7dQ2HFOYCE1t/Sup3lVynikKBB2BpShtCwq3iL6FaR5qNAloe7hOWN2dKZQwTQTNwazsJkEzwKZHosrI0XQXQYXVJFcGKGg7eEXR4zPBnT/Ide0G908kLTsloqRS/ArxN18sbfuMvBE+wSbuYmFfpgv/lCXBwS7NNt5gkkw6YI20RB/jA2DkjGdA8IGiSZofZw9Cpl5lRC0CDq9IWVqYpxQME+nb0x36yu8c4GMubut+w9Sf0siWjvAHhLUwBlr1GpwtUb3PiQ9fNIyWvXuHWTez8StAs6HErQDAu7Oiq9qHOs/yEzTC5dZfNj3t2gtgIgBLVlXr3ChYs06+xtn9235fXTy0ELD44lkfvcHrQXLvDBJq9fwyuPvjItLl3h5Yvcu8P3X/Do70l9Z0aINFt5iefO46amRKJUrb63sbr5kdAnTpELLJnAD3n4G/v/svwMldpItLc19XxFW18wxO7j+t3bows3lyXTNDotfrnF7w946zpvvk1lASl15EpJWy3prqlPnLoeWSEgQAiEYHeb777kwRbX369dvvxs1aw4OgUS6RkA9bE0lOLPh1bYfvGNVxzXVWmxMbcVEvUpLJEkQslpWYDZAM3UCgCpnEdsEgRqcjkV0lB7Dymxy2nHZNw6aPz8w/bXn5FMfH8tBJSEtLYJvX4GPWCyF7Xub21/9Wnr/paKU/LJ2QMBqH7MdKrYC4CS0v/rj6fffN746XbSST9c5wZ0SCUJ9um2Zdl+evOTxq93ou3HY5pkp7NDObVdpro2enS0d/DrueCESE3QDk23zk7QlKL56Li2NN0MjfhNs0lu4rMDSmEZn+SnAkmJkogcCYOmI3Ps55zXIJUMBraB7mWPuIvQ0Y2T0ZyZflTOYTgkUWqE1Ey8ZcqrWJkToyRRh/bOYBfDSxb59Lrjr9KagbOAVZ7HVfqUhpSk2+xfWdxaqkfAdDDOYVfmXGwYonVAEJ9asto6VunkwUzLMZm7LGd5UNPHzCUTFKzmve0nLunNGWjyomcBIEUcYrpzKgsX+rUQ+SQ9dAPNSC2ct3fx66kVrXT7n/xaGDDdxlvErgBHhZtoGn9TAx06md3vqf8AWEoJPWt5ZeMAAAAASUVORK5CYII='
	
	

	def __init__(self):
		super().__init__()
		self.left = 150
		self.top = 150
		self.width = 960
		self.height = 480
		self.rootPath = 'C:/poliigon/'
		self.searchPath = 'Y:/Maps/Poliigon/'
		#self.searchPath = 'Y:/Maps/Poliigon_com/'
		self.dbPath = 'poliigon.json'
		self.db = TinyDB(self.dbPath, storage=CachingMiddleware(JSONStorage))
		self.dbQuery = Query()
		self.icon = self.iconFromBase64(self.iconBase64)
		self.setupUi(self)

	def setupUi(self, MainWindow):
		self.setGeometry(self.left, self.top, self.width, self.height)
		self.setWindowIcon(self.icon)
		self.setWindowTitle('poliigon asset browser')
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

		self.searchBar = QLineEdit('' , self)
		self.searchBar.setMinimumHeight(23)
		self.searchBar.setObjectName('searchBar')
		self.searchBar.setPlaceholderText('Search')
		
		self.gridLayoutControlls.addWidget(self.codecLabel, 0, 0, 1, 1, Qt.AlignTop)
		self.gridLayoutControlls.addWidget(self.alphaLabel, 0, 1, 1, 1, Qt.AlignTop)
		self.gridLayoutControlls.addWidget(self.searchBar, 0, 2, 1, 1, Qt.AlignTop)
		
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
	def on_searchBar_editingFinished(self):
		print('editing finished')

	@pyqtSlot()
	def on_searchBar_returnPressed(self):
		print('return pressed')

	@pyqtSlot(str)
	def on_searchBar_textEdited(self, e):
		print('text edited', e)
		if len(e) > 3:
			self.filesmodel.clear()
			#thisDir = (self.dirModel.filePath(self.treeView.currentIndex()))
			allFileList = self.dirModel.allThumbFiles

			fileList = []
			for f in allFileList:
				#print(e, ' ', os.path.basename(f))
				if e.lower() in os.path.basename(f.lower()):
					fileList.append(f)


			#placeholder thumbnail, gray box
			placeholder = QPixmap(self.listView.iconSize())
			placeholder.fill(Qt.gray)

			#fill all items with placeholder thumbnail which is a gray box
			for i in range(len(fileList)):
				newItem = IconListItem(QIcon(placeholder), os.path.basename(fileList[i]))
				newItem.setToolTip(fileList[i])
				newItem.setThumbPath(fileList[i])
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

	@pyqtSlot()
	def on_Test1_clicked(self):
		print('test1 clicked')
		print(self.dirModel.totalFileCount)

	@pyqtSlot()
	def on_actionUpdateDB_triggered(self):
		print('clicked update')


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
		thisItem = (self.filesmodel.itemFromIndex(self.listView.currentIndex()))
		thisItem.setWebSource()
		thisItem.setDimensions()
		print(thisItem.toolTip())
		print(thisItem.purchased)
		print(thisItem.webSource)
		print(thisItem.dimensions)

		if thisItem.purchased:
			#create material in max here
			pass
		else:
			webbrowser.open_new(thisItem.webSource)
	
	
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
			newItem = IconListItem(QIcon(placeholder), os.path.basename(fileList[i]))
			newItem.setToolTip(fileList[i])
			newItem.setThumbPath(fileList[i])
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
				item.setPurchased(True)
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

	def iconFromBase64(self, base64):
		pixmap = QPixmap()
		pixmap.loadFromData(QByteArray.fromBase64(base64))
		icon = QIcon(pixmap)
		return icon

if __name__ == '__main__':
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	# Now use a palette to switch to dark colors:
	palette = QPalette()
	palette.setColor(QPalette.Window, QColor(53, 53, 53))
	palette.setColor(QPalette.WindowText, Qt.white)
	palette.setColor(QPalette.Base, QColor(25, 25, 25))
	palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
	palette.setColor(QPalette.ToolTipBase, Qt.white)
	palette.setColor(QPalette.ToolTipText, Qt.white)
	palette.setColor(QPalette.Text, Qt.white)
	palette.setColor(QPalette.Button, QColor(53, 53, 53))
	palette.setColor(QPalette.ButtonText, Qt.white)
	palette.setColor(QPalette.BrightText, Qt.red)
	palette.setColor(QPalette.Link, QColor(42, 130, 218))
	palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
	palette.setColor(QPalette.HighlightedText, Qt.black)
	app.setPalette(palette)
	ex = MainWindow()
	sys.exit(app.exec_())
