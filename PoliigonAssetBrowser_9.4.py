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
from pathlib import PurePath
import webbrowser
from math import floor
import tempfile
import time
import configparser
import re
import pickle

#tinyDB Classes
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
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
	
#using reimplemented def
class CustomProxyModel(QSortFilterProxyModel):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.nameRegExp = ""
		self.roleRegExp = ""
	
	def filterAcceptsRow(self, sourceRow, sourceParent):
		index = self.sourceModel().index(sourceRow, 0, sourceParent)

		#name = str(self.sourceModel().data(index, Qt.DisplayRole)).lower()
		role = str(self.sourceModel().data(index, Qt.UserRole + 4))

		return (self.roleRegExp in role)

	def setNameFilter(self, text):
		self.nameRegExp = text.lower()
		self.invalidateFilter()
	
	def setRoleFilter(self, text):
		self.roleRegExp = text
		self.invalidateFilter()

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
		self._sourceModel = None
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

		# middle column buttons
		'''
		self.goto_dbPath_btn = QPushButton('', self)
		self.goto_assetPath_btn = QPushButton('', self)
		self.goto_web_btn = QPushButton('', self)

		self.goto_dbPath_btn.setIcon(self.folderIcon)
		self.goto_assetPath_btn.setIcon(self.folderIcon)
		self.goto_web_btn.setIcon(self.folderIcon)

		self.goto_dbPath_btn.setFixedSize(QSize(20, 20))
		self.goto_assetPath_btn.setFixedSize(QSize(20, 20))
		self.goto_web_btn.setFixedSize(QSize(20, 20))
		'''
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
		_sourceIndex = self._model.mapToSource(_index)
		itemData = self._sourceModel.itemData(_sourceIndex)

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
		self._sourceModel = self._model.sourceModel()
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
		
		#print('viewport ', (self.viewport().width()))
		#print('itemsInRow ', itemsInRow)
		#print('itemsInModel ', itemsInModel)
		#print('scrollbarwidth ', self.verticalScrollBar().width())
		
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
		
		#print(self.selectedIndexes())
		#print(e.index())
		#thisItem = self.model().itemFromIndex(self.currentIndex())

		#Maybe replace with itemData function
		thumb = self.model().data(self.currentIndex() , Qt.UserRole + 1)
		assetFiles = self.model().data(self.currentIndex() , Qt.UserRole + 2)
		basedir = self.model().data(self.currentIndex() , Qt.UserRole + 3)
		contains = self.model().data(self.currentIndex() , Qt.UserRole + 4)
		dims = self.model().data(self.currentIndex() , Qt.UserRole + 6)
		assetsRes = self.model().data(self.currentIndex() , Qt.UserRole + 7)
		
		if contains:
			#creating a maxscript file here with a function to execute in max
			#itemName = (((PurePath(thumb).stem).replace(' ','')).split('.'))[0]
			itemName = (((PurePath(thumb).stem).replace(' ',''))[:-3]) # -3 to remove _tn
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
			#sourceIndex = self.model().mapToSource(self.currentIndex())
			#thisData = self.model().sourceModel().itemData(sourceIndex)			
			self.previewWindow.showPreviewWindow(self.model(), self.currentIndex())
			#self.previewWindow.showPreviewWindow(self.model().sourceModel(), self.model().mapToSource(self.currentIndex()))


			#does not return UserRoles, have to get them from the sourceModel
			#otherData = self.model().itemData(self.currentIndex())
			#print('other data\n',otherData)
	
	

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

	def loadIconFromBytes (self, _bytes):
		#base64 = ('b'+"'"+_bytes+"'").decode('UTF-8')
		base64 = bytes(_bytes,'utf-8')
		#print(base64)
		pixmap = QPixmap()
		pixmap.loadFromData(QByteArray.fromBase64(base64))
		_icon = QIcon(pixmap)
		return _icon

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
			pickedArray = pickle.dumps(bArray)
			#print(str(bArray.toBase64())[2:-1])
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

class viewerSystemModel(QFileSystemModel):
	def __init__(self):
		super().__init__()
		self.fileCount	= {}
		self.thumbFiles = {}
		self.totalFileCount = 0
		self.allThumbFiles = []

		#self.setRootIndexData()
		
		
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
			it = QDirIterator((self.filePath(index)), ['*_tn.*'],  QDir.Files, QDirIterator.Subdirectories)
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
	def setRootIndexData(self):
		index = (self.index(self.rootPath()))
		#print(index)
		c = self.getFileCount(index)
		#print(c)
	'''
	def getTotalFiles(self):
		fileList = []
		it = QDirIterator((self.rootPath()), ['*_tn.*'],  QDir.Files, QDirIterator.Subdirectories)
		while it.hasNext():
			file = it.next()
			fileList.append(file)

		self.totalFileCount = len(fileList)
		self.allThumbFiles = fileList
		self.thumbFiles[self.rootPath()] = fileList


class MainWindow(QMainWindow):
	
	def __init__(self,poliigonThumbPath,poliigonMapsPath):
		super().__init__()
		self.left = 150
		self.top = 150
		self.width = 960
		self.height = 480
		self.poliigonThumbPath = poliigonThumbPath
		self.poliigonMapsPath = poliigonMapsPath
		self.previousDir = self.poliigonThumbPath
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


		self.filterAll = QPushButton('Search All' , self)
		self.filterAll.setMinimumSize(80,23)
		self.filterAll.setObjectName('filterAll')
		self.filterAll.setCheckable(True)

		self.searchBar = QLineEdit('' , self)
		self.searchBar.setMinimumHeight(23)
		self.searchBar.setObjectName('searchBar')
		self.searchBar.setPlaceholderText('Search')
		
		self.gridLayoutControlls.addWidget(self.filterPurchased, 0, 0, 1, 1, Qt.AlignTop)
		self.gridLayoutControlls.addWidget(self.filterAll, 0, 1, 1, 1, Qt.AlignTop)
		self.gridLayoutControlls.addWidget(self.searchBar, 0, 2, 1, 1, Qt.AlignTop)
		
		self.dirModel = viewerSystemModel()
		self.dirModel.setRootPath(self.poliigonThumbPath)
		self.dirModel.getTotalFiles()
		self.dirModel.setFilter( QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs)

		self.treeView = QTreeView()
		self.treeView.setModel(self.dirModel)
		self.treeView.setObjectName('treeView')
		#homeIndex = self.dirModel.parent(self.dirModel.index(self.poliigonThumbPath))
		#self.treeView.setRootIndex(homeIndex)
		self.treeView.setRootIndex(self.dirModel.index(self.poliigonThumbPath))
		self.treeView.resizeColumnToContents(0)
		self.treeView.setRootIsDecorated(True)
		#self.treeView.setHeaderHidden(False)
		self.treeView.hideColumn(1)
		self.treeView.hideColumn(2)
		self.treeView.hideColumn(3)
		self.treeView.setColumnWidth(0,280)
		
		self.filesmodel = IconListModel()
		self.proxyModel = CustomProxyModel(self)
		#self.proxyModel = QSortFilterProxyModel(self)
		self.proxyModel.setSourceModel(self.filesmodel)
		self.proxyModel.setFilterCaseSensitivity(False)
		#self.filesmodel = QStandardItemModel()

		self.listView = IconListView(self.centralwidget)
		#self.listView.setModel(self.filesmodel)
		self.listView.setModel(self.proxyModel)
		self.listView.setObjectName('listView')
		self.listView.setViewMode(1)
		self.listView.setResizeMode(1)
		self.listView.setWrapping(True)
		self.listView.setWordWrap(True)
		self.listView.setUniformItemSizes(True)
		#self.listView.setLayoutMode(QListView.Batched)
		#self.listView.setBatchSize(15)
		self.listView.setIconSize(self.listView.gridSize()*0.85)


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
		self.statusbar.setContentsMargins(11,0,0,0) #int left, int top, int right, int bottom
		MainWindow.setStatusBar(self.statusbar)
		self.statusbar.addWidget(self.statusBarProgress,1)
		self.statusbar.setFixedHeight(5)
		#self.statusbar.adjustSize()

		self.actionReBuildDB = QAction('Re-Build Database', MainWindow)
		self.actionReBuildDB.setObjectName("actionReBuildDB")

		self.actionGenResImages = QAction('Generate Lower Resolution Files', MainWindow)
		self.actionGenResImages.setObjectName("actionGenResImages")

		self.actionGenThumbImages = QAction('Generate Small Thumbnails', MainWindow)
		self.actionGenThumbImages.setObjectName("actionGenThumbImages")

		self.menuFile.addAction(self.actionReBuildDB)
		self.menuFile.addAction(self.actionGenResImages)
		self.menuFile.addAction(self.actionGenThumbImages)
		self.menubar.addAction(self.menuFile.menuAction())

		#self.listView.doubleClicked.connect(self.test)
		# auto connects defs on_Object_signal to object signal 
		# !use setObjectName, won't work with var name
		QMetaObject.connectSlotsByName(self) 

		#timer for triggering item list icon population
		self.tmr = QTimer()
		self.tmr.timeout.connect(self.createItemIcons)
		
		self.show()


	def searchDB(self, file, db, query):
		containsInDB = False
		assetFiles = []
		assetsRes = []
		basedir = ''
		webSource = ''
		assetDims = ''
	
		#if db.contains(query.thumb == file):
		#	containsInDB = True
		s = db.get(query.thumb == file)
		webSource = s['webSource']
		assetDims = s['assetDims']

		if s['assets'] and s['assetsRes']:
			containsInDB = True
			#get highest res from a list of res, string comparisson works in this case, hires > 6k > 3k
			highestRes = (s['assetsRes'].index(max(s['assetsRes'])))
			basedir = s['assets'][highestRes]
			assetsRes = s['assetsRes']

			#list of lists of all asset files in all resolutions
			assetFiles = [
				[
					os.path.join(_dir, f)
					for f in os.listdir(_dir) 
						if os.path.isfile(os.path.join(_dir, f)) 
						and getExt(os.path.join(_dir, f)) != '.db'
				] 
				for _dir in s['assets']
			]

		return {'containsInDB': containsInDB, 'assetFiles': assetFiles, 'basedir':basedir, 'assetsRes': assetsRes, 'webSource': webSource, 'assetDims': assetDims}

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
		x=inString.rfind(pattern)
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

			self.filesmodel.clear()
			thisDir = self.treeView.model().filePath(index)
			print(thisDir)
			#self.treeView.setEnabled(False)

			#get all assets with the path containing selected directory
			if filterAvailable == False:
				searchResult = self.db.search( (self.dbQuery.thumb.search(thisDir, flags=re.IGNORECASE)) & (self.dbQuery.name.search(filterName, flags=re.IGNORECASE)))
			else:
				searchResult = self.db.search( (self.dbQuery.thumb.search(thisDir, flags=re.IGNORECASE)) & (self.dbQuery.name.search(filterName, flags=re.IGNORECASE)) & ~(self.dbQuery.assets == []) )

			'''
			if doPreFilter:
				allFileList = self.dirModel.getFilesFromPath(thisDir)
				fileList = [ f for f in allFileList if preFilterName.lower() in os.path.basename(f.lower())]
			else:
				fileList = self.dirModel.getFilesFromPath(thisDir)
			'''

			#iterator for thumb image creation, batches of 10
			self.iterImg = NthIterator(searchResult, 10)
			
			self.statusBarProgress.setMinimum(0)
			self.statusBarProgress.setValue(0)
			self.statusBarProgress.setMaximum(len(searchResult))

			for count, item in enumerate(searchResult):		
				newItem = IconListItem(self.listView.iconSize(), self.listView.gridSize(), item['name'])
				newItem.setEditable(False)
				
				self.filesmodel.appendRow(newItem)
				qMIndex = self.filesmodel.index(count,0)
				
				self.filesmodel.setData(qMIndex ,item['thumb'], Qt.UserRole + 1) #thumbPath
				
			self.listView.scrollToTop()

			#trigger item icon creation by starting the timer
			self.tmr.start()
		else:
			print('waiting')
			self.threadpool.waitForDone(500)

	def initializeItemList_old(self,index,doPreFilter=False,preFilterName=''):
		
		self.tmr.stop()
		self.threadpool.clear()
		QApplication.processEvents()
		self.statusBarProgress.show()
		activeThreads = self.threadpool.activeThreadCount()
		if activeThreads >= 0:
			#waitForDone = self.threadpool.globalInstance().waitForDone(500)	

			self.filesmodel.clear()
			thisDir = self.treeView.model().filePath(index)
			print(thisDir)
			self.treeView.setEnabled(False)
			if doPreFilter:
				allFileList = self.dirModel.getFilesFromPath(thisDir)
				fileList = [ f for f in allFileList if preFilterName.lower() in os.path.basename(f.lower())]
			else:
				fileList = self.dirModel.getFilesFromPath(thisDir)

			self.iterImg = NthIterator(fileList, 10)
			
			self.statusBarProgress.setMinimum(0)
			self.statusBarProgress.setValue(0)
			self.statusBarProgress.setMaximum(len(fileList))

			for i in range(len(fileList)):		
				newItem = IconListItem(self.listView.iconSize(), self.listView.gridSize(), os.path.basename(fileList[i]))
				newItem.setEditable(False)
				
				self.filesmodel.appendRow(newItem)
				qMIndex = self.filesmodel.index(i,0)
				smallThumbPath = self.insertReplaceString(fileList[i],'_tnSmall.','_tn.')
				self.filesmodel.setData(qMIndex ,fileList[i], Qt.UserRole + 1) #thumbPath
				
				if os.path.isfile(smallThumbPath):
					self.filesmodel.setData(qMIndex ,smallThumbPath, Qt.UserRole + 8) #smallThumbPath
				else:
					self.filesmodel.setData(qMIndex ,fileList[i], Qt.UserRole + 8) #smallThumbPath
			
			self.listView.scrollToTop()

			#trigger item icon creation by starting the timer
			self.tmr.start(250)
		else:
			print('waiting')
			self.threadpool.waitForDone(500)

	def endProgressGenResWindow(self):
		self.threadpool.clear()
		self.threadpool.maxThreadCount()
		self.progressWindow.close()
		self.on_actionReBuildDB_triggered()
	
	def endProgressUpdateDBWindow(self):
		self.threadpool.clear()
		self.threadpool.maxThreadCount()
		self.progressWindow.close()
		self.db.close()
		self.db = TinyDB(self.dbPath, storage=CachingMiddleware(JSONStorage))
		self.statusbar.showMessage('Database has been updated')


	@pyqtSlot()
	def on_searchBar_editingFinished(self):
		print('editing finished')

	@pyqtSlot()
	def on_searchBar_returnPressed(self):
		print('return pressed')
	
	@pyqtSlot(str)
	def on_searchBar_textEdited(self, text):
		#old non-custom proxy
		#self.proxyModel.setFilterRole(Qt.DisplayRole)
		#self.proxyModel.setFilterRegExp(text)
		
		if self.filterAll.isChecked() and len(text) >=3:
			self.initializeItemList(self.treeView.rootIndex(),text,self.filterPurchased.isChecked())
		else:
			self.initializeItemList(self.treeView.currentIndex(),text,self.filterPurchased.isChecked())
			#self.proxyModel.setNameFilter(text)

	
	#TODO: set search through all from above
	@pyqtSlot(bool)
	def on_filterAll_clicked(self, e):
		if e:
			self.sender().setStyleSheet('background-color:'+palette.toRGBCSS(palette.highlightColour)+';')
			self.sender().setText("Search Selected")
			if len(self.searchBar.text()) >= 3:
				self.initializeItemList(self.treeView.rootIndex(), self.searchBar.text(), self.filterPurchased.isChecked())
			#self.proxyModel.setRoleFilter(True)
		else:
			self.sender().setStyleSheet('background-color:'+palette.toRGBCSS(palette.baseAltColour)+';')
			self.sender().setText("Search All")
			currentDir = self.treeView.model().filePath(self.treeView.currentIndex())
			if currentDir != '':
				self.initializeItemList(self.treeView.currentIndex(), self.searchBar.text(), self.filterPurchased.isChecked())
			#self.proxyModel.setRoleFilter(False)

	@pyqtSlot(bool)
	def on_filterPurchased_clicked(self, e):
		if e:
			self.sender().setStyleSheet('background-color:'+palette.toRGBCSS(palette.highlightColour)+';')
			self.sender().setText("Show All")
			
			if self.filterAll.isChecked():
				self.initializeItemList(self.treeView.rootIndex(), self.searchBar.text(), True)
			else:
				self.initializeItemList(self.treeView.currentIndex(), self.searchBar.text(), True)
			#self.proxyModel.setRoleFilter("True")
		else:
			self.sender().setStyleSheet('background-color:'+palette.toRGBCSS(palette.baseAltColour)+';')
			self.sender().setText("Show Available")
			
			if self.filterAll.isChecked():
				self.initializeItemList(self.treeView.rootIndex(), self.searchBar.text(), False)
			else:
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

		self.progressWindow = QProgressDialog('Generating Small Thumbnails...', '', 0, len(self.dirModel.allThumbFiles), self.centralwidget, Qt.FramelessWindowHint)
		self.progressWindow.setObjectName('progressWindow')
		self.progressWindow.setWindowModality(Qt.WindowModal)
		self.progressWindow.setCancelButton(None)
		self.progressWindow.show()

		self.gr = GenerateSmallThumbs(self.dirModel.allThumbFiles, False)
		self.threadpool.setMaxThreadCount(1)
		worker = Worker(self.gr.main,'int')
		worker.signals.progressInt.connect(self.progressWindow.setValue)
		worker.signals.finished.connect(self.endProgressGenResWindow)
		self.threadpool.start(worker)

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
		
		try:
			self.db.close()
			os.remove(self.dbPath)
			self.db = TinyDB(self.dbPath, storage=(CachingMiddleware(JSONStorage)))
			doUpdateDB = True
		except:
			self.progressWindow.close()
			self.messageBox = QMessageBox.critical(self.centralwidget, 'DB Update Error', 'The database is currently in use elsewhere.\nPlease close all other asset browsers and try again.')

		
		if doUpdateDB:
			self.progressWindow.setLabelText('Getting Files...')
			allFiles = self.collectPurchasedFiles()
			self.progressWindow.setLabelText('Updating Database...')
			self.progressWindow.setMinimum(0)
			self.progressWindow.setMaximum(self.dirModel.totalFileCount)
			
			self.threadpool.setMaxThreadCount(1)
			worker = Worker(self.updateDB,'int', allFiles)
			worker.signals.progressInt.connect(self.progressWindow.setValue)
			worker.signals.finished.connect(self.endProgressUpdateDBWindow)
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

	#update db should have all instances of the asset folder 3K 1K HiRes, add those types to db as well
	#error in matching such as tiles04 matches to tiles042 and tiles043, need to do exact match
	#TODO: add metalness maps
	def updateDB(self, searchInFiles, progress_callback):
		#for each thumbnail in the model
		#for i in range(5):
		for i in range(self.dirModel.totalFileCount):
			file = self.dirModel.allThumbFiles[i]
			thumbFileName, fEx = os.path.splitext(file)
			assetsList = []
			assetsResList = []
			
			webSource = self.getWebSource(file)
			assetDims = self.getDimensions(file)
			
			#Get filename from path without ext, remove the '_tn' from the end
			assetName = (PurePath(thumbFileName).stem)[:-3]

			#Get filename from path without ext, remove spaces and remove the '_tn' from the end
			#searchName = (((PurePath(thumbFileName).stem).replace(' ',''))[:-3])
			searchName =  assetName.replace(' ','')


			for j in range(len(searchInFiles)):
				#first file in a purchased directory
				thisFile = searchInFiles[j]
				
				#split out just the file name up to the first _
				if searchName == (os.path.basename(thisFile).split('_'))[0]:
					#append just the directory path of the file ie Y:\Maps\Poliigon_com\Fence_Mesh_Grate\FenceChainLink001_6k
					assetsList.append(os.path.dirname(os.path.abspath(thisFile)))
					#create list by spliting the file name ie ['FenceChainLink001', 'COL', '6K.png']
					assetRes = os.path.basename(thisFile).split('_')
					if len(assetRes) > 1:
						#if last element is ex. "metalness.jpg" then get the second to last element
						#which should be the res designation
						if (assetRes[-1].split('.'))[0].lower() == 'metalness':
							assetsResList.append(assetRes[-2])
						else:
							assetsResList.append((assetRes[-1].split('.'))[0])
					else:
						assetsResList.append('HIRES')

			#if len(assetsList) > 0:
			purchased = True if len(assetsList) > 0 else False
			measured = True if assetDims != '' else False

			#borderIcon (file, size, containsInDB, measured=None, asBytes=False):
			pickledImage = self.filesmodel.borderIcon(file, self.listView.iconSize(), purchased, measured, True)
			#print(file)
			self.db.insert({'name': assetName,'thumb': file, 'assets': assetsList, 'assetsRes': assetsResList, 'webSource': webSource, 'assetDims': assetDims, 'image':(pickledImage)})
				#self.db.insert({'thumb': file, 'assets': assetsList, 'assetsRes': assetsResList})
			
			#need this here, update every 20th otherwise buffer overrun error
			if i%20==0:
				try:
					progress_callback.emit(i)
				except:
					print('error')

	def collectPurchasedFiles(self):
		filesDir = []
		it = QDirIterator(self.poliigonMapsPath, (QDir.Dirs | QDir.NoDotAndDotDot ),  QDirIterator.Subdirectories)
		while it.hasNext():
			thisDir = it.next()
			filesInDir = [f.path for f in os.scandir(thisDir) if f.is_file()]
			if len(filesInDir) > 0:
				#we use the file instead of the dir name because dir names don't match the thumb name
				filesDir.append(filesInDir[0])
		return filesDir

	@pyqtSlot(QModelIndex)
	def on_listView_clicked(self, index):	
		pass
		#sourceIndex = self.sender().model().mapToSource(index)
		#self.sender().model().sourceModel().setDimensions(sourceIndex)
	
	@pyqtSlot(QModelIndex)
	def on_listView_doubleClicked(self, index):
		sourceIndex = self.sender().model().mapToSource(index)
		self.sender().model().sourceModel().exploreAsset(sourceIndex)
	
	'''
	@pyqtSlot(QKeyEvent)
	def on_listView_pressed(self, ev):
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
				
				qMIndex = self.filesmodel.index(i,0)
				smallThumbPath = self.insertReplaceString(item['thumb'],'_tnSmall.','_tn.')
				
				#if contains a small thumbnail then set it otherwise use the large image
				if os.path.isfile(smallThumbPath):
					self.filesmodel.setData(qMIndex ,smallThumbPath, Qt.UserRole + 8) #smallThumbPath
					smallThumb = smallThumbPath
				else:
					self.filesmodel.setData(qMIndex ,item['thumb'], Qt.UserRole + 8) #smallThumbPath
					smallThumb = item['thumb']
				
				parsedItem = self.parseSearchResult(item)

				self.filesmodel.setData(qMIndex, parsedItem['assetFiles'], Qt.UserRole + 2)
				self.filesmodel.setData(qMIndex, parsedItem['basedir'], Qt.UserRole + 3)
				self.filesmodel.setData(qMIndex, parsedItem['containsInDB'], Qt.UserRole + 4)
				self.filesmodel.setData(qMIndex, parsedItem['webSource'], Qt.UserRole + 5)
				self.filesmodel.setData(qMIndex, parsedItem['assetDims'], Qt.UserRole + 6)
				self.filesmodel.setData(qMIndex, parsedItem['assetsRes'], Qt.UserRole + 7)
				
				#worker = Worker(self.createItemImage, None, smallThumb, self.listView.iconSize(), qMIndex, self.filesmodel, parsedItem['containsInDB'])
				worker = Worker(self.createItemImage, None, qMIndex, self.filesmodel, item['image'])
				#worker = Worker(self.createItemImage, None, item, self.listView.iconSize(), qMIndex, self.filesmodel)
				worker.signals.finished.connect(self.releasePoolThread)
				worker.signals.result.connect(self.filesmodel.setThumbs)
				self.threadpool.start(worker, self.threadpoolQLength)	
				
		except StopIteration:
			self.sender().stop()
			self.threadpool.clear()
			self.statusBarProgress.hide()
			self.treeView.setEnabled(True)
		except:
			print('bad error')
		
	@pyqtSlot()	
	def createItemIcons_old(self):
		try:
			next(self.iterImg)
			for j in range(self.iterImg.nth):
				i = j + self.iterImg.getI()
				if i < (self.filesmodel.rowCount()):
					self.threadpoolQLength = self.threadpoolQLength + 1
					
					qMIndex = self.filesmodel.index(i,0)
					thumb = (self.filesmodel.data(qMIndex , Qt.UserRole + 1))
					smallThumb = (self.filesmodel.data(qMIndex , Qt.UserRole + 8))
					searchResult = self.searchDB(thumb, self.db, self.dbQuery)
					
					self.filesmodel.setData(qMIndex, searchResult['assetFiles'], Qt.UserRole + 2)
					self.filesmodel.setData(qMIndex, searchResult['basedir'], Qt.UserRole + 3)
					self.filesmodel.setData(qMIndex, searchResult['containsInDB'], Qt.UserRole + 4)
					self.filesmodel.setData(qMIndex, searchResult['webSource'], Qt.UserRole + 5)
					self.filesmodel.setData(qMIndex, searchResult['assetDims'], Qt.UserRole + 6)
					self.filesmodel.setData(qMIndex, searchResult['assetsRes'], Qt.UserRole + 7)
					
					#worker = Worker(self.createItemImage, None, smallThumb, self.listView.iconSize(), qMIndex, self.filesmodel, searchResult['containsInDB'])
					worker.signals.finished.connect(self.releasePoolThread)
					worker.signals.result.connect(self.filesmodel.setThumbs)
					self.threadpool.start(worker, self.threadpoolQLength)	
		
		except StopIteration:
			self.sender().stop()
			self.threadpool.clear()
			self.statusBarProgress.hide()
			self.treeView.setEnabled(True)
		except:
			print('bad error')
	
	# this doesn't actually work well
	def createItemImage3(self, item, size, qMIndex, thisModel, progress_callback):
		
		smallThumbPath = self.insertReplaceString(item['thumb'],'_tnSmall.','_tn.')
				
		#if contains a small thumbnail then set it otherwise use the large image
		if os.path.isfile(smallThumbPath):
			self.filesmodel.setData(qMIndex ,smallThumbPath, Qt.UserRole + 8) #smallThumbPath
			smallThumb = smallThumbPath
		else:
			self.filesmodel.setData(qMIndex ,item['thumb'], Qt.UserRole + 8) #smallThumbPath
			smallThumb = item['thumb']
		
		parsedItem = self.parseSearchResult(item)

		self.filesmodel.setData(qMIndex, parsedItem['assetFiles'], Qt.UserRole + 2)
		self.filesmodel.setData(qMIndex, parsedItem['basedir'], Qt.UserRole + 3)
		self.filesmodel.setData(qMIndex, parsedItem['containsInDB'], Qt.UserRole + 4)
		self.filesmodel.setData(qMIndex, parsedItem['webSource'], Qt.UserRole + 5)
		self.filesmodel.setData(qMIndex, parsedItem['assetDims'], Qt.UserRole + 6)
		self.filesmodel.setData(qMIndex, parsedItem['assetsRes'], Qt.UserRole + 7)

		icon = thisModel.borderIcon(smallThumb, size, parsedItem['containsInDB'], parsedItem['assetDims'])
		return (qMIndex, icon)
	
	def createItemImage(self, i, thisModel, _bytes, progress_callback):
		icon = thisModel.loadIconFromBytes(_bytes)
		return (i, icon)

	#new create image using qimage, seems to work best
	def createItemImage22(self, file, size, i, thisModel, containsInDB, progress_callback):
		icon = thisModel.borderIcon(file, size, containsInDB, (thisModel.data(i,Qt.UserRole+6)))
		return (i, icon)


	#old one using in class functions
	def createItemImage2(self, file, size, i, thisModel, progress_callback):
		originalImage = QPixmap(file)
		if originalImage.isNull() == False:
			scaledImage = QPixmap(originalImage.scaled(size))
			if scaledImage.isNull() == False:

				#use this if using progress_callback callback function, maybe problematic
				#progress_callback.emit((i, scaledImage))
				
				#use this if not using any signals, connection between threads
				thisModel.setThumbs((i, scaledImage))

				#use this if using singals result connected to setThubs, seems still buggy
				#return (i, scaledImage)

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
