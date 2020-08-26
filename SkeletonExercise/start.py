import pyzed.sl as sl
import cv2
import numpy as np

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
    #init_params.camera_fps = 15  # Set fps at 15

    # Open the camera
    err = zed.open(init_params)
    if err != sl.ERROR_CODE.SUCCESS:
        exit(1)

    # Capture 50 frames and stop
    mat = sl.Mat()
    runtime_parameters = sl.RuntimeParameters()
    key = ''

    zed.enable_positional_tracking()

    obj_param = sl.ObjectDetectionParameters()
    obj_param.enable_tracking = True
    obj_param.detection_model = sl.DETECTION_MODEL.HUMAN_BODY_FAST

    zed.enable_object_detection(obj_param)

    objects = sl.Objects()
    obj_runtime_param = sl.ObjectDetectionRuntimeParameters()
    obj_runtime_param.detection_confidence_threshold = 40

    while key != 113: # for 'q' key
        # Grab an image, a RuntimeParameters object must be given to grab()
        ddtry = []
        ddtry2 = []
        if zed.grab(runtime_parameters) == sl.ERROR_CODE.SUCCESS:
            # A new image is available if grab() returns SUCCESS
            zed.retrieve_image(mat, sl.VIEW.LEFT)
            zed.retrieve_objects(objects, obj_runtime_param)
            obj_array = objects.object_list
            image_data = mat.get_data()
            for i in range(len(obj_array)) :
                obj_data = obj_array[i]
                bounding_box = obj_data.bounding_box_2d
                cv2.rectangle(image_data, (int(bounding_box[0,0]),int(bounding_box[0,1])),
                            (int(bounding_box[2,0]),int(bounding_box[2,1])),
                              get_color_id_gr(int(obj_data.id)), 3)

                keypoint = obj_data.keypoint_2d
                for kp in keypoint:
                    if kp[0] > 0 and kp[1] > 0:
                        cv2.circle(image_data, (int(kp[0]), int(kp[1])), 3, get_color_id_gr(int(obj_data.id)), -1)
                
                for bone in sl.BODY_BONES:
                    kp1 = keypoint[bone[0].value]
                    kp2 = keypoint[bone[1].value]
                   
                    if kp1[0] > 0 and kp1[1] > 0 and kp2[0] > 0 and kp2[1] > 0 :
                        cv2.line(image_data, (int(kp1[0]), int(kp1[1])), (int(kp2[0]), int(kp2[1])), get_color_id_gr(int(obj_data.id)), 2)
                ddtry.append(kp1)
                ddtry2.append(kp2)
            np.savetxt("C:\\Users\\localadmin\\Desktop\\kp1.csv", ddtry)
            np.savetxt("C:\\Users\\localadmin\\Desktop\\kp2.csv", ddtry2)

            cv2.imshow("ZED", image_data)
            
        key = cv2.waitKey(5)

    cv2.destroyAllWindows()


    # Close the camera
    zed.close()
    return 0;
if __name__ == "__main__":
    main()

