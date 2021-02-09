--set of maps for each material
struct poliigonMapSet
(
	assetRes = undefined,
	_AO_ = undefined,
	_COL_ = undefined,
	_DISP_ = undefined,
	_DISP16_ = undefined,
	_GLOSS_ = undefined,
	_NRM_ = undefined,
	_NRM16_ = undefined,
	_REFL_ = undefined,
	_SSS_ = undefined,
	_TRANSMISSION_ = undefined,
	_DIRECTION_ = undefined,
	_ALPHAMASKED_ = undefined
)

--set of set of maps for material
struct poliigonMaterialSet
(
	_2K_ = undefined,
	_3K_ = undefined,
	_4K_ = undefined,
	_6K_ = undefined,
	_HIRES_  = undefined,
	
	fn getMapsForRes res =
	(
		case res of
		(
			"2K":_2K_
			"3K":_3K_
			"4K":_4K_
			"6K":_6K_
			"HIRES":_HIRES_
		)
	),
	
	fn listAvailableRes =
	(
		result = for i in #(_2K_,_3K_ ,_4K_ ,_6K_,_HIRES_) where i != undefined collect i.assetRes
		result
	)
)

--the whole material set of all maps and all resolutions
struct pyPoliigonStruct 
(
	--selectors = #('_AO_' , '_COL_' , '_DISP_' , '_DISP16_' , '_GLOSS_' , '_NRM_' , '_REFL_' , '_SSS_' , '_TRANSMISSION_' , '_DIRECTION_' ,'_ALPHAMASKED_')
	
	_2K_ = undefined,
	_3K_ = undefined,
	_4K_ = undefined,
	_6K_ = undefined,
	_HIRES_  = undefined,
	availableRes = #(),
	
	pyMaterialArray = #(),
	pyDimensions = undefined,
	pyMaterialName = undefined,
	pyScriptFilePath = undefined,

	_AO_ = undefined,
	_COL_ = undefined,
	_DISP_ = undefined,
	_DISP16_ = undefined,
	_GLOSS_ = undefined,
	_NRM_ = undefined,
	_NRM16_ = undefined,
	_REFL_ = undefined,
	_SSS_ = undefined,
	_TRANSMISSION_ = undefined,
	_DIRECTION_ = undefined,
	_ALPHAMASKED_ = undefined,
	
	 
	useAO_var = true,
	useDISP_var = true,
	use16bit_var = true,
	useSphere_var = true,
	useGamma_var = true,
	materialsToCreate = 0,
	materialsCreated = 0,
	spheresInScene = 0,
	chosenRes = undefined,
	
	fn getMapsForRes res =
	(
		case res of
		(
			"2K":_2K_
			"3K":_3K_
			"4K":_4K_
			"6K":_6K_
			"HIRES":_HIRES_
		)
	),
	
	fn listAvailableRes =
	(
		result = for i in #(_2K_,_3K_ ,_4K_ ,_6K_,_HIRES_) where i != undefined collect i.assetRes
		result
	),
	
	ProgressBarRO =
	(
		-- Progress Bar
		rollout ProgressBarRO "Loading..." width:250 height:70 --ProgressBarRollout
		(
			label label_loading "Loading: " pos:[25,10] align:#left
			progressBar CTRL_progressBar "Progress Bar" value:0 pos:[25,30] width:200 height:30 color:(color 95 138 193)
		)
	),
	

	fn convertDims dims = 
	(
		result = #()
		units.MetricType = #meters
		result[1] = units.decodeValue (dims[1] as string + "m")
		result[2] = units.decodeValue (dims[2] as string + "m")

		result
	),

	fn updateProgressBar pBar =
	(
		materialsCreated += 1.0
		pBar.value = (materialsCreated/materialsToCreate)*100 
	),
	
	fn buildMap bmFile bmType = 
	(
		--start = timeStamp()
		bm = Bitmaptexture fileName: bmFile
		bm.name = bmType
		bm.alphaSource = 2
		
		--data map channel must have map gamma set to 1.0
		if (bmType != "_AO_" and bmType != "_COL_" and bmType != "_SSS_") and (useGamma_var) then
		(
			gammaBitmap = openBitmap bmFile gamma:1.0
			bm.bitmap = gammaBitmap
		)


		if pyDimensions != undefined then
		(
			bm.coords.realWorldScale = true
			bm.coords.realWorldWidth = pyDimensions[1]
			bm.coords.realWorldHeight = (bm.bitmap.height * bm.coords.realWorldWidth)/bm.bitmap.width
		)
		else
		(
			bm.coords.realWorldScale = false
			bm.coords.U_Tiling = 1
			bm.coords.V_Tiling = (bm.bitmap.height * bm.coords.U_Tiling)/bm.bitmap.width
		)
		
		if bmType == "_ALPHAMASKED_" then
		(
			bm.monoOutput = 1
			bm.rgbOutput = 1
			bm.alphaSource = 2
		)
		else if bmType == "_NRM_" then
		(
			subMap = copy bm
			bm = VRayNormalMap()
			bm.flip_green = true
			bm.normal_map = subMap
		)
		--end = timeStamp()
		--print ("buildMap took "+ ((end - start) / 1000.0) as string +" seconds" ) as string
		updateProgressBar ProgressBarRO.CTRL_progressBar
		bm
	),
	
	fn parsePyMaterialArray mapSetClass dims =
	(
		pyDimensions = if dims != undefined then convertDims dims --translate to Point2
		
		_AO_ = if mapSetClass._AO_ != undefined then (buildMap mapSetClass._AO_ "_AO_")
		_COL_ = if mapSetClass._COL_ != undefined then (for f in mapSetClass._COL_ collect (buildMap f "_COL_"))  else (#())
		_DISP_ = if mapSetClass._DISP_ != undefined then (for f in mapSetClass._DISP_ collect (buildMap f "_DISP_"))  else (#())
		_DISP16_ = if mapSetClass._DISP16_ != undefined then buildMap mapSetClass._DISP16_ "_DISP16_"
		_GLOSS_ = if mapSetClass._GLOSS_ != undefined then buildMap mapSetClass._GLOSS_  "_GLOSS_"
		_NRM_ = if mapSetClass._NRM_ != undefined then buildMap mapSetClass._NRM_ "_NRM_"
		_NRM16_ = if mapSetClass._NRM16_ != undefined then buildMap mapSetClass._NRM16_ "_NRM_"
		_REFL_ = if mapSetClass._REFL_  != undefined then buildMap  mapSetClass._REFL_ "_REFL_"
		_SSS_ = if mapSetClass._SSS_ != undefined then buildMap mapSetClass._SSS_ "_SSS_"
		_TRANSMISSION_ = if mapSetClass._TRANSMISSION_ != undefined then buildMap mapSetClass._TRANSMISSION_ "_TRANSMISSION_"
		_DIRECTION_ = if mapSetClass._DIRECTION_  != undefined then buildMap mapSetClass._DIRECTION_ "_DIRECTION_"
		_ALPHAMASKED_ = if mapSetClass._ALPHAMASKED_ != undefined then (for f in mapSetClass._ALPHAMASKED_  collect (buildMap f "_ALPHAMASKED_")) else (#())

		
	),

	fn buildMaterial variation = 
	(
		mat = VRayMtl()
		mat.name = pyMaterialName + " var " + variation as string + " " + chosenRes --need to get name
		mat.reflection_lockIOR = off
		mat.reflection_fresnel = off
		mat.texmap_displacement_multiplier = 20

		--DIFFUSE--
		if (_AO_ != undefined and _COL_[variation] != undefined and useAO_var) then 
		(
			BaseMap = CompositeTexturemap ()
			BaseMap.mapEnabled.count = 2
			BaseMap.blendMode[2] = 5
			BaseMap.LayerName[1] = "COLOR"
			BaseMap.LayerName[2] = "AO"
			MapCOL = BaseMap.mapList[1] = _COL_[variation]
			MapAO = BaseMap.mapList[2] = _AO_
			MapCOL.name = "COLOR Var " + variation as string 
			MapAO.name = "AO"
			BaseMap.name = "AO + COLOR"
			mat.texmap_diffuse = BaseMap
			showTextureMap mat mat.texmap_diffuse.mapList[1] on
		)
		else if (_AO_ == undefined and _COL_[variation] != undefined) or (_COL_[variation] != undefined and useAO_var == false) then 
		(
			mat.texmap_diffuse = _COL_[variation]
			mat.texmap_diffuse.name = "COLOR Var " + variation as string 
			showTextureMap mat mat.texmap_diffuse on
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar

        --REFLECTION--
		if (_AO_ != undefined and _REFL_ != undefined and useAO_var) then 
		(
			BaseMap = CompositeTexturemap()
			BaseMap.mapEnabled.count = 2
			BaseMap.blendMode[2] = 5
			BaseMap.LayerName[1] = "Reflection"
			BaseMap.LayerName[2] = "AO"
			BaseMap.mapList[1] = _REFL_
			BaseMap.mapList[2] = _AO_
			BaseMap.name = "AO + REFLECTION"
			mat.texmap_reflection = BaseMap
		)
		else if (_AO_ == undefined and _REFL_ != undefined) or (_REFL_ != undefined and useAO_var == false) then 
		(
			mat.texmap_reflection = _REFL_
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar

		--GLOSS--
		if _GLOSS_ != undefined then
		(
			mat.texmap_reflectionGlossiness = _GLOSS_
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar

		--NORMAL MAP--
		if _NRM_ != undefined or _NRM16_ != undefined then
		(
			if use16bit_var == true then
			(
				if _NRM16_ != undefined then
				(
					mat.texmap_bump = _NRM16_
				)
				else
				(
					mat.texmap_bump = _NRM_
				)
			)
			else
			(
				if _NRM_ != undefined then 
				(
					mat.texmap_bump = _NRM_
				)
				else
				(
					mat.texmap_bump = _NRM16_
				)
			)
			mat.texmap_bump_multiplier = 100
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar

		--TRANSMISSION--
		if _TRANSMISSION_ != undefined then
		(
			mat.option_reflectOnBack = on
			mat.texmap_refraction = _TRANSMISSION_
			mat.texmap_refractionGlossiness = _GLOSS_
			mat.texmap_refraction_fog = _COL_[variation]
			mat.refraction_fogBias = 10
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar

		--DIRECTION MAP--
		if _DIRECTION_ != undefined then
		(
			mat.anisotropy = 0.5
			mat.texmap_anisotropy_rotation = _DIRECTION_
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar

		--ALPHA MAP--
		if _ALPHAMASKED_[variation] != undefined then
		(
			if _ALPHAMASKED_.count < _COL_.count then
			(
				mat.texmap_opacity = _ALPHAMASKED_[1]
			)
			else if _ALPHAMASKED_.count == _COL_.count then
			(
				mat.texmap_opacity = _ALPHAMASKED_[variation]
			)
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar

		--DISPLACEMENT--
		if useDISP_var then
		(
			if _DISP_ != undefined or _DISP16_ != undefined then
			(
				buildMatUsing16bit = false
				if use16bit_var == true then
				(
					if _DISP16_ != undefined then
					(
						buildMatUsing16bit = true
					)
					else
					(
						buildMatUsing16bit = false
					)
				)
				else
				(
					if _DISP_ != undefined then 
					(
						buildMatUsing16bit = false
					)
					else
					(
						buildMatUsing16bit = true
					)
				)
				
				if buildMatUsing16bit == true then
				(
					mat.texmap_displacement = _DISP16_
				)
				else
				(
					if _DISP_.count > 1 then 
					(
						BaseMap = CompositeTexturemap()
						BaseMap.mapEnabled.count = _DISP_.count
						BaseMap.LayerName[1] = "Base"
						BaseMap.mapList[1] = _DISP_[1]
						
						for i = 2 to _DISP_.count do 
						(
							BaseMap.blendMode[i] = 5
							BaseMap.LayerName[i] = "Disp Add " + i as string
							MapAdd = BaseMap.mapList[i] = _DISP_[i]
						)

						mat.texmap_displacement = BaseMap
					)
					else 
					(
						mat.texmap_displacement = _DISP_[1]
					)
				)
				mat.texmap_displacement_multiplier = 5
			)
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar

		--SSS--
		if _SSS_ != undefined then
		(
			subMat = copy mat
			mat = VRay2SidedMtl()
			mat.frontMtl = subMat
			mat.backMtlOn = false
			mat.texmap_translucency = _SSS_
			mat.texmap_translucency_multiplier = 100
			mat.texmap_translucency_on = true
			mat.force1SidedSubMtls = true
			mat.mult_by_front_diffuse = false
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar

		mat
	),

	fn createMaterials =
	(
		clearSelection()
		
		try(destroydialog ProgressBarRO )catch()
		createDialog ProgressBarRO --modal:true
		
		materialsToCreate = 12 -- 12 initial bitmaps to initialize
		parsePyMaterialArray (getMapsForRes chosenRes) pyDimensions


		materialsToCreate =  _COL_.count * 9

		for i = 1 to _COL_.count do
		(
			newMaterial = buildMaterial i
			sphereOBJ = Sphere radius:39.97 pos:[((spheresInScene)*90),0,0] isSelected:off mapcoords:true realWorldMapSize:(if pyDimensions != undefined then true else false) material:newMaterial segs:32
			selectmore sphereOBJ
			spheresInScene += 1
		)
		
		destroydialog ProgressBarRO
		max zoomext sel
		try(deleteFile pyScriptFilePath)catch(print "couldn't delete temporary pyMaterial ms file")
	),

	fn openDialog = (print "opened"; OK),

	fn close = try(destroydialog dialog) catch(),

	pyPoliigonStructRO = 
	(
		-- Subrollout for the advanced settings
		rollout pyPoliigonStructRO  "Advanced Settings" width:300 height:210 --AdvancedSettingsRollout
		(
			
			dropdownlist resList "Map Resolution:" items:availableRes pos:[10,10] --width:120	
			checkbox useAO "Include Ambient Occlusion (AO) maps (if available)" checked:useAO_var pos:[10,60]
			checkbox useDISP "Include Displacement maps (if available)" checked:useDISP_var pos:[10,80]
			checkbox use16bit "Use 16 bit maps (if available)" tooltip:"This will replace all 8 bit images with higher quality 16 bit versions when available." checked:use16bit_var pos:[10,100]
			checkbox useSphere "Apply materials to preview spheres" tooltip:"Add preview spheres into the 3D viewport with the materials applied to them." checked:useSphere_var pos:[10,120]
			checkbox useGamma "Convert non-diffuse textures to gamma 1.0" tooltip:"Add preview spheres into the 3D viewport with the materials applied to them." checked:useGamma_var pos:[10,140]
			button createMaterials_btn "Load Materials" pos:[0,160] width:300 height:50

			on createMaterials_btn pressed do
			(
				useAO_var = useAO.state
				useDISP_var = useDISP.state
				use16bit_var = use16bit.state
				useSphere_var = useSphere.state
				useGamma_var = useGamma.state
				chosenRes = resList.selected
				destroydialog pyPoliigonStructRO
				
				createMaterials()
			)
			
			on pyPoliigonStructRO close do
			(
				useAO_var = useAO.state
				useDISP_var = useDISP.state
				use16bit_var = use16bit.state
				useSphere_var = useSphere.state
				useGamma_var = useGamma.state
			)
		)
	),

	fn show = 
	(
		availableRes = listAvailableRes()
		try(destroydialog pyPoliigonStructRO )catch()
		createDialog pyPoliigonStructRO modal:true
	)

)

pyPoliigonMaterial = pyPoliigonStruct()