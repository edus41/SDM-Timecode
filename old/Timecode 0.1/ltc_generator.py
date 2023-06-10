import numpy as np
from timecode import Timecode
import pyaudio


def bitstring_to_bytes(s, bytecount=1, byteorder="big"):
    return int(s, 2).to_bytes(bytecount, byteorder)


def units_tens(n):
    return n % 10, int(n / 10)


# binary, little-endian
def ble(n, bits=8):
    # terminal condition
    retval = ""
    if n == 0:
        retval = "0"
    else:
        retval = str(n % 2) + ble(n // 2, None)
    if bits is None:
        return retval
    else:
        return (retval + ("0" * bits))[0:bits]


def ltc_encode(timecode, as_string=False):
    LTC = ""
    HLP = ""
    hrs, mins, secs, frs = timecode.frames_to_tc(timecode.frames)
    frame_units, frame_tens = units_tens(frs)
    secs_units, secs_tens = units_tens(secs)
    mins_units, mins_tens = units_tens(mins)
    hrs_units, hrs_tens = units_tens(hrs)

    # frames units / user bits field 1 / frames tens
    LTC += ble(frame_units, 4) + "0000" + ble(frame_tens, 2)
    HLP += "---{u}____-{t}".format(u=frame_units, t=frame_tens)

    # drop frame / color frame / user bits field 2
    LTC += "00" + "0000"
    HLP += "__" + "____"

    # secs units / user bits field 3 / secs tens
    LTC += ble(secs_units, 4) + "0000" + ble(secs_tens, 3)
    HLP += "---{u}____--{t}".format(u=secs_units, t=secs_tens)

    # bit 27 flag / user bits field 4
    LTC += "0" + "0000"
    HLP += "_" + "____"

    # mins units / user bits field 5 / mins tens
    LTC += ble(mins_units, 4) + "0000" + ble(mins_tens, 3)
    HLP += "---{u}____--{t}".format(u=mins_units, t=mins_tens)

    # bit 43 flag / user bits field 6
    LTC += "0" + "0000"
    HLP += "_" + "____"

    # hrs units / user bits field 7 / hrs tens
    LTC += ble(hrs_units, 4) + "0000" + ble(hrs_tens, 2)
    HLP += "---{u}____--{t}".format(u=hrs_units, t=hrs_tens)

    # bit 58 clock flag / bit 59 flag / user bits field 8
    LTC += "0" + "0" + "0000"
    HLP += "_" + "_" + "____"

    # sync word
    LTC += "0011111111111101"
    HLP += "################"
    if as_string:
        return LTC
    else:
        return bitstring_to_bytes(LTC, bytecount=10)


p = pyaudio.PyAudio()

output_device_index = 5


def getAudioDevices():
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get("deviceCount")

    for i in range(0, numdevices):
        if (
            p.get_device_info_by_host_api_device_index(0, i).get("maxOutputChannels")
        ) > 0:
            print(
                "Output Device id ",
                i,
                " - ",
                p.get_device_info_by_host_api_device_index(0, i).get("name"),
            )


def setAudioDevice(device_id):
    output_device_index = device_id


# Abrir un flujo de audio utilizando el dispositivo de salida seleccionado
stream = p.open(
    output_device_index=output_device_index,
    format=pyaudio.paInt16,
    channels=1,
    rate=44100,
    output=True,
)


def make_ltc_audio(timecode):
    rate = 44100
    fps = 25.0
    duration = 1 / fps  # Duración en segundos
    fmt = "pcm_s16le"
    bits = 16
    on_val = 32767
    off_val = -32768
    total_samples = int(rate * duration)
    bytes_per_sample = bits // 8
    total_bytes = total_samples * bytes_per_sample

    tc = Timecode(fps, timecode)
    tc_encoded = []
    # print("PREPARING MIDI TIMECODE BYTES:")
    # print(f"| {start}\n| {fps} fps\n| {duration} secs")
    # print("Generating Timecode Stream")
    for i in range(int(duration * fps) + 1):
        e = ltc_encode(tc, as_string=True)
        tc_encoded.append(e)
        tc.next()

    tc_encoded = "".join(tc_encoded)

    # print('Generating "Double Pulse" Data Stream')
    double_pulse_data = ""
    next_is_up = True
    for byte_char in tc_encoded:
        if byte_char == "0":
            if next_is_up:
                double_pulse_data += "11"
            else:
                double_pulse_data += "00"
            next_is_up = not next_is_up
        else:
            double_pulse_data += "10" if next_is_up else "01"

    # print("Creating PCM Data Stream")
    audio_data = np.zeros(total_samples, dtype=np.int16)

    for sample_num in range(total_samples):
        ratio = sample_num / total_samples
        double_pulse_position = len(double_pulse_data) * ratio
        dpp_intpart = int(double_pulse_position)
        this_val = int(double_pulse_data[dpp_intpart])

        if this_val == 1:
            sample = on_val
        else:
            sample = off_val

        audio_data[sample_num] = sample
    return audio_data.tobytes()
