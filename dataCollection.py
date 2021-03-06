# In this example we will first run the Object Detection module to detect object on the scene.
# And then we will calculate the distance of the object from the camera.


import pyzed.sl as sl
import cv2
import numpy as np
import math
import sys
import xlsxwriter
import datetime

id_colors = [(59, 232, 176),
             (25,175,208),
             (105,102,205),
             (255,185,0),
             (252,99,107)]

def get_color_id_gr(idx):
    color_idx = idx % 5
    arr = id_colors[color_idx]
    return arr

def main():
    # Create a Camera object
    zed = sl.Camera()

    # Create a InitParameters object and set configuration parameters
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD720  # Use HD720 video mode
    init_params.camera_fps = 60  # Set fps at 15
    init_params.coordinate_units = sl.UNIT.METER # Set units in meters

    # Open the camera
    err = zed.open(init_params)
    if err != sl.ERROR_CODE.SUCCESS:
        exit(1)
       
    runtime_parameters = sl.RuntimeParameters()
    runtime_parameters.sensing_mode = sl.SENSING_MODE.STANDARD  # Use STANDARD sensing mode
    
    # Setting the depth confidence parameters   
    runtime_parameters.confidence_threshold = 100
    runtime_parameters.textureness_confidence_threshold = 100
    key = ''

    # Set initialization parameters
    obj_param = sl.ObjectDetectionParameters()
    obj_param.enable_tracking = True

    #Configuration for Tracking Object Motion in Runtime using positional tracking
    if obj_param.enable_tracking :
        # Set positional tracking parameters
        positional_tracking_parameters = sl.PositionalTrackingParameters()
        positional_tracking_parameters.set_floor_as_origin = True

        # Enable positional tracking
        zed.enable_positional_tracking(positional_tracking_parameters)

   # Set runtime parameters
    detection_parameters_rt = sl.ObjectDetectionRuntimeParameters()
    detection_parameters_rt.detection_confidence_threshold = 40

    # Enable object detection with initialization parameters
    zed_error = zed.enable_object_detection(obj_param)
    if zed_error != sl.ERROR_CODE.SUCCESS :
        print("enable_object_detection", zed_error, "\nExit program.")
        zed.close()
        exit(-1)
    
    objects = sl.Objects() # Structure containing all the detected objects

    #Capture images and depth using point_cloud,
    image = sl.Mat()

    #creating an excel sheet to collect data
    x = datetime.datetime.now()
    filename = 'data' + str(x) + '.xlsx'
    workbook = xlsxwriter.Workbook(filename, {'constant_memory': True})
    worksheet = workbook.add_worksheet()

    worksheet.write('A1', 'ID')
    worksheet.write('B1', 'Label')
    worksheet.write('C1', 'x-axis')
    worksheet.write('D1', 'y-axis')
    worksheet.write('E1', 'z-axis')
    worksheet.write('F1', 'Distance from Camera')

    row = 1
    col = 0
  
    while key != 113: # for 'q' key
        # Grab an image, a RuntimeParameters object must be given to grab()
        if zed.grab(runtime_parameters) == sl.ERROR_CODE.SUCCESS:
            # A new image is available if grab() returns SUCCESS
            zed.retrieve_image(image, sl.VIEW.LEFT)
            zed.retrieve_objects(objects, detection_parameters_rt)
            obj_array = objects.object_list
            image_data = image.get_data()
      
            prePosition = [0,0,0]
            
            for i in range(len(obj_array)) :
                obj_data = obj_array[i]
                bounding_box = obj_data.bounding_box_2d
                cv2.rectangle(image_data, (int(bounding_box[0,0]),int(bounding_box[0,1])),
                            (int(bounding_box[2,0]),int(bounding_box[2,1])),
                              get_color_id_gr(int(obj_data.id)), 3)

                #Getting object data         
                obj_label = str(obj_data.label)
                obj_position = obj_data.position
                obj_id = int(obj_data.id)

                # Calculating distance
                distance = math.sqrt((obj_position[0]-prePosition[0])*(obj_position[0]-prePosition[0]) + 
                                   (obj_position[1]-prePosition[1])*(obj_position[1]-prePosition[1]) +
                                   (obj_position[2]-prePosition[2])*(obj_position[2]-prePosition[2]))

                #label string for cordinates and distance 
                obj_cordinates = "X: " + str(obj_position[0]) + " Y: " + str(obj_position[1]) + " Z: " + str(obj_position[1])
                obj_distance = "Distance: " + str(distance)
                
                #Display data on screen
                cv2.putText(image_data, obj_label, (int(bounding_box[0,0]),int(bounding_box[0,1]-50)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255),1)
                cv2.putText(image_data, obj_cordinates, (int(bounding_box[0,0]),int(bounding_box[0,1]-30)), cv2.FONT_HERSHEY_SIMPLEX, 0.6,(255,255,255),1)
                cv2.putText(image_data, obj_distance, (int(bounding_box[0,0]),int(bounding_box[0,1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6,(255,255,255),1)

                #collecting data in excelsheet
                if obj_data and obj_label == "Person":
                    worksheet.write(row, col, obj_id)
                    worksheet.write(row, col + 1, obj_label)
                    worksheet.write(row, col + 2, (str(obj_position[0])))
                    worksheet.write(row, col + 3, (str(obj_position[1])))
                    worksheet.write(row, col + 4, (str(obj_position[2])))
                    worksheet.write(row, col + 5, (str(distance)))

                    row +=1

                prePosition = obj_position            
            
            cv2.imshow("ZED", image_data)
                    
        key = cv2.waitKey(5)

    cv2.destroyAllWindows()

    # Close the camera
    zed.close()
    workbook.close()

if __name__ == "__main__":
    main()
