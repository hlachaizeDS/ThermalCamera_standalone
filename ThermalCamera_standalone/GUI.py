# On importe Tkinter
from tkinter import *
from Thermal import ThermalImageThread
from PIL import Image, ImageTk
from socket_server import *
import numpy as np


"""Parameters"""
IS_384=0
CAMERA_TYPE="Xi400"
AUTOMATIC_DETECTION=2 # 0 for no detection, 1 for image processing, 2 for fixed pixels
OS="Ubuntu" #Ubuntu or Windows
IMAGE_FLIP_VERTICALLY=1 #mirror through vertical axis
IMAGE_FLIP_HORIZONTALLY=0 #mirror through horizontal axis

"""
Put the right calibration files in calibration_files folder.

"""

class MainFrame(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.thermalThread = ThermalImageThread(self, CAMERA_TYPE, IS_384, AUTOMATIC_DETECTION, OS, IMAGE_FLIP_VERTICALLY, IMAGE_FLIP_HORIZONTALLY)

        initimg=np.zeros([100,100,3],dtype=np.uint8)
        raw_img=Image.fromarray(initimg)
        img=ImageTk.PhotoImage(raw_img,master=parent)



        self.ImageLabel=Label(self,height=self.thermalThread.height * self.thermalThread.zoom,
                              width=self.thermalThread.width * self.thermalThread.zoom,
                              image=img)

        self.ImageLabel.pack()
        self.ImageLabel.Image=img


        self.tempLabel=Label(self,text="",width=40)
        self.tempLabel.pack(side="bottom",fill="x")
        self.tempmeanLabel=Label(self,text="",width=40)
        self.tempmeanLabel.pack(side="bottom",fill="x")

        #Binding to get temperatures live
        self.ImageLabel.bind("<Enter>",self.on_enter)
        self.ImageLabel.bind("<Leave>",self.on_leave)

    def on_enter(self, event):
            self.tempLabel.configure(text="Place cursor on image.")

    def on_leave(self, event):
            self.tempLabel.configure(text="")





if __name__ == "__main__":
    # On crée la racine de notre interface
    root = Tk()
    root.title("Thermal Camera")
    MainFrame(root).pack()
    root.mainloop()
