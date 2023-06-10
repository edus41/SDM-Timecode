from customtkinter import *
from timecode import Timecode
import datetime
import threading
import time

from pathlib import Path
from PIL import Image
from ctypes import windll, byref, sizeof, c_int

import ltc_generator as LTC
from timecode_tools import *
from Obtain_Ips import *
from py_audio_class import AudioDevice
from py_midi_class import MidiDevice
from Server import Servidor
from Client import Cliente



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
all_ips=obtain_personal_ips()
current_ip="localhost"
servidor = Servidor()
cliente = Cliente()

servidor._iniciar()
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
            if servidor.iniciado: 
                update_status_labels("WAITING","amarillo")
            else:
                update_status_labels("OFFLINE","rojo")
    else:
        if cliente.conectado:
                update_status_labels("LISENING","green")
        else:
            if cliente.iniciado: 
                update_status_labels("LOOKING","amarillo")
            else:
                update_status_labels("OFFLINE","rojo")
    app.after(100, update_network_satus)    
        
def set_master_mode():
    global mode
    if mode == "master":
        return
    if cliente.iniciado:
        cliente.detener()
    mode = "master"
    set_mode_interfaze()
    time.sleep(1)
    servidor._iniciar()

def set_slave_mode():
    global mode
    if mode == "slave":
        return
    if servidor.iniciado:
        servidor.detener()
    mode="slave"
    set_mode_interfaze()
    time.sleep(1)
    cliente._iniciar()
    
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
    
def recive_timecode():
    global tc
    global fps
    
    if cliente.conectado and mode=="slave":
        mensaje = cliente.recibir_mensaje()
        print(mensaje)
        fps = mensaje["fps"]
        tc = Timecode(fps,mensaje["tc"])
        
        if mtc_switch_state:
            midi_device.sendMTC(add_tcs(mtc_offset,tc,fps))
        if ltc_switch_state:
            audiodata=LTC.make_ltc_audio(add_tcs(ltc_offset,tc,fps))
            ltc_audio_device.play(audiodata)
    app.after(1000 // fps, recive_timecode)

def generar_timecode():
    global tc
    if is_playing:
        tc.next()
        
        if mtc_switch_state:
            midi_device.sendMTC(add_tcs(mtc_offset,tc,fps))
        if ltc_switch_state:
            audiodata=LTC.make_ltc_audio(add_tcs(ltc_offset,tc,fps))
            ltc_audio_device.play(audiodata)

        servidor._enviar_a_todos(mensaje={"fps": fps, "start_timecode": start_timecode, "tc": str(tc), "is_playing": is_playing})
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
    if servidor.iniciado:
        servidor.detener()
    if cliente.iniciado:
        cliente.detener()
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

####--- mucho codigo tkinter.....


update_timecode_labels()
update_network_satus()
blink_on_pause()
if mode=="slave":
    recive_timecode()

app.protocol("WM_DELETE_WINDOW", cerrar_app)
app.mainloop()

