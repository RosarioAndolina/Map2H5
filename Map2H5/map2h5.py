#!/usr/bin/env python3

from PIL import Image, ImageTk
import tkinter
from numpy import array, asarray, zeros, ones, roll, uint8, arange, savetxt, transpose, hstack
import customtkinter
from time import sleep
from matplotlib.pyplot import imshow
from XRDXRFutils import DataXRF
import tkinter as tk
from tkinter import ttk
from PyMca5.PyMcaGui.physics.xrf import McaAdvancedFit
from subprocess import Popen
import os, platform
from FastFit import FastFit

AUDIOSUPPORT = True
try:
    from ElevatorPlayer import ElevatorPlayer
except ModuleNotFoundError:
    AUDIOSUPPORT = False


class RGBFrame(customtkinter.CTkFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        self.out = None
        self.grid_columnconfigure((0,1,2,3), weight = 1)
        
        self.label = customtkinter.CTkLabel(master = self, text = "RGB")
        self.label.grid(row = 0, column = 0, padx = 3, pady = 3, sticky = "nswe")

        self.red = customtkinter.CTkOptionMenu(master = self,
                                               values = list(self.master.master.labels.keys()),
                                               command = self.set_red_channel)
        self.red.grid(row = 0, column = 1, padx = 3, pady = 3)

        self.green = customtkinter.CTkOptionMenu(master = self,
                                                 values = list(self.master.master.labels.keys()),
                                                 command = self.set_green_channel)
        self.green.grid(row = 0, column = 2, padx = 3, pady = 3)

        self.blue = customtkinter.CTkOptionMenu(master = self,
                                                 values = list(self.master.master.labels.keys()),
                                                 command = self.set_blue_channel)
        self.blue.grid(row = 0, column = 3, padx = 3, pady = 3)

    def set_red_channel(self, choice):
        print(self.out.shape)
        self.out[:,:,0] = self.master.master.norm(self.master.master.labels[choice]).astype(uint8)
        self.update_image()

    def set_green_channel(self, choice):
        self.out[:,:,1] = self.master.master.norm(self.master.master.labels[choice]).astype(uint8)
        self.update_image()

    def set_blue_channel(self, choice):
        self.out[:,:,2] = self.master.master.norm(self.master.master.labels[choice]).astype(uint8)
        self.update_image()

    def update_image(self):
        self.master.master.imarray = self.out
        self.master.master.canvas_frame = Zoom_Advanced(master = self.master.master)
        self.master.master.canvas_frame.grid(row = 1, column = 0, columnspan = 3, sticky = "nswe")
        

        


class EMaps(customtkinter.CTkFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.grid_columnconfigure((0,1), weight = 1)

        self.combobox = customtkinter.CTkOptionMenu(master = self,
                                                    values = list(self.master.labels.keys()),
                                                    command = self.showEmap)
        self.combobox.set('data')
        self.combobox.grid(row = 0, column = 0, padx = 5, pady = 3)

        self.rgbframe = RGBFrame(master = self)
        self.rgbframe.grid(row = 0, column = 1, padx = 3, pady = 3, sticky = "we")
        
    def showEmap(self, choice):
        self.master.imarray = self.master.norm(self.master.labels[choice]).astype(uint8)
        self.master.canvas_frame = Zoom_Advanced(master = self.master)
        self.master.canvas_frame.grid(row = 1, column = 0, columnspan = 3, sticky = "nswe")
        #self.master.shift_sbox.set_default()
        
        

class ExistsDialog(customtkinter.CTkToplevel):
    def __init__(self, *args, fname = None,  **kwargs):
        super().__init__(*args, **kwargs)

        self.fname = fname
        self.newfname = None
        self.grid_columnconfigure(0, weight = 1)

        self.label = customtkinter.CTkLabel(master = self, text = f"{fname}\nalready exists")
        self.label.grid(row = 0, column = 0, padx = 3, pady = 10, sticky = "nswe")

        self.btnframe = customtkinter.CTkFrame(master = self)
        self.btnframe.grid(row = 1, column = 0, padx = 3, pady = 10, sticky = "nswe")
        self.btnframe.grid_columnconfigure((0,1,2), weight = 1)

        self.overwrite_btn = customtkinter.CTkButton(master = self.btnframe, text = "overwrite", command = self.overwrite_callback)
        self.overwrite_btn.grid(row = 0, column = 0, padx = 3, pady = 3)

        self.change_btn = customtkinter.CTkButton(master=self.btnframe, text = "change", command = self.change_callback)
        self.change_btn.grid(row = 0, column = 1, padx = 3, pady = 3)

        self.abort_btn = customtkinter.CTkButton(master = self.btnframe, text = "abort", command = lambda: self.destroy())
        self.abort_btn.grid(row =0 , column = 2, padx = 3, pady = 3)

    def overwrite_callback(self):
        os.remove(self.fname)
        pathname, extension = os.path.splitext(self.fname)
        self.newfname = os.path.basename(pathname)
        self.destroy()

    def change_callback(self):
        newfname = customtkinter.filedialog.asksaveasfilename(title = "New Root filename",
                                                          initialdir = os.path.dirname(self.fname),
                                                          filetypes = [("HDF5", "*.h5"),("all", "*")])
        if newfname:
            pathname, extension = os.path.splitext(newfname)
            self.newfname = os.path.basename(pathname)

        self.destroy()

    def get(self):
        return self.newfname

class SaveOptions(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.geometry("300x200")
        self.title("Save Options")
        self.label = customtkinter.CTkLabel(master = self, text = "Select save options")
        self.label.grid(row = 0, column = 0, sticky = "we")

        self.combobox = customtkinter.CTkOptionMenu(master = self,
                                                    values = ['Data', 'E-maps','Both'],
                                                    command = self.save_options)
        self.combobox.set('Data')
        self.combobox.grid(row = 1, column = 0)

        self.grid_columnconfigure(0, weight = 1)

    def save_options(self, choice):
        if choice == "Data" and hasattr(self.master, "data"):
            path = customtkinter.filedialog.asksaveasfilename()
            message = MessageFrame(text = "Saving...")
            message.update()
            self.master.data.save_h5(path)
            message.destroy()
        elif choice == "E-maps":
            print("not implemented yet")

        elif choice == "Both":
            print("not implemented yet")

        self.destroy()


class FitOptions(customtkinter.CTkToplevel):
    def __init__(self, *args, sumspectrum_path = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.sumspectrum_path = sumspectrum_path
        self.geometry("300x200")
        self.title("Fit Options")
        self.label = customtkinter.CTkLabel(master = self, text = "Select fit options")
        self.label.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = "nswe")

        self.combobox = customtkinter.CTkOptionMenu(master = self,
                                                    values = ['configure', 'fast-fit'],
                                                    command = self.fit_options)
        self.combobox.set('configure')
        self.combobox.grid(row = 1, column = 0, padx = 10, pady = 10)
        
        self.grid_columnconfigure(0, weight = 1)
    
    def PyMcaAdvFit(self):
        if self.sumspectrum_path:
            command = ['python3', 'PyMcaAdvFit.py', f'{self.sumspectrum_path}']
            p = Popen(command)
            p.wait()

    def fit_options(self, choice):
        if choice == "configure" and hasattr(self.master, "data"):
            self.PyMcaAdvFit()
        elif choice == "fast-fit":
            cfg = customtkinter.filedialog.askopenfilename(title = "Open config file",
                                                           initialdir = os.getcwd(),
                                                           filetypes = [("CFG", "*.cfg"), ("ALL", "*")])
            outputdir = os.getcwd()
            print("Fitting data...")
            print("outputdir", outputdir)
            print(self.master.data.shape)
            self.master.shift_data(n = self.master.shift_value)
            self.ffit = FastFit(data = self.master.data.data, cfgfile = cfg, outputdir = outputdir)
            print(self.ffit.filename)
            print(self.master.data.shape)
            if os.path.exists(self.ffit.filename):
                dialog = ExistsDialog(fname = self.ffit.filename)
                dialog.update()
                self.wait_window(dialog)
                newfname = dialog.get()
                if newfname:
                    self.ffit.outputRoot = newfname
                else:
                    self.ffit.outputdir = None
                dialog.destroy()
            if self.master.elevator: self.master.player = ElevatorPlayer(0, "player0", 'elevator-music.wav') 
            message = MessageFrame(text = "Fitting...", elevator = self.master.elevator)
            message.update()
            message.focus()
            message.play(lambda: self.master.player.start())
            self.ffit.fit()
            #setattr(self.master, "parameters", self.ffit.get_calibration_pars())
            #setattr(self.master, "labels", self.ffit.get_labels())
            message.stop(lambda: self.master.player.stop())
            message.destroy()
        
        self.destroy()
    
    def get_parameters(self):
        if hasattr(self, "ffit"):
            par = self.ffit.get_calibration_pars()
            if par:
                return par 

    def get_labels(self):
        if hasattr(self, "ffit"):
            labels = self.ffit.get_labels()
            if labels:
                return labels

class MessageFrame(customtkinter.CTkToplevel):
    def __init__(self, *args, text, elevator = False, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.geometry("200x100")
        self.title("")
        self.elevator = elevator
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        
        self.label = customtkinter.CTkLabel(self, text = text)
        self.label.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "nswe")

        self.label.grid(row = 0, column =0, sticky = "nsew")

        
    def play(self, callback = None):
        if self.elevator:
            callback()


    def stop(self, callback = None):
        if self.elevator:
            callback()


class IntSpinbox(customtkinter.CTkFrame):
    def __init__(self, *args,
                 width: int = 100,
                 height: int = 32,
                 step_size: int = 1,
                 command = None,
                 **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)

        self.step_size = step_size
        self.command = command

        self.configure(fg_color=("gray78", "gray28"))  # set frame color

        self.grid_columnconfigure((0, 2), weight=0)  # buttons don't expand
        self.grid_columnconfigure(1, weight=1)  # entry expands

        self.subtract_button = customtkinter.CTkButton(self, text="-", width=height-6, height=height-6,
                                                       command=self.subtract_button_callback)
        self.subtract_button.grid(row=0, column=0, padx=(3, 0), pady=3)

        self.entry = customtkinter.CTkEntry(self, width=width-(2*height), height=height-6, border_width=0)
        self.entry.grid(row=0, column=1, columnspan=1, padx=3, pady=3, sticky="ew")

        self.add_button = customtkinter.CTkButton(self, text="+", width=height-6, height=height-6,
                                                  command=self.add_button_callback)
        self.add_button.grid(row=0, column=2, padx=(0, 3), pady=3)

        self.set_default()

    def set_default(self):        # default value
        self.entry.delete(0, "end")
        self.entry.insert(0, "0")
        self.shift = 0

    def add_button_callback(self):
        try:
            value = int(self.entry.get()) + self.step_size
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
        except ValueError:
            return
        if self.command is not None:
            self.command(1)

    def subtract_button_callback(self):
        try:
            value = int(self.entry.get()) - self.step_size
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
        except ValueError:
            return
        if self.command is not None:
            self.command(-1)

    def get(self) -> int:
        try:
            return int(self.entry.get())
        except ValueError:
            return None

    def set(self, value: int):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(int(value)))

class AutoScrollbar(customtkinter.CTkScrollbar):
    ''' A scrollbar that hides itself if it's not needed.
        Works only if you use the grid geometry manager '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            customtkinter.CTkScrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with this widget')

    def place(self, **kw):
        raise tk.TclError('Cannot use place with this widget')

class Zoom_Advanced(customtkinter.CTkFrame):
    ''' Advanced zoom of the image '''
    def __init__(self, *args, **kwargs):
        ''' Initialize the main Frame '''
        super().__init__(*args, **kwargs)
        #self.master.title('Zoom with mouse wheel')
        # Vertical and horizontal scrollbars for canvas
        vbar = AutoScrollbar(master = self, orientation='vertical')
        hbar = AutoScrollbar(master = self, orientation='horizontal')
        vbar.grid(row=0, column=1, sticky='ns')
        hbar.grid(row=1, column=0, sticky='we')
        # Create canvas and put image on it
        self.canvas = tk.Canvas(self, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        vbar.configure(command=self.scroll_y)  # bind scrollbars to the canvas
        hbar.configure(command=self.scroll_x)
        # Make the canvas expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.move_from)
        self.canvas.bind('<B1-Motion>',     self.move_to)
        self.canvas.bind('<MouseWheel>', self.wheel)  # with Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self.wheel)  # only with Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self.wheel)  # only with Linux, wheel scroll up
        self.imarr = self.master.imarray  # open image
        self.image = Image.fromarray(self.imarr)
        self.width, self.height = self.image.size
        self.imscale = 1.0  # scale for the canvaas image
        self.delta = 1.1  # zoom magnitude
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        self.show_image()

    def scroll_y(self, *args, **kwargs):
        ''' Scroll canvas vertically and redraw the image '''
        self.canvas.yview(*args, **kwargs)  # scroll vertically
        self.show_image()  # redraw the image

    def scroll_x(self, *args, **kwargs):
        ''' Scroll canvas horizontally and redraw the image '''
        self.canvas.xview(*args, **kwargs)  # scroll horizontally
        self.show_image()  # redraw the image

    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.show_image()  # redraw the image

    def wheel(self, event):
        ''' Zoom with mouse wheel '''
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        bbox = self.canvas.bbox(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
        else: return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down
            i = min(self.width, self.height)
            if int(i * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.delta
            scale        /= self.delta
        if event.num == 4 or event.delta == 120:  # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.delta
            scale        *= self.delta
        self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.show_image()

    def show_image(self, event=None):
        ''' Show image on the Canvas '''
        self.image = Image.fromarray(self.imarr)
        bbox1 = self.canvas.bbox(self.container)  # get image area
        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
        bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                 self.canvas.canvasy(0),
                 self.canvas.canvasx(self.canvas.winfo_width()),
                 self.canvas.canvasy(self.canvas.winfo_height()))
        bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),  # get scroll region box
                max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3])]
        if bbox[0] == bbox2[0] and bbox[2] == bbox2[2]:  # whole image in the visible area
            bbox[0] = bbox1[0]
            bbox[2] = bbox1[2]
        if bbox[1] == bbox2[1] and bbox[3] == bbox2[3]:  # whole image in the visible area
            bbox[1] = bbox1[1]
            bbox[3] = bbox1[3]
        self.canvas.configure(scrollregion=bbox)  # set scroll region
        x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(bbox2[1] - bbox1[1], 0)
        x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
        y2 = min(bbox2[3], bbox1[3]) - bbox1[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            x = min(int(x2 / self.imscale), self.width)   # sometimes it is larger on 1 pixel...
            y = min(int(y2 / self.imscale), self.height)  # ...and sometimes not
            image = self.image.crop((int(x1 / self.imscale), int(y1 / self.imscale), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1)), Image.Resampling.NEAREST))
            imageid = self.canvas.create_image(max(bbox2[0], bbox1[0]), max(bbox2[1], bbox1[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

class App(customtkinter.CTk):
    def __init__(self, *args, path = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        customtkinter.set_appearance_mode('dark')       
        customtkinter.set_default_color_theme('dark-blue')
        
        self.geometry('800x500')
        self.title("MyApp")
        self.shift_value = 0

        self.elevator = False
        self.labels = {}
        
        self.grid_rowconfigure(1, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        
        self.menubar = customtkinter.CTkFrame(master = self)
        self.menubar.grid_columnconfigure((0,1,2,3,4), weight = 1)
        self.menubar.grid(row = 0, column = 0, padx = 3, pady = 3, sticky = "we")
        
        self.read_button = customtkinter.CTkButton(master = self.menubar, text = "Read", command = self.read_callback)
        self.read_button.grid(row = 0, column = 0, padx = 3, pady = 3)

        self.add_button = customtkinter.CTkButton(master = self.menubar, text = "Add", command = self.add_callback)
        self.add_button.grid(row = 0, column = 1, padx = 3, pady = 3)
        
        self.shift_sbox = IntSpinbox(master = self.menubar, command=self.shift_callback)
        self.shift_sbox.grid(row = 0, column = 2, padx = 3, pady = 3)
        
        self.fit_button = customtkinter.CTkButton(master = self.menubar, text = "PyMcaFit", command = self.fit_callback)
        self.fit_button.grid(row = 0, column  = 3, padx = 3, pady = 3)
        
        self.save_button = customtkinter.CTkButton(master = self.menubar, text = "Save", command = self.save_callback)
        self.save_button.grid(row = 0, column = 4, padx = 3, pady = 3)

        if not hasattr(self, "canvas_frame"):
            self.canvas_frame = None

        self.norm = lambda x: x/x.max()*255
        self.bind("<Destroy>", self.on_destroy)
        self.bind("<Control-Key-m>", self.on_ctrlM)

        self.emapsmenu = EMaps(master = self)
        #self.emapsmenu.hidden = 1


    def shift_data(self,n,method = 'even'):
    
        def pad(x,n):
            n = abs(n)
            x = hstack((zeros((x.shape[0],n,x.shape[2])), x, zeros((x.shape[0],n,x.shape[2]))))
            return x
        
        x = pad(self.data.data,n)
        if method == 'both':
            x[::2] = roll(x[::2], n, axis = 1)
            x[1::2] = roll(x[1::2], -n, axis = 1)
        elif method == 'even':
            x[::2] = roll(x[::2], n, axis = 1)
        elif method == 'odd':
            x[1::2] = roll(x[1::2], -n, axis = 1)

        self.data.data = x
        self.shift_value = 0

    def read_callback(self):
        self.path = customtkinter.filedialog.askdirectory()
        if self.path:
            if self.elevator: self.player = ElevatorPlayer(0, "player0", 'elevator-music.wav')
            self.message = MessageFrame(text = "Reading...", elevator = self.elevator)
            self.message.play(lambda: self.player.start())
            self.message.update()
            self.data = DataXRF().read_from_map(self.path)
            self.message.stop(lambda: self.player.stop())
            self.message.destroy()
            self.imarray = self.norm(self.data.data.sum(2)).astype(uint8)
            self.labels = {"data" : self.imarray}
            self.emapsmenu.combobox.configure(values = list(self.labels.keys()))
            if platform.system().startswith('Linux'):
                self.sumspectrum_path = f"/tmp/{os.path.basename(self.path)}_my_app.tmp"
            elif platform.system().startswith('Windows'):
                self.sumspectrum_path = f"C:/Users/AppData/Local/Temp/{os.path.basename(self.path)}_my_app.tmp"
            data = self.data.data.sum(0).sum(0)
            npixel = self.data.shape[0]*self.data.shape[1]
            savetxt(self.sumspectrum_path, transpose([arange(self.data.shape[2]),data/npixel]))
            #if self.canvas_frame:
            #    self.canvas_frame.destroy()
            #    self.canvas_frame = None
            self.canvas_frame = Zoom_Advanced(master = self)
            self.canvas_frame.grid(row = 1, column = 0, columnspan = 3, sticky = "nswe")
            self.shift_sbox.set_default()
        
    def add_callback(self):
        if not hasattr(self,"data"):
            return
        path = customtkinter.filedialog.askdirectory()
        if path:
            self.message = MessageFrame(text = "Reading...")
            self.message.update()
            data = DataXRF().read_from_map(path)
            self.message.destroy()
            self.data.data = self.data.data.copy() + data.data
            self.imarray = self.norm(self.data.data.sum(2)).astype(uint8)
            if os.name == "posix":
                self.sumspectrum_path = f"/tmp/{os.path.basename(self.path)}_my_app.tmp"
            else:
                self.sumspectrum_path = f"C:/Users/AppData/Local/Temp/{os.path.basename(self.path)}_my_app.tmp"
            data = self.data.data.sum(0).sum(0)
            npixel = self.data.shape[0]*self.data.shape[1]
            savetxt(self.sumspectrum_path, transpose([arange(self.data.shape[2]),data/npixel]))
            self.canvas_frame = Zoom_Advanced(master = self)
            self.canvas_frame.grid(row = 1, column = 0, columnspan = 3, sticky = "nswe")
            self.shift_sbox.set_default()

            
    
    def save_callback(self):
        selection = SaveOptions()

    def fit_callback(self):
        if hasattr(self, "sumspectrum_path"):
            fitopt = FitOptions(sumspectrum_path = self.sumspectrum_path)
            self.wait_window(fitopt)
            self.parameters = fitopt.get_parameters()
            self.labels = fitopt.get_labels()
            self.shift_sbox.set_default()
            print("parameters", self.parameters)
            print(type(self.labels))
            self.emapsmenu.combobox.configure(values = ["data"]+list(self.labels.keys()))
            self.emapsmenu.rgbframe.out = zeros((self.data.shape[0], self.data.shape[1], 3)).astype(uint8)
            for attr in ['red', 'green', 'blue']:
                getattr(self.emapsmenu.rgbframe, attr).configure(values = list(self.labels.keys()))
            self.labels['data'] = self.imarray
            self.emapsmenu.grid(row = 2, column = 0, padx = 3, pady = 3, sticky = "we")
            self.emapsmenu.showEmap("data")

            

    def shift_callback(self, value):
        if hasattr(self, "imarray") and type(self.imarray) != type(None):
            self.imarray[::2] = roll(self.imarray.copy()[::2], value, axis=1)
            self.shift_value += value
            self.canvas_frame.show_image()

    def on_destroy(self, event):
        if event.widget == self:
            if hasattr(self, "sumspectrum_path"):
                os.remove(self.sumspectrum_path)

    def on_ctrlM(self, event):
        self.elevator = AUDIOSUPPORT and (not self.elevator)
        if not self.elevator:
            if hasattr(self, "player") and self.player.is_playing():
                self.player.stop()

if __name__ == "__main__":
    root = App()
    #app = Zoom_Advanced(root, path=path)
    root.mainloop()
