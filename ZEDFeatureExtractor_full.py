# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 10:50:05 2020

@author: jhvroon
"""


import thread

import pyzed.sl as sl
import cv2
import math

from typing import List





class Feature:
    '''
    Features compute values based on other features and/or the data from the ZED 2.
    
    Args:
        label: label for the feature, used to identify its values in all associated actors.
        actors: ...that should act based on the values from this Feature.
        dependentOn: features whose computed value(s) this feature uses to compute its own value(s).
        
    Attributes:
        value: last computed value for this feature.
        needsTrackPeople: whether or not this feature depends on tracking people with the ZED2.
    '''
    def __init__(self, label, actors:List, dependentOn:List):
        self.label = label
        self.actors = actors
        self.dependentOn = dependentOn
        self.value
        
        self.needsTrackPeople = False
        
    def addActor(self,actor):
        '''Actors can be added during construction or later on.'''
        self.actors.append(actor)
        
    def getValue(self):
        '''Return the last computed value for this Feature.'''
        return self.value
    
    def compute(self, capture):
        '''Computes the value for each new frame and updates the feature's actors accordingly.'''
        self.computeValue(capture)
        for actor in self.actors:
            actor.updateValue(self.label, self.getValue())
            
    def computeValue(self, capture):
        '''Dummy-method. Should be implemented to update with each new frame.''' 
        pass  #TODO implement me in each subclass implementing Feature
    


# =============================================================================
# NaiveDistance
# =============================================================================
naiveDistanceLabel = "NaiveDistance"
class NaiveDistance(Feature):
    '''
    The NaiveDistance is a Feature that lazily computes distances between each detected person and the previous detected person (first person compared to 0,0,0).
    '''
    dependentOn = []
    
    def __init__(self, actors):
        super.__init__(naiveDistanceLabel,actors,NaiveDistance.dependentOn)
        self.actors = actors
        self.needsTrackPeople = True
        
    def computeValue(self, capture):
        '''Computes the distances between each detected person and the previous detected person (first person compared to 0,0,0).'''
        prePosition = [0,0,0]
        obj_array = capture.getObjectArray()
        self.value = []
            
        for i in range(len(obj_array)) :
            obj_data = obj_array[i]
            obj_position = obj_data.position

            # Calculating distance 
            distance = math.sqrt((obj_position[0]-prePosition[0])*(obj_position[0]-prePosition[0]) + 
                               (obj_position[1]-prePosition[1])*(obj_position[1]-prePosition[1]) +
                               (obj_position[2]-prePosition[2])*(obj_position[2]-prePosition[2]))
            self.value.append(distance)

            prePosition = obj_position
        



class Actor:   
    '''
    Actors do something with the data and features extracted from the ZED2
    
    Args:
        expectsValues (List): values that the actor expects (as identified by their label)
        
    Attributes:
        values: dictionary that holds the values that the actor works from
        expectsValues (List): stores the labels of the expected values
    '''
    def __init__(self, expectsValues:List):
        self.values = {}
        self.expectsValues = expectsValues
        
    def update(self,capture):
        '''Dummy-method. Should be implemented to update with each new frame (after feature values have been updated).'''
        pass ##TODO
        
    def updateValue(self, label:str, value):
        '''Stores the given value with in a dictionary under the given label, to be used for updating later on.'''
        self.values[label] = value
        
    def stop(self):
        '''Dummy-method. Should be implemented to clean-up when the actor is stopped.'''
        pass ##TODO
    


# =============================================================================
# Cv2Plotter
# =============================================================================
class Cv2Plotter(Actor):
    '''
    The Cv2Plotter is an Actor that plots the ZED2 data with bounding boxes and NaiveDistances
    '''
    id_colors = [(59, 232, 176),
             (25,175,208),
             (105,102,205),
             (255,185,0),
             (252,99,107)]

    def get_color_id_gr(idx):
        color_idx = idx % 5
        arr = Cv2Plotter.id_colors[color_idx]
        return arr
    
    expectsValues = [] 
    expectsValues.append(naiveDistanceLabel) #list of distances, one for each detected object
    
    def __init__(self):
        super.__init__(Cv2Plotter.expectsValues)
    
    def update(self,capture):
        '''Plot the next frame.'''
        obj_array = capture.getObjectArray()
        image_data = capture.getImageData()
        distances = self.values[naiveDistanceLabel]
        
        # For each tracked object....
        for i in range(len(obj_array)):
            obj_data = obj_array[i]
            
            # 1. Plot a bounding box
            bounding_box = obj_data.bounding_box_2d
            cv2.rectangle(image_data, (int(bounding_box[0,0]),int(bounding_box[0,1])),
                        (int(bounding_box[2,0]),int(bounding_box[2,1])),
                          Cv2Plotter.get_color_id_gr(int(obj_data.id)), 3)
            
            # 2. Plot the distance between the object and the previous object
            obj_label = str(obj_array[i].label)
            
            distance = distances[i]

            cv2.putText(image_data, obj_label, (int(bounding_box[0,0]),int(bounding_box[0,1]-30)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),1)
            cv2.putText(image_data, str(distance), (int(bounding_box[0,0]),int(bounding_box[0,1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),1)
            
        # And plot the whole frame as well:                  
        cv2.imshow("ZED", image_data)
        
    def stop(self):
        '''When stopped, the cv2-window will be closed.'''
        cv2.destroyAllWindows()






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
    def __init__(self, features:List[Feature], actors:List[Actor]):
        self.features = features
        self.actors = actors
        
        dependenciesOK, needsTrackPeople = self.checkFeatures(self.features)
        if not dependenciesOK:
            print("Not all feature dependencies are supplied in the feature list.\nExit program.")
            exit(-1)
        dependenciesOK = self.checkActors(self.actors, self.features)
        
        self.capture = CaptureZEDFeatures(self, needsTrackPeople)
    
    def checkFeatures(self, features:List[Feature]):
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
    
    def checkActors(self, actors:List[Actor], features:List[Feature]):
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
            thread.start_new_thread( self.capture.run )
            
            def stopFunction(capture:CaptureZEDFeatures):
                key = ''
                while key != 113:
                    key = cv2.waitKey(5)
                capture.stop()
                for actor in self.actors:
                    actor.stop()
            thread.start_new_thread( stopFunction , (self.capture) )
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
plotter = Cv2Plotter()
actors = [plotter]

# 2. Construct all the features (and connect them to the actors as needed)
distance = NaiveDistance(plotter)
features = [distance]

# 3. Create the extractor and run
extractor = FeatureExtractor(features, actors)
extractor.start()

# The extractor has a key listener that should kill it when people press 'q'
        
