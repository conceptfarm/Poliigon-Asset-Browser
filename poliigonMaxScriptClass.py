'''
Build MS file like this:
new1 = poliigonMapSet assetRes:"2K" _AO_:"ao_path_2k" _COL_:#("col_path_var1_2k","col_path_var2_2k") ....
new2 = poliigonMapSet assetRes:"3K" _AO_:"ao_path_3k" ...
new3 = poliigonMapSet assetRes:"4K" _AO_:"ao_path_4k" ...
new4 = poliigonMapSet assetRes:"6K" _AO_:"ao_path_6k" ...
new5 = poliigonMapSet assetRes:"HIRES" _AO_:"ao_path_HIRES" ...
matDimensions=[1.0, 1.0]
pyPoliigonMaterial = pyPoliigonStruct _2K_:new1 _3K_:new2 _4K_:new3 _6K_:new4 _HIRES_:new5 pyDimensions:matDimensions pyMaterialName:"materialName" pyScriptFilePath:getSourceFileName()
pyPoliigonMaterial.show()
'''

import os
import tempfile

class MaxScriptCreator():
	def __init__(self, fileResList, file2DList, dimensions, materialName):
		self.fileResList = fileResList
		self.file2DList = file2DList
		self.dimensions = dimensions
		self.materialName = materialName

	def getExt(self, path):
		filename, file_extension = os.path.splitext(path)
		return(file_extension)

	def create(self):
		
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
			if type(maxArray) == list and len(maxArray) == 0:
				print("Error 0 array?")
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
			selectors = ['assetRes','_AO_' , '_COL_' , '_DISP_' , '_DISP16_' , '_GLOSS_' , '_NRM_' , '_NRM16_' , '_BUMP_' , '_BUMP16_' , '_REFL_' , '_SSS_' , '_TRANSMISSION_' , '_DIRECTION_' ,'_ALPHAMASKED_' , '_ROUGHNESS_', '_METALNESS_']
			und = 'undefined'
			new_array = {f:und for f in selectors}
			
			new_array['assetRes'] = fileRes

			if len(fileList) == 1:
				#just one file, probably a graphic, set
				new_array['_COL_'] = [fileList[0]]
				if self.getExt(fileList[0]) == '.png':
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
				new_array['_DISP_'] = dispVariations if len(dispVariations) > 0 else und
				new_array['_ALPHAMASKED_'] = alphaVariations

				'''
				1 - alphamask is present, no color present -> copy to color
				2 - color is present in png format -> copy to alphamask
				'''
				if len(new_array['_COL_']) > 0 and len(new_array['_ALPHAMASKED_']) == 0:
					if self.getExt(colorVariations[0]) == '.png':
						new_array['_ALPHAMASKED_'] = new_array['_COL_']
					else:
						new_array['_ALPHAMASKED_'] = und
				
				elif len(new_array['_ALPHAMASKED_']) > 0 and len(new_array['_COL_']) == 0:
					new_array['_COL_'] = new_array['_ALPHAMASKED_']

			#weird name no selectors
			#no _COL_ selector but there is a file
			#if the file is png copy to alpha as well
			if len(new_array['_COL_']) == 0 and len(fileList) != 0:
				colorVariations = []
				alphaVariations = []
				
				for f in fileList:
					colorVariations.append(f)
					if self.getExt(f) == '.png':
						alphaVariations.append(f)

				new_array['_COL_'] = colorVariations
				new_array['_ALPHAMASKED_'] = alphaVariations
			
			#really weird material without colour component
			new_array['_COL_'] = und if len(new_array['_COL_']) == 0 else new_array['_COL_']
			new_array['_ALPHAMASKED_'] = und if len(new_array['_ALPHAMASKED_']) == 0 else new_array['_ALPHAMASKED_']

			return pyDictToMaxString(new_array)

		# creates a file in system temp directory
		tempMSFile = tempfile.NamedTemporaryFile(mode = 'w+', newline='\n',suffix='.ms',delete=False)
		matStructVar = 'pyPoliigonMaterial=pyPoliigonStruct '

		# write collection of poliigonMapSet for each resolution
		for i, fileList in enumerate(self.file2DList):
			mapStructVar = make(fileList, self.fileResList[i])
			tempMSFile.write('new' + str(i) + '=poliigonMapSet '+ mapStructVar + '\n')
			matStructVar = matStructVar + '_' + self.fileResList[i] + '_:new' + str(i) + ' '

		
		tempMSFile.write('matDimensions=' + ('undefined' if self.dimensions == None or self.dimensions == '' else str(self.dimensions)) + '\n')
		tempMSFile.write(matStructVar + ' pyDimensions:matDimensions pyMaterialName:"' + self.materialName + '" pyScriptFilePath:getSourceFileName() \n')
		tempMSFile.write('pyPoliigonMaterial.show()' + '\n')
		tempMSFile.close()
		
		return tempMSFile
