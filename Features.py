# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 11:44:08 2020

@author: jhvroon
"""

import math

from typing import List
import ZEDFeatureExtractor as ZED
import Actors as A



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
    def __init__(self, label, actors:List[A.Actor], dependentOn:List):
        self.label = label
        self.actors = actors
        self.dependentOn = dependentOn
        self.value
        
        self.needsTrackPeople = False
        
    def addActor(self,actor:A.Actor):
        '''Actors can be added during construction or later on.'''
        self.actors.append(actor)
        
    def getValue(self):
        '''Return the last computed value for this Feature.'''
        return self.value
    
    def compute(self, capture:ZED.CaptureZEDFeatures):
        '''Computes the value for each new frame and updates the feature's actors accordingly.'''
        self.computeValue(capture)
        for actor in self.actors:
            actor.updateValue(self.label, self.getValue())
            
    def computeValue(self, capture:ZED.CaptureZEDFeatures):
        '''Dummy-method. Should be implemented to update with each new frame.''' 
        pass  #TODO implement me in each subclass implementing Feature
    


# =============================================================================
# NaiveDistance
# =============================================================================
class NaiveDistance(Feature):
    '''
    The NaiveDistance is a Feature that lazily computes distances between each detected person and the previous detected person (first person compared to 0,0,0).
    '''
    label = "NaiveDistance"
    dependentOn = []
    
    def __init__(self, actors):
        super.__init__(NaiveDistance.label,actors,NaiveDistance.dependentOn)
        self.actors = actors
        self.needsTrackPeople = True
        
    def computeValue(self, capture:ZED.CaptureZEDFeatures):
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
        