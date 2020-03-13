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
	- grayed out material thumbnails for not purchased materials - needs testing
	- double click thumb -> build material
	- double click thumb -> if asset not purchased -> take to the poliigon website
	- scale thumbs to fit nicely
	
	- dark theme would be nice
	- large size thumbnail preview

'''

import os
import traceback, sys
import platform

from PyQt5.QtWidgets import (QWidget, QSplitter, QHBoxLayout, QFileSystemModel,QTreeView,QListView,  QStyle,QLabel, QComboBox, QPushButton, QApplication, QStyleFactory, QGridLayout, QVBoxLayout, QLayout, QSizePolicy, QProgressBar, QPlainTextEdit, QButtonGroup, QRadioButton, QCheckBox, QFrame, QSpacerItem )
from PyQt5.QtCore import Qt, QCoreApplication, QRect, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QSize,QModelIndex,QMetaObject,QDir,QDirIterator
from PyQt5.QtGui import QIcon,QPixmap,QStandardItemModel,QStandardItem,QImage, QPainter


class WorkerSignals(QObject):
	finished = pyqtSignal()
	error = pyqtSignal(tuple)
	result = pyqtSignal(object)
	progress = pyqtSignal(tuple)


class Worker(QRunnable):
	def __init__(self, fn, fileList, size, i, *args, **kwargs):
		super(Worker, self).__init__()

		# Store constructor arguments (re-used for processing)
		self.fn = fn
		self.args = args
		self.kwargs = kwargs
		self.fileList = fileList
		self.size = size
		self.signals = WorkerSignals()	
		self.i = i

		# Add the callback to our kwargs
		self.kwargs['progress_callback'] = self.signals.progress		

	@pyqtSlot()
	def run(self):
		'''
		Initialise the runner function with passed args, kwargs.
		'''
		
		# Retrieve args/kwargs here; and fire processing using them
		try:
			result = self.fn(self.fileList, self.size, self.i, *self.args, **self.kwargs)
		except:
			traceback.print_exc()
			exctype, value = sys.exc_info()[:2]
			self.signals.error.emit((exctype, value, traceback.format_exc()))
		else:
			self.signals.result.emit(result)  # Return the result of the processing
		finally:
			self.signals.finished.emit()  # Done
		

class MainWindow(QWidget):
	
	def __init__(self):
		super().__init__()
		self.left = 150
		self.top = 150
		self.width = 960
		self.height = 480
		self.setupUi()

	def setupUi(self):
		self.setGeometry(self.left, self.top, self.width, self.height)
		self.threadpool = QThreadPool()
		#self.threadpool.setMaxThreadCount(1)
		self.threadpool.maxThreadCount()
				
		self.rootPath = 'C:/poliigon/'

		self.model = QFileSystemModel()
		self.model.setRootPath(self.rootPath)

		self.filesmodel = QStandardItemModel()

		self.treeView = QTreeView()
		self.treeView.setModel(self.model)
		self.treeView.setObjectName('treeView')
		#homeIndex = self.model.parent(self.model.index(self.rootPath))
		#self.treeView.setRootIndex(homeIndex)
		self.treeView.setRootIndex(self.model.index(self.rootPath))
		self.treeView.resizeColumnToContents(0)
		self.treeView.setRootIsDecorated(True)
		self.treeView.setHeaderHidden(False)
		
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

		self.splitterLayout = QSplitter(self)
		self.splitterLayout.setOrientation(Qt.Horizontal)
		self.splitterLayout.addWidget(self.treeView)
		self.splitterLayout.addWidget(self.listView)
		self.windowLayout = QHBoxLayout(self)
		self.windowLayout.addWidget(self.splitterLayout)
		#windowLayout.addWidget(self.treeView)
		#windowLayout.addWidget(self.listView)
		#self.setLayout(windowLayout)
		
		#self.listView.doubleClicked.connect(self.test)
		QMetaObject.connectSlotsByName(self) # auto connects defs on_Object_signal to object signal !use setObjectName, won't work with var name

		self.show()
	
	
	@pyqtSlot(QModelIndex)
	def on_listView_doubleClicked(self, index):
	#def test(self, index):
		thisItem = (self.filesmodel.itemFromIndex(self.listView.currentIndex()))
		print(thisItem.toolTip())
		self.getFileNumber(thisItem.toolTip())
	
	
	@pyqtSlot(QModelIndex)
	def on_treeView_clicked(self,index):
		self.filesmodel.clear()

		thisDir = (self.model.filePath(self.treeView.currentIndex()))

		#get all the thumbnail images, from scraper they should be *_tn.jpg
		fileList = []
		it = QDirIterator(thisDir, ['*_tn.jpg'],  QDir.Files, QDirIterator.Subdirectories)
		while it.hasNext():
			file = it.next()
			fileList.append(file)

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
		for i in range(len(fileList)):
			worker = Worker(self.List, fileList[i], self.listView.iconSize(), i)
			worker.signals.progress.connect(self.setThumbs)
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
		icon = QIcon(QPixmap.fromImage(img))

		if self.getFileNumber(item.toolTip()) == 0:
			transImg = self.transparentIcon(img)
			icon = QIcon(QPixmap.fromImage(transImg))

		item.setIcon(icon)


	def getFileNumber(self, path):
		def getExt(path):
			filename, file_extension = os.path.splitext(path)
			return(file_extension)
		DIR =  os.path.dirname(os.path.abspath(path))
		print (len([name for name in os.listdir(DIR) if os.path.isfile(name) and getExt(path)!='.txt']))
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


if __name__ == '__main__':
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	ex = MainWindow()
	sys.exit(app.exec_())
