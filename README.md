# 3D Reconstruction Using PhotoScan
<p align="center">
  <img src="https://github.com/laurachrobak/3Dreconstruction/blob/master/crescent_reef_processed.png?raw=true"/>
</p>

+ This repository provides a python script to make 3D reconstructions using PhotoScan

+ A few things that are required include: a PhotoScan license, images, and camera parameters.

# Start
PhotoScan has a GUI version that is easy to use, however, this tutorial uses a python script to access the PhotoScan API. The underwater images that are used to make the results presented here are color corrected using closed-source software and were collected by Drop lab in collaboration with the WHOI and University of Georgia. An object file of the 3D reconstruction can be found [here](https://umich.box.com/s/4lvs2cu2nsgcbptf4c6klisq3lsych7w). The images used to make the reconstruction shown above were taken at Crescent Reef, [Bermuda](https://www.pmel.noaa.gov/co2/story/Crescent+Reef).

# Run
To run this code use the following command in the folder containing photoscan.sh:
```
 ./photoscan.sh -r <processing script>  <input image directory> -o <output directory> -n <output name>
```
And example of this line can be seen below below:
```
 ./photoscan.sh -r /Users/chrobak/Desktop/photoscan-processing-diver-rig.py /Users/chrobak/Desktop/input_images -o /Users/chrobak/Desktop/output_images -n crescent-reef-full
```
# Code Modifications

1) Depending on how many GPUs are being used, change the following line: 
```
	‘PhotoScan.app.gpu_mask = 15’, change 15 to 11, for example, so that only 3 GPUs are used
```
2) The quality and accuracy of the reconstruction can be changed to Low or Medium depending on the output you are looking for. It is good practice to start with a small subset of your images and do a low quality build to make sure everything runs correctly first. Then do a higher quality build of all of the images. Finally, if the previous two reconstructions go smoothly then you can make a high accuracy reconstruction of all of the images. Using one GPU for a high accuracy, quality, and face count reconstruction can take more than a day so its best to start small. 

The above can be changed under, ### Processing parameters
```
accuracy = PhotoScan.Accuracy.HighAccuracy  #align photos accuracy	
quality = PhotoScan.Quality.HighQuality # Build dense cloud quality
face_num = PhotoScan.FaceCount.HighFaceCount # Build mesh polygon count
```
Ex. change to:
```
accuracy = PhotoScan.Accuracy.LowAccuracy  #align photos accuracy
```
3) Certain camera parameters such as camera sensor width and height (in pixels), pixel size, and focal length can be changed under heading, # Create Sensor definitions, according to the camera used to collect the images. Furthermore, if using a stereo camera the baseline between the two cameras, in meters, can be changed in the line below:
```
scalebar.reference.distance = 0.1282
```
