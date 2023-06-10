def MTC_send(timecode, midi_out):
    timecode_str = str(timecode)
    hh = int(timecode_str[:2])
    mm = int(timecode_str[3:5])
    ss = int(timecode_str[6:8])
    ff = int(timecode_str[9:])
    
    digit1 = ff - 16 if ff >= 16 else ff
    digit2 = 17 if ff >= 16 else 16
    digit3 = ss - (ss // 16) * 16 + 32 if ss >= 16 else ss + 32
    digit4 = ss // 16 + 48
    digit5 = mm - (mm // 16) * 16 + 64 if mm >= 16 else mm + 64
    digit6 = mm // 16 + 80
    digit7 = hh - (hh // 16) * 16 + 96 if hh >= 16 else hh + 96
    digit8 = hh // 16 + 114

    midi_out.write_short(0xF1, digit1)
    midi_out.write_short(0xF1, digit2)
    midi_out.write_short(0xF1, digit3)
    midi_out.write_short(0xF1, digit4)
    midi_out.write_short(0xF1, digit5)
    midi_out.write_short(0xF1, digit6)
    midi_out.write_short(0xF1, digit7)
    midi_out.write_short(0xF1, digit8)

