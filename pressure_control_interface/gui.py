from collections import deque
from re import L
import tkinter as tk
import tkinter.ttk as ttk
from ttkthemes import ThemedTk
import tkinter.filedialog as fdialog
import os
import sys
import copy
import time
from serial.tools import list_ports
import serial
#import matplotlib.pyplot as plt
import seaborn as sns
import threading

from ctrlp import CommHandler
from ctrlp import ConfigHandler
from ctrlp.get_files import get_save_path, load_yaml, save_yaml


def _from_rgb(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    rgb_int = [0]*3
    for i, color in enumerate(rgb):
        rgb_int[i] = int(color*255)
    return "#%02x%02x%02x" % tuple(rgb_int)



class Spinbox(ttk.Entry):

    def __init__(self, master=None, **kw):

        ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)
    def set(self, value):
        self.tk.call(self._w, "set", value)


class CommConfig(object):
    def __init__(self,master, hw_path, hw_options):
        self.default_option = "< Choose >"

        hw_options_cp = copy.deepcopy(hw_options)

        self.hw_path=hw_path
        hw_options_cp.insert(0,self.default_option)
        self.num_devices=0
        
        top=self.top=tk.Toplevel(master)
        top.title('Serial Config')
        top.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.fr = tk.Frame(top, bd=2)
        self.fr.pack()
        self.hwvar = tk.StringVar()
        self.l=tk.Label(self.fr, text='Hardware Profile:', width=30)
        self.l.grid(row=0, column=0, sticky='ew', pady=5, padx=10)

        self.e1=ttk.OptionMenu(self.fr, self.hwvar, hw_options_cp[0], *hw_options_cp, command=self.update_hw_config)
        self.e1.grid(row=1, column=0, sticky='ew', pady=5, padx=10)
        
        self.update_port_switchers()

        self.ok_btn=ttk.Button(self.fr,text='Ok',command=self.cleanup, width=30)
        self.ok_btn.grid(row=99, column=0, sticky='ew', pady=5, padx=10)
        self.ok_btn.configure(state='disabled')

    def get_ports(self):
        ports = list(list_ports.comports())
        comports = []
        comport_names = []
        for p in ports:
            comports.append(p.device)
            comport_names.append(p)
        comports.insert(0,self.default_option)
        comport_names.insert(0,self.default_option)
        return comports, comport_names

    def update_port_list(self, event):
        comports, _ = self.get_ports()

        for i, switcher in enumerate(self.port_switchers):
            switcher["menu"].delete(0, "end")
            for port in comports:
                switcher["menu"].add_command(label=port, 
                             command=lambda value=port, i=i: self.comvar[i].set(value))
            

    def update_hw_config(self, val):
        hw_profile=self.hwvar.get()
        if hw_profile != self.default_option:
            path = os.path.join(self.hw_path,hw_profile)
            serial_settings = load_yaml(path)
            self.num_devices=len(serial_settings)
        else:
            self.num_devices=0
        self.update_port_switchers()


    def del_port_switchers(self):
        try:
            self.l2.destroy()
            self.l3.destroy()
            self.fr_port.destroy()
        except:
            pass

    def validate_comports(self):
        if len(self.comvar)==0:
            self.ok_btn.configure(state='disabled')

        else:
            for var in self.comvar:
                if var.get() == self.default_option:
                    self.ok_btn.configure(state='disabled')
                    return

            self.ok_btn.configure(state='normal')



    def update_port_switchers(self):
        self.del_port_switchers()
        self.port_switchers=[]
        self.comvar = []
        if self.num_devices>0:
            self.l2=tk.Label(self.fr, text='', width=30)
            self.l2.grid(row=2, column=0, sticky='ew', pady=5, padx=10)
            self.l3=tk.Label(self.fr, text='Serial Devices:', width=30)
            self.l3.grid(row=3, column=0, sticky='ew', pady=5, padx=10)
            self.fr_port = tk.Frame(self.fr, bd=2)
            self.fr_port.grid(row=4, column=0, sticky='ew', pady=5, padx=10)

            for i in range(self.num_devices):
                var = tk.StringVar()
                cb = lambda name, index, val: self.validate_comports()
                var.trace("w",cb)
                self.comvar.append(var)
                p1=ttk.OptionMenu(self.fr_port, var, self.default_option, *[self.default_option])
                p1.grid(row=0, column=i, sticky='ns', pady=5, padx=10)
                p1.bind("<Enter>", self.update_port_list)
                self.port_switchers.append(p1)
            
            self.update_port_list(None)

    def cleanup(self):
        comports = [self.comvar[i].get() for i in range(len(self.comvar))]
        self.comports=[]
        for comport in comports:
            if comport == self.default_option:
                self.comports=None
                break
            else:
                self.comports.append(comport)

        hw_profile = self.hwvar.get()
        if hw_profile == self.default_option:
            hw_profile = None
        self.hw_profile = hw_profile
        
        self.top.destroy()


class PressureControlGui:
    def __init__(self):
        self.config = None
        self.pressures = None
        self.comm_handler = None
        self.read_thread = None
        self.send_thread = None
        self.command_history = deque([])
        self.command_history_idx = 0
        self.scroll_command_history = False
        self.feedback_idx=0
        # Get the desired save path from save_paths.yaml
        self.traj_folder = get_save_path(which='traj_built')
        self.config_folder = get_save_path(which='config')
        self.data_base= get_save_path(which='preferred')
        self.curr_flag_file = os.path.join(self.traj_folder,"last_sent.txt")

        self.load_settings()
        self.curr_config_file={'basename':None, 'dirname': os.path.join(self.config_folder, 'control')}



    def connect_to_controller(self, hw_profile=None, devices=None):
        if self.comm_handler is not None:
            self.run_read_thread = False
            self.comm_handler.shutdown()
            del self.comm_handler

        self.comm_handler = CommHandler()
        if hw_profile is None or devices is None:
            self.comm_handler.read_serial_settings()
        else:
            self.comm_handler.set_serial_settings(hw_profile=hw_profile,devices=devices)
        self.comm_handler.initialize()
        self.config_handler = ConfigHandler(self.comm_handler.command_handler)
        #self.load_config_file()
        self.channel_types=[]
        for i in range(len(self.comm_handler.serial_settings)):
            num_channels = self.comm_handler.serial_settings[i]['num_channels']
            self.channel_types.extend([self.comm_handler.serial_settings[i]['type']]*num_channels)
        time.sleep(2.0)
        
        self.run_read_thread = True
        self.read_thread = threading.Thread(target=self.read_data)
        self.read_thread.start()

        self.init_control_editor()

        #self.comm_handler.send_command("echo",1)
        #self.comm_handler.send_command("speed",200)
        #self.comm_handler.send_command("cont",1)
        #self.comm_handler.send_command("echo",0)
        #self.comm_handler.send_command("off",None)
        return True


    def start_pressure_thread(self):
        if self.send_thread is None:
            self.run_read_thread = True
            self.send_thread = threading.Thread(target=self.set_pressure_threaded)
            self.send_thread.start()






    def load_settings(self, filename="default.yaml"):
        self.settings = load_yaml(os.path.join(self.config_folder,'gui',filename))

        self.hw_path = os.path.join(self.config_folder,'hardware')
        self.hw_options = [f for f in os.listdir(self.hw_path) if os.path.isfile(os.path.join(self.hw_path, f))]

        self.file_types = self.settings['file_types']
        self.color_scheme = self.settings['color_scheme']

    def get_config(self, filename):
        try:
            config = load_yaml(filename)
            if isinstance(config, dict):
                if config.get('channels'):
                    basename = os.path.basename(filename)
                    self.status_bar.config(text = 'New config "%s" loaded'%(basename))
                    return config
                else:
                    self.status_bar.config(text ='Incorrect config format')
                    return False
            else:
                self.status_bar.config(text ='Incorrect config format')
                return False
            
        except:
            self.status_bar.config(text ='New config was not loaded')
            return False


    def parse_config(self, config):
        self.num_channels = config.get("channels", {}).get('num_channels', None)
        self.curr_pressures = [0.0]*self.num_channels
        self.config=self.config_handler.parse_config(config)


    def send_config(self):
        self.status_bar.config(text ='Sending config...')
        commands = self.config_handler.get_commands()
        for command in commands:
            print(command) 
            if self.comm_handler:
                self.comm_handler.send_command(command['cmd'],command['args'])
                time.sleep(0.1)

        self.comm_handler.send_command('save',None) 
        self.status_bar.config(text ='Sent config!')


    def open_config_file(self):
        filepath = fdialog.askopenfilename(
            filetypes=self.file_types,
            initialdir=self.curr_config_file['dirname'],
            initialfile=self.curr_config_file['basename']
        )
        if not filepath:
            return
        self.curr_config_file['basename'] = os.path.basename(filepath)
        self.curr_config_file['dirname'] = os.path.dirname(filepath)
        self.load_config_file()

    def load_config_file(self):
        """Open a file for editing."""
        if self.curr_config_file['dirname'] is None or self.curr_config_file['basename'] is None:
            return

        filepath = os.path.join(
            self.curr_config_file['dirname'],
            self.curr_config_file['basename']
            )
        
        new_config = False
        if filepath.endswith(".yaml"):
            new_config = self.get_config(filepath)
        if new_config:
            self.parse_config(new_config)
            basename = os.path.basename(filepath)
            self.curr_config_file['basename'] = basename
            self.curr_config_file['dirname'] = os.path.dirname(filepath)
            ##self.init_control_sender()
            #self.init_pressure_editor()
            self.txt_edit.delete("1.0", tk.END)
            with open(filepath, "r") as input_file:
                text = input_file.read()
                self.txt_edit.insert(tk.END, text)
            self.root.title(f"Pressure Control Interface | Config Editor - {basename}")

            self.init_pressure_editor()
            self.config_btns['save']['state']='normal'
            self.config_btns['saveas']['state']='normal'
            self.config_btns['send']['state']='normal'

            #self.open_sliders_btn.configure(state="normal")
        else:
            #self.open_sliders_btn.configure(state="disabled")
            self.del_control_sender()


    def save_config_file_as(self):
        filepath = fdialog.asksaveasfilename(
            defaultextension="txt",
            filetypes=self.file_types,
            initialdir=self.curr_config_file['dirname'],
            initialfile=self.curr_config_file['basename']
        )
        if not filepath:
            return

        self.curr_config_file['basename'] = os.path.basename(filepath)
        self.curr_config_file['dirname'] = os.path.dirname(filepath)

    def save_config_file(self):
        """Save the current file as a new file."""
        filepath = os.path.join(
            self.curr_config_file['dirname'],
            self.curr_config_file['basename']
            )
        
        with open(filepath, "w") as output_file:
            text = self.txt_edit.get(1.0, tk.END)
            output_file.write(text)
        
        
        self.root.title(f"Pressure Control Interface | Config Editor - {os.path.basename(filepath)}")
        self.load_config_file()


    def slider_changed(self, slider_num):
        try:
            #self.channels[slider_num][1].set(val)
            scalevar = self.channels[slider_num][2]
            scale_value=round(scalevar.get(), 2)

            scale = self.channels[slider_num][0]
            box = self.channels[slider_num][0]

            scalevar.set(scale_value)
            scale.set(scale_value)
            box.set(scale_value)

            self.curr_pressures[slider_num] = scale_value

            #if self.livesend.get():
            #    self.set_pressure()

            #print(slider_num, scale_value)
        except tk.TclError:
            pass
        except IndexError:
            pass


    def speed_changed(self, slider_num):
        try:
            #self.channels[slider_num][1].set(val)
            scalevar = self.speed_vals[slider_num]
            scale_value=round(scalevar.get(), 2)
            scalevar.set(scale_value)

            val_to_send=[]
            for val in self.speed_vals:
                if val is not None:
                    val_to_send.append(val.get())
                else:
                    val_to_send.append(0)

            if self.comm_handler:
                self.comm_handler.send_command("speed",val_to_send)

            #if self.livesend.get():
            #    self.set_pressure()

            #print(slider_num, scale_value)
        except tk.TclError:
            pass
        except IndexError:
            pass


    def _set_pressure(self):
        press = copy.deepcopy(self.curr_pressures)
        press.insert(0, self.transition_speed.get())

        if self.comm_handler:
            self.comm_handler.send_command("set",press)
        
        #print(press)

    def send_command_string(self, event=None):
        cmdstring = self.cmd_btns['cmd_var'].get()
        self.cmd_btns['cmd_var'].set("")
        self.comm_handler.send_string(cmdstring)

        if len(self.command_history)>0:
            if cmdstring !=self.command_history[0]:
                self.command_history.appendleft(cmdstring)
        else:
            self.command_history.appendleft(cmdstring)

        if len(self.command_history)>100:
            self.command_history.pop()

        print(self.command_history)
        
        self.command_history_idx=0
        self.scroll_command_history=False

    def reset_command_history(self, event=None):
        self.command_history_idx=0
        self.scroll_command_history=False

    def scroll_command_history_up(self, event=None):
        if not self.scroll_command_history:
            self.scroll_command_history=True
        else:
            self.command_history_idx+=1

            if self.command_history_idx <0:
                self.command_history_idx=0
            elif self.command_history_idx >=len(self.command_history):
                self.command_history_idx=len(self.command_history)-1


        new_cmd = self.command_history[self.command_history_idx]
        self.cmd_btns['cmd_var'].set(new_cmd)

        

    def scroll_command_history_down(self, event=None):
        if not self.scroll_command_history:
            return 

        self.command_history_idx-=1

        if self.command_history_idx <0:
            self.command_history_idx=0
        elif self.command_history_idx >=len(self.command_history):
            self.command_history_idx=len(self.command_history)-1

        new_cmd = self.command_history[self.command_history_idx]
        self.cmd_btns['cmd_var'].set(new_cmd)


    
    def send_command(self, cmd, args):
        self.comm_handler.send_command(cmd, args)


    def set_pressure(self):
        if self.livesend.get():
            return
        else:
            self._set_pressure()
            return


    def set_data_stream(self):
        if self.live_data.get():
            self.comm_handler.send_command("on",None)
        else:
            self.comm_handler.send_command("off",None)


    def read_data(self):
        try:
            while self.run_read_thread:
                line=self.comm_handler.read_all()
                if line:
                    print(line)
                    if line[0][0] is not None:
                        if line[0][0].get('_command', None) is not None:
                            self.updated_echos(line[0][0])
        except serial.serialutil.SerialException:
            pass


    def updated_echos(self, echo):
        txt=self.cmd_btns.get('txt_return',None)
        if txt is not None:
            txt.configure(state='normal')
            #txt.delete(1.0,tk.END)
            txt.insert(tk.END, ('%d\t%s\t%s\n')%(self.feedback_idx,echo['_command'], echo['_args']))

            if self.cmd_btns.get('txt_autoscroll',True).get():
                txt.see("end")

            try:
                num_lines = int(txt.index('end').split('.')[0]) - 2
                num_lines_allowed=self.cmd_btns['num_manual_lines'].get()

                if num_lines>num_lines_allowed:
                    txt.delete(1.0, float(num_lines-num_lines_allowed+1))
            except:
                pass
            txt.configure(state='disabled')
            self.feedback_idx+=1
    
    def set_pressure_threaded(self):
        while self.run_read_thread:
            if self.livesend.get():
                self._set_pressure()
            time.sleep(0.1)
            


    def get_serial_setup(self):
        
        self.config_btns['connect']['state']='disabled'
        self.w=CommConfig(self.root, hw_path=self.hw_path, hw_options=self.hw_options)
        self.root.wait_window(self.w.top)
        self.config_btns['connect']['state']='normal'

        if (self.w.hw_profile is None) or (self.w.comports is None):
            self.status_bar.config(text ='No Devices Connected')
            return

        #print(self.w.hw_profile)
        #print(self.w.comports)
        
        self.connect_to_controller(hw_profile=self.w.hw_profile, devices=self.w.comports,)
        self.status_bar.config(text ='Controller Connected!')
        self.config_btns['connect']['state']='disabled'
        self.config_btns['disconnect']['state']='enabled'

        self.init_manual_editor()

    def reset_serial_setup(self):

        if self.comm_handler is not None:
            self.run_read_thread = False
            self.comm_handler.shutdown()
            self.comm_handler = None
        
        # Clear the text editor
        self.txt_edit.delete("1.0", tk.END)
        self.config=None
        self.config_btns['config_frame'].destroy()

        self.del_sliders()
        # Disable the pressure control tab
        self.tabControl.tab(self.pedit_tab, state="disabled")
        self.tabControl.tab(self.cmd_tab, state="disabled")
        self.tabControl.tab(self.traj_tab, state="disabled")
        


        self.status_bar.config(text ='Controller Disconnected!')
        self.config_btns['connect']['state']='enabled'
        self.config_btns['disconnect']['state']='disabled'


    def init_gui(self):
        # Make a new window
        self.root = ThemedTk(theme="breeze")#tk.Tk()
        self.root.title("Pressure Control Interface")

        # Add the statusbar
        self.status_bar = tk.Label(self.root, text="Hello! Connect to a controller to get started.",
            foreground=self.color_scheme['secondary_normal'],
            width=10,
            height=3,
            font=('Arial',12))
        self.status_bar.pack(expand=False, fill="x", padx=5, pady=5)
        
        # Make tabs
        self.tabControl = ttk.Notebook(self.root)
        self.config_tab = ttk.Frame(self.tabControl)
        self.pedit_tab  = ttk.Frame(self.tabControl)
        self.traj_tab   = ttk.Frame(self.tabControl)
        self.cmd_tab   = ttk.Frame(self.tabControl)

        self.tabControl.add(self.config_tab, text='Configuration')
        self.tabControl.add(self.pedit_tab, text='Pressure Control', state="disabled")
        self.tabControl.add(self.traj_tab, text='Trajectory Control', state="disabled")
        self.tabControl.add(self.cmd_tab, text='Manual Override', state="disabled")
        self.tabControl.pack(expand=True, fill="both")


        self.config_btns={}
        self.pedit_btns={}
        self.traj_btns={}
        self.cmd_btns={}

        self.config_tab.rowconfigure(0, minsize=200, weight=1)
        self.config_tab.columnconfigure(1, minsize=200, weight=1)

        # Build the text pane, but button pane, and the slider pane
        self.txt_edit = tk.Text(self.config_tab)
        self.txt_edit.grid(row=0, column=1, sticky="nsew")
        #self.txt_edit.bind('<KeyRelease>', self.update_config())
        
        self.fr_sidebar = tk.Frame(self.config_tab, bd=2,)
        self.fr_sidebar.grid(row=0, column=0, sticky="ns")

        #self.init_control_editor()
        self.init_control_sender()

        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.root.mainloop()

        
    def del_manual_editor(self):
        try:
            self.cmd_btns['cmd_frame'].destroy()
            self.cmd_btns['txt_frame'].destroy()
        except:
            pass



    def init_manual_editor(self):
        self.del_manual_editor()
        fr_commands = tk.LabelFrame(self.cmd_tab, bd=2,text="Quick Commands")
        fr_commands.pack(expand=False, fill="x", side="top", pady=10, padx=10)

        fr_sender = tk.LabelFrame(self.cmd_tab,  bd=2, text="Send Commands")
        fr_sender.pack(expand=True, fill="both", side="top", pady=10, padx=10)

        fr_text_return = tk.Frame(fr_sender)
        fr_text_return.pack(expand=True, fill="both", side="top", pady=5, padx=5)

        scrollbar = tk.Scrollbar(fr_text_return)

        text_box_return = tk.Text(fr_text_return, state='disabled', height=1, bg='#ffffff',
                        font=('Arial', 11),
                        yscrollcommand = scrollbar.set)

        scrollbar.config( command = text_box_return.yview )

        scrollbar.pack( side = 'right', fill = 'y')
        text_box_return.pack( side = 'left', fill = 'both' )

        fr_txt = tk.Frame(fr_sender, height=2)
        
        fr_txt.pack(expand=False, fill="x", side="top", pady=5, padx=5)

        fr_txt.grid_rowconfigure(0, weight=1)
        fr_txt.grid_columnconfigure(0, weight=1)

        

        button1 = ttk.Button(fr_commands,
            text="Reset",
            command=lambda : self.send_command("reset",None) ,
        )
        button2 = ttk.Button(fr_commands,
            text="Load Onboard",
            command=lambda : self.send_command("load",None),
            state='normal',
        )
        button3 = ttk.Button(fr_commands,
            text="Save Onboard",
            command=lambda : self.send_command("save",None),
            state='normal',
        )

        button1.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        button2.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        button3.grid(row=0, column=2, sticky="ew", padx=5, pady=5)

        # Make the text entry for sending commands
        button4 = ttk.Button(fr_txt,
            text="Send",
            command=self.send_command_string,
            state='normal',
        )       

        autoscroll_var = tk.BooleanVar()
        autoscroll_var.set(self.settings.get('manual_command_sender',{}).get('autoscroll', True))

        autoscroll_btn = ttk.Checkbutton(fr_txt,
            text="Auto-scroll",
            variable=autoscroll_var,
        )


        num_lines = tk.IntVar()
        num_lines.set(self.settings.get('manual_command_sender',{}).get('feedback_window_length', 200))
        spin = Spinbox(fr_txt,
                width=6,
                from_=0, to=10000, increment=1,
                textvariable=num_lines,
                font=('Arial', 12),
                )
        
        command_var = tk.StringVar()
        text_box = ttk.Entry(fr_txt,font=('Courier', 14), textvariable=command_var)
        text_box.bind('<Return>', self.send_command_string)
        text_box.bind('<Up>', self.scroll_command_history_up)
        text_box.bind('<Down>', self.scroll_command_history_down)
        text_box.bind('<Key>',self.reset_command_history)
        text_box.grid(row=0, column=0, sticky="ew")

        button4.grid(row=0, column=1, sticky="e", padx=5, pady=5)
        autoscroll_btn.grid(row=0, column=2, sticky="e", padx=5, pady=5)
        spin.grid(row=0, column=3, sticky="ew", padx=5)


        self.cmd_btns['num_manual_lines'] = num_lines
        self.cmd_btns['open']    = button1
        self.cmd_btns['save']    = button2
        self.cmd_btns['saveas']  = button3
        self.cmd_btns['cmdsend'] = button4
        self.cmd_btns['cmd']     = text_box
        self.cmd_btns['cmd_var']     = command_var
        self.cmd_btns['cmd_frame']     = fr_commands
        self.cmd_btns['txt_frame']     = fr_sender
        self.cmd_btns['return_frame']     = fr_text_return
        self.cmd_btns['txt_return']    = text_box_return
        self.cmd_btns['txt_autoscroll'] = autoscroll_var

        self.tabControl.tab(self.cmd_tab, state="normal")


    def init_control_editor(self):
        fr_buttons = tk.Frame(self.fr_sidebar,  bd=2, )

        button1 = ttk.Button(fr_buttons,
            text="Open Config",
            command=self.open_config_file,
        )
        button2 = ttk.Button(fr_buttons,
            text="Save Config",
            command=self.save_config_file,
            state='disabled',
        )
        button3 = ttk.Button(fr_buttons,
            text="Save Config As",
            command=self.save_config_file_as,
            state='disabled',
        )
        button4 = ttk.Button(fr_buttons,
            text="Send Config",
            command=self.send_config,
            state='disabled',
        )
        button1.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        button2.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        button3.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        button4.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        #btn.grid(row=1, column=2, sticky="ew", padx=5)

        fr_buttons.grid(row=2, column=0, sticky="ns")

        self.config_btns['open']  =button1
        self.config_btns['save']  =button2
        self.config_btns['saveas']=button3
        self.config_btns['send']  =button4
        self.config_btns['config_frame'] = fr_buttons


    def init_control_sender(self):
        self.fr_send_btns = tk.Frame(self.fr_sidebar, bd=2,)
        self.fr_send_btns.grid(row=1, column=0, sticky="ns", pady=20)


        #self.open_sliders_btn = ttk.Button(self.fr_send_btns,
        #    text="Open Sliders",
        #    command=self.init_pressure_editor,
        #)
        #self.open_sliders_btn.grid(row=0, column=2, sticky="ew", padx=5)
        #self.open_sliders_btn.configure(state="disabled")

        connect_btn = ttk.Button(self.fr_send_btns,
            text="Connect Controller",
            command=self.get_serial_setup,
            state='active',
        )

        disconnect_btn = ttk.Button(self.fr_send_btns,
            text="Disconnect Controller",
            command=self.reset_serial_setup,
            state='disabled',
        )

        connect_btn.grid(row=0, column=0, sticky="ew", padx=5)
        disconnect_btn.grid(row=1, column=0, sticky="ew", padx=5)

        self.config_btns['connect']=connect_btn
        self.config_btns['disconnect']=disconnect_btn


    def del_control_sender(self):
        try:
            self.fr_send_btns.destroy()
        except:
            pass
        

    def del_sliders(self):
        try:
            self.fr_sliders.destroy()
            self.fr_slider_btns.destroy()
            for chan in self.channels:
                for item in chan:
                    item.destroy()
        except:
            pass


    def set_graph_colors(self):
        self.graph_palette = {}
        graph_colors = self.color_scheme['graph']
        for color_key in graph_colors:
            palette = graph_colors[color_key].get('palette',None)
            args = graph_colors[color_key].get('args', {})
            if isinstance(palette, list):
                self.graph_palette[color_key] = palette
            elif isinstance(palette, str):
                if palette == "hls":
                    self.graph_palette[color_key] = sns.hls_palette(self.num_channels, **args)
                elif palette == "husl":
                    self.graph_palette[color_key] = sns.husl_palette(self.num_channels, **args)
                elif palette == "dark":
                    self.graph_palette[color_key] = sns.dark_palette(self.num_channels, **args)
                elif palette == "light":
                    self.graph_palette[color_key] = sns.light_palette(self.num_channels, **args)
                elif palette == "diverging":
                    self.graph_palette[color_key] = sns.diverging_palette(self.num_channels, **args)
                elif palette == "diverging":
                    self.graph_palette[color_key] = sns.diverging_palette(self.num_channels, **args)
                elif palette == "blend":
                    self.graph_palette[color_key] = sns.blend_palette(self.num_channels, **args)
                elif palette == "xkcd":
                    self.graph_palette[color_key] = sns.xkcd_palette(self.num_channels, **args)
                elif palette == "crayon":
                    self.graph_palette[color_key] = sns.crayon_palette(self.num_channels, **args)
                elif palette == "mpl":
                    self.graph_palette[color_key] = sns.mpl_palette(self.num_channels, **args)
                else:
                    self.graph_palette[color_key] = sns.color_palette(palette, self.num_channels)
            else:
                self.graph_palette[color_key] = sns.color_palette("bright", self.num_channels)

        sns.set_palette(self.graph_palette['primary'])


    def init_pressure_editor(self):
        self.del_sliders()

        self.set_graph_colors()

        self.livesend = tk.IntVar()
        self.livesend.set(0)
        self.transition_speed = tk.DoubleVar()
        self.transition_speed.set(self.config.get('transitions', 0.0))
        
        self.fr_slider_btns = tk.Frame(self.pedit_tab, bd=2, )
        self.fr_slider_btns.grid(row=99, column=0, sticky="ns", pady=5)

        button = ttk.Button(self.fr_slider_btns,
            text="Set Pressures",
            command=self.set_pressure,
        )

        button.grid(row=0, column=0, sticky="ew", padx=5)

        button2 = ttk.Checkbutton(self.fr_slider_btns,
            text="Send Pressures Live",
            variable=self.livesend,
        )

        button2.grid(row=0, column=1, sticky="ew", padx=5)


        spin = Spinbox(self.fr_slider_btns,
                width=6,
                from_=0.0, to=1000, increment=0.1,
                textvariable=self.transition_speed,
                font=('Arial', 14),
                )
        spin.grid(row=0, column=2, sticky="ew", padx=5)


        self.live_data = tk.IntVar()
        self.live_data.set(0)
        cb = lambda name, index, val: self.set_data_stream()
        self.live_data.trace("w",cb)
        button3 = ttk.Checkbutton(self.fr_slider_btns,
            text="Data Stream",
            variable=self.live_data,
        )

        button3.grid(row=0, column=3, sticky="ew", padx=5)

        self.fr_sliders = tk.Frame(self.pedit_tab, bd=2)
        self.fr_sliders.grid(row=98, column=0, sticky="ns", pady=20)
        self.init_sliders(self.fr_sliders)

        self.start_pressure_thread()

        # Enable the pressure control tab
        self.tabControl.tab(self.pedit_tab, state="normal")


    def init_sliders(self, fr_sliders):
        self.channels=[]
        self.speed_vals=[]
        for i in range(self.num_channels):
            # Get current info
            curr_max = self.config['max_pressure'][i]
            curr_min = self.config['min_pressure'][i]
            curr_on = self.config['channels']['states'][i]

            if curr_on:
                curr_state = "normal"
            else:
                curr_state = "disabled"

            # Create a variable to share with the slider and spinbox
            spinval = tk.DoubleVar()
            spinval.set(self.curr_pressures[i])
            cb = lambda name, index, val, i=i: self.slider_changed(i)
            spinval.trace("w",cb)

            # Create the slider
            #scale = tk.Scale(fr_sliders, variable=spinval,
            #    orient=tk.VERTICAL, length=130,
            #    from_=curr_max, to=curr_min, resolution=0.1,
            #    state=curr_state,
            #    font=('Arial', 12),
            #    activebackground=self.color_scheme['primary_'+curr_state],
            #    troughcolor=self.color_scheme['secondary_'+curr_state],
            #    )
            scale = tk.Scale(fr_sliders, variable=spinval,
                orient=tk.VERTICAL, length=130,
                from_=curr_max, to=curr_min, resolution=0.1,
                state=curr_state,
                font=('Arial', 12),
                activebackground=_from_rgb(self.graph_palette['primary_light'][i]),
                troughcolor=_from_rgb(self.graph_palette['primary'][i]),
                )
            scale.grid(row=2, column=i, sticky="ew", padx=5)

            # Create the spinbox
            spin = Spinbox(fr_sliders,
                width=5,
                from_=curr_min, to=curr_max, increment=0.1,
                textvariable=spinval, state=curr_state,
                font=('Arial', 12),
                )
            spin.grid(row=4, column=i, sticky="ew", padx=5, pady=10)


            # Add max and min labels
            label_title = ttk.Label(fr_sliders, text="%d"%(i+1), width=2, font=('Arial', 20, 'bold'), state=curr_state)
            label_max = ttk.Label(fr_sliders, text="%0.1f"%(curr_max), width=7, font=('Arial', 10), state=curr_state)
            label_min = ttk.Label(fr_sliders, text="%0.1f"%(curr_min), width=7, font=('Arial', 10), state=curr_state)
            label_title.grid(row=0, column=i, sticky="s", pady=0)
            label_max.grid(row=1, column=i, sticky="s", pady=0)
            label_min.grid(row=3, column=i, sticky="n", pady=0)


            if self.channel_types[i]=="dynamixel":
                speedval=tk.DoubleVar()
                speedval.set(200)
                cb = lambda name, index, val, i=i: self.speed_changed(i)
                speedval.trace("w",cb)
                speed = Spinbox(fr_sliders,
                    width=5,
                    from_=0, to=1023, increment=1,
                    textvariable=speedval, state=curr_state,
                    font=('Arial', 12),
                    )
                speed.grid(row=5, column=i, sticky="ew", padx=5, pady=10)
                self.speed_vals.append(speedval)
            else:
                self.speed_vals.append(None)

            

            

            self.channels.append([scale, spin, spinval, label_max, label_min])
        
    def update_sliders(self):
        
        self.channels


    def on_gui_reset(self):
        self.shutdown()
        self.root.destroy()
        self.init_gui()

    def on_window_close(self):
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.shutdown()
            self.root.destroy()
            

    def shutdown(self):
        try:
            self.run_read_thread = False
        except:
            raise


if __name__ == "__main__":
    gui = PressureControlGui()
    try:
        if len(sys.argv)==2:
            gui.load_settings(sys.argv[1])
        gui.init_gui()
    except KeyboardInterrupt:
        gui.on_window_close()