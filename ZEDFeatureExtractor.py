# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 11:43:25 2020

@author: jhvroon
"""

import _thread

import pyzed.sl as sl
import cv2
from typing import List

import Features as F
import Actors as A


class CaptureZEDFeatures:
    '''
    The CaptureZEDFeatures captures features from the ZED2 camera.
    
    Args:
        featureExtractor (FeatureExtractor): used to connect the extracted features baked into the ZED2 camera to other features and actors defined in this package.
        trackPeople (bool): indicates whether people tracking should be enabled. Should in most cases be used (otherwise, why use the ZED 2?), but can be disabled to save on resources.
        
    Attributes:
        featureExtractor: stores the featureExtractor
        zed: the camera object
        runtime_parameters: parameters for configuring the camera
        trackpeople: stores if we should track people
        detection_parameters_rt: if we track people, holds parameters for configuring the camera to do so
        objects: the detected objects
        image: the recorded image
    '''
    def __init__(self, featureExtractor, trackPeople):
        self.featureExtractor = featureExtractor
        
        # 1. Create the ZED camera object:
        # Create a Camera object
        self.zed = sl.Camera()
        # Create a InitParameters object and set configuration parameters
        init_params = sl.InitParameters()
        init_params.camera_resolution = sl.RESOLUTION.HD720  # Use HD720 video mode
        init_params.camera_fps = 60  # Set fps at 15
        init_params.coordinate_units = sl.UNIT.METER # Set units in meters
        # Open the camera
        err = self.zed.open(init_params)
        if err != sl.ERROR_CODE.SUCCESS:
            exit(1)
        
        self.runtime_parameters = sl.RuntimeParameters()
        self.runtime_parameters.sensing_mode = sl.SENSING_MODE.STANDARD  # Use STANDARD sensing mode
        
        # Setting the depth confidence parameters
        self.runtime_parameters.confidence_threshold = 100
        self.runtime_parameters.textureness_confidence_threshold = 100
        
        # 2. If we are to track people, initialize:
        self.trackPeople = trackPeople
        if self.trackPeople:
            # Set initialization parameters
            obj_param = sl.ObjectDetectionParameters()
            obj_param.enable_tracking = True
        
            #Configuration for Tracking Object Motion in Runtime using positional tracking
            if obj_param.enable_tracking:
                # Set positional tracking parameters
                positional_tracking_parameters = sl.PositionalTrackingParameters()
                positional_tracking_parameters.set_floor_as_origin = True
        
                # Enable positional tracking
                self.zed.enable_positional_tracking(positional_tracking_parameters)
        
            # Set runtime parameters
            self.detection_parameters_rt = sl.ObjectDetectionRuntimeParameters()
            self.detection_parameters_rt.detection_confidence_threshold = 40
        
            # Enable object detection with initialization parameters
            zed_error = self.zed.enable_object_detection(obj_param)
            if zed_error != sl.ERROR_CODE.SUCCESS :
                print("enable_object_detection", zed_error, "\nExit program.")
                self.zed.close()
                exit(-1)
            
            self.objects = sl.Objects() # Structure containing all the detected objects
        
        #Capture images and depth using point_cloud,
        self.image = sl.Mat()
        
        
    
    def run(self):
        '''Runs the camera and feature extraction until the stop function is called.'''
        self.stopped = False
        
        while not self.stopped:
            # Grab an image, a RuntimeParameters object must be given to grab()
            if self.zed.grab(self.runtime_parameters) == sl.ERROR_CODE.SUCCESS:
                # A new image is available if grab() returns SUCCESS
                self.zed.retrieve_image(self.image, sl.VIEW.LEFT)
                
                if self.trackPeople:
                    self.zed.retrieve_objects(self.objects, self.detection_parameters_rt)
                    self.obj_array = self.objects.object_list
                
                self.image_data = self.image.get_data()
                  
                self.featureExtractor.onFeatureUpdate()
    
        # Close the camera
        self.zed.close()      
            
    def stop(self):
        '''Stops the camera and feature extraction. (Note: you cannot restart the camera after calling stop, as currently the camera object is destroyed.)'''
        self.stopped = True
            
    def getObjects(self):
        '''Returns the objects detected in the most recent frame from the camera.'''
        return self.objects
        
    def getObjectArray(self):
        '''Returns the array of objects from the objects detected in the most recent frame from the camera. Can also be extracted manually with getObjects().object_list'''
        return self.obj_array
    
    def getImage(self):
        '''Returns the latest frame from the camera.'''
        return self.image
    
    def getImageData(self):
        '''Returns data from the latest frame from the camera. Can also be extracted manually with getImage().getData()'''
        return self.image_data




class FeatureExtractor:    
    def __init__(self, features:List[F.Feature], actors:List[A.Actor]):
        self.features = features
        self.actors = actors
        
        dependenciesOK, needsTrackPeople = self.checkFeatures(self.features)
        if not dependenciesOK:
            print("Not all feature dependencies are supplied in the feature list.\nExit program.")
            exit(-1)
        dependenciesOK = self.checkActors(self.actors, self.features)
        
        self.capture = CaptureZEDFeatures(self, needsTrackPeople)
    
    def checkFeatures(self, features:List[F.Feature]):
        '''Returns if all features only depend on features that are listed earlier in the list. Also checks if any feature needs to track people.'''
        dependenciesOK = True
        needsTrackPeople = False
        checked = []
        for feature in features:
            if not needsTrackPeople:
                needsTrackPeople = feature.needsTrackPeople
            for featureNeeded in feature.dependentOn:
                if checked.count(featureNeeded) <= 0:
                    dependenciesOK = False
            checked.append(feature)
        return dependenciesOK, needsTrackPeople
    
    def checkActors(self, actors:List[A.Actor], features:List[F.Feature]):
        '''Returns if all actors depend on features that are listed in the featurelist.'''
        dependenciesOK = True
        for actor in actors:
            for value in actor.expectsValues:
                matchingFeature = False
                for feature in features:
                    if value is feature.label:
                        matchingFeature = True
                dependenciesOK = matchingFeature
        return dependenciesOK
                    
    def start(self):
        '''Starts the ZED2 capture. Also starts a key listener that terminates the capture when the user presses the q-key.'''
        try:
            _thread.start_new_thread( self.capture.run )
            
            def stopFunction(capture:CaptureZEDFeatures):
                key = ''
                while key != 113:
                    key = cv2.waitKey(5)
                capture.stop()
                for actor in self.actors:
                    actor.stop()
            _thread.start_new_thread( stopFunction , (self.capture) )
        except:
            print("Error: unable to start thread")

    def onFeatureUpdate(self):
        '''Should be called whenever a new frame has been loaded from the ZED, computes all feature values for the next frame, and updates all actors.'''
        for feature in self.feature:
            feature.compute(self.capture)
        for actor in self.actors:
            actor.update(self.capture)
    
        


# =============================================================================
# Where we actually construct and run the code:
# =============================================================================
# 1. Construct all the actors            
plotter = A.Cv2Plotter()
actors = [plotter]

# 2. Construct all the features (and connect them to the actors as needed)
distance = F.NaiveDistance(plotter)
features = [distance]

# 3. Create the extractor and run
extractor = FeatureExtractor(features, actors)
extractor.start()

# The extractor has a key listener that should kill it when people press 'q'
        
        