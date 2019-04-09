import PhotoScan
import argparse
import time
import os
os.environ["CUDA_VISIBLE_DEVICES"]="1"
os.environ["CUDA_VISIBLE_DEVICES"]="2"
## Autoprocessing script for multiple sub-folders in some master folder

#compatibility Agisoft PhotoScan Professional 1.4.2

def progress_print(p):
        print('Current task progress: {:.2f}% '.format(p), end='\r')

def export_camera_pose(chunk, output_path):
	file = open(output_path, "wt")
	if chunk.transform:
		T = chunk.transform.matrix
	else:
		T = PhotoScan.Matrix().diag([1,1,1,1])
	print("Exporting camera poses to ", output_path)
	
	for camera in chunk.cameras:
		if camera.transform:
			coords = T.mulp(camera.center)
			file.write(camera.label + "\t{:.5f}".format(coords[0]) + "\t{:.5f}".format(coords[1]) + "\t{:.5f}".format(coords[2]) + "\n")

	file.close()
	print("Script finished")

def load_images(types,path):
	print("Processing " + path)
	list_files = os.listdir(path)
	list_photos = list()
	for entry in list_files: #finding image files
		file = path + "/" + entry
		if os.path.isfile(file):
			if file[-3:].lower() in types:
				list_photos.append(file)
	return list_photos

def process(images_path, output_path, model_name):
	
	# Font settings
	os.environ['QT_QPA_FONTDIR'] = '/usr/share/fonts/truetype/dejavu/'

	# Below code was to enable all available GPUs, was throwing an error.
	#PhotoScan.app.gpu_mask = 2 ** len(PhotoScan.app.enumGPUDevices()) - 1 #setting GPU mask
	
	PhotoScan.app.gpu_mask = 15 # gpu_mask is a bitmask. 3 in binary = 11 so only two GPUs are used.
	if PhotoScan.app.gpu_mask:
		PhotoScan.app.cpu_enable = False 
	else:
		PhotoScan.app.cpu_enable = True
		
	
	### Processing parameters
	accuracy = PhotoScan.Accuracy.HighAccuracy  #align photos accuracy
	reference_preselection = False
	generic_preselection = True
	keypoints         = 40000 	# Align photos key point limit
	tiepoints         = 4000 	# Align photos tie point limit
	source            = PhotoScan.DataSource.DenseCloudData # Build mesh/DEM source
	surface           = PhotoScan.SurfaceType.Arbitrary # Build mesh surface type
	quality           = PhotoScan.Quality.HighQuality # Build dense cloud quality
	filtering         = PhotoScan.FilterMode.AggressiveFiltering # Depth filtering
	interpolation     = PhotoScan.Interpolation.EnabledInterpolation # Build mesh interpolation
	mosaic_blending   = PhotoScan.BlendingMode.MosaicBlending # Blending mode
	average_blending  = PhotoScan.BlendingMode.AverageBlending
	disabled_blending = PhotoScan.BlendingMode.DisabledBlending


	face_num = PhotoScan.FaceCount.HighFaceCount # Build mesh polygon count
	mapping = PhotoScan.MappingMode.GenericMapping #Build texture mapping
	atlas_size = 4096
	TYPES = ["jpg", "jpeg", "tif", "tiff", "png"]


	# Load images into master list of fore and aft.
	list_photos_master = load_images(TYPES, images_path)


	# Create PhotoScan document
	project_file = os.path.join(output_path,"Model.psx")
	doc = PhotoScan.Document()	
	doc.save(project_file)
	chunk = doc.addChunk()
	chunk.label = model_name

	
	print("Saving PhotoScan project to: ", project_file)
	print("Chunk label: ", str(chunk.label))

	# Add Images to Chunk
	chunk.addPhotos(list_photos_master)
	
	# Load ref file.
	#chunk.loadReference(path=reference_path, format=PhotoScan.ReferenceFormat.ReferenceFormatCSV, columns='zanxy', delimiter=',')

	# Set coordinate system for lat lon values.
	#chunk.crs = PhotoScan.CoordinateSystem("EPSG::4326")

 
	# TODO Load calibration parameters from file


	# Create Sensor definitions
	sensor_fore              = chunk.addSensor()
	sensor_fore.label        = "Left Sensor"
	sensor_fore.type         = PhotoScan.Sensor.Type.Frame
	sensor_fore.width        = 1360 #chunk.cameras[-1].sensor.width
	sensor_fore.height       = 1024 #chunk.cameras[-1].sensor.height
	sensor_fore.pixel_size   = [0.00645, 0.00645]
	sensor_fore.focal_length = 8 # Focal length is 10.4mm, 14.6mm effective length in water.
	#sensor_fore.antenna.location_ref   = PhotoScan.Vector([0.38, 0, 0.25])

	sensor_aft              = chunk.addSensor()
	sensor_aft.label        = "Right Sensor"
	sensor_aft.type         = PhotoScan.Sensor.Type.Frame
	sensor_aft.width        = 1360 #chunk.cameras[-1].sensor.width
	sensor_aft.height       = 1024 #chunk.cameras[-1].sensor.height
	sensor_aft.pixel_size   = [0.00645, 0.00645]
	sensor_aft.focal_length = 8
	#sensor_aft.antenna.location_ref  = PhotoScan.Vector([0.53, 0, 0.25])

	for camera in chunk.cameras:
		if "LC" in camera.label:
			camera.sensor = sensor_fore
			print("Added ",camera.label,"to left group")
		elif "RC" in camera.label:
			camera.sensor = sensor_aft
			print("Added ",camera.label,"to right group")
		else: 
			print("No sensor defined for ",camera.label)

	# Add scalebars between stereo images
	# This is the baseline between two cameras.
	# Iver3 system is 6" baseline, 0.1524 meters.
	index = 0
	# while(True):
	# 	scalebar = chunk.addScalebar(chunk.cameras[index],chunk.cameras[index+1])
	# 	scalebar.reference.distance = 0.1282
	# 	index+=2
	# 	if index >= len(chunk.cameras):
	# 		break
	while(True):
		scalebar = chunk.addScalebar(chunk.cameras[index],chunk.cameras[index+1])
		scalebar.reference.distance = 0.1282
		index+=2
		if index >= len(chunk.cameras):
			break	

	### Estimate image quality	
	chunk.estimateImageQuality(chunk.cameras)
	badImages = 0
	#for camera in chunk.cameras:
	#	if float(camera.photo.meta["Image/Quality"]) < 0.5:
	#		camera.enabled = False
	#		badImages+=1
	print("Removed ",badImages," from chunk")

	### Align photos
	chunk.matchPhotos(
		accuracy = accuracy,
		generic_preselection = generic_preselection,
		reference_preselection = reference_preselection,
		filter_mask = False,
		keypoint_limit = keypoints,
		tiepoint_limit = tiepoints,
		progress=progress_print)

	chunk.alignCameras()
	chunk.optimizeCameras()
	chunk.resetRegion()
	doc.read_only = False
	doc.save()	
				
	###building dense cloud
	chunk.buildDepthMaps(
		quality = quality,
		filter = filtering,
		progress=progress_print)
	chunk.buildDenseCloud(
		point_colors = True,
		progress=progress_print)
	doc.save()
	
	###building mesh
	chunk.buildModel(
		surface = surface,
		source = source,
		interpolation = interpolation,
		face_count = face_num,
		progress=progress_print)
	doc.save()


	###build texture
	chunk.buildUV(
		mapping = mapping,
		count = 1, progress=progress_print)
	chunk.buildTexture(
		blending = mosaic_blending,
		size = atlas_size,
		progress=progress_print)
	doc.save()
	
	###export model
	chunk.exportModel(
		path = os.path.join(output_path, chunk.label+ ".obj"),
		binary=False,
		texture_format=PhotoScan.ImageFormatJPEG,
		texture=True,
		normals=False,
		colors=False,
		cameras=False,
		format = PhotoScan.ModelFormatOBJ)
	
	### Export GeoTiff file
	chunk.buildDem(
		source = source,
		interpolation = interpolation,
		projection = chunk.crs,
		progress = progress_print)
	chunk.exportDem(
		path = os.path.join(output_path, chunk.label + '_DEM.jpeg'),
		image_format = PhotoScan.ImageFormat.ImageFormatJPEG,
		raster_transform = PhotoScan.RasterTransformType.RasterTransformPalette,
		projection = chunk.crs,
		nodata = -32767,
		write_kml = True,
		write_world = True,
		write_scheme = True,
		tiff_big = True)

	# Export orthomosaic
	chunk.buildOrthomosaic(
		surface = PhotoScan.DataSource.ElevationData,
		blending = mosaic_blending,
		fill_holes = True)
	chunk.exportOrthomosaic(
		path = os.path.join(output_path, chunk.label + '_' + str(mosaic_blending) + '_orthomosaic.tif'),
		projection = chunk.crs)

	chunk.buildOrthomosaic(
		surface = PhotoScan.DataSource.ElevationData,
		blending = average_blending,
		fill_holes = True)
	chunk.exportOrthomosaic(
		path = os.path.join(output_path, chunk.label + '_' + str(average_blending) + '_orthomosaic.tif'),
		projection = chunk.crs)

	chunk.buildOrthomosaic(
		surface = PhotoScan.DataSource.ElevationData,
		blending = disabled_blending,
		fill_holes = True)
	chunk.exportOrthomosaic(
		path = os.path.join(output_path, chunk.label + '_' + str(disabled_blending) + '_orthomosaic.tif'),
		projection = chunk.crs)

	### Export camera poses
	export_camera_pose(chunk, os.path.join(output_path, chunk.label + '_camera_pose.csv'))
	
	### Generate report 
	chunk.exportReport(os.path.join(output_path, chunk.label + '_report.pdf'))
	print("Processed " + chunk.label)
	return True

def change_images():
	# Requires same file names just in a different folder  
	new_path = "D:/new_image_folder/" #the new location of the image folder (same filenames)
	for camera in chunk.cameras:
		camera.photo.path = "/".join([new_path, camera.photo.path.rsplit("/",1)[1]])

def main():

	t0 = time.time()
	print("Script started...")

	parser = argparse.ArgumentParser( description='This script processes images in the input folder with PhotoScan to perform 3D reconstructions.')
	parser.add_argument('images_path', type=str,  help='Path to the folder with images to be processed. Both fore and aft.')
	#parser.add_argument('ref_file', type=str, help='Path to reference file for image data.')
	parser.add_argument('-n', '--name', help='Model name.')
	parser.add_argument('-o', '--output', help='Output folder to store the PhotoScan output.')

	args = parser.parse_args()
	
	if not (os.path.isdir(args.images_path)):
		print("Not valid path input. Script aborted.")
		return False	
	
	if not os.path.isdir(args.output):
		os.makedirs(args.output)

	
	process(args.images_path, args.output, args.name)
	t1 = time.time()
	t1 -= t0
	t1 = float(t1)
	print("Script finished in " + "{:.2f}".format(t1) + " seconds.\n")
	return

main()
