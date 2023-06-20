#Python Classes
import os
#import traceback, sys
#import platform
from pathlib import PurePath, Path
#import webbrowser
#from math import floor
#import time
#import configparser
#import re
#import random
#import json
#import glob

#from PIL import Image
#from io import BytesIO
#import base64

#tinyDB Classes
# from tinydb import TinyDB, Query
# from tinydb.storages import JSONStorage
# from tinydb.storages import MemoryStorage
# from tinydb.middlewares import CachingMiddleware

#Custom Classes
# from lib.poliigonGenerateResolutionsClass import GenerateResolutions
# from lib.poliigonGenerateSmallThumbsClass import GenerateSmallThumbs
# from lib.poliigonConfigDialogClass import PoliigonBrowserConfigDialog
# from lib.poliigonImageCollection import imageCollectionBase64
# from lib.poliigonBase64ToImage import Base64ToImage
# from lib.poliigonDarkPalette import QtDarkPalette
#from lib.poliigonMaxScriptClass import MaxScriptCreator
#from lib.poliigonIconBrowserClasses import IconListItem, LargePreviewWindow, IconListView, IconListModel

#PyQt Classes
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

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
		self.totalFileCount = 0
		self.allThumbFiles = []
		self.setRootPath(rootPath)
		self.populateModel()
		
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
		def getParents(_rootPath, filePath):
			paths = []
			parentPath = os.path.dirname(filePath)
			paths.append(parentPath)
			
			while parentPath != _rootPath:
				parentPath = os.path.dirname(parentPath)
				paths.append(parentPath)

			return paths

		#count = 0
		it = QDirIterator(self.rootPath(), ['*.json'],  QDir.Files, QDirIterator.Subdirectories)
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
