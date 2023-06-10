#!/usr/bin/env python
from customtkinter import *
from timecode import Timecode
import datetime
import time
from threading import Thread

from pathlib import Path
from PIL import Image
from ctypes import windll, byref, sizeof, c_int

import ltc_generator as LTC
from timecode_tools import *
from py_audio_class import AudioDevice
from py_midi_class import MidiDevice
from client_class import Client
from server_class import Server
#----------------------------------------------------------#
#--------------------GLOBAL VARIABLES----------------------#
#----------------------------------------------------------#

#---GENERAL--#

colors={"green":"#3DBC78", "grisClaro":"#9FA1A0","grisOscuro":"#262626","grisMedio":"#777777","grisBlanco":"#AFAFAF","rojo":"#A52F2F","amarillo":"#BCB851"}
script_directory = Path(__file__).resolve().parent / "img"
icon_path = script_directory /  "icon.ico"

#---CLASS INIT---#

audio_device = AudioDevice()
ltc_audio_device = AudioDevice()
midi_device = MidiDevice()

fps = 25
start_timecode = '00:00:00:00'
tc = Timecode(fps, start_timecode)

is_playing = False
is_pin = False
is_lock = False
mode="master"

#---Audio---#
audio_output_devices = ltc_audio_device.get_output_devices()
audio_file_path=None
audio_volume=0.8

#--NETWORK--#
current_ip="localhost"
servidor = Server()
cliente = Client()
servidor.start()
#----LTC----#
ltc_switch_state = False
ltc_offset = Timecode(fps,"00:00:00:00")
ltc_offset_value=add_tcs(tc,ltc_offset,fps)
ltc_fps = 25

#----MTC----#
mtc_switch_state = False
mtc_offset = Timecode(fps,"00:00:00:00")
mtc_offset_value = add_tcs(tc,mtc_offset,fps)
mtc_output_devices =  midi_device.get_all_output_devices()
mtc_fps = 25

#----------------------------------------------------------#
#------------------------FUNCTIONS-------------------------#
#----------------------------------------------------------#
def update_status_labels(mensaje,color):
    global network_status
    network_status_label.configure(text=mensaje,text_color=colors[color])

def update_network_satus():
    global mode
    if mode == "master":
        if servidor.clientes_conectados != []:
            update_status_labels("TRANSMITING","green")
        else:
            if servidor.online: 
                update_status_labels("WAITING","amarillo")
            else:
                update_status_labels("OFFLINE","rojo")
    else:
        if cliente.connected:
                update_status_labels("LISENING","green")
        else:
            if cliente.init: 
                update_status_labels("LOOKING","amarillo")
            else:
                update_status_labels("OFFLINE","rojo")
    app.after(100, update_network_satus)
        
def set_master_mode():
    
    global mode
    global is_playing
    global start_timecode
    global tc
    
    if mode == "master":
        return
    
    mode = "master"
    fps = 25
    start_timecode = '00:00:00:00'
    tc = Timecode(fps, start_timecode)
    is_playing = False
    update_status_labels("OFFLINE","rojo")
    
    cliente.stop()
    set_mode_interfaze()
    servidor.start()
    
def set_slave_mode():
    global mode
    global is_playing
    global start_timecode
    global tc
    
    if mode == "slave":
        return
    
    mode="slave"
    fps = 25
    start_timecode = '00:00:00:00'
    tc = Timecode(fps, start_timecode)
    is_playing=False
    
    update_status_labels("OFFLINE","rojo")
    
    servidor.stop()
    set_mode_interfaze()
    cliente.start()
    
def set_mode_interfaze():
    if mode == "master":
        master_mode_label.configure(text_color=colors["green"])
        slave_mode_label.configure(text_color=colors["grisMedio"])
        play_pause_button.configure(state="normal", image=play_image)
        stop_button.configure(state="normal", image=stop_image)
        clock_button.configure(state="normal", image=clock_image)
        forward_button.configure(state="normal", image=forward_image)
        backward_button.configure(state="normal", image=backward_image)
        audio_open_button.configure(state="normal")
        audio_close_button.configure(state="normal")
        audio_slider.configure(state="normal",button_color=colors["grisClaro"],progress_color=colors["green"])
        audio_output_selector.configure(state="normal")
        audio_label.configure(text="Open An Audio File")
        
    else:
        master_mode_label.configure(text_color=colors["grisMedio"])
        slave_mode_label.configure(text_color=colors["green"])
        play_pause_button.configure(state="disabled", image=play_disable_image)
        stop_button.configure(state="disabled", image=stop_disable_image)
        clock_button.configure(state="disabled", image=clock_disable_image)
        forward_button.configure(state="disabled", image=forward_disable_image)
        backward_button.configure(state="disabled", image=backward_disable_image)
        audio_open_button.configure(state="disabled")
        audio_close_button.configure(state="disabled")
        audio_slider.configure(state="disabled",button_color=colors["grisMedio"],progress_color=colors["grisMedio"])
        audio_output_selector.configure(state="disabled")
        audio_label.configure(text="Audio Player Is Disable In Slave Mode",state="disabled")   
        
def toggle_playback():
    global is_playing
    is_playing = not is_playing
    if is_playing:
        play_pause_button.configure(image=pause_image)
        generar_timecode()
    else:
        ltc_audio_device.cerrar_stream()
        play_pause_button.configure(image=play_image)

def update_general_state():
    None
    
def reiniciar_timecode():
    global tc
    global is_playing
    tc = Timecode(fps, start_timecode)
    is_playing = False
    play_pause_button.configure(image=play_image)
    
def ltc_player():
    audiodata = LTC.make_ltc_audio(add_tcs(ltc_offset,tc,fps))
    ltc_audio_device.play(audiodata)
    
def recive_timecode():
    global tc
    global fps
    global start_timecode
    global is_playing
    
    if cliente.conectado:
        
        mensaje = eval(cliente.ultimo_mensaje)
        
        fps = mensaje["fps"]
        tc = Timecode(fps,mensaje["tc"])
        start_timecode = mensaje["start_timecode"]
        is_playing = mensaje["is_playing"]
        
        if mtc_switch_state:
            mtc_thread=Thread(target=midi_device.sendMTC(add_tcs(mtc_offset,tc,fps)))
            mtc_thread.start()
            
        if ltc_switch_state:
            mtc_thread=Thread(target=ltc_player())
            mtc_thread.start()  

    app.after(1000 // fps, recive_timecode)

def generar_timecode():
    global tc
    if is_playing:
        tc.next()
        
        if mtc_switch_state:
            mtc_thread=Thread(target=midi_device.sendMTC(add_tcs(mtc_offset,tc,fps)))
            mtc_thread.start()
            
        if ltc_switch_state:
            mtc_thread=Thread(target=ltc_player())
            mtc_thread.start() 
            
        servidor.send_to_all({"fps": fps, "start_timecode": start_timecode, "tc": str(tc), "is_playing": is_playing})
        app.after(1000 // fps, generar_timecode)

def update_timecode_labels():
    timecode_str = str(tc)
    hh_time.configure(text=timecode_str[:2])
    mm_time.configure(text=timecode_str[3:5])
    ss_time.configure(text=timecode_str[6:8])
    ff_time.configure(text=timecode_str[9:])   
    
    if mtc_switch_state:
        mtc_time.configure(text= add_tcs(mtc_offset,tc,fps))
    if ltc_switch_state:
        ltc_time.configure(text= add_tcs(ltc_offset,tc,fps))
    app.after(1000 // fps, update_timecode_labels)
        
def set_timecode_clock():
    global tc
    current_time = datetime.datetime.now()
    current_time_str = current_time.strftime("%H:%M:%S:%f")[:-3] 
    tc = Timecode(fps, start_timecode=current_time_str)
    
def time_forward():
    global tc
    limit = Timecode(fps, '23:49:59:00')
    if tc > limit:
        tc = Timecode(fps, f'23:59:59:{fps-1}')
    else:
        for i in range(10*fps):
            tc.next()
    
def time_backward():
    global tc
    limit = Timecode(fps, '00:00:10:00')
    if tc < limit:
        tc = Timecode(fps, '00:00:00:00')
    else:
        for i in range(10*fps):
            tc.back()
    
def pin_window():
    global is_pin
    is_pin= not is_pin
    app.attributes('-topmost', is_pin)
    if is_pin:
        pin_button.configure(image=pin_on_image)
    else:
        pin_button.configure(image=pin_off_image)

def lock_window():
    global is_lock
    is_lock= not is_lock
    if is_lock:
        block_button.configure(image=block_closed_image)
    else:
        block_button.configure(image=block_open_image)

def set_ltc_state():
    global ltc_switch_state 
    ltc_switch_state = not ltc_switch_state
    if ltc_switch_state:
        ltc_time.configure(text=add_tcs(ltc_offset,tc,fps),text_color=colors["green"])
    else:
        ltc_time.configure(text=ltc_offset,text_color=colors["grisClaro"])

def set_ltc_fps(choice):
    global ltc_fps
    if choice == "24 FPS":
        ltc_fps = 24
    elif choice == "25 FPS":
        ltc_fps = 25
    elif choice == "30 FPS":
        ltc_fps = 30
        
def set_mtc_fps(choice):
    global ltc_fps
    if choice == "24 FPS":
        ltc_fps = 24
    elif choice == "25 FPS":
        ltc_fps = 25
    elif choice == "30 FPS":
        ltc_fps = 30     

def set_mtc_state():
    global mtc_switch_state
    mtc_switch_state = not mtc_switch_state
    if mtc_switch_state:
        mtc_time.configure(text=add_tcs(mtc_offset,tc,fps),text_color=colors["green"])
    else:
        mtc_time.configure(text=mtc_offset,text_color=colors["grisClaro"])

def set_ltc_offset():
    global ltc_offset
    
    hh_str = ltc_hh_offset_time.get() or "0"
    mm_str = ltc_mm_offset_time.get() or "0"
    ss_str = ltc_ss_offset_time.get() or "0"
    ff_str = ltc_ff_offset_time.get() or "0"
    
    if not hh_str.isdigit() or not mm_str.isdigit() or not ss_str.isdigit() or not ff_str.isdigit():
        ltc_hh_offset_time.delete(0, 'end')
        ltc_mm_offset_time.delete(0, 'end')
        ltc_ss_offset_time.delete(0, 'end')
        ltc_ff_offset_time.delete(0, 'end')
        ltc_hh_offset_time.select_clear()
        return
    
    hh = int(hh_str)
    mm = int(mm_str)
    ss = int(ss_str)
    ff = int(ff_str)

    if hh > 23 or mm > 59 or ss > 59 or ff > ltc_fps - 1:
        ltc_hh_offset_time.delete(0, 'end')
        ltc_mm_offset_time.delete(0, 'end')
        ltc_ss_offset_time.delete(0, 'end')
        ltc_ff_offset_time.delete(0, 'end')
        return
    
    new_time = f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"
    
    ltc_offset = Timecode(ltc_fps, new_time)
    
    ltc_offset_label.configure(text=ltc_offset)
    ltc_time.configure(text=ltc_offset)
    
    ltc_hh_offset_time.delete(0, 'end')
    ltc_mm_offset_time.delete(0, 'end')
    ltc_ss_offset_time.delete(0, 'end')
    ltc_ff_offset_time.delete(0, 'end')
    
def set_mtc_offset():
    global mtc_offset
    
    hh_str = mtc_hh_offset_time.get() or "0"
    mm_str = mtc_mm_offset_time.get() or "0"
    ss_str = mtc_ss_offset_time.get() or "0"
    ff_str = mtc_ff_offset_time.get() or "0"
    
    if not hh_str.isdigit() or not mm_str.isdigit() or not ss_str.isdigit() or not ff_str.isdigit():
        mtc_hh_offset_time.delete(0, 'end')
        mtc_mm_offset_time.delete(0, 'end')
        mtc_ss_offset_time.delete(0, 'end')
        mtc_ff_offset_time.delete(0, 'end')
        mtc_hh_offset_time.select_clear()
        return
    
    hh = int(hh_str)
    mm = int(mm_str)
    ss = int(ss_str)
    ff = int(ff_str)

    if hh > 23 or mm > 59 or ss > 59 or ff > mtc_fps - 1:
        mtc_hh_offset_time.delete(0, 'end')
        mtc_mm_offset_time.delete(0, 'end')
        mtc_ss_offset_time.delete(0, 'end')
        mtc_ff_offset_time.delete(0, 'end')
        return
    
    new_time = f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"
    
    mtc_offset = Timecode(mtc_fps, new_time)
    
    mtc_offset_label.configure(text=mtc_offset)
    mtc_time.configure(text=mtc_offset)
    
    mtc_hh_offset_time.delete(0, 'end')
    mtc_mm_offset_time.delete(0, 'end')
    mtc_ss_offset_time.delete(0, 'end')
    mtc_ff_offset_time.delete(0, 'end')

def blink_on_pause():
    if not is_playing and tc != "00:00:00:00":
        if  div1_label.cget("text") == ":":
            div1_label.configure(text="")
            div2_label.configure(text="")
            div3_label.configure(text="")
        else:
            div1_label.configure(text=":")
            div2_label.configure(text=":")
            div3_label.configure(text=":") 
    else:  
        div1_label.configure(text=":")
        div2_label.configure(text=":")
        div3_label.configure(text=":") 
                 
    app.after(400, blink_on_pause)

def audio_slider_event(value):
    None  

def audio_output_selector_callback(choice):
    for clave, valor in audio_output_devices.items():
        if valor == choice:
            device_index = clave
            break  # Detener el bucle una vez que se encuentre la primera coincidencia
    audio_device.set_output_device(device_index)
    
def ltc_audio_output_selector_callback(choice):
    for clave, valor in audio_output_devices.items():
        if valor == choice:
            device_index = clave
            break  # Detener el bucle una vez que se encuentre la primera coincidencia
    ltc_audio_device.set_output_device(device_index)
    
def mtc_output_selector_callback(choice):
        for clave, valor in mtc_output_devices.items():
            if valor == choice:
                device_index = clave
                break
        print(f"current: {midi_device.current_output_device_index}")
        print(f"new: {device_index} : {choice}")
        if device_index != midi_device.current_output_device_index:
            midi_device.set_output_device(device_index)
    
def cerrar_app():
    if not servidor.stop_event.is_set():
        servidor.stop()
    if not cliente.stop_event.is_set():
        cliente.stop()
    app.destroy()

def center_window(window):
    
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = int((screen_width / 2) - (window.winfo_width() / 2))
    y = int((screen_height / 2) - (window.winfo_height() / 2))

    window.geometry(f"+{x}+{y}")
    
def SaveLastClickPos(event):
    global lastClickX, lastClickY
    lastClickX = event.x
    lastClickY = event.y
    
def Dragging(event):
    app.geometry(f'+{event.x - lastClickX + app.winfo_x()}+{event.y - lastClickY + app.winfo_y()}')
    
#------------------------------------------------------------------------------
#--------------------------------Tkinker APP-----------------------------------
#------------------------------------------------------------------------------

set_appearance_mode("dark")
set_default_color_theme("blue")    

lastClickX = 0
lastClickY = 0

app = CTk()
app.geometry("1200x700")
app.resizable(width=False, height=False)
app.attributes('-topmost', is_pin)
app.title("SDM TIMECODE")
app.iconbitmap(default=icon_path)
center_window(app)

HWND = windll.user32.GetParent(app.winfo_id()) # the window we want to change

DWMWA_CAPTION_COLOR = 0x00242424 # r: 00, b: 50, g: 50
DWMWA_TITLE_COLOR = 0x00AFAFAF # FF means full (100)
DWMWA_BORDER_COLOR = 0x0078BC3D # r: full, g: full, b: 00

windll.dwmapi.DwmSetWindowAttribute(HWND, 35, byref(c_int(DWMWA_CAPTION_COLOR)), sizeof(c_int))
windll.dwmapi.DwmSetWindowAttribute(HWND, 36, byref(c_int(DWMWA_TITLE_COLOR)), sizeof(c_int))
windll.dwmapi.DwmSetWindowAttribute(HWND, 34, byref(c_int(DWMWA_BORDER_COLOR)), sizeof(c_int))

#------------
#------------

master=CTkFrame(app, width=1200, height=700,fg_color="transparent")
master.place(x=0,y=0)

#------------
#------------
mode_frame = CTkFrame(master, width=150, height=50,fg_color="transparent")
mode_frame.place(x=40,y=630)
slave_mode_label = CTkButton(mode_frame, text="SLAVE MODE", fg_color="transparent", width=150,height=20,anchor="nw", font=("IBM Plex Sans Bold",18),text_color=colors["grisMedio"],hover_color="#242424",command=set_slave_mode)
slave_mode_label.place(x=0,y=0)
master_mode_label = CTkButton(mode_frame, text="MASTER MODE", fg_color="transparent", width=150,height=20,anchor="sw", font=("IBM Plex Sans Bold",18),text_color=colors["green"],hover_color="#242424",command=set_master_mode)
master_mode_label.place(x=0,y=22)

#------------
#------------

status_frame = CTkFrame(master, width=150, height=42, fg_color="transparent")
status_frame.place(x=1010,y=630)
network_status_label = CTkLabel(status_frame, text="••• SENDING", fg_color="transparent", width=150,height=20,anchor="ne", font=("IBM Plex Sans Bold",18),text_color=colors["green"])
network_status_label.place(x=0,y=0)
ip_label = CTkLabel(status_frame, text="192.168.000.001", fg_color="transparent", width=150,height=20,anchor="se", font=("IBM Plex Sans Light",18),text_color=colors["grisClaro"])
ip_label.place(x=0,y=22)

#------------
#------------
    
block_open_image = CTkImage(dark_image=Image.open(script_directory /  "block_open.png"),size=(18,22))
block_closed_image = CTkImage(dark_image=Image.open(script_directory /  "block_closed.png"),size=(18,22))
backward_image = CTkImage(dark_image=Image.open(script_directory /  "backward.png"),size=(25,25))
stop_image = CTkImage(dark_image=Image.open(script_directory /  "stop.png"),size=(35,35))
play_image = CTkImage(dark_image=Image.open(script_directory / "play.png"),size=(60,60))
pause_image = CTkImage(dark_image=Image.open(script_directory / "pause.png"),size=(60,60))
clock_image = CTkImage(dark_image=Image.open(script_directory /  "clock.png"),size=(35,35))
forward_image = CTkImage(dark_image=Image.open(script_directory /  "forward.png"),size=(25,25))
pin_off_image = CTkImage(dark_image=Image.open(script_directory /  "pin_off.png"),size=(20,25))
pin_on_image = CTkImage(dark_image=Image.open(script_directory /  "pin_on.png"),size=(20,25))
stop_disable_image = CTkImage(dark_image=Image.open(script_directory /  "stop_disable.png"),size=(35,35))
play_disable_image = CTkImage(dark_image=Image.open(script_directory / "play_disable.png"),size=(60,60))
forward_disable_image = CTkImage(dark_image=Image.open(script_directory /  "forward_disable.png"),size=(25,25))
backward_disable_image = CTkImage(dark_image=Image.open(script_directory /  "backward_disable.png"),size=(25,25))
clock_disable_image = CTkImage(dark_image=Image.open(script_directory /  "clock_disable.png"),size=(35,35))

constrols_frame = CTkFrame(master, width=702, height=80, fg_color="transparent")
constrols_frame.place(x=249,y=600)

block_button=CTkButton(constrols_frame,width=40, height=40,text="",image=block_open_image, fg_color="transparent",hover_color=colors["grisOscuro"],command=lock_window)
block_button.place(x=70,y=20)

backward_button=CTkButton(constrols_frame,width=60, height=60,text="",image=backward_image, fg_color="transparent",hover_color=colors["grisOscuro"],command=time_backward)
backward_button.place(x=137,y=10)

stop_button=CTkButton(constrols_frame,width=60, height=60,text="",image=stop_image, fg_color="transparent",hover_color=colors["grisOscuro"],command=reiniciar_timecode)
stop_button.place(x=224,y=10)

play_pause_button=CTkButton(constrols_frame,width=80, height=80,image=play_image,text="", fg_color="transparent",hover_color=colors["grisOscuro"],command=toggle_playback)
play_pause_button.place(x=311,y=0)

clock_button=CTkButton(constrols_frame,width=60, height=60,image=clock_image,text="", fg_color="transparent",hover_color=colors["grisOscuro"],command=set_timecode_clock)
clock_button.place(x=418,y=10)

forward_button=CTkButton(constrols_frame,width=60, height=60,text="",image=forward_image, fg_color="transparent",hover_color=colors["grisOscuro"],command=time_forward)
forward_button.place(x=505,y=10)

pin_button=CTkButton(constrols_frame,width=40, height=40,image=pin_off_image,text="", fg_color="transparent",hover_color=colors["grisOscuro"],command=pin_window)
pin_button.place(x=592,y=20)

#------------
#------------

timecode_frame= CTkFrame(master, width=1200, height=290, fg_color="transparent")
timecode_frame.place(x=0,y=210)

hh_frame = CTkFrame(timecode_frame, width=250, height=250, fg_color="transparent")
hh_frame.place(x=40,y=0)

hh_time = CTkLabel(hh_frame, text="00", fg_color="transparent", width=250,height=300, font=("IBM Plex Sans Thin",200),text_color=colors["green"])
hh_time.place(x=0,y=0)

hh_label = CTkLabel(hh_frame, text="HOURS", fg_color="transparent", width=250,height=65, font=("IBM Plex Sans Light",16), anchor="s",text_color=colors["grisClaro"])
hh_label.place(x=0,y=0)

div1_frame = CTkFrame(timecode_frame, width=40, height=300, fg_color="transparent")
div1_frame.place(x=290,y=0)

div1_label = CTkLabel(div1_frame, text=":", fg_color="transparent", width=40,height=300, font=("IBM Plex Sans Thin",200),text_color=colors["green"])
div1_label.place(x=-8,y=-15)

mm_frame = CTkFrame(timecode_frame, width=250, height=250, fg_color="transparent")
mm_frame.place(x=330,y=0)

mm_time = CTkLabel(mm_frame, text="00", fg_color="transparent", width=250,height=300, font=("IBM Plex Sans Thin",200),text_color=colors["green"])
mm_time.place(x=0,y=0)

mm_label = CTkLabel(mm_frame, text="MINUTES", fg_color="transparent", width=250,height=65, font=("IBM Plex Sans Light",16), anchor="s",text_color=colors["grisClaro"])
mm_label.place(x=0,y=0)

div2_frame = CTkFrame(timecode_frame, width=40, height=300, fg_color="transparent")
div2_frame.place(x=580,y=0)

div2_label = CTkLabel(div2_frame, text=":", fg_color="transparent", width=40,height=300, font=("IBM Plex Sans Thin",200),text_color=colors["green"])
div2_label.place(x=-8,y=-15)

ss_frame = CTkFrame(timecode_frame, width=250, height=250, fg_color="transparent")
ss_frame.place(x=620,y=0)

ss_time = CTkLabel(ss_frame, text="00", fg_color="transparent", width=250,height=300, font=("IBM Plex Sans Thin",200),text_color=colors["green"])
ss_time.place(x=0,y=0)

ss_label = CTkLabel(ss_frame, text="SECONDS", fg_color="transparent", width=250,height=65, font=("IBM Plex Sans Light",16), anchor="s",text_color=colors["grisClaro"])
ss_label.place(x=0,y=0)

div3_frame = CTkFrame(timecode_frame, width=40, height=300, fg_color="transparent")
div3_frame.place(x=870,y=0)

div3_label = CTkLabel(div3_frame, text=":", fg_color="transparent", width=40,height=300, font=("IBM Plex Sans Thin",200),text_color=colors["green"])
div3_label.place(x=-8,y=-15)

ff_frame = CTkFrame(timecode_frame, width=250, height=250, fg_color="transparent")
ff_frame.place(x=910,y=0)

ff_time = CTkLabel(ff_frame, fg_color="transparent", width=250,height=300,text="00", font=("IBM Plex Sans Thin",200),text_color=colors["green"])
ff_time.place(x=0,y=0)

ff_label = CTkLabel(ff_frame, text="FRAMES", fg_color="transparent", width=250,height=65, font=("IBM Plex Sans Light",16), anchor="s",text_color=colors["grisClaro"])
ff_label.place(x=0,y=0)

#------------
#------------
    
audio_frame= CTkFrame(master, width=1120, height=40,corner_radius=20)
audio_frame.place(x=40,y=500)

audio_label = CTkLabel(audio_frame, text="AUDIO FILE NAME.WAV - DURACION 00:03:12:00", fg_color="transparent", width=600,height=40, font=("IBM Plex Sans Light",15))
audio_label.place(x=260,y=0)

audio_open_button = CTkButton(audio_frame,width=120,height=30, text="OPEN AUDIO",corner_radius=15,fg_color=colors["grisOscuro"],hover_color="#303030")
audio_open_button.place(x=5,y=5)

audio_close_button = CTkButton(audio_frame,width=120,height=30, text="CLOSE AUDIO",corner_radius=15,fg_color=colors["grisOscuro"],hover_color="#303030")
audio_close_button.place(x=995,y=5)
    
audio_slider_frame=CTkFrame(audio_frame, width=200, height=30, fg_color="#272727",corner_radius=16)
audio_slider_frame.place(x=785,y=5)
    
audio_slider = CTkSlider(audio_slider_frame, from_=0, to=100, command=audio_slider_event,width=190,button_color=colors["grisClaro"],progress_color=colors["green"],button_hover_color=colors["green"])
audio_slider.place(x=5,y=7)

audio_output_selector = CTkOptionMenu(audio_frame,values=list(audio_output_devices.values()),
                                         command=audio_output_selector_callback,
                                         height=30, width=200,corner_radius=20,fg_color="#272727",button_color=colors["grisOscuro"],button_hover_color=colors["green"],dropdown_font=("IBM Plex Sans Light",14),font=("IBM Plex Sans Light",13),dynamic_resizing=False)
audio_output_selector.place(x=135,y=5)

#------------
#------------

ltc_frame= CTkFrame(master, width=530, height=180, fg_color="#303030",corner_radius=16)
ltc_frame.place(x=55,y=20)

ltc_time= CTkLabel(ltc_frame, width=530, height=90, text="00:00:00:00", fg_color="transparent", font=("IBM Plex Sans Regular",60),text_color=colors["grisClaro"])
ltc_time.place(x=0,y=45)

ltc_switch_frame= CTkFrame(ltc_frame, width=140, height=27, fg_color=colors["grisOscuro"])
ltc_switch_frame.place(x=15,y=13)

ltc_switch = CTkSwitch(ltc_switch_frame, text="LTC SENDER", onvalue="on", offvalue="off",switch_height=15,switch_width=30,progress_color=colors["green"], command=set_ltc_state)
ltc_switch.place(x=10,y=1)

ltc_hh_offset_time = CTkEntry(ltc_frame, placeholder_text="HH", width=32, height=25)
ltc_hh_offset_time.place(x=295,y=13)
ltc_mm_offset_time = CTkEntry(ltc_frame, placeholder_text="MM", width=32, height=25)
ltc_mm_offset_time.place(x=330,y=13)
ltc_ss_offset_time = CTkEntry(ltc_frame, placeholder_text="SS", width=32, height=25)
ltc_ss_offset_time.place(x=365,y=13)
ltc_ff_offset_time = CTkEntry(ltc_frame, placeholder_text="FF", width=32, height=25)
ltc_ff_offset_time.place(x=400,y=13)
ltc_offset_label=CTkLabel(ltc_frame, text="00:00:00:00", fg_color="transparent", width=80,height=25, font=("IBM Plex Sans Light",14))
ltc_offset_label.place(x=435,y=35)
ltc_offset_button= CTkButton(ltc_frame, width=80, height=25, text="SET OFFSET", fg_color=colors["green"],text_color=colors["grisOscuro"], font=("IBM Plex Sans SemiBold",10),corner_radius=6,hover_color=colors["grisMedio"],command=set_ltc_offset)
ltc_offset_button.place(x=435,y=13)

ltc_output_label = CTkLabel(ltc_frame, text="OUTPUT AUDIO DEVICE", fg_color="transparent", width=50,height=20, font=("IBM Plex Sans Light",10),anchor="w")
ltc_output_label.place(x=18,y=132)

ltc_output_selector = CTkOptionMenu(ltc_frame,values=list(audio_output_devices.values()),
                                         command=ltc_audio_output_selector_callback,
                                         height=20, width=410,corner_radius=5,fg_color="#272727",button_color=colors["grisOscuro"],button_hover_color=colors["green"],dropdown_font=("IBM Plex Sans Light",13),font=("IBM Plex Sans Light",12))
ltc_output_selector.place(x=15,y=152)

ltc_fps_label = CTkLabel(ltc_frame, text="FPS", fg_color="transparent", width=50,height=20, font=("IBM Plex Sans Light",10),anchor="w")
ltc_fps_label.place(x=438,y=132)
ltc_fps_selector = CTkOptionMenu(ltc_frame,values=["24 FPS","25 FPS","30 FPS"],
                                         command=set_ltc_fps,
                                         height=20, width=80,corner_radius=5,fg_color="#272727",button_color=colors["grisOscuro"],button_hover_color=colors["green"],dropdown_font=("IBM Plex Sans Light",13),font=("IBM Plex Sans Light",12))
ltc_fps_selector.place(x=435,y=152)
ltc_fps_selector.set("25 FPS")

#-------
#-------

mtc_frame= CTkFrame(master, width=530, height=180, fg_color="#303030",corner_radius=16)
mtc_frame.place(x=625,y=20)

mtc_time= CTkLabel(mtc_frame, width=530, height=90, text="00:00:00:00", fg_color="transparent", font=("IBM Plex Sans Regular",60),text_color=colors["grisClaro"])
mtc_time.place(x=0,y=45)

mtc_switch_frame= CTkFrame(mtc_frame, width=140, height=27, fg_color=colors["grisOscuro"])
mtc_switch_frame.place(x=15,y=13)
mtc_switch = CTkSwitch(mtc_switch_frame, text="MTC SENDER", onvalue="on", offvalue="off",switch_height=15,switch_width=30,progress_color=colors["green"],command=set_mtc_state)
mtc_switch.place(x=10,y=1)

mtc_hh_offset_time = CTkEntry(mtc_frame, placeholder_text="HH", width=32, height=25)
mtc_hh_offset_time.place(x=295,y=13)
mtc_mm_offset_time = CTkEntry(mtc_frame, placeholder_text="MM", width=32, height=25)
mtc_mm_offset_time.place(x=330,y=13)
mtc_ss_offset_time = CTkEntry(mtc_frame, placeholder_text="SS", width=32, height=25)
mtc_ss_offset_time.place(x=365,y=13)
mtc_ff_offset_time = CTkEntry(mtc_frame, placeholder_text="FF", width=32, height=25)
mtc_ff_offset_time.place(x=400,y=13)
mtc_offset_label=CTkLabel(mtc_frame, text="00:00:00:00", fg_color="transparent", width=80,height=25, font=("IBM Plex Sans Light",14))
mtc_offset_label.place(x=435,y=35)
mtc_offset_button= CTkButton(mtc_frame, width=80, height=25, text="SET OFFSET", fg_color=colors["green"],text_color=colors["grisOscuro"], font=("IBM Plex Sans SemiBold",10),corner_radius=6,hover_color=colors["grisMedio"],command=set_mtc_offset)
mtc_offset_button.place(x=435,y=13)

mtc_output_label = CTkLabel(mtc_frame, text="MIDI OUTPUT DEVICE", fg_color="transparent", width=50,height=20, font=("IBM Plex Sans Light",10),anchor="w")
mtc_output_label.place(x=18,y=132)

mtc_output_selector = CTkOptionMenu(mtc_frame,values=list(mtc_output_devices.values()),
                                         command=mtc_output_selector_callback,
                                         height=20, width=410,corner_radius=5,fg_color="#272727",button_color=colors["grisOscuro"],button_hover_color=colors["green"],dropdown_font=("IBM Plex Sans Light",13),font=("IBM Plex Sans Light",12))
mtc_output_selector.place(x=15,y=152)

mtc_fps_label = CTkLabel(mtc_frame, text="FPS", fg_color="transparent", width=50,height=20, font=("IBM Plex Sans Light",10),anchor="w")
mtc_fps_label.place(x=438,y=132)
mtc_fps_selector = CTkOptionMenu(mtc_frame,values=["24 FPS","25 FPS","30 FPS"],
                                         command=set_mtc_fps,
                                         height=20, width=80,corner_radius=5,fg_color="#272727",button_color=colors["grisOscuro"],button_hover_color=colors["green"],dropdown_font=("IBM Plex Sans Light",13),font=("IBM Plex Sans Light",12))
mtc_fps_selector.place(x=435,y=152)
mtc_fps_selector.set("25 FPS")

#-------
""" if not is_playing:
    audio_frame.bind('<Button-1>', SaveLastClickPos)
    audio_frame.bind('<B1-Motion>', Dragging)
    timecode_frame.bind('<Button-1>', SaveLastClickPos)
    timecode_frame.bind('<B1-Motion>', Dragging)
    hh_frame.bind('<Button-1>', SaveLastClickPos)
    hh_frame.bind('<B1-Motion>', Dragging)
    hh_time.bind('<Button-1>', SaveLastClickPos)
    hh_time.bind('<B1-Motion>', Dragging)
    hh_label.bind('<Button-1>', SaveLastClickPos)
    hh_label.bind('<B1-Motion>', Dragging)
    mm_frame.bind('<Button-1>', SaveLastClickPos)
    mm_frame.bind('<B1-Motion>', Dragging)
    mm_time.bind('<Button-1>', SaveLastClickPos)
    mm_time.bind('<B1-Motion>', Dragging)
    mm_label.bind('<Button-1>', SaveLastClickPos)
    mm_label.bind('<B1-Motion>', Dragging)
    ss_frame.bind('<Button-1>', SaveLastClickPos)
    ss_frame.bind('<B1-Motion>', Dragging)
    ss_time.bind('<Button-1>', SaveLastClickPos)
    ss_time.bind('<B1-Motion>', Dragging)
    ss_label.bind('<Button-1>', SaveLastClickPos)
    ss_label.bind('<B1-Motion>', Dragging)
    ff_frame.bind('<Button-1>', SaveLastClickPos)
    ff_frame.bind('<B1-Motion>', Dragging)
    ff_time.bind('<Button-1>', SaveLastClickPos)
    ff_time.bind('<B1-Motion>', Dragging)
    ff_label.bind('<Button-1>', SaveLastClickPos)
    ff_label.bind('<B1-Motion>', Dragging)
    div1_frame.bind('<Button-1>', SaveLastClickPos)
    div1_frame.bind('<B1-Motion>', Dragging)
    div1_label.bind('<Button-1>', SaveLastClickPos)
    div1_label.bind('<B1-Motion>', Dragging)
    div2_frame.bind('<Button-1>', SaveLastClickPos)
    div2_frame.bind('<B1-Motion>', Dragging)
    div2_label.bind('<Button-1>', SaveLastClickPos)
    div2_label.bind('<B1-Motion>', Dragging)
    div3_frame.bind('<Button-1>', SaveLastClickPos)
    div3_frame.bind('<B1-Motion>', Dragging)
    div3_label.bind('<Button-1>', SaveLastClickPos)
    div3_label.bind('<B1-Motion>', Dragging)
    mode_frame.bind('<Button-1>', SaveLastClickPos)
    mode_frame.bind('<B1-Motion>', Dragging)
    slave_mode_label.bind('<Button-1>', SaveLastClickPos)
    slave_mode_label.bind('<B1-Motion>', Dragging)
    master_mode_label.bind('<Button-1>', SaveLastClickPos)
    master_mode_label.bind('<B1-Motion>', Dragging)
    status_frame.bind('<Button-1>', SaveLastClickPos)
    status_frame.bind('<B1-Motion>', Dragging)
    sending_label.bind('<Button-1>', SaveLastClickPos)
    sending_label.bind('<B1-Motion>', Dragging)
    ip_label.bind('<Button-1>', SaveLastClickPos)
    ip_label.bind('<B1-Motion>', Dragging)
    master.bind('<Button-1>', SaveLastClickPos)
    master.bind('<B1-Motion>', Dragging)
    constrols_frame.bind('<Button-1>', SaveLastClickPos)
    constrols_frame.bind('<B1-Motion>', Dragging) """

#-------    

audio_output_selector.configure(values=list(audio_output_devices.values()))
ltc_output_selector.configure(values=list(audio_output_devices.values()))
mtc_output_selector.configure(values=list(mtc_output_devices.values()))

update_thread=Thread(target=update_timecode_labels())
update_thread.start()

update_net_thread=Thread(target=update_network_satus())
update_net_thread.start()

blink_thread=Thread(target=blink_on_pause())
blink_thread.start()

if mode=="slave":
    recive_timecode()

app.protocol("WM_DELETE_WINDOW", cerrar_app)
app.mainloop()

