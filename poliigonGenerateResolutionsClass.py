import os
import errno
import glob
import ntpath

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from PIL import Image

#Class for looping through the database and generating downsized resolution
#files for each asset

class GenerateResolutions():
	
	#Disable decompression bomb error checking
	Image.MAX_IMAGE_PIXELS = 1000000000
	Image.warnings.simplefilter('ignore', Image.DecompressionBombWarning)
	
	def __init__(self, db, overwrite=False, progress_callback=None):
		self.db = db
		self.overwrite = overwrite
		#self.main()


	#finds in list and returns position in list
	def findInList(self, _find, _list): 
		return [i for i,x in enumerate(_list) if x.lower()==_find]

	#gets all images files and returns a list of files
	def getAllImageFiles(self, inDir):
		imageExt = ['*.jpg','*.jpeg','*.png','*.tiff','*.gif','*.tga','*.tif']
		result=[]
		
		for ext in imageExt:
			fileList = glob.glob(inDir + '/' + ext)
			result = result + fileList

		return result

	#creates a dir and returns the path, if error then False
	def makeSurePathExists(self, path):
		try:
			os.makedirs(path)
			return path
		except OSError as exception:
			#print('dir already here')
			if exception.errno != errno.EEXIST:
				return False
			elif exception.errno == errno.EEXIST:
				return path

	#creates a dir with the resolution parameters at end
	def createAssetDir(self, inPath, outSize):
		return self.makeSurePathExists((inPath + '_' + outSize.upper()))

	#takes a image object and resizes it based on resolution desired
	def resizeFile(self, saveDir, inImageObject, outSize, overwrite=False):
		imgFormat = inImageObject.format
		imgFileName = ntpath.basename(inImageObject.filename)
		f,imageExt = os.path.splitext(inImageObject.filename)
		
		#get the last instance of _ and remove everything after that
		imgFileNameBase = imgFileName[:imgFileName.rfind('_')]

		maxDim = 6114

		if outSize.lower() == '6k':
			maxDim = 6114
		elif outSize.lower() == '4k':
			maxDim = 4096
		elif outSize.lower() == '3k':
			maxDim = 3072
		elif outSize.lower() == '2k':
			maxDim = 2048

		outImageFilePath = str(saveDir + '/' + imgFileNameBase + '_' + outSize + imageExt)
		
		if (os.path.isfile(outImageFilePath) == False or overwrite == True):
			if inImageObject.width >= inImageObject.height:
				width = maxDim
				height = int(maxDim * inImageObject.height/inImageObject.width)
			else:
				height = maxDim
				width = int(maxDim * inImageObject.width/inImageObject.height)


			if inImageObject.mode == 'I;16':
				print('16-bit')
				outImageObject = inImageObject.resize((width, height),resample=Image.NEAREST)
			else:
				outImageObject = inImageObject.resize((width, height),resample=Image.LANCZOS)
			outImageObject.save(outImageFilePath, imgFormat)
			outImageObject.close()


	#gets all images paths and itterates an image object resize
	def doFileResize(self, baseDir, baseRes, resolutionsList, overwrite=False):
		allFiles = self.getAllImageFiles(baseDir)
		
		#base dir is now dir without _resolution part of the path if not hires, 
		#hires paths have no _resolution at end
		if baseRes.lower() != 'hires':
			baseDir = baseDir[:-3]
		
		for file in allFiles:
			print(file)
			fileObject = Image.open(file)
			for res in resolutionsList:
				newDir = self.createAssetDir(baseDir, res)
				if newDir:
					newFile = self.resizeFile(newDir, fileObject, res, overwrite)
			fileObject.close()


	def main(self, **kwargs):
		progress_callback = kwargs['progress_callback']
		#dbiter = iter(db)
		#for i in range(5):
		#	dbEntry = (next(dbiter))
		
		i = 0
		for dbEntry in self.db:
			if (len(self.findInList('hires',dbEntry['assetsRes'])) > 0):
				resolutions = ['6K','4K','3K','2K']
				_index = (self.findInList('hires',dbEntry['assetsRes']))[0]
				self.doFileResize(dbEntry['assets'][_index], dbEntry['assetsRes'][_index], resolutions, self.overwrite)
			
			elif (len(self.findInList('6k',dbEntry['assetsRes'])) > 0):
				resolutions = ['4K','3K','2K']
				_index = (self.findInList('6k',dbEntry['assetsRes']))[0]
				self.doFileResize(dbEntry['assets'][_index], dbEntry['assetsRes'][_index], resolutions, self.overwrite)
			
			elif (len(self.findInList('4k',dbEntry['assetsRes'])) > 0):
				resolutions = ['3K','2K']
				_index = (self.findInList('4k',dbEntry['assetsRes']))[0]
				self.doFileResize(dbEntry['assets'][_index], dbEntry['assetsRes'][_index], resolutions, self.overwrite)
			
			elif (len(self.findInList('3k',dbEntry['assetsRes'])) > 0):
				resolutions = ['2K']
				_index = (self.findInList('3k',dbEntry['assetsRes']))[0]
				self.doFileResize(dbEntry['assets'][_index], dbEntry['assetsRes'][_index], resolutions, self.overwrite)

			i = i + 1

			if progress_callback != None:
				try:
					progress_callback.emit(i)
				except:
					print('error')
		

'''
#use:
rootPath = 'C:/poliigon/'
searchPath = 'Y:/Maps/Poliigon_com/'
dbPath = 'poliigon.json'
db = TinyDB(dbPath, storage=CachingMiddleware(JSONStorage))

gr = GenerateResolutions(db)
db.close()
'''