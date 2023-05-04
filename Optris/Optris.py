import numpy as np
import imageio
from pathlib import Path
from Optris.libirimager import *
import time
import logging

class Optris:
    INITTIME = 1

    """
    Barebones Optris image getter
    """
    def __init__(self):
        """
        Initialize USB, etc.
        """
        evo_irimager_usb_init()
        #evo_irimager_set_focusmotor_pos(68)
        self.size = evo_irimager_get_thermal_image_size()
        self._inittime = time.time()
        return

    def img(self) -> np.ndarray:
        """
        Get an image from the camera in Celcius form
        :return:
        """
        # Camera will return garbage frames for a few seconds after init.
        # Make sure we've waited 5 seconds before getting the first image
        if self._inittime:
            dt = time.time() - self._inittime
            if dt < self.INITTIME:
                logging.warning("Waiting for optris spinup")
                time.sleep(self.INITTIME - dt)
            self._inittime = None

        ret = evo_irimager_get_thermal_image(*self.size)
        return raw_to_C(ret)

    def C_to_uint8(self, img: np.ndarray) -> np.ndarray:
        """
        Convert a float numpy array to an 8bit array suitable for png saving.
        Each png count is .25 degrees, ranging from 20C -> 70C
        :param img:
        :return:
        """
        img.clip(20.0, 70.0)
        return (img/0.25).astype(np.uint8)

    def save_png(self, img: np.ndarray, fname: Path):
        """
        Save the given file to a png
        :param img:
        :param fname:
        :return:
        """
        imageio.imwrite(str(fname), self.C_to_uint8(img))
        return

    def display(self, img=None):
        """
        Show the provided img
        :param img:
        :return:
        """
        import matplotlib.pyplot as plt
        if img is None: img = self.img()
        plt.imshow(img)
        plt.show()
        return
