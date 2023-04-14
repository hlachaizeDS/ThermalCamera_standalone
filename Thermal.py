"""
This module handles extracting well temperatures from Optris images
"""
from Optris.Optris import *
import numpy as np
#import imageio
from pathlib import Path
from typing import Union
import logging
import time
from matplotlib import pyplot as plt
import threading
from PIL import Image, ImageTk
import datetime
import os
from time import *
import cv2 as cv
import pandas as pd
import pickle
from MTM import matchTemplates
from socket_server import *
import json


class ThermalImageThread:

    def __init__(self, mainFrame):

        """Parameters"""
        self.is_384 = 0                     #format of the plate
        self.OS = "Windows"                  # Ubuntu or Windows
        self.camera_type = "Xi400"          # so far only Xi400
        self.automatic_detection = 2        # 0 for no detection, 1 for image processing, 2 for fixed pixels
        self.flip_vertically = 1            # mirror through vertical axis
        self.flip_horizontally = 0          # mirror through horizontal axis
        self.zoom = 1.2                     # Zoom factor, used only for display of UI
        self.delay = 0.05                   # refresh of thermal images
        self.cm = plt.get_cmap('seismic')   # Color map

        # delay between the reception of the snapshot order and the actual snapshot,
        # based on substring in the step name, in second

        self.delay_snapshots = {
            "_dispense": 10,
            "_incubation": 0,
            "_evacuation": 0
        }

        """--------------"""

        if self.OS=="Ubuntu":
            self.root_path = "\\home\\dnascript\\Desktop\\thermal-monitor"
        elif self.OS=="Windows":
            self.root_path = "Thermal_Camera"


        self.cm = plt.get_cmap('seismic')               #Color map

        if self.camera_type=='Xi400':
            self.width = 382
            self.height = 288
        else:
            raise Exception("Camera type unknown.")


        """Initialize connection with the camera"""
        self.o = Optris()
        self.thermalFrame = None    #Contains temperature data
        self.topng = None    #the frame we'll save as png
        self.frame = None   #the frame we show on the gui
        self.thermalFrame=None
        self.thread = None
        self.mainFrame=mainFrame


        """Server to take snapshots"""
        now = datetime.datetime.now()
        self.snapshot_folder = str(now.year) + force2digits(now.month) + '\\' + str(now.year) + force2digits(
            now.month) + force2digits(now.day) + '_' + force2digits(now.hour) + force2digits(now.minute) + force2digits(
            now.second) + "_"

        if self.OS=="Ubuntu":
            self.socket_server=Pipe_Syntax("/tmp/thermal-monitor")
        else:
            self.socket_server = Pipe()
        self.socket_server.start()



        if self.is_384:
            protoTF = 305
            self.letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
        else:
            protoTF = 5
            self.letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

        db_template = pickle.load(open('db_template_proto' + str(protoTF) + '.p', "rb"))

        self.listTemplate = db_template['listTemplates']
        self.dictTemplates = db_template['dictTemplates']
        self.line_coordinates = db_template['line_coordinates']
        self.column_coordinates = db_template['column_coordinates']
        self.detection_limit = db_template['detection_limit']

        self.nb_numbers = len(self.line_coordinates)
        self.nb_letters = len(self.column_coordinates)

        # start a thread that constantly pools the video sensor for
        # the most recently read frame
        self.thread = threading.Thread(target=self.in_video_loop, daemon=True)
        self.thread.start()

    def in_video_loop(self):

        while True:
            self.thermalFrame = self.o.img()
            if self.flip_vertically:
                self.thermalFrame=np.fliplr(self.thermalFrame)
            if self.flip_horizontally:
                self.thermalFrame=np.flipud(self.thermalFrame)

            frame = self.thermalFrame
            frame = (frame - frame.min()) * (60.0 / (frame.max() - frame.min()))
            frame = Optris.C_to_uint8(self.o, frame)

            frame=self.cm(frame)
            frame = Image.fromarray((frame[:, :, :3] * 255).astype(np.uint8)).resize((int(self.width * self.zoom), int(self.height * self.zoom)))
            self.topng = frame

            if self.automatic_detection==1:
                self.mean_temperature_auto()
            elif self.automatic_detection==2:
                self.wells_temp=self.get_wells_temp_fixed_pixels()
                self.mean_temperature_fixed_pixels()
            else:
                self.img_to_display=np.array(self.topng)
            self.frame = ImageTk.PhotoImage(Image.fromarray(self.img_to_display.astype(np.uint8)))

            self.mainFrame.ImageLabel.configure(image=self.frame)
            self.mainFrame.ImageLabel.Image = self.frame

            # get coordinates of pointer

            label_size=[self.mainFrame.ImageLabel.winfo_width(),self.mainFrame.ImageLabel.winfo_height()]
            image_size=[self.frame.width(),self.frame.height()]
            x = (self.mainFrame.ImageLabel.winfo_pointerx() - int((1/2)*(label_size[0]-image_size[0])) - self.mainFrame.ImageLabel.winfo_rootx()) / self.zoom
            y = (self.mainFrame.ImageLabel.winfo_pointery() - int((1/2)*(label_size[1]-image_size[1])) - self.mainFrame.ImageLabel.winfo_rooty()) / self.zoom

            if x < self.width and x > -1:
                if y < self.height and y > -1:
                    self.mainFrame.tempLabel.configure(
                        text=str("%.1f" % self.mainFrame.thermalThread.thermalFrame[int(y)][int(x)]) + "°C")

            self.mainFrame.update()

            if self.socket_server.data!=[]:
                [to_snap,exp,cycle,step]=self.socket_server.data
                self.socket_server.received=b""
                self.socket_server.data=[]

            if int(to_snap)==1:
                self.snapshot_in_cycle(1,self.snapshot_folder + exp.replace("\"",""),int(cycle),step.replace("\"",""))

            sleep(self.delay)


    def snapshot_in_cycle(self,thermalImages,folder_path,cycle,step):

            #if thermalImages are not active, we return
            if thermalImages==0 :
                return

            # If it's just a test we dont take pictures
            #if (folder_path[len(folder_path) - 4:] == "test"):
            #    return

            #we eventually delay the capture
            for key in self.delay_snapshots:
                if key in step:
                    self.pause(self.delay_snapshots[key])
                    break
            sleep(0.3)

            now = datetime.datetime.now()

            final_path = self.root_path + "\\" + folder_path + "\\" + str(cycle) + "\\" + str(now.year) + force2digits(
                now.month) + force2digits(now.day) + '_' + force2digits(now.hour) + force2digits(now.minute) + force2digits(
                now.second) + '_C' + str(cycle) + '_' + step

            if self.OS=="Ubuntu":
                final_path=final_path.replace("\\","/")
                os.makedirs((self.root_path + "\\" + folder_path + "\\" + str(cycle)).replace("\\","/"), exist_ok=True)
                imageio.imwrite((final_path + ".png"), self.img_to_display)
            else:
                os.makedirs(self.root_path + "\\" + folder_path + "\\" + str(cycle), exist_ok=True)
                imageio.imwrite((final_path + ".png"), self.img_to_display)
            np.savetxt(final_path + ".csv", self.thermalFrame, delimiter=';', fmt='%.2f')
            #imageio.imwrite(final_path + "_detection.png", self.img_to_display)
            #imageio.imwrite(final_path+"_Temp.png", self.thermalFrame.astype(np.uint8))

            if self.automatic_detection==1:
                self.generate_temperature_table(final_path)
            elif self.automatic_detection==2:
                self.generate_temperature_table_fixed_pixel(final_path)

    def get_wells_temp_fixed_pixels(self):
        # Coordinates on image(with zoom), [x,y]

        # import config of the coordinates of the extremities, saved in a file
        if self.is_384:
            with open("fixed_thermal_config-384.json", 'r') as f:
                config = json.load(f)
        else:
            with open("fixed_thermal_config.json", 'r') as f:
                config = json.load(f)

        top_left = [config["top_left"]["X"], config["top_left"]["Y"]]
        bottom_left = [config["bottom_left"]["X"], config["bottom_left"]["Y"]]
        top_right = [config["top_right"]["X"], config["top_right"]["Y"]]
        bottom_right = [config["bottom_right"]["X"], config["bottom_right"]["Y"]]

        self.wells = return_coordinates([top_left, bottom_left, top_right, bottom_right], self.is_384) #wells are in a dictionnary, value is [coordx,coordy]
        wells_temp = {}
        for well,coord in self.wells.items():
            wells_temp[well]=self.thermalFrame[int(coord[1]/self.zoom)][int(coord[0]/self.zoom)]

        return wells_temp



    def generate_temperature_table(self, final_path):

        wells_dict = {'Temperatures': self.letters}

        input_img = np.array(self.topng)
        input_img = cv.cvtColor(input_img, cv.COLOR_BGR2GRAY)
        img_p, img_q = input_img.shape[0], input_img.shape[1]
        img_for_matching = input_img[self.detection_limit[0]:self.detection_limit[1], :]

        hits = matchTemplates(self.listTemplate,
                              img_for_matching,
                              score_threshold=0,
                              N_object=1,
                              method=cv.TM_CCOEFF_NORMED,
                              maxOverlap=0)
        dictTemplate = self.dictTemplates[hits[:1]['TemplateName'].values[0]]
        w = dictTemplate['width']
        h = dictTemplate['height']
        offset_line = dictTemplate['base_line']
        offset_column = dictTemplate['base_column']

        top_left0 = hits[:1]['BBox'].values[0][:2]
        top_left = (top_left0[0], top_left0[1] + self.detection_limit[0])

        bottom_right = (top_left[0] + w, top_left[1] + h)

        line_coordinates_shifted = self.line_coordinates + top_left[1] - offset_line
        column_coordinates_shifted = self.column_coordinates + top_left[0] - offset_column

        temperature_table = self.thermalFrame
        xl_p, xl_q = temperature_table.shape[0], temperature_table.shape[1]
        fp, fq = img_p / xl_p, img_q / xl_q

        idx = 0
        for n in range(self.nb_numbers):
            idx += 1
            wells_dict[idx] = []
            for m in range(self.nb_letters):
                x = column_coordinates_shifted[m, n]
                y = line_coordinates_shifted[n, m]
                try:
                    wells_dict[idx].append(temperature_table[int(y / fp), int(x/fq)])
                except:
                    wells_dict[idx].append(None)

        df = pd.DataFrame(wells_dict)
        df.to_excel(final_path + '_wells.xlsx', sheet_name='temp_table', index=False)

    def generate_temperature_table_fixed_pixel(self, final_path):

        temp_list=[]
        if self.is_384==0:
            nb_columns=12
            nb_rows=8
        else:
            nb_columns = 24
            nb_rows = 16

        for row in range(nb_rows+1):
            if row==0:
                temp_list.append( [""]+[col+1 for col in range(nb_columns)])
            else:
                row_list=[chr(ord("A")+row-1)]
                for col in range(1,nb_columns+1):
                    row_list.append(self.wells_temp[chr(ord("A")+row-1)+ str(col)])
                temp_list.append(row_list)

        np.savetxt(final_path + "_wells.csv", np.array(temp_list), delimiter=';', fmt="%s")

    def mean_temperature_auto(self):
        temperatures = []
        self.img_to_display = np.array(self.topng)
        img_p, img_q = self.img_to_display.shape[0], self.img_to_display.shape[1]
        input_img = cv.cvtColor(self.img_to_display, cv.COLOR_BGR2GRAY)
        img_for_matching = input_img[self.detection_limit[0]:self.detection_limit[1], :]

        hits = matchTemplates(self.listTemplate,
                              img_for_matching,
                              score_threshold=0,
                              N_object=1,
                              method=cv.TM_CCOEFF_NORMED,
                              maxOverlap=0)

        dictTemplate = self.dictTemplates[hits[:1]['TemplateName'].values[0]]
        w = dictTemplate['width']
        h = dictTemplate['height']
        offset_line = dictTemplate['base_line']
        offset_column = dictTemplate['base_column']

        top_left0 = hits[:1]['BBox'].values[0][:2]
        top_left = (top_left0[0], top_left0[1] + self.detection_limit[0])

        bottom_right = (top_left[0] + w, top_left[1] + h)

        line_coordinates_shifted = self.line_coordinates + top_left[1] - offset_line
        column_coordinates_shifted = self.column_coordinates + top_left[0] - offset_column
        xl_p, xl_q = self.thermalFrame.shape
        fp, fq = img_p / xl_p, img_q / xl_q
        # Comment the next line to avoid displaying the green rectangle around the handle
        cv.rectangle(self.img_to_display, top_left, bottom_right, (0, 255, 0), 2)
        for n in range(self.nb_numbers):
            for m in range(self.nb_letters):
                x = int(column_coordinates_shifted[m, n])
                y = int(line_coordinates_shifted[n, m])
                # Comment the next line to avoid displaying the green circles on the wells
                self.img_to_display = cv.circle(self.img_to_display, (x, y), radius=2, color=(0, 255, 0), thickness=-1)
                try:
                    temperatures.append(self.thermalFrame[int(y / fp), int(x/fq)])
                except:
                    pass
        self.mainFrame.tempmeanLabel.configure(text="Mean temperature " + "%.1f" % round(np.mean(temperatures), 2) + "°C")

    def pause(self,time_to_pause_for):

        time_to_go_to = time.time() + time_to_pause_for
        while (time.time() < time_to_go_to):
            self.mainFrame.parent.update()
            print('yeah')
            sleep(0.02)

    def mean_temperature_fixed_pixels(self):

        temperatures=[]

        self.img_to_display = np.array(self.topng)
        for well,temp in self.wells_temp.items():
            self.img_to_display = cv.circle(self.img_to_display, (self.wells[well][0], self.wells[well][1]), radius=1, color=(0, 255, 0), thickness=-1)
            temperatures.append(temp)

        self.mainFrame.tempmeanLabel.configure(text="Mean temperature " + "%.1f" % round(np.mean(temperatures), 2) + "°C")

def force2digits(number):
    if number<10:
        return '0'+str(number)
    else:
        return str(number)

def return_coordinates(extremities,is384):

    wells={}
    [top_left,bottom_left,top_right,bottom_right]=extremities
    if is384:
        col_nb=24
        row_nb=16
    else:
        col_nb=12
        row_nb=8

    for col in range(col_nb):
        for row in range(row_nb):
            well_name=chr(ord("A")+row)+ str(col+1)

            well_x = top_left[0] + (col / (col_nb - 1)) * (top_right[0] - top_left[0]) + (col / (col_nb - 1)) * (
                        row / (row_nb - 1)) * (bottom_right[0] - bottom_left[0] - top_right[0] + top_left[0]) + (
                        row / (row_nb - 1))*(bottom_left[0]-top_left[0])

            well_y = top_left[1] + (col / (col_nb - 1)) * (top_right[1] - top_left[1]) + (col / (col_nb - 1)) * (
                        row / (row_nb - 1)) * (bottom_right[1] - bottom_left[1] - top_right[1] + top_left[1]) + (
                        row / (row_nb - 1)) * (bottom_left[1]-top_left[1])

            wells[well_name]=[int(well_x),int(well_y)]

    return wells

if __name__ == '__main__':
    top_left = [5, 5]
    bottom_left = [5, 100]
    top_right = [100, 5]
    bottom_right = [100, 100]
    wells=return_coordinates([top_left,bottom_left,top_right,bottom_right],0)
    for well in wells.items():
        print(wells[well][0])



