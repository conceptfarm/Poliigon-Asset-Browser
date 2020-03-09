'''
sources:
	multithreading:
	https://www.learnpyqt.com/courses/concurrent-execution/multithreading-pyqt-applications-qthreadpool/
	
	thumbnail framework:
	https://stackoverflow.com/questions/26829754/how-to-use-the-threads-to-create-the-images-thumbnail
'''
'''
TODO:
	- convert to pyside to be usable in max
	- double click thumb -> build material
	- double click thumb -> if asset not downloaded take to the poliigon website
	- dark theme would be nice
	- large size thumbnail preview

'''

import os
import traceback, sys
import platform

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFileSystemModel,QTreeView,QListView,  QStyle,QLabel, QComboBox, QPushButton, QApplication, QStyleFactory, QGridLayout, QVBoxLayout, QLayout, QSizePolicy, QProgressBar, QPlainTextEdit, QButtonGroup, QRadioButton, QCheckBox, QFrame, QSpacerItem )
from PyQt5.QtCore import Qt, QCoreApplication, QRect, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QSize,QModelIndex,QMetaObject,QDir,QDirIterator
from PyQt5.QtGui import QIcon,QPixmap,QStandardItemModel,QStandardItem,QImage


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
		self.treeView.setRootIndex(self.model.index(self.rootPath))
		self.treeView.resizeColumnToContents(0)

		self.listView = QListView()
		self.listView.setModel(self.filesmodel)
		self.listView.setViewMode(1)
		self.listView.setResizeMode(1)
		self.listView.setWrapping(True)
		self.listView.setWordWrap(True)
		self.listView.setGridSize(QSize(180,180))
		self.listView.setUniformItemSizes(True)
		self.listView.setIconSize(QSize(120,120))

		windowLayout = QHBoxLayout()
		windowLayout.addWidget(self.treeView)
		windowLayout.addWidget(self.listView)
		self.setLayout(windowLayout)

		QMetaObject.connectSlotsByName(self) # auto connects defs on_Object_signal to object signal

		self.show()


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
			self.filesmodel.setItem(i, QStandardItem(QIcon(placeholder), os.path.basename(fileList[i])))

		#start workers for each thumbnail to generate
		for i in range(len(fileList)):
			worker = Worker(self.List, fileList[i], self.listView.iconSize(), i)
			worker.signals.progress.connect(self.setThumbs)
			self.threadpool.start(worker)


	def List(self, file, size, i, progress_callback):
		originalImage = QImage(file)
		if originalImage != None:
			scaledImage = QImage(originalImage.scaled(size))
			if scaledImage != None:
				progress_callback.emit((i, scaledImage))

	
	def setThumbs(self, tup):
		index, img = tup
		#index = tup[0]
		#img = tup[1]
		icon = QIcon(QPixmap.fromImage(img))
		item = QStandardItem(self.filesmodel.item(index))
		self.filesmodel.setItem(index, QStandardItem(icon, item.text()))


if __name__ == '__main__':
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	ex = MainWindow()
	sys.exit(app.exec_())
