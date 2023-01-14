import threading
import gphoto2 as gp
import numpy as np
from scipy import ndimage
import cv2
import os
import platform
import time;
import atexit

if(platform.system() == "Darwin"):
    os.system("killall -9 ptpcamerad")



class CameraControl:
    image = None
    photoCount = 0

    def __init__(self):
        if(platform.system() == "Darwin"):
            os.system("killall -9 ptpcamerad")
        # Init camera
        try:
            self.camera = gp.Camera()
            self.camera.init()
            self.camera_config = self.camera.get_config()
        except:
            print("Camera not found")
            self.camera = None
        self.timeout = 3000  # milliseconds
        atexit.register(self.cleanup)
    
    def setCoreId(self, coreId):
        self.coreId = coreId
        

    def cleanup(self):
        self.stopLiveView = True
        time.sleep(0.1)
        print("Running cleanup...")
        self.camera.exit()

    def setLiveView(self, liveView):
        if(liveView):
            self.stopLiveView = False

            self.t = threading.Thread(target=self.runLiveView, name='liveViewWorker')
            self.t.daemon = True
            self.t.start()    
        else:
            self.stopLiveView = True
    
    def sortPhotos(self):
        print("Sorting photos")
        # organize photos
        
        # get a list of all files in the folder
        jpeg_files = []
        iterations = 0

            # filter the list to only include jpeg files
        files = os.listdir(os.getcwd())
        files.sort()
        jpeg_files = [f for f in files if f.endswith('.JPG') or f.endswith('.jpg')]
        
        # sort the first 20 files
        # create a new folder with a numeric title (001, 002, 003 etc)
        i = 1
        while True:
            new_folder_path = os.path.join(os.getcwd(), '{:03d}'.format(i))
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
                break
            i += 1

        # move all jpeg files into the new folder
        for jpeg in jpeg_files[:20]:
            old_path = os.path.join(os.getcwd(), jpeg)
            new_path = os.path.join(new_folder_path, jpeg)
            os.rename(old_path, new_path)
        print("done sorting")


    def waitForPhoto(self, coreId):
        self.coreId = coreId
        timeout = 3000  # milliseconds
        while True:
            event_type, event_data = self.camera.wait_for_event(timeout)
            if event_type == gp.GP_EVENT_FILE_ADDED:
                cam_file = self.camera.file_get(
                    event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                target_path = os.path.join(os.getcwd(), event_data.name)
                print("Image is being saved to {}".format(target_path))
                cam_file.save(target_path)
                self.photoCount = self.photoCount + 1
                if(self.photoCount == 20):
                    self.photoCount = 0
                    self.t = threading.Thread(target=self.sortPhotos, name='photo-sort')
                    self.t.daemon = True
                    self.t.start()


    def runLiveView(self):
        while True:
            # Get the preview frame
            data = self.camera.capture_preview()
            data = gp.check_result(gp.gp_file_get_data_and_size(data))
            array = np.fromstring(memoryview(data).tobytes(), dtype=np.uint8)
            img = cv2.imdecode(array, cv2.IMREAD_COLOR)
            # Convert the frame to a numpy array
            # img = file_data.reshape(file_data.shape[1], file_data.shape[0], 3)
            height, width = img.shape[:2]

            # Calculate the coordinates of the top-left corner of the middle square
            left = (width - 500) // 2
            top = (height - 500) // 2
            # Get the middle 500x500 pixel square
            middle_square = img[top:top+500, left:left+500]
            # Convert the frame to grayscale
            gray = cv2.cvtColor(middle_square, cv2.COLOR_BGR2GRAY)

            # Calculate the Laplacian of the frame
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()
            self.laplacian = variance

            # Display the frame in a window
            self.image = img
            # cv2.imshow("Live View", img)
            
            # Display the laplacian in the window as well
            # cv2.imshow("Laplacian", laplacian)

            if(self.stopLiveView):
                time.sleep(0.1)
                self.camera_config = self.camera.get_config()
                
                child = self.camera_config.get_child_by_name("capture")
                #to-enable:
                child.set_value(0)
                #to-disable:
                # child.set_value("20,1,3,14,1,60f,1,0")
                self.camera.set_single_config("capture", child)
                self.image = None
                # self.camera.set_config(self.camera_config)
                break


