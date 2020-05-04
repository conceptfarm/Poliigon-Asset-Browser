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
	
	- root folder display
	- large size thumbnail preview
	- config on startup (build database, thumbs folder, assets folder)
	- checkbox -> display only purchased
	- root item should have the count data and all the thumb images, so check on that
	- fix pngs with jpeg extension

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


'''

import os
import traceback, sys
import platform
from pathlib import PurePath
import webbrowser
from math import floor
import tempfile
import time

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

from PyQt5.QtWidgets import (QWidget, QProgressDialog, QMessageBox ,QMainWindow ,QSplitter, QHBoxLayout, QFileSystemModel,QTreeView,QListView, QStyle,QLabel, QLineEdit, QComboBox, QPushButton, QApplication, QStyleFactory, QGridLayout, QVBoxLayout, QLayout, QSizePolicy, QProgressBar, QPlainTextEdit, QButtonGroup, QRadioButton, QCheckBox, QFrame, QSpacerItem ,QMenuBar, QMenu,QStatusBar,QAction)
from PyQt5.QtCore import Qt, QCoreApplication, QRect, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QSize,QModelIndex,QMetaObject,QDir,QDirIterator,QByteArray, QUrl, QMimeData, QVariant,QTimer,QPoint
from PyQt5.QtGui import QIcon,QPixmap,QStandardItemModel,QStandardItem,QImage, QPainter, QPalette, QColor, QPen, QResizeEvent, QDrag


rulerBase64 = b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAAFFmlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTAzLTI3VDAzOjM4OjU5LTA0OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMC0wMy0yN1QwMzo0MDowNS0wNDowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMC0wMy0yN1QwMzo0MDowNS0wNDowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo0ZjlhOGI1Ni02OWMyLTI5NDgtODA4Zi0wYTViZDA3MTFhZWUiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6NGY5YThiNTYtNjljMi0yOTQ4LTgwOGYtMGE1YmQwNzExYWVlIiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6NGY5YThiNTYtNjljMi0yOTQ4LTgwOGYtMGE1YmQwNzExYWVlIj4gPHhtcE1NOkhpc3Rvcnk+IDxyZGY6U2VxPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iY3JlYXRlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo0ZjlhOGI1Ni02OWMyLTI5NDgtODA4Zi0wYTViZDA3MTFhZWUiIHN0RXZ0OndoZW49IjIwMjAtMDMtMjdUMDM6Mzg6NTktMDQ6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7FQijGAAAA+0lEQVRIDWP4//8/A5nYBIgvA/FzHPg+EEcwUGDBSiD+CsTrceCnIEsosWAzED8GYg4oZkGTXwvyCSUWbATiz0A8F4o9qG0ByAcP8chTxQfvgbgICYdR2weg1GKEhNWGVBDRJQ5AqWgqFLvQwgegfCAAxRxDMohARcVSJFw1ID4wgHK2A/FWKI2Ot2JhvyTWgpNQr96FpgoQ/RpaGt6F4o9Qw5DVgPBbtCBCxiD1T0EW3AbinVBbl0LpLCC2QnJNLxBLoKlBZ+P0AV0t8MBhgR0Qc1HDAhj2A2IdHBorqGEBsXhwWHAZmqbXk4EfE1PpB0DT9HMy8FNCzRYAW1JcK+CIZ7gAAAAASUVORK5CYII='

iconBase64 = b'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAIAAADYYG7QAAAABnRSTlMAAAAAAABupgeRAAAEYUlEQVRYhd2ZzW8bRRiHn9nvXX/E+SAFEkCqygVVolJBoFZCVIJKlUBccuGWK/8Afw4CAUVwgBsttIC49JBDewFVQsCptGkS7Di2d73r3RkOcRLbya7Xa/vCe9zdeeeZmd+88867ghmYwPIAos70vvSpHdiUVyitYFfQTJIeKpnGnyjeVNNxarg1dPPkYRIR7BM0C2MVAxLYFbxFDAdxyoNSxF38OmEb1PyBTBdvCauE0LI+U5KwjV8n7s4NSDdxF3GqaEbeJjImaBLsI3szBRI6ThV3EcPKi3JsSpFEBA26Byg5PZDAKuEtYbpnyGUirJ6PXyfys4WV2Yfh4C1iVdAy5SITwhaAXUHLjCMyIWwT1InDCYE0A7eGU0PPlIuSRD5+nZ4PHM2lN2Yukx7dQ2HFOYCE1t/Sup3lVynikKBB2BpShtCwq3iL6FaR5qNAloe7hOWN2dKZQwTQTNwazsJkEzwKZHosrI0XQXQYXVJFcGKGg7eEXR4zPBnT/Ide0G908kLTsloqRS/ArxN18sbfuMvBE+wSbuYmFfpgv/lCXBwS7NNt5gkkw6YI20RB/jA2DkjGdA8IGiSZofZw9Cpl5lRC0CDq9IWVqYpxQME+nb0x36yu8c4GMubut+w9Sf0siWjvAHhLUwBlr1GpwtUb3PiQ9fNIyWvXuHWTez8StAs6HErQDAu7Oiq9qHOs/yEzTC5dZfNj3t2gtgIgBLVlXr3ChYs06+xtn9235fXTy0ELD44lkfvcHrQXLvDBJq9fwyuPvjItLl3h5Yvcu8P3X/Do70l9Z0aINFt5iefO46amRKJUrb63sbr5kdAnTpELLJnAD3n4G/v/svwMldpItLc19XxFW18wxO7j+t3bows3lyXTNDotfrnF7w946zpvvk1lASl15EpJWy3prqlPnLoeWSEgQAiEYHeb777kwRbX369dvvxs1aw4OgUS6RkA9bE0lOLPh1bYfvGNVxzXVWmxMbcVEvUpLJEkQslpWYDZAM3UCgCpnEdsEgRqcjkV0lB7Dymxy2nHZNw6aPz8w/bXn5FMfH8tBJSEtLYJvX4GPWCyF7Xub21/9Wnr/paKU/LJ2QMBqH7MdKrYC4CS0v/rj6fffN746XbSST9c5wZ0SCUJ9um2Zdl+evOTxq93ou3HY5pkp7NDObVdpro2enS0d/DrueCESE3QDk23zk7QlKL56Li2NN0MjfhNs0lu4rMDSmEZn+SnAkmJkogcCYOmI3Ps55zXIJUMBraB7mWPuIvQ0Y2T0ZyZflTOYTgkUWqE1Ey8ZcqrWJkToyRRh/bOYBfDSxb59Lrjr9KagbOAVZ7HVfqUhpSk2+xfWdxaqkfAdDDOYVfmXGwYonVAEJ9asto6VunkwUzLMZm7LGd5UNPHzCUTFKzmve0nLunNGWjyomcBIEUcYrpzKgsX+rUQ+SQ9dAPNSC2ct3fx66kVrXT7n/xaGDDdxlvErgBHhZtoGn9TAx06md3vqf8AWEoJPWt5ZeMAAAAASUVORK5CYII='

def getExt(path):
	filename, file_extension = os.path.splitext(path)
	return(file_extension)


#creates a temp .ms file to be dropped into max window
#should be deleted after drop somewhere
def createMSFile(basepath, fileList, dimensions, materialName):
	
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




	tempMSFile = tempfile.NamedTemporaryFile(mode = 'w+', newline='\n',suffix='.ms',delete=False)
	selectors = ['_AO_' , '_COL_' , '_DISP_' , '_DISP16_' , '_GLOSS_' , '_NRM_' , '_NRM16_' , '_REFL_' , '_SSS_' , '_TRANSMISSION_' , '_DIRECTION_' ,'_ALPHAMASKED_']
	und = 'undefined'
	maxArray = '#('
	new_array = [und for i in selectors]
	#print(new_array)

	if len(fileList) == 1:
		#just one file, probably a graphic, set
		new_array[1] = [basepath + '\\' + fileList[0]]
		if getExt(fileList[0]) == '.png':
			new_array[-1] = new_array[1]
	else:
		colorVariations = []
		dispVariations = []
		alphaVariations = []
		for f in fileList: 
			for i in range(len(selectors)): 
				if selectors[i] in f and selectors[i] == '_COL_': 
					colorVariations.append(basepath + '\\' + f)
				elif selectors[i] in f and selectors[i] == '_DISP_': 
					dispVariations.append(basepath + '\\' + f)
				elif selectors[i] in f and selectors[i] == '_ALPHAMASKED_': 
					alphaVariations.append(basepath + '\\' + f)
				elif selectors[i] in f:
					new_array[i] = basepath + '\\' + f
		
		new_array[1] = colorVariations
		new_array[2] = dispVariations
		new_array[-1] = alphaVariations

		'''
		1 - alphamask is present, no color present -> copy to color
		2 - color is present in png format -> copy to alphamask

		'''

		if len(new_array[1]) > 0 and len(new_array[-1]) == 0:
			if getExt(colorVariations[0]) == '.png':
				new_array[-1] = new_array[1]
				print(new_array[-1])
				print(new_array[1])
		elif len(new_array[-1]) > 0 and len(new_array[1]) == 0:
			new_array[1] = new_array[-1]

	#weird name no selectors
	if len(new_array[1]) == 0 and len(fileList) != 0:
		colorVariations = []
		alphaVariations = []
		for f in fileList:
			colorVariations.append(basepath + '\\' + f)
			if getExt(f) == '.png':
				alphaVariations.append(basepath + '\\' + f)

		new_array[1] = colorVariations
		new_array[-1] = alphaVariations

	n = pyListToMaxArray(new_array)
	#print(n)

	tempMSFile.write('matArray=' + n + '\n')
	tempMSFile.write('matDimensions=' + ('undefined' if dimensions == None else str(dimensions)) + '\n')
	tempMSFile.write('print matArray' + '\n')
	tempMSFile.write('print matDimensions' + '\n')
	tempMSFile.write('getSourceFileName()' + '\n')
	#tempMSFile.write('pyPoliigonMaterial = pyPoliigonStruct pyMaterialArray:matArray pyDimensions:matDimensions pyScriptFilePath:getSourceFileName()' + '\n')
	tempMSFile.write('pyPoliigonMaterial.pyMaterialArray = matArray; pyPoliigonMaterial.pyDimensions=matDimensions; pyPoliigonMaterial.pyMaterialName="'+materialName+'"; pyPoliigonMaterial.pyScriptFilePath=getSourceFileName()' + '\n')
	tempMSFile.write('pyPoliigonMaterial.show()' + '\n')
	tempMSFile.close()

	return tempMSFile

def iconFromBase64(base64):
	pixmap = QPixmap()
	pixmap.loadFromData(QByteArray.fromBase64(base64))
	icon = QIcon(pixmap)
	return icon

def imageFromBase64(base64):
	_image = QImage()
	_image.loadFromData(QByteArray.fromBase64(base64))
	return _image

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

class IconListView(QListView):
	iconSpaceSize = 180
	
	def __init__(self):
		super().__init__()
		self.setSizing()

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
		super(IconListView, self).resizeEvent(e)

	def setSizing(self):
		self.setMinimumWidth(self.iconSpaceSize+2+self.verticalScrollBar().width())
		self.viewport().setMinimumWidth(self.iconSpaceSize+2)
		self.setGridSize(QSize(self.iconSpaceSize,self.iconSpaceSize))

	def startDrag(self, e):
		
		#print(self.selectedIndexes())
		#print(e.index())
		#thisItem = self.model().itemFromIndex(self.currentIndex())
		thumb = self.model().data(self.currentIndex() , Qt.UserRole + 1)
		assets = self.model().data(self.currentIndex() , Qt.UserRole + 2)
		basedir = self.model().data(self.currentIndex() , Qt.UserRole + 3)
		contains = self.model().data(self.currentIndex() , Qt.UserRole + 4)
		dims = self.model().data(self.currentIndex() , Qt.UserRole + 6)
		
		if contains:
			#creating a maxscript file here with a function to execute in max
			itemName = (((PurePath(thumb).stem).replace(' ',''))[:-3])
			tempMSFile = createMSFile(basedir, assets, dims, itemName)

			url = QUrl.fromLocalFile(tempMSFile.name)
			mime = QMimeData()
			mime.setUrls([url])
			drag = QDrag(self)
			drag.setMimeData(mime)
			drag.exec(Qt.CopyAction | Qt.CopyAction);

	def keyPressedEvent(self, _key):
		print(_key)


class IconListModel(QStandardItemModel):
	
	issueUpdate = pyqtSignal()
	rulerIcon = imageFromBase64(rulerBase64)
	def __init__(self):
		super().__init__()
		self.progress_callback = pyqtSignal()
	

	def borderIcon (self, input, borderColour=Qt.gray, borderWidth=0, measured=None):
		
		if borderWidth > 0:
			p = QPainter(input)
			if measured:
				p.drawImage(QPoint(5,(input.height()-5-self.rulerIcon.height())),self.rulerIcon)
			pen = QPen()
			pen.setColor(borderColour)
			pen.setWidth(borderWidth)
			p.setPen(pen)
			p.drawRect(0,0,input.width()-1,input.height()-1)
			p.end()
		return input

	def data(self, index, role):
		return super(IconListModel, self).data(index, role)
	

	def setData(self, index, value, role):
		return super(IconListModel, self).setData(index, value, role)

	def setThumbs(self, tup):
		index, img = tup
		containsInDB = self.data(index,Qt.UserRole + 4)
		
		if containsInDB:
			transImg = self.borderIcon(img, Qt.green, 3, (self.data(index,Qt.UserRole+6)))
			icon = QIcon((transImg))
		else:
			icon = QIcon((img))
			
		self.setData(index, icon, Qt.DecorationRole)
		#self.dataChanged.emit(index,index)

	def setWebSource(self, index):
		if self.data(index,Qt.UserRole+4):
			fLocation = os.path.dirname(self.data(index,Qt.UserRole+1)) + '/webSource.txt'
			try:
				f = open(fLocation, 'r')
				self.setData(index, f.readline(), Qt.UserRole+5)
				f.close()
			except:
				pass

	def setDimensions(self, index):
		if self.data(index,Qt.UserRole+4):
			fLocation = os.path.dirname(self.data(index,Qt.UserRole+1)) + '/dimensions.txt'
			try:
				f = open(fLocation, 'r')
				self.setData(index, ((f.readline()).strip('][').split(', ')) , Qt.UserRole+6)
				f.close()
			except:
				pass
	
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

class viewerSystemModel(QFileSystemModel):
	def __init__(self):
		super().__init__()
		self.fileCount	= {}
		self.thumbFiles = {}
		self.totalFileCount = 0
		self.allThumbFiles = []
		self.setRootIndexData()
		
		
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

	def setRootIndexData(self):
		index = (self.index(self.rootPath()))
		print(index)
		c = self.getFileCount(index)
		print(c)



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
		self.dbQuery = Query()
		self.icon = iconFromBase64(iconBase64)
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
		
		self.filterPurchased = QPushButton('Filter Available', self)
		self.filterPurchased.setMinimumSize(80,23)
		self.filterPurchased.setObjectName('filterPurchased')
		self.filterPurchased.setCheckable(True)
		#self.filterPurchased.clicked[bool].connect(self.showDebugLog)


		self.alphaLabel = QPushButton('Test 2' , self)
		self.alphaLabel.setMinimumSize(80,23)

		self.searchBar = QLineEdit('' , self)
		self.searchBar.setMinimumHeight(23)
		self.searchBar.setObjectName('searchBar')
		self.searchBar.setPlaceholderText('Search')
		
		self.gridLayoutControlls.addWidget(self.filterPurchased, 0, 0, 1, 1, Qt.AlignTop)
		self.gridLayoutControlls.addWidget(self.alphaLabel, 0, 1, 1, 1, Qt.AlignTop)
		self.gridLayoutControlls.addWidget(self.searchBar, 0, 2, 1, 1, Qt.AlignTop)
		
		self.dirModel = viewerSystemModel()
		self.dirModel.setRootPath(self.rootPath)
		self.dirModel.getTotalFiles()

		

		self.treeView = QTreeView()
		self.treeView.setModel(self.dirModel)
		self.treeView.setObjectName('treeView')
		#homeIndex = self.dirModel.parent(self.dirModel.index(self.rootPath))
		#self.treeView.setRootIndex(homeIndex)
		self.treeView.setRootIndex(self.dirModel.index(self.rootPath))
		self.treeView.resizeColumnToContents(0)
		self.treeView.setRootIsDecorated(True)
		#self.treeView.setHeaderHidden(False)
		self.treeView.hideColumn(1)
		self.treeView.hideColumn(2)
		self.treeView.hideColumn(3)
		self.treeView.setColumnWidth(0,280)
		
		self.filesmodel = IconListModel()
		#self.filesmodel = QStandardItemModel()

		self.listView = IconListView()
		self.listView.setModel(self.filesmodel)
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

		#timer for triggering item list icon population
		self.tmr = QTimer()
		self.tmr.timeout.connect(self.createItemIcons)
		
		self.show()

	
	#@pyqtSlot(QResizeEvent)
	#def resizeEvent(self, e):
	#	print('resize event', self.sender(), e)

	@pyqtSlot()
	def on_searchBar_editingFinished(self):
		print('editing finished')

	@pyqtSlot()
	def on_searchBar_returnPressed(self):
		print('return pressed')

	@pyqtSlot(str)
	def on_searchBar_textEdited(self, e):
		#print('text edited', e)
		if len(e) > 3:
			self.tmr.stop()
			self.filesmodel.clear()
			self.threadpool.releaseThread()
			self.threadpool.clear()
			#thisDir = (self.dirModel.filePath(self.treeView.currentIndex()))
			allFileList = self.dirModel.allThumbFiles

			fileList = []
			for f in allFileList:
				#print(e, ' ', os.path.basename(f))
				if e.lower() in os.path.basename(f.lower()):
					fileList.append(f)

			self.statusbar.showMessage('Found ' + str(len(fileList)) + ' matches')

			self.iterImg = NthIterator(fileList, 10)

			for i in range(len(fileList)):		
				newItem = IconListItem(self.listView.iconSize(), self.listView.gridSize(), os.path.basename(fileList[i]))
				newItem.setToolTip(fileList[i])
				newItem.setEditable(False)
				self.filesmodel.setItem(i, newItem)
				qMIndex = self.filesmodel.index(i,0)
				self.filesmodel.setData(qMIndex ,fileList[i], Qt.UserRole + 1) #thumbPath
			
			self.listView.scrollToTop()
			
			self.tmr.start(150)


	@pyqtSlot(bool)
	def on_filterPurchased_clicked(self, e):
		print('test1 clicked', e)
		bricks = (self.dirModel.rootPath())
		print(self.dirModel.rootPath()+'/Bricks')
		print(self.dirModel.getFilesFromPath(bricks))

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
		self.statusbar.showMessage('Database has been updated')

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
					assetsList.append(os.path.dirname(os.path.abspath(thisFile)))
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
				filesDir.append(filesInDir[0])
		return filesDir


	@pyqtSlot(QModelIndex)
	def on_listView_clicked(self, index):	
		self.sender().model().setDimensions(index)
		print('set dims')
	
	@pyqtSlot(QModelIndex)
	def on_listView_doubleClicked(self, index):
		#thisItem = (self.filesmodel.itemFromIndex(self.listView.currentIndex()))
		
		#print(self.sender().model().data(index, Qt.UserRole + 3))
		
		#self.sender().model().setWebSource(index)
		#self.sender().model().setDimensions(index)
		self.sender().model().exploreAsset(index)
		'''
		if thisItem.purchased:
			#print(self.filesmodel.data(self.listView.currentIndex(), Qt.UserRole + 1))
			#print(thisItem.assetFiles)
			path = os.path.realpath(thisItem.assetBaseDir)
			os.startfile(path)
		else:
			webbrowser.open_new(thisItem.webSource)
		'''
	
	def checkIfContains(self, file, db, query):
		containsInDB = False
		assetFiles = []
		basedir = ''
	
		if db.contains(query.thumb == file):
			containsInDB = True
			s = db.search(query.thumb == file)
			
			#get the first instance and first asset - this is fine, other instances are just duplicates
			#might need to change if need more choice in asset types 1k, 3k, hires - right now just the first on the list
			basedir = s[0]['assets'][0]
			assetFiles = [f for f in os.listdir(basedir) if os.path.isfile(os.path.join(basedir, f)) and getExt(os.path.join(basedir, f)) != '.db' ]

		return {'containsInDB': containsInDB, 'assetFiles': assetFiles, 'basedir':basedir}

	def setSearchedData(self, thisModel, fileList):
		for i in range(len(fileList)):	
			searchResult = self.checkIfContains(fileList[i], self.db, self.dbQuery)
			qMIndex = thisModel.index(i,0)
			thisModel.setData(qMIndex, searchResult['assetFiles'], Qt.UserRole + 2)
			thisModel.setData(qMIndex, searchResult['basedir'], Qt.UserRole + 3)
			thisModel.setData(qMIndex, searchResult['containsInDB'], Qt.UserRole + 4)


	@pyqtSlot(QModelIndex)
	def on_treeView_clicked(self,index):
		self.tmr.stop()
		self.filesmodel.clear()
		
		self.threadpool.releaseThread()
		self.threadpool.clear()
		
		thisDir = self.dirModel.filePath(self.treeView.currentIndex())
		fileList = self.dirModel.getFilesFromPath(thisDir)
		
		self.iterImg = NthIterator(fileList, 10)
		
		for i in range(len(fileList)):		
			newItem = IconListItem(self.listView.iconSize(), self.listView.gridSize(), os.path.basename(fileList[i]))
			newItem.setToolTip(fileList[i])
			newItem.setEditable(False)
			self.filesmodel.setItem(i, newItem)
			qMIndex = self.filesmodel.index(i,0)
			self.filesmodel.setData(qMIndex ,fileList[i], Qt.UserRole + 1) #thumbPath
		
		self.listView.scrollToTop()

		self.tmr.start(150)
	
	@pyqtSlot()	
	def createItemIcons(self):
		self.threadpool.setMaxThreadCount(3)
		try:
			next(self.iterImg)
			for j in range(self.iterImg.nth):
				i = j + self.iterImg.getI()
				if i < (self.filesmodel.rowCount()):
					qMIndex = self.filesmodel.index(i,0)
					thumb = (self.filesmodel.data(qMIndex , Qt.UserRole + 1))
					searchResult = self.checkIfContains(thumb, self.db, self.dbQuery)
					self.filesmodel.setData(qMIndex, searchResult['assetFiles'], Qt.UserRole + 2)
					self.filesmodel.setData(qMIndex, searchResult['basedir'], Qt.UserRole + 3)
					self.filesmodel.setData(qMIndex, searchResult['containsInDB'], Qt.UserRole + 4)
					self.filesmodel.setDimensions(qMIndex)


					worker = Worker(self.List, 'tuple', thumb, self.listView.iconSize(), qMIndex, self.filesmodel)
					worker.signals.progressTuple.connect(self.filesmodel.setThumbs)
					self.threadpool.start(worker)	
		
		except StopIteration:
			self.sender().stop()


	def List(self, file, size, i, thisModel, progress_callback):
		originalImage = QPixmap(file)
		if originalImage.isNull() == False:
			scaledImage = QPixmap(originalImage.scaled(size))
			if scaledImage.isNull() == False:
				progress_callback.emit((i, scaledImage))


	def getFileNumber(self, path):
		def getExt(path):
			filename, file_extension = os.path.splitext(path)
			return(file_extension)
		DIR =  os.path.dirname(os.path.abspath(path))
		#print (len([name for name in os.listdir(DIR) if os.path.isfile(name) and getExt(path)!='.txt']))
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
