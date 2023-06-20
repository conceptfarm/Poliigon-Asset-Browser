--set of maps for each material
struct poliigonMapSet
(
	assetRes = undefined,
	_AO_ = undefined,
	_COL_ = undefined,
	_DISP_ = undefined,
	_DISP16_ = undefined,
	_GLOSS_ = undefined,
	_BUMP_ = undefined,
	_BUMP16_ = undefined,
	_NRM_ = undefined,
	_NRM16_ = undefined,
	_REFL_ = undefined,
	_SSS_ = undefined,
	_TRANSMISSION_ = undefined,
	_DIRECTION_ = undefined,
	_ALPHAMASKED_ = undefined,
	_ROUGHNESS_ = undefined,
	_METALNESS_ = undefined,
	
	
	fn listAvailable =
	(
		result = for i in #( _AO_ , _COL_ , _DISP_ , _DISP16_ , _GLOSS_ , _NRM_ , _NRM16_ , _BUMP_ , _BUMP16_ , _REFL_ , _SSS_ , _TRANSMISSION_ , _DIRECTION_ ,_ALPHAMASKED_ , _ROUGHNESS_, _METALNESS_) where i != undefined collect i
		result
	)
)

--set of set of maps for material
struct poliigonMaterialSet
(
	_2K_ = undefined,
	_3K_ = undefined,
	_4K_ = undefined,
	_6K_ = undefined,
	_8K_ = undefined,
	_HIRES_  = undefined,
	
	fn getMapsForRes res =
	(
		case res of
		(
			"2K":_2K_
			"3K":_3K_
			"4K":_4K_
			"6K":_6K_
			"8K":_8K_
			"HIRES":_HIRES_
		)
	),
	
	fn listAvailableRes =
	(
		result = for i in #(_2K_,_3K_ ,_4K_ ,_6K_,_8K_,_HIRES_) where i != undefined collect i.assetRes
		result
	)
)

--the whole material set of all maps and all resolutions
struct pyPoliigonStruct 
(
	--selectors = #('_AO_' , '_COL_' , '_DISP_' , '_DISP16_' , '_GLOSS_' , '_NRM_' , '_REFL_' , '_SSS_' , '_TRANSMISSION_' , '_DIRECTION_' ,'_ALPHAMASKED_' , '_ROUGHNESS_' , '_METALNESS_')
	
	_2K_ = undefined,
	_3K_ = undefined,
	_4K_ = undefined,
	_6K_ = undefined,
	_8K_ = undefined,
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
	_BUMP_ = undefined,
	_BUMP16_ = undefined,
	_REFL_ = undefined,
	_SSS_ = undefined,
	_TRANSMISSION_ = undefined,
	_DIRECTION_ = undefined,
	_ALPHAMASKED_ = undefined,
	_ROUGHNESS_ = undefined,
	_METALNESS_ = undefined,
	 
	useAO_var = true,
	useDISP_var = true,
	use16bit_var = true,
	useSphere_var = true,
	useGamma_var = true,
	useVrayBitmap_var = false,
	useUVWRandom_var = false,
	
	UVWRandomMap = undefined,
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
			"8K":_8K_
			"HIRES":_HIRES_
		)
	),
	
	fn listAvailableRes =
	(
		result = for i in #(_2K_,_3K_ ,_4K_ ,_6K_,_8K_,_HIRES_) where i != undefined collect i.assetRes
		result
	),
	
	ProgressBarRO =
	(
		-- Progress Bar
		rollout ProgressBarRO "Loading..." width:250 height:70
		(
			label label_loading "Loading: " pos:[25,10] align:#left
			progressBar CTRL_progressBar "Progress Bar" value:0 pos:[25,30] width:200 height:30 color:(color 95 138 193)
		)
	),

	fn isClass _class =
	(
		local result = false
		try
		(
			local temp = execute (_class + "()")
			result = true
		)
		catch
		(
			result = false
		)
		result
	),

	fn convertDims dims = 
	(
		result = #()
		units.MetricType = #meters
		result[1] = units.decodeValue (dims[1] as string + "m")
		result[2] = units.decodeValue (dims[2] as string + "m")

		result
	),
	
	fn calculateMapDimensions bmPath pyDimensions useUVWRandom=
	(
		-- needs work here
		-- calculate dims and output array #( useRealWorld true | false, u/width float, v/height float )
		-- if using uvw rando create a that map 
		-- ISSUE: SEEMS LIKE THE MAP IS NOT CALCULATED IN REAL WORLD UNITS
		result = #(false, 1.0, 1.0)
		bm_width  = 1.0
		bm_height = 1.0
		bmReadable = false
		
		try(
			bminfo = getBitmapInfo bmPath
			bm_width  = bmInfo[3]
			bm_height = bmInfo[4]
			bmReadable = true
			
		)catch(
			bmReadable = false
		)
		
		if pyDimensions != undefined then
		(			
			if bmReadable then
			(
				result[1] = true
				result[2] = pyDimensions[1]
				result[3] = (bm_height * pyDimensions[1])/bm_width
			)
			else 
			(
				result[1] = true
				result[2] = pyDimensions[1]
				result[3] = pyDimensions[2]
			)
			
			if useUVWRandom then
			(
				UVWRandomMap = VRayUVWRandomizer()
				UVWRandomMap.coords.coords.realWorldScale = true
				UVWRandomMap.coords.coords.realWorldWidth = result[2]
				UVWRandomMap.coords.coords.realWorldHeight = result[3]
				UVWRandomMap.coords.mode_by_node_name = on
				UVWRandomMap.coords.mode_by_node_handle = on
				UVWRandomMap.coords.variance_rot_max = 0
			)
		)
		else if pyDimensions == undefined then
		(
			if bmReadable then
			(
				result[1] = false
				result[2] = 1.0
				result[3] = (bm_width * 1.0) / bm_height
			)
			
			if useUVWRandom then
			(
				UVWRandomMap = VRayUVWRandomizer()
				UVWRandomMap.coords.coords.realWorldScale = false
				UVWRandomMap.coords.coords.u_tiling = result[2]
				UVWRandomMap.coords.coords.v_tiling = result[3]
				UVWRandomMap.coords.mode_by_node_name = on
				UVWRandomMap.coords.mode_by_node_handle = on
				UVWRandomMap.coords.variance_rot_max = 0
			)
		)

		result
	),

	fn updateProgressBar pBar =
	(
		materialsCreated += 1.0
		pBar.value = (materialsCreated/materialsToCreate)*100 
	),
	
	fn buildMap bmFile bmType useVrayBitmap useUVWRandom mapDims = 
	(
		--start = timeStamp()
		local bm = undefined
		
		if getFilenameType bmFile == ".tx" then useVrayBitmap = true
				
		if useVrayBitmap then 
		(
			bm = VrayBitmap()
			bm.HDRIMapName = bmFile
			bm.alphaSource = 2
		)
		else
		(
			bm = Bitmaptexture fileName: bmFile
			bm.alphaSource = 2
		)
		
		bm.name = bmType
		
		--data map channel must have map gamma set to 1.0
		if (bmType != "_AO_" and bmType != "_COL_" and bmType != "_REFL_" and bmType != "_SSS_" and bmType != "_TRANSMISSION_" and bmType != "_METALNESS_") and (useGamma_var) then
		(
			if useVrayBitmap then 
			(
				bm.color_space = 0 		--color space transform is none
				bm.rgbColorSpace = 3 	-- rgb primaries Raw
			)
			else
			(
				gammaBitmap = openBitmap bmFile gamma:1.0
				bm.bitmap = gammaBitmap
			)
		)
		--color map channel must have map gamma set to 2.2
		else
		(
			if useVrayBitmap then 
			(
				bm.color_space = 2 		--color space transform is sRGB
				bm.rgbColorSpace = 1 	-- rgb primaries sRGB
			)
			else
			(
				gammaBitmap = openBitmap bmFile gamma:2.2
				bm.bitmap = gammaBitmap
			)
		)

		--dimensions
		if useUVWRandom == false then
		(
			if mapDims[1] == true then
			(
				if useVrayBitmap then 
				(
					bm.UVGen.realWorldScale = true
					bm.UVGen.realWorldWidth = mapDims[2]
					bm.UVGen.realWorldHeight = mapDims[3]
				)
				else
				(
					bm.coords.realWorldScale = true
					bm.coords.realWorldWidth = mapDims[2]
					bm.coords.realWorldHeight = mapDims[3]
				)
			)
			else
			(
				if useVrayBitmap then 
				(
					bm.UVGen.realWorldScale = false
					bm.UVGen.U_Tiling = mapDims[2]
					bm.UVGen.V_Tiling = mapDims[3]
				)
				else
				(
					bm.coords.realWorldScale = false
					bm.coords.U_Tiling = mapDims[2]
					bm.coords.V_Tiling = mapDims[3]
				)
			)
		)
		else 
		(
			bm.mapSource = UVWRandomMap
			bm.mapSource_on = true
		)
		
		--Alphamasked alpha settings
		if bmType == "_ALPHAMASKED_" then
		(
			--same variables name for both Bitmaptexture and VrayBitmap
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
		-- get first available asset path
		availableAssets = mapSetClass.listAvailable()
		firstAsset = if classof availableAssets[1] == string then availableAssets[1] else availableAssets[1][1]
		
		-- calculate real world dimensions or u/v tiling from bitmap path
		mapDims = calculateMapDimensions firstAsset pyDimensions useUVWRandom_var
		
		_AO_ = if mapSetClass._AO_ != undefined then (buildMap mapSetClass._AO_ "_AO_" useVrayBitmap_var useUVWRandom_var mapDims)
		_COL_ = if mapSetClass._COL_ != undefined then (for f in mapSetClass._COL_ collect (buildMap f "_COL_" useVrayBitmap_var useUVWRandom_var mapDims))  else (#())
		_DISP_ = if mapSetClass._DISP_ != undefined then (for f in mapSetClass._DISP_ collect (buildMap f "_DISP_" useVrayBitmap_var useUVWRandom_var mapDims))  else (#())
		_DISP16_ = if mapSetClass._DISP16_ != undefined then buildMap mapSetClass._DISP16_ "_DISP16_" useVrayBitmap_var useUVWRandom_var mapDims
		_GLOSS_ = if mapSetClass._GLOSS_ != undefined then buildMap mapSetClass._GLOSS_  "_GLOSS_" useVrayBitmap_var useUVWRandom_var mapDims
		_BUMP_ = if mapSetClass._BUMP_ != undefined then buildMap mapSetClass._BUMP_ "_BUMP_" useVrayBitmap_var useUVWRandom_var mapDims
		_BUMP16_ = if mapSetClass._BUMP16_ != undefined then buildMap mapSetClass._BUMP16_ "_BUMP_" useVrayBitmap_var useUVWRandom_var mapDims
		_NRM_ = if mapSetClass._NRM_ != undefined then buildMap mapSetClass._NRM_ "_NRM_" useVrayBitmap_var useUVWRandom_var mapDims
		_NRM16_ = if mapSetClass._NRM16_ != undefined then buildMap mapSetClass._NRM16_ "_NRM_" useVrayBitmap_var useUVWRandom_var mapDims
		_REFL_ = if mapSetClass._REFL_  != undefined then buildMap  mapSetClass._REFL_ "_REFL_" useVrayBitmap_var useUVWRandom_var mapDims
		_SSS_ = if mapSetClass._SSS_ != undefined then buildMap mapSetClass._SSS_ "_SSS_" useVrayBitmap_var useUVWRandom_var mapDims
		_TRANSMISSION_ = if mapSetClass._TRANSMISSION_ != undefined then buildMap mapSetClass._TRANSMISSION_ "_TRANSMISSION_" useVrayBitmap_var useUVWRandom_var mapDims
		_DIRECTION_ = if mapSetClass._DIRECTION_  != undefined then buildMap mapSetClass._DIRECTION_ "_DIRECTION_" useVrayBitmap_var useUVWRandom_var mapDims
		_ALPHAMASKED_ = if mapSetClass._ALPHAMASKED_ != undefined then (for f in mapSetClass._ALPHAMASKED_  collect (buildMap f "_ALPHAMASKED_" useVrayBitmap_var useUVWRandom_var mapDims)) else (#())
		_ROUGHNESS_ = if mapSetClass._ROUGHNESS_  != undefined then buildMap mapSetClass._ROUGHNESS_ "_ROUGHNESS_" useVrayBitmap_var useUVWRandom_var mapDims
		_METALNESS_ = if mapSetClass._METALNESS_  != undefined then buildMap mapSetClass._METALNESS_ "_METALNESS_" useVrayBitmap_var useUVWRandom_var mapDims
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
			mat.brdf_useRoughness = false
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
		
		--BUMP MAP--
		if _BUMP_ != undefined or _BUMP16_ != undefined then
		(
			if use16bit_var == true then
			(
				if _BUMP16_ != undefined then
				(
					if classof mat.texmap_bump == VRayNormalMap then
					(
						mat.texmap_bump.bump_map = _BUMP16_
						mat.texmap_bump.bump_map_on = true
					)
					else
					(
						mat.texmap_bump = _BUMP16_
					)
				)
				else
				(
					if classof mat.texmap_bump == VRayNormalMap then
					(
						mat.texmap_bump.bump_map = _BUMP_
						mat.texmap_bump.bump_map_on = true
					)
					else
					(
						mat.texmap_bump = _BUMP_
					)
				)
			)
			else
			(
				if _BUMP_ != undefined then 
				(
					if classof mat.texmap_bump == VRayNormalMap then
					(
						mat.texmap_bump.bump_map = _BUMP_
						mat.texmap_bump.bump_map_on = true
					)
					else
					(
						mat.texmap_bump = _BUMP_
					)
				)
				else
				(
					if classof mat.texmap_bump == VRayNormalMap then
					(
						mat.texmap_bump.bump_map = _BUMP16_
						mat.texmap_bump.bump_map_on = true
					)
					else
					(
						mat.texmap_bump = _BUMP16_
					)
				)
			)
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
		
		/*
		NOTE ON METALNESS/ROUGHNESS MODEL
		Vray doesn't seem to work as intended with metalness/roughness textures
		This is a workaround to make the texture look like the official sample
		*/
		
		/* OLD
		--METALNESS--
		if _METALNESS_ != undefined then
		(
			mat.texmap_reflection = _METALNESS_
			--Should be this
			--mat.texmap_metalness = _METALNESS_
			--mat.reflection_metalness : float
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar
		
		
		--ROUGHNESS--
		if _ROUGHNESS_ != undefined then
		(
			mat.texmap_reflectionGlossiness = _ROUGHNESS_
			mat.brdf_useRoughness = true
			--mat.diffuse_roughness : float
			--mat.option_diffuse_roughness_model : integer
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar
		*/
		
		--METALNESS--
		if _METALNESS_ != undefined then
		(
			mat.texmap_metalness = _METALNESS_
			mat.reflection_metalness = 1.0
			mat.reflection = (color 255 255 255 )
			mat.reflection_fresnel = true
			mat.reflection_ior = 1.1 --most metals are between 1.002(Aluminium) and 1.35(Gold)
			mat.brdf_type = 0 --setting BRDF to Phong seems to look the most like the sample
		)
		updateProgressBar ProgressBarRO.CTRL_progressBar
		
		
		--ROUGHNESS--
		if _ROUGHNESS_ != undefined then
		(
			mat.texmap_reflectionGlossiness = _ROUGHNESS_
			mat.brdf_useRoughness = true
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
		
		materialsToCreate = 16 -- 16, number of public members of poliigonMapSet
		parsePyMaterialArray (getMapsForRes chosenRes) pyDimensions
		materialsToCreate =  _COL_.count * 13 -- 13, number of unique maps AO, COL, NRM 8/16, ...

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
		rollout pyPoliigonStructRO  "Advanced Settings" width:300 height:260 --AdvancedSettingsRollout
		(
			
			dropdownlist resList "Map Resolution:" items:availableRes pos:[10,10] --width:120	
			checkbox useAO "Include Ambient Occlusion (AO) maps (if available)" checked:useAO_var pos:[10,60]
			checkbox useDISP "Include Displacement maps (if available)" checked:useDISP_var pos:[10,80]
			checkbox use16bit "Use 16 bit maps (if available)" tooltip:"This will replace all 8 bit images with higher quality 16 bit versions when available." checked:use16bit_var pos:[10,100]
			checkbox useSphere "Apply materials to preview spheres" tooltip:"Add preview spheres into the 3D viewport with the materials applied to them." checked:useSphere_var pos:[10,120]
			checkbox useGamma "Convert non-diffuse textures to gamma 1.0" tooltip:"Add preview spheres into the 3D viewport with the materials applied to them." checked:useGamma_var pos:[10,140]
			checkbox useVrayBitmap "Use VrayBitmap" tooltip:"Uses VrayBitmap bitmap instead of the 3dsmax native Bitmap." checked:useVrayBitmap_var pos:[10,160]
			checkbox useUVWRandom "Apply UVWRandomizer (VrayBitmap Only)" tooltip:"Applies UVWRandomizer as the mapping channel map" checked:useVrayBitmap_var pos:[10,180]
			button createMaterials_btn "Load Materials" pos:[0,210] width:300 height:50

			on useVrayBitmap changed state do
			(
				useUVWRandom.state = state
			)
			
			on createMaterials_btn pressed do
			(
				useAO_var = useAO.state
				useDISP_var = useDISP.state
				use16bit_var = use16bit.state
				useSphere_var = useSphere.state
				useGamma_var = useGamma.state
				useVrayBitmap_var = useVrayBitmap.state
				useUVWRandom_var = useUVWRandom.state
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
				useVrayBitmap_var = useVrayBitmap.state
				useUVWRandom_var = useUVWRandom.state
			)
			
		)
	),

	fn show = 
	(
		availableRes = listAvailableRes()
		if isClass "VrayBitmap" then
		(
			useVrayBitmap_var = true
			useUVWRandom_var = true
		)
		try(destroydialog pyPoliigonStructRO )catch()
		createDialog pyPoliigonStructRO modal:true
	)
)

pyPoliigonMaterial = pyPoliigonStruct()