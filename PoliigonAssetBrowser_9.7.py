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
import platform
from pathlib import PurePath, Path
import webbrowser
from math import floor
import tempfile
import time
import configparser
import re
import pickle
import random

#tinyDB Classes
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.storages import MemoryStorage
from tinydb.middlewares import CachingMiddleware

#Custom Classes
from poliigonGenerateResolutionsClass import GenerateResolutions
from poliigonGenerateSmallThumbsClass import GenerateSmallThumbs
from poliigonConfigDialogClass import PoliigonBrowserConfigDialog
from poliigonImageCollection import imageCollectionBase64
from poliigonDarkPalette import QtDarkPalette

#PyQt Classes
#from PyQt5.QtWidgets import (QWidget,QSizePolicy, QProgressDialog, QMessageBox ,QMainWindow ,QSplitter, QHBoxLayout, QFileSystemModel, QTreeView,QListView, QStyle,QLabel, QLineEdit, QComboBox, QPushButton, QApplication, QStyleFactory, QGridLayout, QVBoxLayout, QLayout, QSizePolicy, QProgressBar, QPlainTextEdit, QButtonGroup, QRadioButton, QCheckBox, QFrame, QSpacerItem ,QMenuBar, QMenu,QStatusBar,QAction,QDialog)
#from PyQt5.QtCore import Qt, QCoreApplication, QRect, QRectF, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QSize, QModelIndex, QMetaObject, QDir, QDirIterator,QByteArray, QUrl, QMimeData, QVariant,QTimer,QPoint, QSortFilterProxyModel
#from PyQt5.QtGui import QIcon,QPixmap,QStandardItemModel,QStandardItem,QImage, QPainter, QPalette, QColor, QPen, QResizeEvent, QDrag, QKeyEvent
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

icons = imageCollectionBase64()
palette = QtDarkPalette()
appIcon = None#icons.qIconFromBase64(icons.appIconBase64)

def getExt(path):
	filename, file_extension = os.path.splitext(path)
	return(file_extension)

#creates a temp .ms file to be dropped into max window
#should be deleted after drop somewhere
def createMSFile(basepath, fileResList, file2DList, dimensions, materialName):
	
	def pyListToMaxArray(maxArray):
		result = '#('
		for s in maxArray:
			if type(s) == str:
				result = result + '"' + s + '"' +','
			if type(s) == list and len(s) > 0:
				result = result + pyListToMaxArray(s) + ','
			elif type(s) == list and len(s) == 0:
				result = result + '"' + 'undefined' + '"' +','
		result = list(result)
		result[-1] = ')'
		return ''.join(result)

	def pyValueToMaxValue(maxArray):
		if type(maxArray) == list and len(maxArray) > 0:
			return pyListToMaxArray(maxArray)
		elif maxArray == 'undefined':
			return maxArray
		else:
			return '"' + maxArray + '"'

	def pyDictToMaxString(pyDict):
		result=''
		for key, value in pyDict.items():
			result = result + key + ':'+ pyValueToMaxValue(value) + ' '
		return result
	
	def make(fileList, fileRes):
		selectors = ['assetRes','_AO_' , '_COL_' , '_DISP_' , '_DISP16_' , '_GLOSS_' , '_NRM_' , '_NRM16_' , '_REFL_' , '_SSS_' , '_TRANSMISSION_' , '_DIRECTION_' ,'_ALPHAMASKED_']
		und = 'undefined'
		new_array = {f:und for f in selectors}
		
		new_array['assetRes'] = fileRes

		if len(fileList) == 1:
			#just one file, probably a graphic, set
			new_array['_COL_'] = [fileList[0]]
			if getExt(fileList[0]) == '.png':
				new_array['_ALPHAMASKED_'] = new_array['_COL_']
		else:
			colorVariations = []
			dispVariations = []
			alphaVariations = []
			for f in fileList: 
				for i in range(len(selectors)): 
					if selectors[i] in f and selectors[i] == '_COL_': 
						colorVariations.append(f)
					elif selectors[i] in f and selectors[i] == '_DISP_': 
						dispVariations.append(f)
					elif selectors[i] in f and selectors[i] == '_ALPHAMASKED_': 
						alphaVariations.append(f)
					elif selectors[i] in f:
						new_array[selectors[i]] = f
			
			new_array['_COL_'] = colorVariations
			new_array['_DISP_'] = dispVariations
			new_array['_ALPHAMASKED_'] = alphaVariations

			'''
			1 - alphamask is present, no color present -> copy to color
			2 - color is present in png format -> copy to alphamask

			'''

			if len(new_array['_COL_']) > 0 and len(new_array['_ALPHAMASKED_']) == 0:
				if getExt(colorVariations[0]) == '.png':
					new_array['_ALPHAMASKED_'] = new_array['_COL_']
				else:
					new_array['_ALPHAMASKED_'] = und
			elif len(new_array['_ALPHAMASKED_']) > 0 and len(new_array['_COL_']) == 0:
				new_array['_COL_'] = new_array['_ALPHAMASKED_']

		#weird name no selectors
		if len(new_array['_COL_']) == 0 and len(fileList) != 0:
			colorVariations = []
			alphaVariations = []
			
			for f in fileList:
				colorVariations.append(f)
				if getExt(f) == '.png':
					alphaVariations.append(f)

			new_array['_COL_'] = colorVariations
			new_array['_ALPHAMASKED_'] = alphaVariations
		return pyDictToMaxString(new_array)

	tempMSFile = tempfile.NamedTemporaryFile(mode = 'w+', newline='\n',suffix='.ms',delete=False)
	matStructVar = 'pyPoliigonMaterial=pyPoliigonStruct '

	for i, fileList in enumerate(file2DList):
		mapStructVar = make(fileList, fileResList[i])
		tempMSFile.write('new' + str(i) + '=poliigonMapSet '+ mapStructVar + '\n')
		matStructVar = matStructVar + '_' + fileResList[i] + '_:new' + str(i) + ' '

	
	tempMSFile.write('matDimensions=' + ('undefined' if dimensions == None else str(dimensions)) + '\n')
	tempMSFile.write(matStructVar + ' pyDimensions:matDimensions pyMaterialName:"'+materialName+'" pyScriptFilePath:getSourceFileName() \n')
	tempMSFile.write('pyPoliigonMaterial.show()' + '\n')
	tempMSFile.close()
	
	'''
	Build MS file like this:
	new1 = poliigonMapSet assetRes:"2K" _AO_:"somethign1"
	new2 = poliigonMapSet assetRes:"3K" _AO_:"somethign2" _COL_:#("some","one")
	new3 = poliigonMapSet assetRes:"4K" _AO_:"somethign3"
	new4 = poliigonMapSet assetRes:"6K" _AO_:"somethign4"
	new5 = poliigonMapSet assetRes:"HIRES" _AO_:"somethign5"

	pyPoliigonMaterial = pyPoliigonStruct _2K_:new1 _3K_:new2 _4K_:new3 _6K_:new4 _HIRES_:new5 pyDimensions:matDimensions pyMaterialName:"materialName" pyScriptFilePath:getSourceFileName()
	pyPoliigonMaterial.show()
	'''

	return tempMSFile

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
	

class IconListItem(QStandardItem):

	def __init__(self, _iconSize, _itemSize, _itemText):
		super().__init__(_itemText)
		self._iconSize = _iconSize
		self.setPlaceholder()
		self.setSizeHint(_itemSize)

	#def clone(self):
		#obj = super(IconListItem, self).clone()
		#return IconListItem(_iconSize, _itemSize, _itemText, containsInDB)
		#return obj

	def setPlaceholder(self):
		placeholder = QPixmap(self._iconSize)
		placeholder.fill(Qt.gray)
		self.setIcon(QIcon(placeholder))


class LargePreviewWindow(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent
		self.previewMaxSize = QSize(900,900)
		self.placehloderImg = self.setPlaceholder()
		self._model = None
		self._index = None
		self.setupUi()

	def setPlaceholder(self):
		placeholder = QPixmap(900,900)
		placeholder.fill(Qt.gray)
		return placeholder
	
	def setupUi(self):	
		self.setWindowFlags(Qt.Popup)
		self.setModal(True)
		self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.setUpdatesEnabled(True)
		
		self.verticalLayout = QVBoxLayout(self)
		self.verticalLayout.setContentsMargins(11, 11, 11, 11)
		self.verticalLayout.setSpacing(11)


		self.gridLayoutImage = QGridLayout()
		self.gridLayoutData = QGridLayout()
		
		for i in range(6):
			self.gridLayoutData.setRowMinimumHeight(i,22)
			self.gridLayoutData.setRowStretch(i,0)

		for i in range(2):
			self.gridLayoutData.setColumnMinimumWidth(i,25)
			self.gridLayoutData.setColumnStretch(i,0)

		self.previewWidget = QLabel('',self)
		self.previewWidget.setMaximumSize(self.previewMaxSize)
		self.previewWidget.setPixmap(self.placehloderImg)
		#self.previewWidget.setScaledContents(True)
		self.previewWidgetPolicy = QSizePolicy()
		self.previewWidgetPolicy.setWidthForHeight(True)
		self.previewWidgetPolicy.setHorizontalPolicy(QSizePolicy.Expanding)
		self.previewWidgetPolicy.setVerticalPolicy(QSizePolicy.Maximum)
		self.previewWidget.setSizePolicy(self.previewWidgetPolicy)
		self.gridLayoutImage.addWidget(self.previewWidget, 0, 0, 1, 1)

		# left column labels
		self.dbPath_lbl = QLabel('Database Asset Path:', self)
		self.assetPath_lbl = QLabel('Asset Path:', self)
		self.dims_lbl = QLabel('Asset Dimensions:', self)
		self.web_lbl = QLabel('Asset Web Address:', self)
		self.res_lbl = QLabel('Asset Resolutions:', self)
		self.contains_lbl = QLabel('Asset Available:', self)

		self.dbPath_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		self.assetPath_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		self.dims_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		self.web_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		self.res_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		self.contains_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

		self.dbPath_lbl.setMaximumWidth(150)
		self.assetPath_lbl.setMaximumWidth(150)
		self.dims_lbl.setMaximumWidth(150)
		self.web_lbl.setMaximumWidth(150)
		self.res_lbl.setMaximumWidth(150)
		self.contains_lbl.setMaximumWidth(150)

		# right column data column
		self.dbPath_result_lbl = QLabel('--', self)
		self.assetPath_result_lbl = QLabel('--', self)
		self.dims_result_lbl = QLabel('--', self)
		self.web_result_lbl = QLabel('--', self)
		self.res_result_lbl = QLabel('--', self)
		self.contains_result_lbl = QLabel('--', self)

		self.dbPath_result_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
		self.assetPath_result_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
		self.dims_result_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
		self.web_result_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
		self.res_result_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
		self.contains_result_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

		self.dbPath_result_lbl.setTextFormat(Qt.RichText)
		self.dbPath_result_lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
		self.dbPath_result_lbl.setOpenExternalLinks(True)

		self.assetPath_result_lbl.setTextFormat(Qt.RichText)
		self.assetPath_result_lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
		self.assetPath_result_lbl.setOpenExternalLinks(True)

		self.web_result_lbl.setTextFormat(Qt.RichText)
		self.web_result_lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
		self.web_result_lbl.setOpenExternalLinks(True)

		sI1 = QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
		sI2 = QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

		# widget adds
		self.gridLayoutData.addWidget(self.dbPath_lbl, 0, 0)
		self.gridLayoutData.addWidget(self.assetPath_lbl, 1, 0)
		self.gridLayoutData.addWidget(self.web_lbl, 2, 0)
		self.gridLayoutData.addWidget(self.contains_lbl, 3, 0)
		self.gridLayoutData.addWidget(self.res_lbl, 4, 0)
		self.gridLayoutData.addWidget(self.dims_lbl, 5, 0)
		
		'''
		self.gridLayoutData.addWidget(self.goto_dbPath_btn, 0, 1, Qt.AlignLeft)
		self.gridLayoutData.addWidget(self.goto_assetPath_btn, 1, 1, Qt.AlignLeft)
		self.gridLayoutData.addWidget(self.goto_web_btn, 2, 1, Qt.AlignLeft)	

		'''
		self.gridLayoutData.addWidget(self.dbPath_result_lbl, 0, 2)
		self.gridLayoutData.addWidget(self.assetPath_result_lbl, 1, 2)
		self.gridLayoutData.addWidget(self.web_result_lbl, 2, 2)
		self.gridLayoutData.addWidget(self.contains_result_lbl, 3, 2)
		self.gridLayoutData.addWidget(self.res_result_lbl, 4, 2)
		self.gridLayoutData.addWidget(self.dims_result_lbl, 5, 2)
		self.gridLayoutData.addItem(sI1, 6, 0)
		self.gridLayoutData.addItem(sI2, 0, 3)
		
		self.verticalLayout.addLayout(self.gridLayoutImage)
		self.verticalLayout.addLayout(self.gridLayoutData)
		self.hide()
	
	'''
	257: Qt.UserRole+1 -> thumb path
	258: Qt.UserRole+2 -> asset files
	259: Qt.UserRole+3 -> base dir, dir of highest res asset
	260: Qt.UserRole+4 -> contains
	261: Qt.UserRole+5 -> websource
	262: Qt.UserRole+6 -> dimensions
	263: Qt.UserRole+7 -> assets resolution list
	263: Qt.UserRole+8 -> small thumb path
	'''
	
	# takes 2 QSize and outputs QRectF
	def centerFit(self, sourceSize, targetSize):

		tw = targetSize.width()
		th = targetSize.height()

		w = sourceSize.width()
		h = sourceSize.height()

		#find the minimal scale to scale-by to fit the target size
		scale = tw/w if tw/w < th/h else th/h
		
		x0 = (tw - w*scale)/2
		y0 = (th - h*scale)/2
		x1 = tw - (tw - w*scale)/2
		y1 = th - (th - h*scale)/2

		return QRectF(QPoint(x0, y0), QPoint(x1, y1))

	#generates and fits a preview image into a preview image max size
	def formatPreviewImage(self, previewImagePath):
		previewImage = QPixmap(previewImagePath)
		if previewImage.width()>self.previewMaxSize.width() or previewImage.height()>self.previewMaxSize.height():
			bgImage = QPixmap(self.previewMaxSize)
			bgImage.fill(Qt.transparent)
			
			p = QPainter(bgImage)
			source = QRectF(0,0,previewImage.width(),previewImage.height())
			target = self.centerFit(previewImage.size(), self.previewMaxSize)
			p.drawPixmap(target,previewImage,source)		
			p.end()
			return bgImage
		else:
			return previewImage

	def populateData(self, _index):
		itemData = self._model.itemData(_index)

		#convert dims string '[W, H]' to 'Wm x Hm'
		def formatDims(dimString):
			dimList = dimString.strip('][').split(', ')
			return (dimList[0] + 'm x ' + dimList[1] + 'm')

		def formatLink(filePath, webLink=True):
			if webLink:
				return '<a href="'+filePath+'">'+filePath+'</a>'
			else:
				return ('<a href="file:///'+filePath+'">'+filePath+'</a>')

		#Make nice dims and assetRes
		previewImage = self.formatPreviewImage(itemData[257])
		contains = 'Yes' if itemData[260] else 'No'
		assetDir = formatLink(itemData[259],False) if itemData[259] else '--'
		assetRes = ', '.join(itemData[263]) if itemData[263] else '--'
		webSource = formatLink(itemData[261]) if itemData[261] else '--'
		dims = formatDims(itemData[262]) if itemData[262] else '--'
		
		self.previewWidget.setPixmap(previewImage)
		self.previewWidget.adjustSize()
		self.dbPath_result_lbl.setText(formatLink(os.path.dirname(itemData[257]),False))
		self.contains_result_lbl.setText(contains)
		self.assetPath_result_lbl.setText(assetDir)
		self.res_result_lbl.setText(assetRes)
		self.web_result_lbl.setText(webSource)
		self.dims_result_lbl.setText(dims)
		self.setMaximumHeight(150)
		self.adjustSize()

	def showPreviewWindow(self, _model, _index):
		self._model = _model
		self._index = _index
		self.rowCount = self._model.rowCount()
		self.populateData(_index)		
		self.show()

	def keyPressEvent(self, e):
		super().keyPressEvent(e)
		
		if e.key() == Qt.Key_Space:
			self.close()

		if e.key() == Qt.Key_Right:
			newRow = (self._index.row() + 1) % self.rowCount
			newIndex = self._model.index(newRow,0)
			self._index = newIndex
			self.populateData(newIndex)

		if e.key() == Qt.Key_Left:
			newRow = (self._index.row() + self.rowCount - 1) % self.rowCount
			newIndex = self._model.index(newRow,0)
			self._index = newIndex
			self.populateData(newIndex)
			

class IconListView(QListView):
	iconSpaceSize = 180
	
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setSizing()
		self.parent = parent
		self.previewWindow = LargePreviewWindow(self)

	def calculateSize(self):
		itemsInRow = floor((self.viewport().width() - 15) / self.iconSpaceSize)
		itemsInModel = (self.model().rowCount())
		
		if itemsInModel <= itemsInRow: #or itemsInRow < 2:
			return self.iconSpaceSize
		else:
			return self.iconSpaceSize + floor(((self.viewport().width() - 15) % self.iconSpaceSize)/itemsInRow)

	def resizeEvent(self, e):
		#print(self.calculateSize())
		self.setGridSize(QSize(self.calculateSize(),180))
		super().resizeEvent(e)

	def setSizing(self):
		self.setMinimumWidth(self.iconSpaceSize + 2 + self.verticalScrollBar().width())
		self.viewport().setMinimumWidth(self.iconSpaceSize + 2)
		self.setGridSize(QSize(self.iconSpaceSize,self.iconSpaceSize))

	def startDrag(self, e):

		itemData = self.model().itemData(self.currentIndex())
		
		thumb = itemData[257] # +1
		assetFiles = itemData[258] # +2
		basedir = itemData[259] # +3
		contains = itemData[260] # +4
		dims = itemData[262] # +6
		assetsRes = itemData[263] # +7


		#Maybe replace with itemData function
		#thumb = self.model().data(self.currentIndex() , Qt.UserRole + 1)
		#assetFiles = self.model().data(self.currentIndex() , Qt.UserRole + 2)
		#basedir = self.model().data(self.currentIndex() , Qt.UserRole + 3)
		#contains = self.model().data(self.currentIndex() , Qt.UserRole + 4)
		#dims = self.model().data(self.currentIndex() , Qt.UserRole + 6)
		#assetsRes = self.model().data(self.currentIndex() , Qt.UserRole + 7)
		
		if contains:
			#creating a maxscript file here with a function to execute in max
			#itemName = (((PurePath(thumb).stem).replace(' ','')).split('.'))[0]
			itemName = ((PurePath(thumb).stem).replace(' ',''))[:-3] # -3 to remove _tn
			tempMSFile = createMSFile(basedir, assetsRes, assetFiles, dims, itemName)

			url = QUrl.fromLocalFile(tempMSFile.name)
			mime = QMimeData()
			mime.setUrls([url])
			drag = QDrag(self)
			drag.setMimeData(mime)
			drag.exec(Qt.CopyAction | Qt.CopyAction)
	
	def keyPressEvent(self, e):
		super(IconListView, self).keyPressEvent(e)
		
		if e.key() == Qt.Key_Space:	
			self.previewWindow.showPreviewWindow(self.model(), self.currentIndex())


class IconListModel(QStandardItemModel):
	
	issueUpdate = pyqtSignal()
	rulerIcon = icons.qImageFromBase64(icons.rulerIconBase64) #rulerIcon = imageFromBase64(icons.rulerIconBase64)
	
	def __init__(self):
		super().__init__()
		self.progress_callback = pyqtSignal()
	
	# takes 2 QSize and outputs QRectF
	def centerFit(self, sourceSize, targetSize):

		tw = targetSize.width()
		th = targetSize.height()

		w = sourceSize.width()
		h = sourceSize.height()

		#find the minimal scale to scale-by to fit the target size
		scale = tw/w if tw/w < th/h else th/h
		
		x0 = (tw - w*scale)/2
		y0 = (th - h*scale)/2
		x1 = tw - (tw - w*scale)/2
		y1 = th - (th - h*scale)/2

		return QRectF(QPoint(x0, y0), QPoint(x1, y1))

	def loadIconFromBase64 (self, _bytes):
		base64 = bytes(_bytes,'utf-8')
		#print(base64)
		pixmap = QPixmap()
		pixmap.loadFromData(QByteArray.fromBase64(base64))
		_icon = QIcon(pixmap)
		#print(_icon)
		#self.setData(_index, _icon, Qt.DecorationRole)
		return _icon

	def updateIconFromBase64 (self, _bytes, containsInDB=True):
		base64 = bytes(_bytes,'utf-8')
		originalImage = QPixmap()
		originalImage.loadFromData(QByteArray.fromBase64(base64))

		if originalImage.isNull() == False:
			p = QPainter(originalImage)
			
			if containsInDB:
				pen = QPen()
				pen.setColor(Qt.green)
				pen.setWidth(3)
				p.setPen(pen)
				p.drawRect(0,0,originalImage.width()-1,originalImage.height()-1)
			
			p.end()
		
		bArray = QByteArray()
		_buffer = QBuffer(bArray)
		_buffer.open(QIODevice.WriteOnly)
		originalImage.save(_buffer, "JPG")
		return str(bArray.toBase64())[2:-1]

	def borderIcon (self, file, size, containsInDB, measured=None, asBytes=False):
		
		bgImage = QPixmap(size)
		#bgImage.fill(Qt.transparent)
		bgImage.fill(palette.baseColour)
		
		originalImage = QImage(file)

		if originalImage.isNull() == False:
			p = QPainter(bgImage)
			source = QRectF(0,0,originalImage.width(),originalImage.height())
			target = self.centerFit(originalImage.size(), size)
			p.drawImage(target,originalImage,source)	
			
			if measured:
				p.drawImage(QPoint(5,(size.height()-5-self.rulerIcon.height())),self.rulerIcon)
			
			if containsInDB:
				pen = QPen()
				pen.setColor(Qt.green)
				pen.setWidth(3)
				p.setPen(pen)
				p.drawRect(0,0,size.width()-1,size.height()-1)
			
			p.end()
		
		if asBytes:
			bArray = QByteArray()
			_buffer = QBuffer(bArray)
			_buffer.open(QIODevice.WriteOnly)
			bgImage.save(_buffer, "JPG")
			#pickedArray = pickle.dumps(bArray)
			return str(bArray.toBase64())[2:-1]
		else:
			return QIcon(bgImage)


	def data(self, index, role):
		return super(IconListModel, self).data(index, role)
	
	def setData(self, index, value, role):
		return super(IconListModel, self).setData(index, value, role)

	def setThumbs(self, tup):
		index, icon = tup
		self.setData(index, icon, Qt.DecorationRole)
	
	def exploreAsset(self, index):
		if self.data(index,Qt.UserRole+4):
			path = self.data(index,Qt.UserRole+3)
			os.startfile(path)
		else:
			fLocation = os.path.dirname(self.data(index,Qt.UserRole+1)) + '/webSource.txt'
			try:
				f = open(fLocation, 'r')
				webSource = f.readline()
				if webSource !=None:
					self.setData(index, f.readline(), Qt.UserRole+5)
					webbrowser.open_new(webSource)
				f.close()
			except:
				pass
	'''
	257: Qt.UserRole+1 -> thumb path
	258: Qt.UserRole+2 -> asset files
	259: Qt.UserRole+3 -> base dir, dir of highest res asset
	260: Qt.UserRole+4 -> contains
	261: Qt.UserRole+5 -> websource
	262: Qt.UserRole+6 -> dimensions
	263: Qt.UserRole+7 -> assets resolution list
	264: Qt.UserRole+8 -> small thumb path
	'''

#Proxy model for the file model
#Filters only dirs
#Filters only the rootpath and children
class FileProxyModel(QSortFilterProxyModel):
	def setIndexPath(self, index):
		self._index_path = index
		self.invalidateFilter()

	def filterAcceptsRow(self, sourceRow, sourceParent):
		if hasattr(self, '_index_path'):
			ix = self.sourceModel().index(sourceRow, 0, sourceParent)
			itemIsDir = (Path(self.sourceModel().filePath(ix)).is_dir())
			if self._index_path.parent() == sourceParent and self._index_path != ix or not itemIsDir:
				return False
		return super(FileProxyModel, self).filterAcceptsRow(sourceRow, sourceParent)

#File model for the file tree view
class FileSystemModel(QFileSystemModel):
	def __init__(self, rootPath):
		super().__init__()
		self.fileCount	= {}
		#self.thumbFiles = {}
		self.totalFileCount = 0
		self.allThumbFiles = []
		self.setRootPath(rootPath)
		self.populateModel()

		#self.setRootIndexData()
		
		
	def columnCount(self, parent = QModelIndex()):
		return super(FileSystemModel, self).columnCount()+1

	def data(self, index, role):
		if index.column() == self.columnCount() - 1:
			if role == Qt.DisplayRole:
				return (self.getFileCount(index))
			#if role == Qt.TextAlignmentRole:
			#	return Qt.AlignHCenter

		return super(FileSystemModel, self).data(index, role)
	
	#new def
	def getFileCount(self, index):
		if self.filePath(index) in self.fileCount:		
			return str(self.fileCount[self.filePath(index)])
		else:
			return('--')

	def populateModel(self):

		#input file path and returns a list of parent directories until and including root path
		def getParents(_rootPath,filePath):
			paths = []
			parentPath = os.path.dirname(filePath)
			paths.append(parentPath)
			
			while parentPath != _rootPath:
				parentPath = os.path.dirname(parentPath)
				paths.append(parentPath)

			return paths

		#count = 0
		it = QDirIterator(self.rootPath(), ['*_tn.*'],  QDir.Files, QDirIterator.Subdirectories)
		while it.hasNext():
			fileName = it.next()
			dirName = os.path.dirname(fileName)
			parentDirs = getParents(self.rootPath(), fileName)

			self.allThumbFiles.append(fileName)

			for parentDir in parentDirs:
				try:
					self.fileCount[parentDir] = self.fileCount[parentDir] + 1
				except:
					self.fileCount[parentDir] = 1

			self.fileCount[fileName] = '--'
			#count += 1

		self.totalFileCount = self.fileCount[self.rootPath()]
	
	'''	
	def getFileCount(self, index):
		if index in self.fileCount:
			#print('present', (self.fileCount[index]))
			return str(self.fileCount[index])
		else:
			#print(self.filePath(index))
			i = 0
			fileList = []
			it = QDirIterator((self.filePath(index)), ['*_tn.*'],  QDir.Files, QDirIterator.Subdirectories)
			while it.hasNext():
				i+=1
				file = it.next()
				fileList.append(file)
				
			if i == 0:
				i = '-'
			self.fileCount[index] = i
			self.thumbFiles[(self.filePath(index))] = fileList
			return str(self.fileCount[index])
	
	def getTotalFiles(self):
		fileList = []
		it = QDirIterator((self.rootPath()), ['*_tn.*'],  QDir.Files, QDirIterator.Subdirectories)
		while it.hasNext():
			file = it.next()
			fileList.append(file)

		self.totalFileCount = len(fileList)
		self.allThumbFiles = fileList
		self.thumbFiles[self.rootPath()] = fileList
	'''	

class MainWindow(QMainWindow):
	
	def __init__(self, poliigonThumbPath, poliigonMapsPath):
		super().__init__()
		self.left = 150
		self.top = 150
		self.width = 960
		self.height = 480
		self.poliigonThumbPath = poliigonThumbPath
		self.poliigonMapsPath = poliigonMapsPath
		self.dbPath = os.path.join(self.poliigonThumbPath, 'poliigon.json')
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

		self.actionReBuildDB = QAction('Re-Build Database', MainWindow)
		self.actionReBuildDB.setObjectName("actionReBuildDB")

		self.actionReBuildDBAssets = QAction('Re-Build Assets Database', MainWindow)
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

		if item['assets'] and item['assetsRes']:
			containsInDB = True
			#get highest res from a list of res, string comparisson works in this case, hires > 6k > 3k
			highestRes = (item['assetsRes'].index(max(item['assetsRes'])))
			basedir = item['assets'][highestRes]
			assetsRes = item['assetsRes']

			#list of lists of all asset files in all resolutions
			assetFiles = [
				[
					os.path.join(_dir, f)
					for f in os.listdir(_dir) 
						if os.path.isfile(os.path.join(_dir, f)) 
						and getExt(os.path.join(_dir, f)) != '.db'
				] 
				for _dir in item['assets']
			]

		return {'containsInDB': containsInDB, 'assetFiles': assetFiles, 'basedir':basedir, 'assetsRes': assetsRes, 'webSource': webSource, 'assetDims': assetDims}

	#insert string at pattern, replaces pattern
	def insertReplaceString(self, inString, insertString, pattern):
		x = inString.rfind(pattern)
		if x > -1:
			return (inString[:x] + insertString + inString[(x+len(pattern)):])
		else:
			return inString

	def initializeItemList(self,index, filterName='', filterAvailable=False):
		
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
				searchResult = self.db.search( (self.dbQuery.thumb.search(thisDir, flags=re.IGNORECASE)) & (self.dbQuery.name.search(filterName, flags=re.IGNORECASE)))
			else:
				searchResult = self.db.search( (self.dbQuery.thumb.search(thisDir, flags=re.IGNORECASE)) & (self.dbQuery.name.search(filterName, flags=re.IGNORECASE)) & ~(self.dbQuery.assets == []) )

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
				
				self.iconListModel.setData(qMIndex ,item['thumb'], Qt.UserRole + 1) #thumbPath
				
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
		if len(text) >=3:
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
		#self.db.close()
		#self.db = TinyDB(self.dbPath, storage=CachingMiddleware(JSONStorage))
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

	def getWebSource(self, thumbFilePath):
		fLocation = os.path.dirname(thumbFilePath) + '/webSource.txt'
		try:
			f = open(fLocation, 'r')
			result = f.readline()
			f.close()
			return result
		except:
			return ''

	def getDimensions(self, thumbFilePath):
		fLocation = os.path.dirname(thumbFilePath) + '/dimensions.txt'
		try:
			f = open(fLocation, 'r')
			result = f.readline()
			f.close()
			return result
		except:
			return ''

	#Updates everything, updates thumbs and assets directory
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
		#for i in range(5):
		for i in range(self.fileModel.totalFileCount):
			file = self.fileModel.allThumbFiles[i]
			thumbFileName, fEx = os.path.splitext(file)
			assetsList = []
			assetsResList = []
			
			webSource = self.getWebSource(file)
			assetDims = self.getDimensions(file)
			
			#Get filename from path without ext, remove the '_tn' from the end
			assetName = (PurePath(thumbFileName).stem)[:-3]
			searchName = assetName.replace(' ','')

			if assetsDict.get(searchName) != None:
				assetsList = assetsDict.get(searchName).get('assets')
				assetsResList = assetsDict.get(searchName).get('assetsRes')

			#Get filename from path without ext, remove spaces and remove the '_tn' from the end
			#searchName = (((PurePath(thumbFileName).stem).replace(' ',''))[:-3])
			searchName =  assetName.replace(' ','')

			purchased = True if assetsList != [] else False
			measured = True if assetDims != '' else False

			#borderIcon 							(file, size, containsInDB, measured=None, asBytes=False):
			base64Image = self.iconListModel.borderIcon(file, self.iconListView.iconSize(), purchased, measured, True)
			#print(file)
			self.db.insert({'name': assetName,'thumb': file, 'assets': assetsList, 'assetsRes': assetsResList, 'webSource': webSource, 'assetDims': assetDims, 'image':base64Image})
				#self.db.insert({'thumb': file, 'assets': assetsList, 'assetsRes': assetsResList})
			
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
		
		def resFromDirPath(_dir):
			res = ''
			assetRes = PurePath(_dir).stem.split('_')
			if len(assetRes) > 1:
				res = assetRes[-1]
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
					assetsRes = resFromDirPath(thisDir)	
					
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

	#need a new creator that uses the list of results
	#issue with thread safe iterator
	@pyqtSlot()	
	def createItemIcons(self):
		try:
			batch = self.iterImg.nextBatch()
			#print(self.iterImg)
			#print(batch)
			#print(self.iterImg.getI())
			
			
			for count, item in enumerate(batch):
				i = count + self.iterImg.getI()
				self.threadpoolQLength = self.threadpoolQLength + 1
				
				qMIndex = self.iconListModel.index(i,0)
				smallThumbPath = self.insertReplaceString(item['thumb'],'_tnSmall.','_tn.')
				
				#if contains a small thumbnail then set it otherwise use the large image
				if os.path.isfile(smallThumbPath):
					self.iconListModel.setData(qMIndex, smallThumbPath, Qt.UserRole + 8) #smallThumbPath
					smallThumb = smallThumbPath
				else:
					self.iconListModel.setData(qMIndex, item['thumb'], Qt.UserRole + 8) #smallThumbPath
					smallThumb = item['thumb']
				
				parsedItem = self.parseSearchResult(item)

				self.iconListModel.setData(qMIndex, parsedItem['assetFiles'], Qt.UserRole + 2)
				self.iconListModel.setData(qMIndex, parsedItem['basedir'], Qt.UserRole + 3)
				self.iconListModel.setData(qMIndex, parsedItem['containsInDB'], Qt.UserRole + 4)
				self.iconListModel.setData(qMIndex, parsedItem['webSource'], Qt.UserRole + 5)
				self.iconListModel.setData(qMIndex, parsedItem['assetDims'], Qt.UserRole + 6)
				self.iconListModel.setData(qMIndex, parsedItem['assetsRes'], Qt.UserRole + 7)

				#print(item['image'],'\n image', random.randint(0,1000000))
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
		except:
			print('bad error')
		
	
	def loadItemIcon(self, i, thisModel, _bytes, **kwargs):
		icon = thisModel.loadIconFromBase64(_bytes)
		return (i, icon)

	'''
	def getFileNumber(self, path):
		def getExt(path):
			filename, file_extension = os.path.splitext(path)
			return(file_extension)
		DIR = os.path.dirname(os.path.abspath(path))
		return (len([name for name in os.listdir(DIR) if os.path.isfile(name) and getExt(path)!='.txt']))

	
	def borderIcon (self, input, borderColour):
		input = QPixmap.fromImage(input)
		p = QPainter(input)
		pen = QPen()
		pen.setColor(borderColour)
		pen.setWidth(1)
		p.setPen(pen)
		p.drawRect(0,0,input.width()-1,input.height()-1)
		p.end()
		return input

	def transparentIcon (self, input, borderColour):
		input = QPixmap.fromImage(input)
		image = QImage(input.size(),QImage.Format_ARGB32_Premultiplied)
		image.fill(Qt.transparent)
		p = QPainter(image)
		p.setOpacity(0.5)
		p.drawPixmap(0,0,input)
		p.setOpacity(1.0)
		pen = QPen()
		pen.setColor(borderColour)
		pen.setWidth(1)
		p.setPen(pen)
		p.drawRect(0,0,input.width()-1,input.height()-1)
		p.end()
		return image
	
	
	#expects full file path	
	def getStemFromPath(self, path):
		return PurePath(os.path.dirname(os.path.abspath(path))).stem
	'''


if __name__ == '__main__':
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	app.setPalette(palette)

	config = configparser.ConfigParser()
	config.read('poliigonBrowser.ini')
	configuration = False

	poliigonMapsPath = ''
	poliigonThumbsPath = ''
	
	appIcon = icons.qIconFromBase64(icons.appIconBase64)

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
