#!/usr/bin/env python

# python-gphoto2 - Python interface to libgphoto2
# http://github.com/jim-easterbrook/python-gphoto2
# Copyright (C) 2019  Göktuğ Başaran
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License

# *******************************************************
# camera.wait_for_event() function waits for a capture trigger
# to arrive and returns the folder and name of the new file.
# When it does, camera.file_get() is used to download
# the image directly from the camera, without using SD
# card
#
# camera.trigger_capture() or Trigger Button on the
# camera can be used to start capturing.
#
# gp_capture_image_and_download() method takes about 2 seconds
# to process since it saves the image to SD CARD
# first then downloads it, which takes a lot of time.
# *******************************************************

# Additional comment by Jim Easterbrook: My cameras save to SD card or
# RAM according to the capture target setting. Use of
# camera.wait_for_event() or camera.capture() makes no difference to
# where the image is saved.

import locale
import os
import sys

import gphoto2 as gp


def main():
    os.system("killall -9 ptpcamerad")
    locale.setlocale(locale.LC_ALL, '')
    # Init camera
    camera = gp.Camera()
    camera.init()
    timeout = 3000  # mi
    camera_config = camera.get_config()

        
    child = camera_config.get_child_by_name("iso")
    child.set_value("1600")
    camera.set_single_config("iso", child)

    child = camera_config.get_child_by_name("shutterspeed")
    child.set_value("1/500")
    camera.set_single_config("shutterspeed", child)
    while True:
        event_type, event_data = camera.wait_for_event(timeout)
        if event_type == gp.GP_EVENT_FILE_ADDED:
            cam_file = camera.file_get(
                event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
            target_path = os.path.join(os.getcwd(), event_data.name)
            print("Image is being saved to {}".format(target_path))
            cam_file.save(target_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())