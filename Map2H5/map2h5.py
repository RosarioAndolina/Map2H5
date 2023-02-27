import customtkinter
from XRDXRFutils import SyntheticDataXRF
from time import sleep

#class InfoBoxFrame(customtkinter.CTkFrame):
#    def __init__(self, *args, command = None, **kwargs):
#        super().__init__(*args, **kwargs)
#
#        self.grid_rowconfigure(1, weight = 1)
#        self.grid_columnconfigure(1, weight = 1)        

        

class InfoBox(customtkinter.CTkFrame):
    def __init__(self, *args, command = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)

        self.infobox = customtkinter.CTkTextbox(master = self)
        self.infobox.grid(row = 1, column = 0, padx = 10, pady = 5, sticky = "snew", rowspan = 2)

        self.start_button = customtkinter.CTkButton(master = self, text = "Start", command = command)
        self.start_button.grid(row = 0, column = 1, padx = 10, pady = 10)
       
        #self.infobox_frame = customtkinter.CTkFrame(master = self)
        #self.infobox_frame.grid(row = 1, column = 1, padx = 0, pady = 0, sticky = "snew")
  
    def insert(self, text):
        self.infobox.insert("insert", text + "\n")

class EntryButton(customtkinter.CTkFrame):
    def __init__(self, *args, text_entry = None, text_button = None, command = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.text_entry = text_entry
        self.text_button = text_button
        self.command = command

        self.configure(fg_color = ('gray20'))
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight = 0)

        self.entry = customtkinter.CTkEntry(master = self, placeholder_text = self.text_entry, border_width = 1)
        self.entry.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = "ew")

        self.button = customtkinter.CTkButton(master = self, text = self.text_button, command = self.button_callback)
        self.button.grid(row = 0, column = 1, padx = (0,10), pady = 10)


    def button_callback(self):
        if self.command:
            self.commandout = self.command()
            self.set(self.commandout)

    def get(self):
        return self.entry.get()

    def set(self, text):
        self.entry.delete(0, "end")
        self.entry.insert(0, text)

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Map to HDF5")
        
        self.data = None

        customtkinter.set_appearance_mode('dark')       
        customtkinter.set_default_color_theme('dark-blue')
        self.geometry("1020x400")
        self.minsize(400, 200)

        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(3, weight = 1)
 
        self.label = customtkinter.CTkLabel(master = self, text = "Select .map files directory and generate an H5 file")
        self.label.grid(row = 0, column = 0, padx = 10, pady = 3)
        
        self.dir_entry = EntryButton(master = self, text_entry = "directory path", text_button = "Browse", command = self.dir_entry_callback)
        self.dir_entry.grid(row = 1, column = 0, padx = 10, pady = 5, sticky = "ew")

        self.h5out = EntryButton(master = self, text_entry = "HDF5 output file name", text_button = "Browse", command = self.h5out_callback)
        self.h5out.grid(row = 2, column = 0, padx = 10, pady = 5, sticky = "ew")

        self.infobox = InfoBox(master = self, command = self.infobox_callback, height = 50)
        self.infobox.grid(row = 3, column = 0, padx = 10, pady = 5, sticky = "nsew")

    def dir_entry_callback(self):
        return customtkinter.filedialog.askdirectory()

    def h5out_callback(self):
        return customtkinter.filedialog.asksaveasfilename(filetypes = [("HDF5","*.h5")])

    def infobox_callback(self):
        self.datadir = self.dir_entry.get()
        if self.datadir: 
            self.infobox.insert(f"reading: {self.datadir}")
            self.data = SyntheticDataXRF().read(self.datadir)
            self.outfile = self.h5out.get()
            self.infobox.insert(f"saving: {self.outfile}")
            self.data.save_h5(self.outfile)
            self.infobox.insert("Done!")

if __name__ == "__main__":
    app = App()
    app.mainloop()
