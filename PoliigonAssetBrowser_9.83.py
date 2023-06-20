'''
sources:
	multithreading:
	https://www.learnpyqt.com/courses/concurrent-execution/multithreading-pyqt-applications-qthreadpool/
	
	thumbnail framework:
	https://stackoverflow.com/questions/26829754/how-to-use-the-threads-to-create-the-images-thumbnail

	transparent icon:
	https://forum.qt.io/topic/64597/qpixmap-and-opacity-and-transparency
	
	reimplemented model filter
	https://stackoverflow.com/questions/39488901/change-qsortfilterproxymodel-behaviour-for-multiple-column-filtering

TODO:
	- move iconListView, IconListModel, IconListItem and LargePreview to a new module
	- convert to pyside to be usable in 3dsmax
	- root folder display
	- large size thumbnail preview
	- config on startup (build database, thumbs folder, assets folder)
	- root item should have the count data and all the thumb images, so check on that
	
DONE:
	- file count merge from previous
	- grayed out material thumbnails for not purchased materials - needs testing
	- double click thumb -> if asset not purchased -> take to the poliigon website
	- double click thumb -> if purchased -> build material
	- search bar
	- dark theme would be nice
	- scroll to top
	- semi transparent thumbs don't work well, may need another way to dif purchased and not
	- scale thumbs to fit nicely - done - issue: when number of items is less than can fit on the row -> scaling looks weird
	- checkbox -> display only purchased
	- fix pngs with jpeg extension

'''

#Python Classes
import os
import traceback, sys
#import platform
from pathlib import PurePath, Path
#import webbrowser
#from math import floor
#import time
import configparser
import re
#import random
import json
import glob

from PIL import Image
from io import BytesIO
import base64

#tinyDB Classes
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.storages import MemoryStorage
from tinydb.middlewares import CachingMiddleware

#Custom Classes
from lib.poliigonGenerateResolutionsClass import GenerateResolutions
from lib.poliigonGenerateSmallThumbsClass import GenerateSmallThumbs
from lib.poliigonConfigDialogClass import PoliigonBrowserConfigDialog
from lib.poliigonImageCollection import imageCollectionBase64
from lib.poliigonBase64ToImage import Base64ToImage
from lib.poliigonDarkPalette import QtDarkPalette
#from lib.poliigonMaxScriptClass import MaxScriptCreator
from lib.poliigonIconBrowserClasses import IconListItem, IconListView, IconListModel, LargePreviewWindow
from lib.poliigonFileBrowserClasses import FileProxyModel, FileSystemModel

#PyQt Classes
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

b64ToImage = Base64ToImage()
icons = imageCollectionBase64()
palette = QtDarkPalette()
appIcon = None

# def getExt(path):
# 	filename, file_extension = os.path.splitext(path)
# 	return(file_extension)

class NthIterator:
	def __init__(self, data, nth):
		self.nth = nth
		self.data = data
		self.i = 0

	def __iter__(self):
		self.i = 0
		return self

	def getI(self):
		return (self.i-self.nth)

	def __next__(self):
		try:
			x = self.i
			self.i += self.nth
			return self.data[x]
		except:
			raise StopIteration

	def genData(self,start, stop):
		count = start
		while count < stop:
			if count > len(self.data)-1:
				break
			yield self.data[count]
			count += 1
			
	def nextBatch(self):
		while True:
			x = self.i
			
			if self.i > len(self.data):
				raise StopIteration
			
			self.i += self.nth
			res = []
			for item in self.genData(x,self.i):
				res.append(item)
			return res

class WorkerSignals(QObject):
	finished = pyqtSignal()
	error = pyqtSignal(tuple)
	result = pyqtSignal(object)
	progressTuple = pyqtSignal(tuple)
	progressInt = pyqtSignal(int)
	progressMin = pyqtSignal(int)
	progressMax = pyqtSignal(int)
	progressFormat = pyqtSignal(str)
	progressLabel = pyqtSignal(str)
	progressNone = pyqtSignal()

class Worker(QRunnable):
	def __init__(self, fn, progressType=None, *args, **kwargs):
		super().__init__()

		# Store constructor arguments (re-used for processing)
		self.setAutoDelete(True)
		self.fn = fn
		self.args = args
		self.kwargs = kwargs
		self.signals = WorkerSignals()

		# Add the callback to our kwargs
		self.kwargs['progress_callback'] = None
		if progressType == 'tuple':
			self.kwargs['progress_callback'] = self.signals.progressTuple
		elif progressType == 'int':
			self.kwargs['progress_callback'] = self.signals.progressInt
		elif progressType == None:
			self.kwargs['progress_callback'] = self.signals.progressNone
		
		self.kwargs['progress_setmin'] = self.signals.progressMin
		self.kwargs['progress_setmax'] = self.signals.progressMax
		self.kwargs['progress_setformat'] = self.signals.progressFormat
		self.kwargs['progress_setlabel'] = self.signals.progressLabel
	
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

class MainWindow(QMainWindow):
	
	def __init__(self, poliigonThumbPath, poliigonMapsPath):
		super().__init__()
		self.left = 150
		self.top = 150
		self.width = 960
		self.height = 480
		self.poliigonThumbPath = poliigonThumbPath
		self.poliigonMapsPath = poliigonMapsPath
		self.dbPath = os.path.join(self.poliigonThumbPath, 'poliigon.db')
		self.db = TinyDB(self.dbPath, storage=CachingMiddleware(JSONStorage))
		self.dbQuery = Query()
		self.statusBarProgress = QProgressBar()
		self.statusBarProgress.hide()
		self.statusBarProgress.setFixedHeight(15)
		#self.icon = icons.qIconFromBase64(icons.appIconBase64)
		self.setupUi(self)

	def setupUi(self, MainWindow):
		self.setGeometry(self.left, self.top, self.width, self.height)
		self.setWindowIcon(appIcon)
		self.setWindowTitle('poliigon asset browser')
		self.threadpool = QThreadPool().globalInstance()
		self.threadpoolQLength = 0
		self.threadpool.setMaxThreadCount(5)
		#self.threadpool.maxThreadCount()
		
		self.centralwidget = QWidget(MainWindow)		
		self.verticalLayout = QVBoxLayout(self.centralwidget)
		self.verticalLayout.setContentsMargins(11, 11, 11, 11)
		self.verticalLayout.setSpacing(11)

		self.gridLayoutControlls = QGridLayout()
		
		self.filterPurchased = QPushButton('Filter Available', self)
		self.filterPurchased.setMinimumSize(80,23)
		self.filterPurchased.setObjectName('filterPurchased')
		self.filterPurchased.setCheckable(True)
		#self.filterPurchased.clicked[bool].connect(self.showDebugLog)

		self.searchBar = QLineEdit('' , self)
		self.searchBar.setMinimumHeight(23)
		self.searchBar.setObjectName('searchBar')
		self.searchBar.setPlaceholderText('Search')
		
		self.gridLayoutControlls.addWidget(self.filterPurchased, 0, 0, 1, 1, Qt.AlignTop)
		self.gridLayoutControlls.addWidget(self.searchBar, 0, 2, 1, 1, Qt.AlignTop)
		
		self.fileModel = FileSystemModel(self.poliigonThumbPath)
		#self.fileModel.getTotalFiles()
		#self.fileModel.setFilter( QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs)

		home_index = self.fileModel.parent(self.fileModel.index(self.poliigonThumbPath))
		home_path = self.fileModel.filePath(home_index)
		root_index = self.fileModel.setRootPath(home_path)

		self.fileProxyModel = FileProxyModel()
		self.fileProxyModel.setSourceModel(self.fileModel)
		self.fileProxyModel.setIndexPath(QPersistentModelIndex(self.fileModel.index(self.poliigonThumbPath)))

		self.treeView = QTreeView()
		self.treeView.setModel(self.fileProxyModel)
		self.treeView.setObjectName('treeView')
		self.treeView.setRootIndex(self.fileProxyModel.mapFromSource(root_index))
		self.treeView.expandAll()
		self.treeView.resizeColumnToContents(0)
		self.treeView.hideColumn(1)
		self.treeView.hideColumn(2)
		self.treeView.hideColumn(3)
		self.treeView.setColumnWidth(0,280)
		
		self.iconListModel = IconListModel()

		self.iconListView = IconListView(self.centralwidget)
		self.iconListView.setModel(self.iconListModel)
		self.iconListView.setObjectName('iconListView')
		self.iconListView.setViewMode(1)
		self.iconListView.setResizeMode(1)
		self.iconListView.setWrapping(True)
		self.iconListView.setWordWrap(True)
		self.iconListView.setUniformItemSizes(True)
		self.iconListView.setIconSize(self.iconListView.gridSize()*0.85)

		self.splitterLayout = QSplitter()
		self.splitterLayout.setOrientation(Qt.Horizontal)
		self.splitterLayout.addWidget(self.treeView)
		self.splitterLayout.addWidget(self.iconListView)
		
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
		self.statusbar.setContentsMargins(11,0,0,0) #int left, int top, int right, int bottom
		MainWindow.setStatusBar(self.statusbar)
		self.statusbar.addWidget(self.statusBarProgress,1)
		self.statusbar.setFixedHeight(5)
		#self.statusbar.adjustSize()

		self.actionReBuildDB = QAction('Re-Build Database (rebuild everything)', MainWindow)
		self.actionReBuildDB.setObjectName("actionReBuildDB")

		self.actionReBuildDBAssets = QAction('Re-Build Assets DB (if you added new assets)', MainWindow)
		self.actionReBuildDBAssets.setObjectName("actionReBuildDBAssets")

		self.actionGenResImages = QAction('Generate Lower Resolution Files', MainWindow)
		self.actionGenResImages.setObjectName("actionGenResImages")

		self.actionGenThumbImages = QAction('Generate Small Thumbnails', MainWindow)
		self.actionGenThumbImages.setObjectName("actionGenThumbImages")

		self.menuFile.addAction(self.actionReBuildDB)
		self.menuFile.addAction(self.actionReBuildDBAssets)
		self.menuFile.addAction(self.actionGenResImages)
		self.menuFile.addAction(self.actionGenThumbImages)
		self.menubar.addAction(self.menuFile.menuAction())

		#self.iconListView.doubleClicked.connect(self.test)
		# auto connects defs on_Object_signal to object signal 
		# !use setObjectName, won't work with var name
		QMetaObject.connectSlotsByName(self) 

		#timer for triggering item list icon population
		self.tmr = QTimer()
		self.tmr.timeout.connect(self.createItemIcons)
		
		self.show()

	def parseSearchResult(self, item):
		containsInDB = False
		assetFiles = []
		assetsRes = []
		basedir = ''
		webSource = ''
		assetDims = ''
	
		webSource = item['webSource']
		assetDims = item['assetDims']
		
		def getExt(path):
			filename, file_extension = os.path.splitext(path)
			return(file_extension)

		if item['assets'] and item['assetsRes']:
			containsInDB = True
			#get highest res from a list of res, string comparisson works in this case, hires > 6k > 3k
			highestRes = (item['assetsRes'].index(max(item['assetsRes'])))
			basedir = item['assets'][highestRes]
			assetsRes = item['assetsRes']

			#list of lists of all asset files in all resolutions
			try:
				assetFiles = [
					[
						os.path.join(_dir, f)
						for f in os.listdir(_dir) 
							if os.path.isfile(os.path.join(_dir, f)) 
							and getExt(os.path.join(_dir, f)) != '.db'
					] 
					for _dir in item['assets']
				]
			except:
				print("error on assetFiles")

		return {'containsInDB': containsInDB, 'assetFiles': assetFiles, 'basedir':basedir, 'assetsRes': assetsRes, 'webSource': webSource, 'assetDims': assetDims}

	#insert string at pattern, replaces pattern
	def insertReplaceString(self, inString, insertString, pattern):
		x = inString.rfind(pattern)
		if x > -1:
			return (inString[:x] + insertString + inString[(x+len(pattern)):])
		else:
			return inString

	# initializes data for the icon list model
	# finds relavant items and creates placeholder icons
	# starts the timer work workers to start creating item icons and setting data
	# timer starts createItemIcons def
	# used on tree view click or search bar or filter available
	def initializeItemList(self, index, filterName='', filterAvailable=False):
		self.tmr.stop()
		self.threadpool.clear()
		QApplication.processEvents()
		self.statusBarProgress.show()
		activeThreads = self.threadpool.activeThreadCount()
		if activeThreads >= 0:
			#waitForDone = self.threadpool.globalInstance().waitForDone(500)	

			self.iconListModel.clear()
			#thisDir = self.treeView.model().filePath(index)
			thisDir = self.treeView.model().sourceModel().filePath(self.treeView.model().mapToSource(index))
			#print(thisDir)
			#self.treeView.setEnabled(False)

			#get all assets with the path containing selected directory
			if filterAvailable == False:
				searchResult = self.db.search( (self.dbQuery.jsonFile.search(thisDir, flags=re.IGNORECASE)) & (self.dbQuery.name.search(filterName, flags=re.IGNORECASE)))
			else:
				searchResult = self.db.search( (self.dbQuery.jsonFile.search(thisDir, flags=re.IGNORECASE)) & (self.dbQuery.name.search(filterName, flags=re.IGNORECASE)) & ~(self.dbQuery.assets == []) )

			
			#iterator for thumb image creation, batches of 10
			self.iterImg = NthIterator(searchResult, 10)
			
			self.statusBarProgress.setMinimum(0)
			self.statusBarProgress.setValue(0)
			self.statusBarProgress.setMaximum(len(searchResult))

			for count, item in enumerate(searchResult):		
				newItem = IconListItem(self.iconListView.iconSize(), self.iconListView.gridSize(), item['name'])
				newItem.setEditable(False)
				
				self.iconListModel.appendRow(newItem)
				qMIndex = self.iconListModel.index(count,0)
				
				self.iconListModel.setData(qMIndex , item['jsonFile'], self.iconListModel.jsonPathRole) #jsonPath
				
			self.iconListView.scrollToTop()

			#trigger item icon creation by starting the timer
			self.tmr.start(50)
		else:
			print('waiting')
			self.threadpool.waitForDone(500)

	
	def endProgressGenResWindow(self):
		self.threadpool.clear()
		self.threadpool.maxThreadCount()
		self.progressWindow.close()
		self.on_actionReBuildDB_triggered()
	

	def endProgressUpdateDBWindowAssets(self):
		self.threadpool.clear()
		self.threadpool.maxThreadCount()
		self.progressWindow.close()
		#self.dbAssets.close()
		#self.dbAssets = TinyDB(self.dbAssetsPath, storage=CachingMiddleware(JSONStorage))
		self.statusbar.showMessage('Database has been updated')

	@pyqtSlot()
	def on_searchBar_editingFinished(self):
		print('editing finished')

	@pyqtSlot()
	def on_searchBar_returnPressed(self):
		print('return pressed')
	
	@pyqtSlot(str)
	def on_searchBar_textEdited(self, text):
		if len(text) >=3 or len(text) ==0:
			self.initializeItemList(self.treeView.currentIndex(), text, self.filterPurchased.isChecked())

	
	@pyqtSlot(bool)
	def on_filterPurchased_clicked(self, e):
		if e:
			self.sender().setStyleSheet('background-color:'+palette.toRGBCSS(palette.highlightColour)+';')
			self.sender().setText("Show All")
			self.initializeItemList(self.treeView.currentIndex(), self.searchBar.text(), True)

		else:
			self.sender().setStyleSheet('background-color:'+palette.toRGBCSS(palette.baseAltColour)+';')
			self.sender().setText("Show Available")
			self.initializeItemList(self.treeView.currentIndex(), self.searchBar.text(), False)


	@pyqtSlot()
	def on_actionGenResImages_triggered(self):

		self.progressWindow = QProgressDialog('Generating Image Files...', '', 0, len(self.db), self.centralwidget, Qt.FramelessWindowHint)
		self.progressWindow.setObjectName('progressWindow')
		self.progressWindow.setWindowModality(Qt.WindowModal)
		self.progressWindow.setCancelButton(None)
		self.progressWindow.show()

		self.gr = GenerateResolutions(self.db, False)
		self.threadpool.setMaxThreadCount(1)
		worker = Worker(self.gr.main,'int')
		worker.signals.progressInt.connect(self.progressWindow.setValue)
		worker.signals.finished.connect(self.endProgressGenResWindow)
		self.threadpool.start(worker)

	@pyqtSlot()
	def on_actionGenThumbImages_triggered(self):

		self.progressWindow = QProgressDialog('Generating Small Thumbnails...', '', 0, len(self.fileModel.allThumbFiles), self.centralwidget, Qt.FramelessWindowHint)
		self.progressWindow.setObjectName('progressWindow')
		self.progressWindow.setWindowModality(Qt.WindowModal)
		self.progressWindow.setCancelButton(None)
		self.progressWindow.show()

		self.gr = GenerateSmallThumbs(self.fileModel.allThumbFiles, False)
		self.threadpool.setMaxThreadCount(1)
		worker = Worker(self.gr.main,'int')
		worker.signals.progressInt.connect(self.progressWindow.setValue)
		worker.signals.finished.connect(self.endProgressGenResWindow)
		self.threadpool.start(worker)



	###########################################
	## DATABASE UPDATE FUNCTIONS AND ACTIONS ##
	###########################################

	#Callback to run on update end
	def endProgressWindow(self):
		self.threadpool.clear()
		self.threadpool.maxThreadCount()
		self.progressWindow.close()
		self.db.storage.flush()
		self.statusbar.showMessage('Database has been updated')

	def setFormatProgressDialog(self, val):
		progressBar = self.progressWindow.findChild(QProgressBar)
		if progressBar:
			print('found')
			progressBar.setFormat(val)

	#Scan the purchased file and scan the thumbs and update the db with those
	@pyqtSlot()
	def on_actionReBuildDB_triggered(self, doUpdateDB=False):
		
		#display update window sooner, so user doesn't wonder whats going on
		#QProgressDialog(labelText, cancelButtonText, int minimum, int maximum, parent, Qt::WindowFlags())
		self.progressWindow = QProgressDialog('Loading...', '', 0, 100, self.centralwidget, Qt.FramelessWindowHint)
		self.progressWindow.setObjectName('progressWindow')
		self.progressWindow.setWindowModality(Qt.WindowModal)
		self.progressWindow.setCancelButton(None)
		self.progressWindow.show()

		#don't like this but, I think this is needed here
		QApplication.processEvents()
		#self.db.drop_tables()
		try:
			#self.db.close()
			#os.remove(self.dbPath)
			#self.db = TinyDB(self.dbPath, storage=(CachingMiddleware(JSONStorage)))
			self.db.drop_tables()
			doUpdateDB = True
		except:
			self.progressWindow.close()
			self.messageBox = QMessageBox.critical(self.centralwidget, 'DB Update Error', 'The database is currently in use elsewhere.\nPlease close all other asset browsers and try again.')

		
		if doUpdateDB:
			self.threadpool.setMaxThreadCount(1)
			worker = Worker(self.updateAll,'int', True)
			worker.signals.progressFormat.connect(self.setFormatProgressDialog)
			worker.signals.progressLabel.connect(self.progressWindow.setLabelText)
			worker.signals.progressMin.connect(self.progressWindow.setMinimum)
			worker.signals.progressMax.connect(self.progressWindow.setMaximum)
			worker.signals.progressInt.connect(self.progressWindow.setValue)
			worker.signals.finished.connect(self.endProgressWindow)
			self.threadpool.start(worker)
		

	#Scan the purchased files and update db with those only
	@pyqtSlot()
	def on_actionReBuildDBAssets_triggered(self, doUpdateDB=False):
		
		#display update window sooner, so user doesn't wonder whats going on
		#QProgressDialog(labelText, cancelButtonText, int minimum, int maximum, parent, Qt::WindowFlags())
		self.progressWindow = QProgressDialog('Loading...', '', 0, 100, self.centralwidget, Qt.FramelessWindowHint)
		self.progressWindow.setObjectName('progressWindow')
		self.progressWindow.setWindowModality(Qt.WindowModal)
		self.progressWindow.setCancelButton(None)
		self.progressWindow.setAutoClose(False)
		self.progressWindow.show()

		#don't like this but, I think this is needed here
		QApplication.processEvents()
		
		self.progressWindow.setLabelText('Getting Files...')
		self.progressWindow.setMinimum(0)
		self.progressWindow.setMaximum(100)
		
	
		doUpdateDB=True
		if doUpdateDB:
			self.threadpool.setMaxThreadCount(1)
			worker = Worker(self.updateAll,'int')
			worker.signals.progressFormat.connect(self.setFormatProgressDialog)
			worker.signals.progressLabel.connect(self.progressWindow.setLabelText)
			worker.signals.progressMin.connect(self.progressWindow.setMinimum)
			worker.signals.progressMax.connect(self.progressWindow.setMaximum)
			worker.signals.progressInt.connect(self.progressWindow.setValue)
			worker.signals.finished.connect(self.endProgressWindow)
			self.threadpool.start(worker)	

	def generateBase64Image(self, jsonFilePath):
		smallThumbFile = glob.glob(jsonFilePath.replace('.json','_tnSmall.*'))
		thumbFile = glob.glob(jsonFilePath.replace('.json','_tn.*'))
		if len(smallThumbFile) > 0 or len(thumbFile) > 0:
			outImageObject = None
			imgFormat = None
			if len(thumbFile) > 0 and len(smallThumbFile) == 0:
				#if large thumb but no small thumb
				imgFilePath = thumbFile[0]
				inImageObject = Image.open(imgFilePath)
				imgFormat = inImageObject.format
				
				f,imageExt = os.path.splitext(imgFilePath)
				img_str = ""
				
				#get the last instance of _ and remove everything after that
				imgFileNameBase = imgFilePath[:imgFilePath.rfind('_tn.')]

				maxDim = 200

				outImageFilePath = str(imgFileNameBase + '_tnSmall' + imageExt)
			
				if inImageObject.width >= inImageObject.height:
					width = maxDim
					height = int(maxDim * inImageObject.height/inImageObject.width)
				else:
					height = maxDim
					width = int(maxDim * inImageObject.width/inImageObject.height)

				outImageObject = inImageObject.resize((width, height),resample=Image.NEAREST)
				outImageObject.save(outImageFilePath, imgFormat)
			else:
				outImageObject = Image.open(smallThumbFile[0])
				imgFormat = outImageObject.format
			
			buff = BytesIO()
			outImageObject.save(buff, imgFormat)
			img_str = base64.b64encode(buff.getvalue())
			img_str = str(img_str)[2:-1]
						
			outImageObject.close()
			
			return img_str
		else:
			return ''


	def readAssetJson( self, jsonFilePath ):
		result = {"name":"", "altName": "", "dims":"", "webSource":"", "thumb":""}
		try:
			with open( jsonFilePath, 'r+') as f:
				result = json.load(f)
				# try fix if thumb is not generated
				if result["thumb"] == '':
					print('fixing ', jsonFilePath)
					result["thumb"] = self.generateBase64Image(jsonFilePath)
					f.seek(0)
					f.truncate()
					json.dump(result, f, indent=2)
			return result
		except Exception as e:
			print(e)
			return result


	# Updates everything, updates thumbs and assets directory
	def updateThumbsDB(self, assetsDict, **kwargs):
		progress_callback = kwargs['progress_callback']
		progress_setlabel = kwargs['progress_setlabel']
		progress_setformat = kwargs['progress_setformat']
		progress_setmin = kwargs['progress_setmin']
		progress_setmax = kwargs['progress_setmax']

		progress_setlabel.emit('Updating database...')
		progress_setformat.emit('%p%')
		progress_setmin.emit(0)
		progress_setmax.emit(self.fileModel.totalFileCount)

		updateEvery = 20

		#for each thumbnail in the model
		for i in range(len(self.fileModel.allThumbFiles)):
			jsonFile = self.fileModel.allThumbFiles[i]
			assetsList = []
			assetsResList = []
			
			jsonData = self.readAssetJson(jsonFile)
			webSource = jsonData["webSource"]
			assetDims = jsonData["dims"]
			base64ImageString = jsonData["thumb"]
			assetName = jsonData["name"]
			searchName = jsonData["altName"]

			if assetsDict.get(searchName) != None:
				assetsList = assetsDict.get(searchName).get('assets')
				assetsResList = assetsDict.get(searchName).get('assetsRes')

			purchased = True if assetsList != [] else False
			measured = True if assetDims != '' else False

			#borderIcon 							(file, size, containsInDB, measured=None, asBytes=False):
			base64Image = self.iconListModel.borderIcon(base64ImageString, self.iconListView.iconSize(), purchased, measured)
			# write to db
			self.db.insert({'name': assetName,'jsonFile': jsonFile, 'assets': assetsList, 'assetsRes': assetsResList, 'webSource': webSource, 'assetDims': assetDims, 'image':base64Image})
			'''
			if i == 1:
				# test writing QIcon image as a serialized object instead
				testIcon = self.iconListModel.borderIcon(base64ImageString, self.iconListView.iconSize(), purchased, measured, False)
				testPixmap = self.iconListModel.borderIcon(base64ImageString, self.iconListView.iconSize(), purchased, measured, False, True)

				buffer = QByteArray()
				write_stream = QDataStream(buffer, QIODevice.WriteOnly)
				write_stream << testPixmap
				
				with open('testIcon.txt', 'w+') as someFile:
					# encoding to base64 saves space
					# writing buffer.data() and just buffer is exactly the same binary
					img_str = base64.b64encode(buffer.data())
					someFile.write(base64.b64encode(buffer).decode('UTF-8'))
				
				with open('testIconCache.txt', 'w+') as someFile:
					# encoding to base64 saves space
					# writing buffer.data() and just buffer is exactly the same binary
					img_str = base64.b64encode(buffer.data())
					someFile.write(str(testIcon.cacheKey()))
				
				with open('testImg.txt', 'w+') as someFile:
					# encoding to base64 saves space
					# writing buffer.data() and just buffer is exactly the same binary
					someFile.write(base64Image)
					'''
			

			#need this here, update every 20th otherwise buffer overrun error
			if i % updateEvery == 0:
				try:
					progress_callback.emit(i)
				except:
					print('error')
	
	#Updates only db entries with matching names from assets list
	def updateAssetsDB(self, assetsDict, **kwargs):
		
		#test function for db query
		def dbTestFunc(val, _name):
			return val.replace(' ','').lower() == _name.lower()

		progress_callback = kwargs['progress_callback']
		progress_setformat = kwargs['progress_setformat']
		progress_setlabel = kwargs['progress_setlabel']
		progress_setmin = kwargs['progress_setmin']
		progress_setmax = kwargs['progress_setmax']
		
		progress_setlabel.emit('Updating database...')
		progress_setformat.emit('%p%')
		progress_setmin.emit(0)
		progress_setmax.emit(len(assetsDict))

		updateEvery = 20

		for count, (key, value) in enumerate(assetsDict.items()):
			assetsList = value['assets']
			assetsResList = value['assetsRes']

			#update icon here
			existingItem = (self.db.get(self.dbQuery.name.test(dbTestFunc, key)))
			if existingItem:
				newItemIcon = self.iconListModel.updateIconFromBase64(existingItem['image'])

				self.db.update({'assets':assetsList, 'assetsRes':assetsResList, 'image': newItemIcon},self.dbQuery.name.test(dbTestFunc, key) )
						
			if count % updateEvery == 0:
				try:
					progress_callback.emit(count)
				except:
					pass
	
	# Scans purchased directory and creates a dict of purchased files
	# and resolutions grouped by asset name
	def collectPurchasedFiles(self, **kwargs):
		
		def resFromFilePath(_file):
			res = ''
			fileParts = PurePath(_file).stem.split('_')
			
			if len(fileParts) > 1:
				if fileParts[-1].lower() == 'metalness' or fileParts[-1].lower() == 'specular':
					res = fileParts[-2]
				else:
					res = fileParts[-1]
			else:
				res = 'HIRES'

			return res

		progress_callback = kwargs['progress_callback']
		progress_setformat = kwargs['progress_setformat']
		progress_setmin = kwargs['progress_setmin']
		progress_setmax = kwargs['progress_setmax']
		progress_setlabel = kwargs['progress_setlabel']
		
		progress_setlabel.emit('Getting Files...')
		progress_setformat.emit('%v files')
		progress_setmin.emit(0)
		progress_setmax.emit(0)

		masterList = {}
		updateEvery = 30
		count = 0
		
		it = QDirIterator(self.poliigonMapsPath, (QDir.Dirs | QDir.NoDotAndDotDot ),  QDirIterator.Subdirectories)
		while it.hasNext():
			thisDir = it.next()
			
			searchName = None
			
			for fname in os.listdir(thisDir):
				if os.path.isdir(os.path.join(thisDir,fname)):
					#break if found a directory, looking for final leaf
					break
				
				elif PurePath(fname).suffix != '.db':
					searchName = fname.split('_')[0]
					assets = thisDir
					assetsRes = resFromFilePath(fname)	
					
					if masterList.get(searchName) == None:
						masterList.update({searchName:{'assets':[assets], 'assetsRes':[assetsRes]}})
					else:
						itemAssetsList = masterList.get(searchName).get('assets')
						itemAssetsResList = masterList.get(searchName).get('assetsRes')
						itemAssetsList.append(assets)
						itemAssetsResList.append(assetsRes)
						
					count +=1
					if count % updateEvery == 0: 
						try:
							progress_setlabel.emit(('Getting Files... ' + str(count)))
						except:
							pass
						#progress_callback.emit(count)

					#break, only need one file as long as not thumb.db
					break

		return masterList
	
	def updateAll(self, updateThumbs=False, **kwargs):
		
		results = self.collectPurchasedFiles(**kwargs)

		if updateThumbs:
			self.updateThumbsDB(results, **kwargs)
		else:
			self.updateAssetsDB(results, **kwargs)

		return None
	
	@pyqtSlot(QModelIndex)
	def on_iconListView_clicked(self, index):	
		pass

	
	@pyqtSlot(QModelIndex)
	def on_iconListView_doubleClicked(self, index):
		self.sender().model().exploreAsset(index)
	
	'''
	@pyqtSlot(QKeyEvent)
	def on_iconListView_pressed(self, ev):
		print('pressed key')
		print(ev.key())
	'''

	@pyqtSlot(QModelIndex)
	def on_treeView_clicked(self,index):
		self.initializeItemList(index, self.searchBar.text(), self.filterPurchased.isChecked())
	
	@pyqtSlot()	
	def releasePoolThread(self):
		self.statusBarProgress.setValue(self.statusBarProgress.value() + 1)
		#print('thread done')
		#print(self.threadpool.stackSize())
		#self.threadpool.releaseThread()

	# Gets items from iterator in batches
	# sets item data for the icon list model
	# starts workers to create icon images
	@pyqtSlot()	
	def createItemIcons(self):
		try:
			batch = self.iterImg.nextBatch()
			
			for count, item in enumerate(batch):
				i = count + self.iterImg.getI()
				self.threadpoolQLength = self.threadpoolQLength + 1
				
				qMIndex = self.iconListModel.index(i,0)
				#smallThumbPath = self.insertReplaceString(item['thumb'],'_tnSmall.','_tn.')
				#print(smallThumbPath)
				
				parsedItem = self.parseSearchResult(item)
				#setItemData(qMIndex, QMap(int, QVariable))
				
				# self.iconListModel.setData(qMIndex, parsedItem['assetFiles'], self.iconListModel.assetFilesRole)
				# self.iconListModel.setData(qMIndex, parsedItem['basedir'], self.iconListModel.baseDirRole)
				# self.iconListModel.setData(qMIndex, parsedItem['containsInDB'], self.iconListModel.containsRole)
				# self.iconListModel.setData(qMIndex, parsedItem['webSource'], self.iconListModel.websourceRole)
				# self.iconListModel.setData(qMIndex, parsedItem['assetDims'], self.iconListModel.assetDimsRole)
				# self.iconListModel.setData(qMIndex, parsedItem['assetsRes'], self.iconListModel.assetsResRole)
				
				self.iconListModel.setItemData(
					qMIndex,
					{
						self.iconListModel.assetFilesRole : parsedItem['assetFiles'],
						self.iconListModel.baseDirRole : parsedItem['basedir'],
						self.iconListModel.containsRole : parsedItem['containsInDB'],
						self.iconListModel.websourceRole : parsedItem['webSource'],
						self.iconListModel.assetDimsRole : parsedItem['assetDims'],
						self.iconListModel.assetsResRole : parsedItem['assetsRes']
					}
				)

				imageBytes = item['image']
				#worker = Worker(self.loadItemIcon, None, smallThumb, self.iconListView.iconSize(), qMIndex, self.iconListModel, parsedItem['containsInDB'])
				worker = Worker(self.loadItemIcon, None, qMIndex, self.iconListModel, imageBytes)
				#worker = Worker(self.loadItemIcon, None, item, self.iconListView.iconSize(), qMIndex, self.iconListModel)
				worker.signals.finished.connect(self.releasePoolThread)
				worker.signals.result.connect(self.iconListModel.setThumbs)
				self.threadpool.start(worker, self.threadpoolQLength)	
				
		except StopIteration:
			self.sender().stop()
			self.threadpool.clear()
			self.statusBarProgress.hide()
			self.treeView.setEnabled(True)
		except Exception as e:
			print(e)
		
	
	def loadItemIcon(self, i, thisModel, _bytes, **kwargs):
		icon = thisModel.loadIconFromBase64(_bytes)
		return (i, icon)


if __name__ == '__main__':
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	app.setPalette(palette)

	config = configparser.ConfigParser()
	config.read('poliigonBrowser.ini')
	configuration = False

	poliigonMapsPath = ''
	poliigonThumbsPath = ''
	
	appIcon = b64ToImage.qIconFromBase64(icons.appIconBase64)

	try:
		poliigonThumbsPath = (config['poliigonBrowserSettings']['poliigonThumbsPath'])
		poliigonMapsPath = (config['poliigonBrowserSettings']['poliigonMapsPath'])
		configuration = True
	except:
		configDialog = PoliigonBrowserConfigDialog(appIcon, 400)
		var = configDialog.exec()
		#return 1 if accepted, 0 if rejected
		if var == 1:
			poliigonThumbsPath = (configDialog.le1.text())
			poliigonMapsPath = (configDialog.le2.text())
			configuration = True
	
	if configuration == True:
		ex = MainWindow(poliigonThumbsPath, poliigonMapsPath)
	
	sys.exit(app.exec_())
