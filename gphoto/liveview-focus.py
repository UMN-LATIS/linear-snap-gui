import gphoto2 as gp
import numpy as np
from scipy import ndimage
import cv2
import os
import platform
import threading
import time;
if(platform.system() == "Darwin"):
    os.system("killall -9 ptpcamerad")

# Connect to the first camera found
camera = gp.Camera()
camera.init()

def waitForPhoto():
    if(platform.system() == "Darwin"):
        os.system("killall -9 ptpcamerad")
    # Init camera
    camera = gp.Camera()
    camera.init()
    timeout = 3000  # milliseconds
    while True:
        event_type, event_data = camera.wait_for_event(timeout)
        if event_type == gp.GP_EVENT_FILE_ADDED:
            cam_file = camera.file_get(
                event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
            target_path = os.path.join(os.getcwd(), event_data.name)
            print("Image is being saved to {}".format(target_path))
            cam_file.save(target_path)

# Put the camera into liveview mode
# camera.set_liveview(True)
# t = threading.Thread(target=waitForPhoto, name='captureWorker')
# t.daemon = True
# t.start()
# Get the liveview image data

while True:
    # Get the preview frame
    data = camera.capture_preview()
    data = gp.check_result(gp.gp_file_get_data_and_size(data))
    array = np.fromstring(memoryview(data).tobytes(), dtype=np.uint8)
    img = cv2.imdecode(array, 1)
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
    print(variance)

    # Display the frame in a window
    cv2.imshow("Live View", img)
    
    # Display the laplacian in the window as well
    cv2.imshow("Laplacian", laplacian)

    # Check for user input to exit
    key = cv2.waitKey(1)
    if key == 27:
        break



# Release the camera resources
camera.exit()

t = threading.Thread(target=waitForPhoto, name='captureWorker')
t.daemon = True
t.start()
while True:
    print("hey")
    time.sleep(1)
# Close all windows
cv2.destroyAllWindows()