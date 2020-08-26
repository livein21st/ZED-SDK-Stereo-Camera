# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 11:44:24 2020

@author: jhvroon
"""

import cv2

from typing import List
import ZEDFeatureExtractor as ZED
import Features as F



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
        
    def update(self,capture:ZED.CaptureZEDFeatures):
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
    expectsValues.append(F.naiveDistanceLabel) #list of distances, one for each detected object
    
    def __init__(self):
        super.__init__(Cv2Plotter.expectsValues)
    
    def update(self,capture:ZED.CaptureZEDFeatures):
        '''Plot the next frame.'''
        obj_array = capture.getObjectArray()
        image_data = capture.getImageData()
        distances = self.values[F.naiveDistanceLabel]
        
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
