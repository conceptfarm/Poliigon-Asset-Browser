import os
import errno
from pathlib import PurePath, Path

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from PIL import Image

# Class for looping through the database and generating 
# downsized resolution files for each asset

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
			fileList = [str(item) for item in (Path(inDir).glob(ext))]
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
	def createAssetDir(self, inPath, res, assetWorkflow):
		baseDir = self.removeLeaf(inPath, 1)
		if assetWorkflow != False:
			res = res + '_' + assetWorkflow
		return self.makeSurePathExists( baseDir.joinpath(res.upper()) )

	def createAssetFilePaths(self, inFile, baseDir, resolutionsList, assetWorkflow, overwrite):
		result = {}
		
		imgFileName = PurePath(inFile).stem
		imageExt = PurePath(inFile).suffix
		workflow = ''
		imgFileNameBase = ''
		
		if assetWorkflow != False:
			#metalness/specular we need to remove the resolution and the metalness/specular part
			workflow = '_' + assetWorkflow
			imgFileNameBase = (imgFileName.rsplit('_', maxsplit = 2))[0]
		else:
			#get the last instance of _ and remove everything after that
			imgFileNameBase = (imgFileName.rsplit('_', maxsplit = 1))[0]

		for res in resolutionsList:
			newDir = self.createAssetDir(baseDir, res, assetWorkflow)
			if newDir:
				outImageFilePath = str(str(newDir) + '/' + imgFileNameBase + '_' + res + workflow + imageExt)

				if (os.path.isfile(outImageFilePath) == False or overwrite == True):
					result[res] = outImageFilePath
				else:
					result[res] = False
		return result
	
	#Removes n amount of leaves from a directory - returns processed directory
	def removeLeaf(self, _dir, n):
		result = PurePath('')
		pathParts = PurePath(_dir).parts
		for i in range(0,len(pathParts) - n ):
			result = result.joinpath(pathParts[i])
		return result

	'''
	baseDir can be old style like Bricks10_2k or Bricks10
	or new style like Bricks10/2K or Bricks10/HIRES
	We need to conform all the old style to new
	'''
	def conformPaths(self, baseDir):
		pathParts = PurePath(baseDir).parts
		dir0 = pathParts[-1]
		dir1 = pathParts[-2]
		
		allFiles = self.getAllImageFiles(baseDir)

		if len(allFiles) > 0:
			#Asset name from filename, just use any first file found
			assetName = (PurePath(allFiles[0]).stem).split('_')[0]
			assetRes = (PurePath(allFiles[0]).stem).split('_')[-1]
			assetWorkflow = False
			
			if assetRes.lower() == 'metalness' or assetRes.lower() == 'specular':
				print(allFiles[0])
				assetWorkflow = assetRes.upper() #ie: METALNESS
				assetRes = (PurePath(allFiles[0]).stem).split('_')[-2] + '_' + assetRes.upper() #ie: 4K_METALNESS
				
			#if already conformed to new style (asseName/RES/) do nothing
			if (dir0.lower() == assetRes.lower()) and dir1.lower() == assetName.lower() :
				return (PurePath(baseDir), assetWorkflow)
			else:
				# go to root dir , create a assetName dir and inside create assetRes dir
				# root/assetName/assetRes
				newPath = self.removeLeaf(baseDir, 1).joinpath(assetName).joinpath(assetRes.upper())
				newPathObj = self.makeSurePathExists(newPath)
				if newPathObj != False:
					result = False
					for f in allFiles:
						fileName = PurePath(f).name
						#move files to a new location
						Path(f).rename(newPath.joinpath(fileName))
						
						if Path(newPath.joinpath(fileName)).is_file():
							result = (newPathObj, assetWorkflow)
						else:
							result = (False, False)
							break

					try:
						#sometimes old dirs were not named after the assetName
						os.rmdir(baseDir)
					except:
						print('Couldn\'t delete dir')

					return result
				else:
					return (False, False)
		else:
			return (False, False)
	'''
	#takes a image object and resizes it based on resolution desired
	def resizeFile_old(self, saveDir, inImageObject, outSize, assetWorkflow, overwrite=False):
		imgFormat = inImageObject.format
		imgFileName = PurePath(inImageObject.filename).stem
		imageExt = PurePath(inImageObject.filename).suffix
		workflow = ''
		imgFileNameBase = ''


		if assetWorkflow != False:
			#metalness/specular we need to remove the resolution and the metalness/specular part
			workflow = '_' + assetWorkflow
			imgFileNameBase = (imgFileName.rsplit('_', maxsplit = 2))[0]
		else :
			#get the last instance of _ and remove everything after that
			imgFileNameBase = (imgFileName.rsplit('_', maxsplit = 1))[0]

		maxDim = 6114

		if outSize.lower() == '6k':
			maxDim = 6114
		elif outSize.lower() == '4k':
			maxDim = 4096
		elif outSize.lower() == '3k':
			maxDim = 3072
		elif outSize.lower() == '2k':
			maxDim = 2048

		outImageFilePath = str(str(saveDir) + '/' + imgFileNameBase + '_' + outSize + workflow + imageExt)
		
		if (os.path.isfile(outImageFilePath) == False or overwrite == True):
			if inImageObject.width >= inImageObject.height:
				width = maxDim
				height = int(maxDim * inImageObject.height/inImageObject.width)
			else:
				height = maxDim
				width = int(maxDim * inImageObject.width/inImageObject.height)


			if 'I;16' in inImageObject.mode:
				outImageObject = inImageObject.resize((width, height),resample=Image.NEAREST)
			else:
				outImageObject = inImageObject.resize((width, height),resample=Image.LANCZOS)
			
			outImageObject.save(outImageFilePath, imgFormat)
			outImageObject.close()
	'''
	#takes a image object and resizes it based on resolution desired
	def resizeFile(self, savePath, inImageObject, outSize):

		maxDim = 6114

		if outSize.lower() == '6k':
			maxDim = 6114
		elif outSize.lower() == '4k':
			maxDim = 4096
		elif outSize.lower() == '3k':
			maxDim = 3072
		elif outSize.lower() == '2k':
			maxDim = 2048
		
		if inImageObject.width >= inImageObject.height:
			width = maxDim
			height = int(maxDim * inImageObject.height/inImageObject.width)
		else:
			height = maxDim
			width = int(maxDim * inImageObject.width/inImageObject.height)

		if 'I;16' in inImageObject.mode:
			outImageObject = inImageObject.resize((width, height),resample=Image.NEAREST)
		else:
			outImageObject = inImageObject.resize((width, height),resample=Image.LANCZOS)
		
		outImageObject.save(savePath, inImageObject.format)
		outImageObject.close()

	#gets all images paths and itterates an image object resize
	def doFileResize(self, baseDir, baseRes, resolutionsList, overwrite=False):
		
		#conform assets to the new style directory structure
		baseDir, assetWorkflow = self.conformPaths(baseDir)
		
		if baseDir != False:

			allFiles = self.getAllImageFiles(baseDir)
					
			for file in allFiles:
				filesToCreate = self.createAssetFilePaths(file, baseDir, resolutionsList, assetWorkflow, overwrite)

				if any(filesToCreate.values()) == (not False):
					fileObject = Image.open(file)
					
					for res, newFilePath in filesToCreate.items():
						if newFilePath != False:
							newFile = self.resizeFile(newFilePath, fileObject, res)
							print(newFile)

					fileObject.close()

	def main(self, **kwargs):
		progress_callback = kwargs['progress_callback']
		
		i = 0
		for dbEntry in self.db:
			if (len(self.findInList('hires',dbEntry['assetsRes'])) > 0):
				resolutions = ['6K','4K','3K','2K']
				_index = (self.findInList('hires',dbEntry['assetsRes']))[0]
				self.doFileResize(dbEntry['assets'][_index], dbEntry['assetsRes'][_index], resolutions, self.overwrite)

			elif (len(self.findInList('8k',dbEntry['assetsRes'])) > 0):
				resolutions = ['6K','4K','3K','2K']
				_index = (self.findInList('8k',dbEntry['assetsRes']))[0]
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

			if i % 5 == 0:
				try:
					progress_callback.emit(i)
				except:
					#print('error')
					pass

'''
#use:
rootPath = 'C:/poliigon/'
searchPath = 'Y:/Maps/Poliigon_com/'
dbPath = 'C:/poliigon/poliigon.json'
db = TinyDB(dbPath, storage=CachingMiddleware(JSONStorage))

gr = GenerateResolutions(db)
gr.main()
db.close()
'''