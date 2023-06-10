def tc_to_frames(timecode,fps):
    return sum(f * int(t) for f,t in zip((3600*fps, 60*fps, fps, 1), timecode.split(':')))

def frames_to_tc(frames, fps):
    return '{0:02d}:{1:02d}:{2:02d}:{3:02d}'.format(frames // (3600*fps),
                                                    (frames // (60*fps)) % 60,
                                                    (frames // fps) % 60,
                                                    frames % fps)

    
def add_tcs(tc1, tc2, fps):
    tc1_Total_frames = tc_to_frames(str(tc1), fps)
    tc2_Total_frames = tc_to_frames(str(tc2), fps)
    total_frames = tc1_Total_frames + tc2_Total_frames

    if total_frames >= 24 * 3600 * fps:
        # Si la suma supera 24:00:00:00, devolver 29:59:59:25
        return f'29:59:59:{fps}'

    return frames_to_tc(total_frames, fps)