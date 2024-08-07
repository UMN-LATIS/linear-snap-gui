import threading
import gphoto2 as gp
import numpy as np
from scipy import ndimage
import cv2
import os
import platform
import time;
import atexit
from pubsub import pub
import pathlib
import shutil
from multiprocessing.connection import Client

if(platform.system() == "Darwin"):
    os.system("killall -9 ptpcamerad")



class CameraControl:
    image = None
    t = None
    photoCount = 0
    stopWaiting = False
    stopLiveView = True
    laplacian = 0
    likelyBlank = False
    camera = None
    new_folder_path = ""
    requiresRefocus = False
    stackCenter = None


    def __init__(self, config):
        self.config = config
        if(platform.system() == "Darwin"):
            os.system("killall -9 ptpcamerad")
        # Init camera
        try:
            self.camera = gp.Camera()
            # self.camera.init()
            # self.camera_config = self.camera.get_config()
        except:
            print("Camera not found")
            self.camera = None
        self.timeout = 3000  # milliseconds
        atexit.register(self.cleanup)
    
    def reset(self):
        self.photoCount = 0
        self.laplacian = 0
        self.likelyBlank = False
        self.requiresRefocus = False

    def setCoreId(self, coreId):
        self.coreId = coreId



    def cleanup(self):
        self.stopLiveView = True
        time.sleep(0.1)
        print("Running cleanup...")
        if(self.camera is not None):
            self.camera.exit()

    def setLiveView(self, liveView):
        if(liveView):
            if(self.stopLiveView == False):
                return
            self.stopLiveView = False

            self.t = threading.Thread(target=self.runLiveView, name='liveViewWorker')
            self.t.daemon = True
            self.t.start()    
        else:
            self.stopLiveView = True
    
    def sortPhotos(self, temp_folder_path, new_folder_path):
        print("Sorting photos")
        # organize photos
        
        # get a list of all files in the folder
        jpeg_files = []
        iterations = 0

            # filter the list to only include jpeg files
        files = os.listdir(temp_folder_path)
        files.sort()
        jpeg_files = [f for f in files if f.endswith('.JPG') or f.endswith('.jpg')]
        
        # sort the first 20 files
        # create a new folder with a numeric title (001, 002, 003 etc)
        i = 1
        while True:
            created_folder_path = os.path.join(new_folder_path, '{:03d}'.format(i))
            if not os.path.exists(created_folder_path):
                os.makedirs(created_folder_path)
                break
            i += 1

        # move all jpeg files into the new folder
        stackDepth = int(self.config.configValues["StackDepth"])
        for jpeg in jpeg_files[:stackDepth]:
            old_path = os.path.join(temp_folder_path, jpeg)
            new_path = os.path.join(created_folder_path, jpeg)
            os.rename(old_path, new_path)
        print("done sorting")

        print("display the middle image")
        self.image = cv2.imread(os.path.join(created_folder_path,jpeg_files[round(stackDepth / 2)]))

        # get the filesize of each photo
        file_sizes = []
        for jpeg in jpeg_files[:stackDepth]:
            file_sizes.append(os.path.getsize(os.path.join(created_folder_path, jpeg)))
        
        # check if the biggest size is within 3 positions of the start or the end of the list
        biggest_size = max(file_sizes)
        biggest_size_index = file_sizes.index(biggest_size)
        self.stackCenter = biggest_size_index
        if biggest_size_index < 3 or biggest_size_index > len(file_sizes) - 3:
            print("Biggest size is within 3 positions of the start or the end of the list")
            self.requiresRefocus = True

        # check if the biggest size is less than 10% bigger than the smallest size
        smallest_size = min(file_sizes)
        if biggest_size < smallest_size * 1.1:
            self.requiresRefocus = True



    def testForBlank(self, photo):
        # Load the image
        image = cv2.imread(photo)
        if image is None:
            return
        # Get the image height and width
        height, width = image.shape[:2]
        # Get the center point
        x, y = int(width/2), int(height/2)
        # Crop the image to a 500x500 square, centered around the center point
        cropped_image = image[y-250:y+250, x-250:x+250]
        # Get the average brightness of the image
        b, g, r, a = cv2.mean(cropped_image)
        avg_brightness = (b + g + r) / 3
        # Check if the average brightness is below a certain threshold
        threshold = 20
        if avg_brightness < threshold:
            print("End of core")
            self.stopWaiting = True
            pub.sendMessage("coreStatus", message="end")


    def notifyCoreComplete(self):
        address = ('localhost', 6234)
        try:
            conn = Client(address, authkey=b'dendroFun')
            print("Broadcasting Core Complete Message")
            conn.send(self.new_folder_path)
            # conn.send(self.new_folder_path)
            conn.close()
        except: 
            print("Error sending message to LinearStitch")

    def prepForCore(self, coreId):
        self.coreId = coreId
        timestr = time.strftime("%Y%m%d-%H%M%S")
        self.new_folder_path = os.path.join(self.config.configValues["BasePath"], coreId + "-" + timestr)
        if not os.path.exists(self.new_folder_path):
            os.makedirs(self.new_folder_path)

        if(platform.system() == "Darwin"):
            os.system("killall -9 ptpcamerad")
        self.camera.init()
        self.setupCamera(self.config.configValues["captureISO"]);



    def waitForPhoto(self, coreId):
        print("Starting waitForPhoto thread")
        
        temp_folder_path = os.path.join(self.new_folder_path, "scratch")
        if not os.path.exists(temp_folder_path):
            os.makedirs(temp_folder_path)
        
        self.photoCount = 0;
        print("Waiting for Photos")
        
        self.newPosition = True
        self.stopWaiting = False
        timeout = 3000  # milliseconds
        while True:
            event_type, event_data = self.camera.wait_for_event(timeout)
            if event_type == gp.GP_EVENT_FILE_ADDED:
                print("new loop")
                cam_file = self.camera.file_get(
                    event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                target_path = os.path.join(temp_folder_path, event_data.name)
                print("Image is being saved to {}".format(target_path))
                cam_file.save(target_path)
                if(self.newPosition):
                    self.newPosition = False
                    print("new position")
                    self.blank = threading.Thread(target=self.testForBlank,args=(target_path,), name='test-for-blank')
                    self.blank.daemon = True
                    self.blank.start()
                self.photoCount = self.photoCount + 1
                if(self.photoCount == int(self.config.configValues["StackDepth"])):
                    print("end of position")
                    self.photoCount = 0
                    self.sort = threading.Thread(target=self.sortPhotos, args=(temp_folder_path,self.new_folder_path, ), name='photo-sort')
                    self.sort.daemon = True
                    self.sort.start()
                    self.newPosition = True
            if(self.stopWaiting):
                print("Breaking")
                print("Cleaning up scratch")
                shutil.rmtree(pathlib.Path(temp_folder_path))
                time.sleep(2)
                self.camera.exit()
                print("Exited camera")
                break
    

    def setupCamera(self, isoValue): 
        self.camera_config = self.camera.get_config()

        if(self.config.configValues["cameraModel"] == "Canon R8"):
            child = self.camera_config.get_child_by_name("iso")
            child.set_value(isoValue)
            self.camera.set_single_config("iso", child)
            child = self.camera_config.get_child_by_name("shutterspeed")
            child.set_value(self.config.configValues["previewShutter"])
            self.camera.set_single_config("shutterspeed", child)

            child = self.camera_config.get_child_by_name("whitebalance")
            child.set_value("Color Temperature")
            self.camera.set_single_config("whitebalance", child)

            child = self.camera_config.get_child_by_name("colortemperature")
            child.set_value(self.config.configValues["colorTemperature"])
            self.camera.set_single_config("colortemperature", child)
        elif(self.config.configValues["cameraModel"] == "Sony ILX-LR1"):
            child = self.camera_config.get_child_by_name("iso")
            child.set_value(isoValue)
            self.camera.set_single_config("iso", child)
            child = self.camera_config.get_child_by_name("shutterspeed")
            child.set_value(self.config.configValues["previewShutter"])
            self.camera.set_single_config("shutterspeed", child)

            child = self.camera_config.get_child_by_name("whitebalance")
            child.set_value("Choose Color Temperature")
            self.camera.set_single_config("whitebalance", child)

            child = self.camera_config.get_child_by_name("colortemperature")
            child.set_value(float(self.config.configValues["colorTemperature"]))
            self.camera.set_single_config("colortemperature", child)




    def runLiveView(self):
        if(platform.system() == "Darwin"):
            os.system("killall -9 ptpcamerad")
        self.camera.init()
        print("Init LiveView")

        self.setupCamera(self.config.configValues["previewISO"]);
        frameCount = 0
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


            # wait until we've had 5 frames to start doing math, in case the buffer has old frames
            if(frameCount > 5):
                # Calculate the Laplacian of the frame
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                variance = laplacian.var()
                self.laplacian = variance

                # check if the center of the image is black and set a flag
                b, g, r, a = cv2.mean(middle_square)
                avg_brightness = (b + g + r) / 3
                # Check if the average brightness is below a certain threshold
                threshold = 40
                if avg_brightness < threshold:
                    self.likelyBlank = True
            

            # Display the frame in a window
            self.image = img
            # cv2.imshow("Live View", img)
            
            # Display the laplacian in the window as well
            # cv2.imshow("Laplacian", laplacian)

            if(self.stopLiveView):
                time.sleep(0.1)
                self.camera_config = self.camera.get_config()
                
                # alt key is "capture" on digital rebels
                if(self.config.configValues["cameraModel"] == "Canon R8"):
                    child = self.camera_config.get_child_by_name("viewfinder")
                    child.set_value(0)
                    self.camera.set_single_config("viewfinder", child)
                self.image = None
                self.camera.exit()
                # self.camera.set_config(self.camera_config)
                break

            frameCount = frameCount + 1

