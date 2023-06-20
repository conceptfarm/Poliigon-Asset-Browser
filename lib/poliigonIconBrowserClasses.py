#Python Classes
import os
from pathlib import PurePath, Path
import webbrowser
from math import floor
import glob
import base64

# PyQt Classes
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Custom Classes
from lib.poliigonMaxScriptClass import MaxScriptCreator
from lib.poliigonBase64ToImage import Base64ToImage
from lib.poliigonImageCollection import imageCollectionBase64
from lib.poliigonDarkPalette import QtDarkPalette

palette = QtDarkPalette()
icons = imageCollectionBase64()
b64ToImage = Base64ToImage()

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
		placeholder.fill(Qt.green)
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
	
	# centers this widget to the center of the main window 
	def centerPos(self):
		self.adjustSize()
		parentGeo = self.parent.parent.parent().geometry()
		selfGeo = self.geometry()
		offset = parentGeo.center() - selfGeo.center()
		selfGeo.translate(offset)
		self.setGeometry(selfGeo)

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

	# generates and fits a large preview image into a preview image max size
	def formatPreviewImage(self, previewImagePath):
		findPath = previewImagePath.replace('.json','_tn.*')
		thumbFile = glob.glob(findPath)
		if len(thumbFile) > 0:
			previewImage = QPixmap(thumbFile[0])
			if previewImage.width() > self.previewMaxSize.width() or previewImage.height() > self.previewMaxSize.height():
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
		else:
			return QPixmap() #empty image

	def populateData(self, _index):
		itemData = self._model.itemData(_index)

		# convert dims string '[W, H]' to 'Wm x Hm'
		def formatDims(dimString):
			dimList = dimString.strip('][').split(', ')
			return (dimList[0] + 'm x ' + dimList[1] + 'm')

		def formatLink(filePath, webLink=True):
			if webLink:
				return '<a href="'+filePath+'">'+filePath+'</a>'
			else:
				return ('<a href="file:///'+filePath+'">'+filePath+'</a>')

		# Make nice dims and assetRes
		previewImage = self.formatPreviewImage(itemData[self._model.jsonPathRole])
		contains = 'Yes' if itemData[self._model.containsRole] else 'No'
		assetDir = formatLink(itemData[self._model.baseDirRole],False) if itemData[self._model.baseDirRole] else '--'
		assetRes = ', '.join(itemData[self._model.assetsResRole]) if itemData[self._model.assetsResRole] else '--'
		webSource = formatLink(itemData[self._model.websourceRole]) if itemData[self._model.websourceRole] else '--'
		dims = formatDims(itemData[self._model.assetDimsRole]) if itemData[self._model.assetDimsRole] else '--'
		
		self.previewWidget.setPixmap(previewImage)
		self.previewWidget.adjustSize()
		self.dbPath_result_lbl.setText(formatLink(os.path.dirname(itemData[self._model.jsonPathRole]),False))
		self.contains_result_lbl.setText(contains)
		self.assetPath_result_lbl.setText(assetDir)
		self.res_result_lbl.setText(assetRes)
		self.web_result_lbl.setText(webSource)
		self.dims_result_lbl.setText(dims)
		self.setMaximumHeight(150)
		self.centerPos()

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
		self.setGridSize(QSize(self.calculateSize(), self.iconSpaceSize))
		super().resizeEvent(e)

	def setSizing(self):
		self.setMinimumWidth(self.iconSpaceSize + 2 + self.verticalScrollBar().width())
		self.viewport().setMinimumWidth(self.iconSpaceSize + 2)
		self.setGridSize(QSize(self.iconSpaceSize,self.iconSpaceSize))

	def startDrag(self, e):
		itemData = self.model().itemData(self.currentIndex())
		
		assetFiles = itemData[self.model().assetFilesRole] # +2
		contains = itemData[self.model().containsRole]
		dims = itemData[self.model().assetDimsRole]
		assetsRes = itemData[self.model().assetsResRole]
		itemName = itemData[Qt.DisplayRole]
		
		if contains:
			#creating a maxscript file here with a function to execute in max
			#itemName = (((PurePath(jsonFile).stem).replace(' ','')).split('.'))[0]
			#itemName = ((PurePath(jsonFile).stem).replace(' ',''))[:-3] # -3 to remove _tn
			
			#tempMSFile = createMSFile(basedir, assetsRes, assetFiles, dims, itemName)
			scriptCreator = MaxScriptCreator(assetsRes, assetFiles, dims, itemName)
			tempMSFile = scriptCreator.create()

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
	rulerIcon = b64ToImage.qImageFromBase64(icons.rulerIconBase64)
	checkmarkIcon = b64ToImage.qImageFromBase64(icons.checkmarkBase64)
	
	def __init__(self):
		super().__init__()
		self.progress_callback = pyqtSignal()
		
		self.jsonPathRole = Qt.UserRole +1
		self.assetFilesRole = Qt.UserRole + 2 		# asset files
		self.baseDirRole = Qt.UserRole + 3 			# base dir, dir of highest res asset
		self.containsRole = Qt.UserRole + 4 		# contains
		self.websourceRole = Qt.UserRole + 5 		# websource
		self.assetDimsRole = Qt.UserRole + 6 		# dimensions
		self.assetsResRole = Qt.UserRole + 7 		# assets resolution list
		self.smallThumbPathRole = Qt.UserRole + 8 	# small thumb path
	
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
		_icon = b64ToImage.qIconFromBase64(_bytes, True)
		return _icon
	
	
	def updateIconFromBase64 (self, _bytes, containsInDB=True):
		originalImage = b64ToImage.qIconFromBase64(_bytes, True)

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
		buffer = QBuffer(bArray)
		buffer.open(QIODevice.WriteOnly)
		originalImage.save(buffer, "JPG")
		return base64.b64encode(bArray).decode('UTF-8') #str(bArray.toBase64())[2:-1]

	# takes base64 image string from json asset file
	# size, contains, measured  
	# return either QIcon or image as base64 in bytes
	# border icon gets added to the overall db and later display as an icon
	# consider serialzing QIcon object instead of image
	# try moving contains and measured to loadIconFromBase64 method
	def borderIcon (self, base64String, size, containsInDB, measured=None, outputType='base64JPG'):
		bgImage = QPixmap(size)
		#bgImage.fill(Qt.transparent)
		bgImage.fill(palette.baseColour)

		#originalImage = QImage(file)
		originalImage = b64ToImage.qImageFromBase64(base64String, True)

		if originalImage.isNull() == False:
			p = QPainter(bgImage)
			source = QRectF(0,0,originalImage.width(),originalImage.height())
			target = self.centerFit(originalImage.size(), size)
			p.drawImage(target,originalImage,source)	
			
			if measured:
				p.drawImage(QPoint(5,(size.height()-5-self.rulerIcon.height())),self.rulerIcon)
			
			if containsInDB:
				#p.drawImage(QPoint(5, 5),self.checkmarkIcon)
				pen = QPen()
				pen.setColor(Qt.green)
				pen.setWidth(3)
				p.setPen(pen)
				p.drawRect(0,0,size.width()-1,size.height()-1)
			
			p.end()
		
		if outputType == 'base64JPG':
			bArray = QByteArray()
			_buffer = QBuffer(bArray)
			_buffer.open(QIODevice.WriteOnly)
			bgImage.save(_buffer, "JPG")
			return base64.b64encode(bArray).decode('UTF-8') #str(bArray.toBase64())[2:-1]
		
		elif outputType == 'pixmap':
			return bgImage
		
		elif outputType == 'base64QIcon':
			# cache the whole QIcon
			_icon = QIcon(bgImage)
			buffer = QByteArray()
			write_stream = QDataStream(buffer, QIODevice.WriteOnly)
			write_stream << _icon
			return base64.b64encode(buffer).decode('UTF-8')
		
		else:
			return QIcon(bgImage)


	def data(self, index, role):
		return super(IconListModel, self).data(index, role)
	
	def setData(self, index, value, role):
		return super(IconListModel, self).setData(index, value, role)

	def setThumbs(self, tup):
		index, icon = tup
		try:
			self.setData(index, icon, Qt.DecorationRole)
		except:
			pass
	
	def exploreAsset(self, index):
		if self.data(index, self.containsRole): #if purchased go to file
			path = self.data(index, self.baseDirRole)
			try:
				os.startfile(path)
			except:
				print("no file directory exists")
		else:
			try:
				webSource = self.data(index, self.websourceRole)
				if webSource != None:
					webbrowser.open_new(webSource)
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
