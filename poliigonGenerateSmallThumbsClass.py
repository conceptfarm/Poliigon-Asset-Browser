import os
import errno
import glob


from PIL import Image

#Class for looping through the database and generating downsized resolution
#files for each asset

class GenerateSmallThumbs():
	
	#Disable decompression bomb error checking
	#Image.MAX_IMAGE_PIXELS = 1000000000
	#Image.warnings.simplefilter('ignore', Image.DecompressionBombWarning)
	
	def __init__(self, inputFileList, overwrite=False, progress_callback=None):
		self.inputFileList = inputFileList
		self.overwrite = overwrite


	#takes a image object and resizes it based on resolution desired
	def resizeFile(self, inImageObject, overwrite=False):
		imgFormat = inImageObject.format
		imgFilePath = (inImageObject.filename)
		f,imageExt = os.path.splitext(inImageObject.filename)
		
		#get the last instance of _ and remove everything after that
		imgFileNameBase = imgFilePath[:imgFilePath.rfind('_tn.')]

		maxDim = 200

		outImageFilePath = str(imgFileNameBase + '_tnSmall' + imageExt)
		
		if (os.path.isfile(outImageFilePath) == False or overwrite == True):
			if inImageObject.width >= inImageObject.height:
				width = maxDim
				height = int(maxDim * inImageObject.height/inImageObject.width)
			else:
				height = maxDim
				width = int(maxDim * inImageObject.width/inImageObject.height)

			#lanczos resapler can't handle 16-bit images, so we filter
			if inImageObject.mode == 'I;16':
				outImageObject = inImageObject.resize((width, height),resample=Image.NEAREST)
			else:
				outImageObject = inImageObject.resize((width, height),resample=Image.LANCZOS)
			
			outImageObject.save(outImageFilePath, imgFormat)
			outImageObject.close()


	#gets all images paths and iterates an image object resize
	def doFileResize(self, file, overwrite=False):
		fileObject = Image.open(file)
		newFile = self.resizeFile(fileObject, overwrite)
		fileObject.close()


	def main(self, **kwargs):
		progress_callback = kwargs['progress_callback']
		
		i = 0
		for file in self.inputFileList:
			print(file)
			self.doFileResize(file, self.overwrite)
			i = i + 1

			if progress_callback != None and i%10 == 0:
				try:
					progress_callback.emit(i)
				except:
					print('error')

		return True