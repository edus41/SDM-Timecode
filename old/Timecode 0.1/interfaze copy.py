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
            midi_device.sendMTC(add_tcs(mtc_offset,tc,fps))
            
        if ltc_switch_state:
            audiodata = LTC.make_ltc_audio(add_tcs(ltc_offset,tc,fps))
            ltc_audio_device.play(audiodata)
            
        servidor.send_to_all({"fps": fps, "start_timecode": start_timecode, "tc": str(tc), "is_playing": is_playing})
        app.after(1000 // fps, generar_timecode)

        
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

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
  
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

