
from tkinter import *
from Thermal import ThermalImageThread
from PIL import Image, ImageTk
from socket_server import *
import numpy as np


class MainFrame(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.thermalThread = ThermalImageThread(self)

        initimg=np.zeros([100,100,3],dtype=np.uint8)
        raw_img=Image.fromarray(initimg)
        img=ImageTk.PhotoImage(raw_img,master=parent)



        self.ImageLabel=Label(self,height=self.thermalThread.height * self.thermalThread.zoom,
                              width=self.thermalThread.width * self.thermalThread.zoom,
                              image=img)

        self.ImageLabel.grid(row=1,column=1,columnspan=4)
        self.ImageLabel.Image=img


        self.tempLabel=Label(self,text="",width=40)
        self.tempLabel.grid(row=2,column=1,columnspan=4)
        self.tempmeanLabel=Label(self,text="",width=40)
        self.tempmeanLabel.grid(row=3,column=1,columnspan=4)

        #Binding to get temperatures live
        self.ImageLabel.bind("<Enter>",self.on_enter)
        self.ImageLabel.bind("<Leave>",self.on_leave)

        #-------------Snapshot feature
        #Snapshot folder
        Label(self,height=1).grid(row=4)
        self.snapshotFolder_label=Label(self,text="Snapshot folder")
        self.snapshotFolder_label.grid(row=5,column=2, sticky='e')
        self.snapshotFolder_str=StringVar()
        self.snapshotFolder=Entry(self,textvariable=self.snapshotFolder_str)
        self.snapshotFolder.grid(row=5,column=3)
        #Snapshot name
        self.snapshotName_label = Label(self, text="Snapshot name")
        self.snapshotName_label.grid(row=6, column=2, sticky='e')
        self.snapshotName_str = StringVar()
        self.snapshotName = Entry(self, textvariable=self.snapshotName_str)
        self.snapshotName.grid(row=6, column=3)
        #Snapshot Button
        self.snapshot_button=Button(self,text="Snap",command=lambda:self.thermalThread.snapshot_in_cycle(1,self.snapshotFolder_str.get(),"",self.snapshotName_str.get()))
        self.snapshot_button.grid(row=5,column=4,rowspan=2,sticky='w')

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
