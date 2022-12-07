#!/usr/bin/env python
# coding: utf-8

# In[1]:


import moviepy.editor as mpy
import numpy as np
import os
import subprocess
import json

# In[2]:


import random
from copy import deepcopy
from itertools import cycle
from collections import namedtuple
from collections import defaultdict


# ## Get Beats and Duration

# In[3]:


def get_files(fdir, starts_with, sort_by_date=False):
    files = os.listdir(fdir)
    mov = [os.path.join(fdir, f) for f in files if f.startswith(
        starts_with)]  # or f.startswith("VID")]
    mov.sort()

    if sort_by_date:
        # sort by creation date
        mov.sort(key=os.path.getmtime)
    return mov


# In[4]:


def beats_clip(audfile):
    song_name = os.path.basename(audfile)
    print(song_name)

    snd = mpy.AudioFileClip(audfile)
    new_audioclip = mpy.CompositeAudioClip([snd])
    return song_name, new_audioclip


def beat_times(beats_track, threshold=0.2):
    times = np.genfromtxt(beats_track, delimiter="\t",
                          usecols=0, dtype=np.float)
    times.sort()
    print(np.diff(times, 1).min(), np.diff(
        times, 1).max(), np.diff(times, 1).mean())

    diff = np.empty(times.shape)
    diff[0] = np.inf
    diff[1:] = np.diff(times)
    mask = diff > threshold

    new_times = times[mask]
    # print(new_times)

    dur = np.diff(new_times, 1)
    # print(dur)
    print(dur.min(), dur.max(), dur.mean())
    return new_times, dur


def get_audioclip_n_beats(audfile, beats_track, threshold=0.2):
    new_time, dur = beat_times(beats_track, threshold)
    song_name, new_audioclip = beats_clip(audfile)
    return song_name, new_audioclip, new_time, dur


# #  Load Videos and Subclips Highlights

# In[5]:


def load_videos(mov):
    vids = {}
    for file in mov:
        try:
            vids[file] = mpy.VideoFileClip(file)
        except Exception as ex:
            print(file, "something gone wrong")
            mov.remove(file)
            continue
    return vids, mov


def get_non_linear_subclips(mov, vids, dur, ntime):
    vtype = "NL"
    subclips = []
    NUMofClips = 2
    # speeds = np.random.randint(2, size=ntime)
    ndur = len(dur)
    speeds = np.ones(ndur)
    speeds[dur < 0.3] = 0
    for i in range(ntime-1):
        span = dur[i]
        speed = speeds[i]
        while True:
            file = np.random.choice(mov)
            try:
                duration = vids[file].duration
            except Exception as ex:
                print(file, "wrong")
                continue
            if speed == 1:
                span = span/2
            start_time = np.random.uniform(0, duration-span)
            if duration-span > 0:
                break
        # remove file for less than 2 sec duration
        if int(duration/2) <= 1:
            mov.remove(file)
        if span > 4:  # Remove if a big cut has been done from a file
            mov.remove(file)
        end_time = start_time+span
        subclips.append((file, start_time, end_time, speed))
    return subclips


def get_linear_subclips(mov, vids, dur, ntime):
    vtype = "L"
    subclips = []
    # speeds = np.random.randint(2, size=ntime)
    ndur = len(dur)
    speeds = np.ones(ndur)
    speeds[dur < 0.3] = 0

    cc = cycle(mov)
    change = True
    selected_time = {}
    for i in range(ntime-1):
        span = dur[i]
        speed = speeds[i]
        while True:
            file = next(cc)
            try:
                duration = vids[file].duration
            except Exception as ex:
                print(file, "wrong")
                continue
            if speed == 1:
                span = span/2
            start_time = np.random.uniform(0, duration-span)
            if duration-span > 0:
                break
        # remove file for less than 2 sec duration
    #     if int(duration/2) <=1:
    #         mov.remove(file)
        # remove if

        end_time = start_time+span
        subclips.append((file, start_time, end_time, speed))
    return subclips


def get_subclips(vids, subclips):
    vc = []
    for file, st, et, speed, in subclips:
        vid = vids[file]
        width = vid.w
        if width != 1920:
            vid = vid.resize(width=1920)
        clip = vid.subclip(st, et)
        if speed == 1:
            clip = clip.speedx(factor=0.5)
        vc.append(clip)
    return vc


def get_subclips_2(subclips):
    vc = []
    for file, st, et, speed, in subclips:
        vid = mpy.VideoFileClip(file)
        width = vid.w
        if width != 1920:
            vid = vid.resize(width=1920)
        clip = vid.subclip(st, et)
        if speed == 1:
            clip = clip.speedx(factor=0.5)
        vc.append(clip)
    return vc

def generate_video_hl(vc, new_audioclip, outfile, fps=30, fadeout=1, afadeout=2, clip=None):
    if clip is None:
        clip = mpy.concatenate_videoclips(vc, method="compose")
        clip = clip.fadeout(fadeout)

    try:
        audiofile = os.path.join(os.path.dirname(outfile), "out_audio.mp3")
        clip.audio.write_audiofile(audiofile, fps=44100)
    except Exception as ex:
        print(ex)
        pass


    clipduration = clip.duration
    min,sec = divmod(clipduration,60)
    print("Duration of generated clip is {0:.2f} seconds or {1:.0f}:{2:.0f} ".format(clipduration,min,sec))
    if new_audioclip.duration < clipduration:
        naudio = new_audioclip.audio_loop(
            duration=clipduration).audio_fadeout(afadeout)
    else:
        naudio = new_audioclip.set_duration(
            clipduration).audio_fadeout(afadeout)

    clip_withsound = clip.set_audio(naudio)
    clip_withsound.write_videofile(
        outfile, temp_audiofile="out.m4a", audio_codec="aac", fps=fps)
    clip.close()
    return clip_withsound

# _=[a.close() for a in vids]


# # Linear Video

# In[6]:


def get_events(vdurs, intervals):
    ndur = len(intervals)
    tt = 0
    out = defaultdict(list)
    istart = 0
    for iv, vv in enumerate(vdurs):
        tt = 0
        count = 0
        for ip, ii in enumerate(intervals[istart:]):
            #             print(iv,vv,ip,ii)
            count += 1
            if tt+ii+1 > vv:# add one second so there is a gap
                break
            if count > 5:
                break
            tt += ii
        out[iv] = intervals[istart:ip+istart]
        istart = ip+istart
        # print(out[iv])
        if istart+1 >= ndur:
            istart = 0  # restart
    return out

def correct_times(res):
    res = np.array(res)
    shape = res.shape
    resa = res.ravel()
    d = np.diff(resa)
    nd = len(d)
    d[d>0]=0
    resa[:nd]=resa[:nd]+d
    resa = resa.reshape(shape).tolist()
    return resa


def start_time(vv, ii):
    ilen = len(ii)
    iend = 0
    if ilen != 0:
        iend = ii[-1]
    # out_ar = np.array([0, vv/4, vv/3, vv/2, vv-iend])
    out_ar, s= np.linspace(0, vv,ilen, endpoint=False,retstep=True )
    ret_ = list(zip(out_ar[:ilen], ii+out_ar[:ilen]))
    print(vv, sum(ii), ii, s, ii>s)
    if sum(ii>s) >0:
        ret_ = correct_times(ret_)
    print(ret_)

    return ret_


def get_subclips_linear(mov, vids, intervals, vdurs=None):
    if vdurs is None:
        vdurs = np.array([vids[file].duration for file in mov])
    
    out = get_events(vdurs, intervals)
    subclips = defaultdict(list)
    for k, i in out.items():
        subclips[mov[k]] = start_time(vdurs[k], i)
    return subclips


def get_linear_clips(subclips, mov, vids):
    vc = []
    for file in mov:
        vals = subclips[file]
        vid = vids[file]
        # temporary change
        width = vid.w
        if width != 1920:
            vid = vid.resize(width=1920)

        if len(vals) == 0:
            vid = vid.speedx(factor=0.5)
            vc.append(vid)

        for st, et in vals:
            span = et-st
            span = span/2
            index = np.random.binomial(1, 0.3)
            if index == 1:
                clip = vid.subclip(st, et)
            else:
                et = st+span
                clip = vid.subclip(st, et)
                clip = clip.speedx(factor=0.5)
            vc.append(clip)
    return vc


def generate_linear_clip(vc, new_audioclip, outfile, fps=30, fadeout=1, afadeout=2):
    clip = mpy.concatenate_videoclips(vc, method="compose")

    clipduration = clip.duration
    print("Duration of generated clip is {}".format(clipduration))
    if new_audioclip.duration < clipduration:
        naudio = new_audioclip.audio_loop(
            duration=clipduration).audio_fadeout(afadeout)
    else:
        naudio = new_audioclip.set_duration(
            clipduration).audio_fadeout(afadeout)

    clip = clip.fadeout(1)
    clip_withsound = clip.set_audio(naudio)
    clip_withsound.write_videofile(
        outfile, temp_audiofile="out.m4a", audio_codec="aac", fps=fps)
    return clip_withsound


# # HIGHLIGHTS MAIN Code
#

# In[7]:


def generate_highlights(fdir, audfile, beats_track,
                        clip_time=60, vtype="L", starts_with="IMG",
                        sort_by_date=False, fps=30, fadeout=1, afadeout=2):

    assert vtype in ["L", "NL"], "Vtype should be L or NL"

    folder_name = os.path.basename(fdir)
    mov = get_files(fdir, starts_with, sort_by_date=sort_by_date)
    gc = generate_highlights_with_mov(mov, audfile, beats_track,
                                      clip_time=clip_time, vtype=vtype, fps=fps, starts_with="IMG", fadeout=fadeout, afadeout=afadeout, folder_name=folder_name)


def generate_highlights_with_mov(mov, audfile, beats_track,
                                 clip_time=60, vtype="L", starts_with="IMG",
                                 fps=30, fadeout=1, afadeout=2, folder_name=None):

    CMDLINE = ["pkill", "-f", "ffmpeg"]

    print("No of files:", len(mov))

    if folder_name is None:
        folder_name = os.path.basename(os.path.dirname(mov[0]))

    song_name, new_audioclip, new_time, dur = get_audioclip_n_beats(
        audfile, beats_track, threshold=0.2)

    if dur.cumsum()[-1] < clip_time:
        # If clip_time is big take maximum duration
        clip_time = dur.cumsum()[-1]

    print("Clip Time is :", clip_time)
    ntime = np.where(dur.cumsum() >= clip_time)[0][0]
    print("ntime is ", ntime)

    vids, mov = load_videos(mov)
    vlen = len(vids)
    print("No of  vids files:", vlen)

    if ntime > len(vids):
        print("Taking ntime as {}".format(vlen))
        ntime = vlen

    if vtype == "NL":
        subclips = get_non_linear_subclips(mov, vids, dur, ntime)
    elif vtype == "L":
        subclips = get_linear_subclips(mov, vids, dur, ntime)

    print("No of  subclips files:", len(subclips))

    sj_fname = "{1}_clips_{0}_{2}.json".format(folder_name, vtype, starts_with)
    write_subclips_json(sj_fname, subclips)


    vc = get_subclips(vids, subclips)

    print("No of  VC files:", len(vc))

    outfile = "{3}_{2}_Automated_movie_{0}_with_{1}.mp4".format(
        folder_name, song_name, starts_with, vtype)

    print(f"Be Patient {outfile} is being generated.....")
    generated_clip = generate_video_hl(
        vc, new_audioclip, outfile, fps=fps, fadeout=fadeout, afadeout=afadeout)
    print(f"{outfile} generated")
    iret = subprocess.call(CMDLINE)
    print(iret)
    return generated_clip


def write_subclips_json(fname, subclips):
    with open(fname, "w") as fout:
        json.dump({"subclips": subclips}, fout)


# # Linear Continuous Clips

# In[8]:


def generate_continuous(fdir, audfile, beats_track, starts_with="IMG",
                        sort_by_date=False, fps=30, fadeout=1, afadeout=2, threshold=0.2):

    folder_name = os.path.basename(fdir)
    mov = get_files(fdir, starts_with, sort_by_date=sort_by_date)
    gc = generate_continues_files(mov, audfile, beats_track, starts_with, fps=fps, fadeout=fadeout,
                                  afadeout=afadeout, threshold=threshold, folder_name=folder_name)
    return gc


def generate_continues_files(mov, audfile, beats_track, starts_with="IMG", fps=30, fadeout=1, afadeout=2,
                             threshold=0.2, folder_name=None):

    if folder_name is None:
        folder_name = os.path.basename(os.path.dirname(mov[0]))

    print("No of files:", len(mov))

    song_name, new_audioclip, new_time, dur = get_audioclip_n_beats(
        audfile, beats_track, threshold=threshold)

    vids, mov = load_videos(mov)
    print("No of  vids files:", len(vids))

    subclips = get_subclips_linear(mov, vids, dur)
    sums = sum([len(e) for i, e in subclips.items()])
    print("No of  subclips files:", sums)

    sj_fname = "{2}_{1}_subclips_{0}.mp4".format(
        folder_name, starts_with, vtype)
    write_subclips_json(sj_fname, subclips)

    vc = get_linear_clips(subclips, mov, vids)

    print("No of  VC files:", len(vc))
    vtype = "Linear"

    outfile = "{3}_{2}_Automated_movie_{0}_with_{1}.mp4".format(
        folder_name, song_name, starts_with, vtype)
    print(f"Be Patient {outfile} is being generated.....")

    generated_clip = generate_linear_clip(
        vc, new_audioclip, outfile, fps=30, fadeout=1, afadeout=2)
    return generated_clip


# # .

# In[9]:

def read_orderfile(fname):
    # fdir=r"/Users/sukhbindersingh/Desktop/youtube/kolaramma_temple"
    fname = os.path.abspath(fname)
    fdir = os.path.dirname(fname)
    with open(fname, "r") as fin:
        files = fin.readlines()

    mov = [os.path.join(fdir, f.strip()) for f in files]
    return mov

def get_non_linear_subclips_VDURS(mov, vdurs, dur, ntime ):
    vtype="NL"
    subclips=[]
    NUMofClips=2
    # speeds = np.random.randint(2, size=ntime)
    ndur = len(dur)
    cc = cycle(dur)
    for i in range(ntime-1):
        span=next(cc)
        while True:
            file = np.random.choice(mov)
            try:
                duration = vdurs[file]
            except Exception as ex:
                print(file, "wrong")
                continue
            start_time = np.random.uniform(0,duration-span)
            if duration-span >0:
                break
        # remove file for less than 2 sec duration 
        if int(duration/2) <=1:
            mov.remove(file)
        if span >4: # Remove if a big cut has been done from a file
            mov.remove(file)
        end_time = start_time+span
        subclips.append((file, start_time, end_time,0))
    return subclips

# # Ignore this

# In[ ]:


# vids, mov = load_videos(mov)


# # In[ ]:


# vdurs= np.array([vids[file].duration for file in mov])


# In[ ]:


# vmean=vdurs.mean()
# vmean


# In[ ]:

# Intervals...
rnd = np.random.default_rng()
# . lessthan=vdurs<=3   add all speed 0.5
#  between >3 to 10  split 3 random.uniform(2,4,size=3)
# between >10 to 30 split 5 random.uniform(2,10, size=5)
# between >30 to 60 split 5 random.uniform(5,15, size=5)
# >60 random.uniform(2,20, size=8)


def get_intervals(vdur):

    intervals = []
    speeds = []

    if vdur <= 3:
        intervals.append(vdur)
        speeds.append(0.5)
        return intervals, speeds

    if vdur > 3 and vdur <= 10:
        size = 3
        a, b = 2, 4
    elif vdur > 10 and vdur <= 30:
        size = 5
        a, b = 2, 10
    elif vdur > 30 and vdur <= 60:
        size = 5
        a, b = 5, 15
    elif vdur > 60:
        size = 8
        a, b = 2, 20

    count = 0
    while True:
        intervals = rnd.uniform(a, b, size=size)
        speeds = np.ones(size)
        speeds[intervals <= 2.5] = 0.5
        if intervals.sum() < vdur-1:  # less than vdur-1 sec
            break
        count += 1
        if count > 50:
            size = size-1
            count = 0

    return intervals, speeds


def get_subclips_from_durs(mov, vdurs):
    subclips = defaultdict(list)
    for m, vdur in zip(mov, vdurs):
        inter, speeds = get_intervals(vdur)
        subclips[m] = list(zip(inter, speeds))
    return subclips


def get_linear_clips_no_intervals(subclips, mov, vids):
    vc = []
    for file in mov:
        vals = subclips[file]
        vid = vids[file]
        # temporary change
        width = vid.w
        if width != 1920:
            vid = vid.resize(width=1920)

        est = 0
        for dur, speed in vals:
            st = est
            et = est+dur
            if speed == 1:
                clip = vid.subclip(st, et)
            else:
                clip = vid.subclip(st, et)
                clip = clip.speedx(factor=0.5)
            vc.append(clip)
            est = et+0.1
    return vc


apindpind = r"/Users/sukhbindersingh/Documents/PindPind.txt"
mpindpind = r"/Users/sukhbindersingh/Downloads/Pind Pind - Gippy Grewal (DJJOhAL.Com).mp3"


# In[ ]:


asarejahan = r"/Users/sukhbindersingh/Documents/sarejahan.txt"
msarejahan = r"/Users/sukhbindersingh/Downloads/y2mate.com - SARE JAHAN SE ACCHA NO COPYRIGHT SONG  INDEPENDENCE DAY SPECIAL  COPYRIGHT FREE MUSIC2021.mp3"


# In[ ]:


# In[ ]:


abeija = r"/Users/sukhbindersingh/Documents/Beijaflor.txt"
mbeija = r"/Users/sukhbindersingh/Downloads/y2mate.com - Beijaflor.mp3"


# In[ ]:


ayoga = r"/Users/sukhbindersingh/Documents/yogastyle.txt"
myoga = r"/Users/sukhbindersingh/Downloads/Yoga Style - Chris Haugen.mp3"


# In[10]:


aflute = r"/Users/sukhbindersingh/Documents/ekOnkarFlute.txt"
mflute = r"/Users/sukhbindersingh/Downloads/y2mate.com - EK ONKAR SATNAM KARTA PURAKH MOOL MANTAR ON FLUTE BY SARDAR BALJINDER SINGH BALLU FLUTE.mp3"


# In[ ]:


ahbd = r"/Users/sukhbindersingh/Documents/happybirthdayJatta.txt"
mhbd = r"/Users/sukhbindersingh/Downloads/PunjabiSongs/Happy Birthday Jatta.mp3"


# In[ ]:


adeadforest = r"/Users/sukhbindersingh/Documents/DeadForest.txt"
mdeadforest = r"/Users/sukhbindersingh/Downloads/Dead Forest - Brian Bolger.mp3"


# In[ ]:


aekonkar = r"/Users/sukhbindersingh/Documents/ekonkar.txt"
mekonkar = r"/Users/sukhbindersingh/Downloads/y2mate.com - Ek Onkar  Copyright Free Devotional background music  Copyright Free Bhajan  Hindi Geeto  Gana.mp3"


# In[ ]:


aragga = r"/Users/sukhbindersingh/Documents/ragga_dance.txt"
mragga = r"/Users/sukhbindersingh/Downloads/Raga - Dance of Music - Aakash Gandhi.mp3"

beats_track = r"/Users/sukhbindersingh/Documents/Viking.txt"
audfile = r"/Users/sukhbindersingh/Downloads/Viking - Aakash Gandhi.mp3"
# In[ ]:


# vc = get_linear_clips_no_intervals(subclips,mov,vids)


# # In[ ]:


# song_name, new_audioclip, new_time, dur = get_audioclip_n_beats(audfile, beats_track, threshold=0.2)
# outfile="Testing_new_linear_pvalley.mp4"
# generated_clip = generate_linear_clip(vc[:20], new_audioclip, outfile, fps=30, fadeout=1, afadeout=2)


# In[ ]:


# vdurs.sum()/60


# # In[ ]:


# # In[ ]:


# if vc:
#     _=[a.close() for a in vc]


# # In[ ]:


# if vids:
#     for i, vid in vids.items():
#         vid.close()


# # In[ ]:


# fdir=r"/Users/sukhbindersingh/Desktop/youtube/KailasaGiri/Kaiwara  National Park"
# gc = generate_highlights(fdir, audfile, beats_track,
#                         clip_time=120, vtype="L", starts_with="IMG",
#                         sort_by_date=False, fps=30, fadeout=1, afadeout=2)


# # In[ ]:


# fdir=r"/Users/sukhbindersingh/Desktop/youtube/kolaramma_temple"
# gc = generate_continuous(fdir, audfile, beats_track,
#                         starts_with="IMG",
#                         sort_by_date=False, fps=30, fadeout=1, afadeout=2, threshold=0.5)


# # In[9]:


# fdir=r"/Users/sukhbindersingh/Desktop/youtube/Gyatri Misson foundation"
# with open(fdir+r"/orderfiles.txt", "r") as fin:
#     files = fin.readlines()

# mov = [os.path.join(fdir,f.strip()) for f in files]


# In[ ]:


# fdir=r"/Users/sukhbindersingh/Desktop/youtube/shree bhoga nandeswaraswami temple"
# mfiles =["IMG_2627.MOV", "IMG_2628.MOV", "IMG_2691.MOV", "IMG_2696.MOV","IMG_2698.MOV","IMG_2699.MOV","IMG_2710.MOV","IMG_2712.MOV","IMG_2786.MOV"]
# mov = [os.path.join(fdir,f) for f in mfiles]
# gc=generate_highlights_with_mov(mov,audfile, beats_track, clip_time=30, vtype="NL" )


# # In[ ]:


# print(len(mov))
# mov


# # Upto here

# In[11]:


# gc = generate_continues_files(mov, audfile, beats_track,
#                         starts_with="ALL",fps=30, fadeout=1, afadeout=2, threshold=0.5)


# # In[ ]:


# gc = generate_continues_files(mov[155:], audfile, beats_track,
#                         starts_with="ALLpart2",fps=30, fadeout=1, afadeout=2)


# # Linear subclips

# In[ ]:


def get_linear_subclips_json(mov, vdurs, dur):
    vtype = "L"
    subclips = []
    # speeds = np.random.randint(2, size=ntime)
    ndur = len(dur)
    speeds = np.ones(ndur)
    speeds[dur < 0.3] = 0

    cc = cycle(mov)
    change = True
    selected_time = {}
    for i in range(ntime-1):
        span = dur[i]
        speed = speeds[i]
        while True:
            file = next(cc)
            try:
                duration = vids[file].duration
            except Exception as ex:
                print(file, "wrong")
                continue
            if speed == 1:
                span = span/2
            start_time = np.random.uniform(0, duration-span)
            if duration-span > 0:
                break
        # remove file for less than 2 sec duration
    #     if int(duration/2) <=1:
    #         mov.remove(file)
        # remove if

        end_time = start_time+span
        subclips.append((file, start_time, end_time, speed))
    return subclips


if __name__ == "__main__":

    vtype = "L"

    # # Select Music

    # In[ ]:

    apindpind = r"/Users/sukhbindersingh/Documents/PindPind.txt"
    mpindpind = r"/Users/sukhbindersingh/Downloads/Pind Pind - Gippy Grewal (DJJOhAL.Com).mp3"

    # In[ ]:

    asarejahan = r"/Users/sukhbindersingh/Documents/sarejahan.txt"
    msarejahan = r"/Users/sukhbindersingh/Downloads/y2mate.com - SARE JAHAN SE ACCHA NO COPYRIGHT SONG  INDEPENDENCE DAY SPECIAL  COPYRIGHT FREE MUSIC2021.mp3"

    # In[ ]:

    # In[ ]:

    abeija = r"/Users/sukhbindersingh/Documents/Beijaflor.txt"
    mbeija = r"/Users/sukhbindersingh/Downloads/y2mate.com - Beijaflor.mp3"

    # In[ ]:

    ayoga = r"/Users/sukhbindersingh/Documents/yogastyle.txt"
    myoga = r"/Users/sukhbindersingh/Downloads/Yoga Style - Chris Haugen.mp3"

    # In[10]:

    aflute = r"/Users/sukhbindersingh/Documents/ekOnkarFlute.txt"
    mflute = r"/Users/sukhbindersingh/Downloads/y2mate.com - EK ONKAR SATNAM KARTA PURAKH MOOL MANTAR ON FLUTE BY SARDAR BALJINDER SINGH BALLU FLUTE.mp3"

    # In[ ]:

    ahbd = r"/Users/sukhbindersingh/Documents/happybirthdayJatta.txt"
    mhbd = r"/Users/sukhbindersingh/Downloads/PunjabiSongs/Happy Birthday Jatta.mp3"

    # In[ ]:

    adeadforest = r"/Users/sukhbindersingh/Documents/DeadForest.txt"
    mdeadforest = r"/Users/sukhbindersingh/Downloads/Dead Forest - Brian Bolger.mp3"

    # In[ ]:

    aekonkar = r"/Users/sukhbindersingh/Documents/ekonkar.txt"
    mekonkar = r"/Users/sukhbindersingh/Downloads/y2mate.com - Ek Onkar  Copyright Free Devotional background music  Copyright Free Bhajan  Hindi Geeto  Gana.mp3"

    # In[ ]:

    aragga = r"/Users/sukhbindersingh/Documents/ragga_dance.txt"
    mragga = r"/Users/sukhbindersingh/Downloads/Raga - Dance of Music - Aakash Gandhi.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/Lifelong.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Lifelong - Anno Domini Beats.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/Contrast.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Contrast - Anno Domini Beats.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/Coast.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Coast - Anno Domini Beats.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/bhangra beats.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/y2mate.com - Punjabi Bahangra Beat  Indian Background Music  No Copyright Music.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/19thfloor.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/19th Floor - Bobby Richards.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/CleannDance.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Clean and Dance - An Jone.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/FindMeHere.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Find Me Here - Patrick Patrikios.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/Beat18Punjabi.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/beat18.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/epicAdventure.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Epic Adventure Cinematic Music _ MOVIE.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/youshould.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/You Should - Patrick Patrikios.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/outOnMySkateboard.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Out On My Skateboard - Mini Vandals.mp3"

    # In[12]:

    beats_track = r"/Users/sukhbindersingh/Documents/Better.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Better - Anno Domini Beats.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/Armsdealer.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Arms Dealer - Anno Domini Beats.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/Shake.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Shake - Anno Domini Beats.mp3"

    # In[11]:

    beats_track = r"/Users/sukhbindersingh/Documents/EverlastingArms.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Leaning On the Everlasting Arms - Zachariah Hickman.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/cashMachine.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Cash Machine - Anno Domini Beats.mp3"

    # In[10]:

    beats_track = r"/Users/sukhbindersingh/Documents/PositiveFuse.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Positive Fuse - French Fuse.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/mridangam.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/y2mate.com - violin and mridangam Indian Instrumental music no copyright.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/Viking.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Viking - Aakash Gandhi.mp3"

    # In[ ]:

    beats_track = r"/Users/sukhbindersingh/Documents/indianBackground.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/y2mate.com - Free Indian Background Music No Copyright  No copyright Indian Music  Copyrightfree music tracks.mp3"

    # In[23]:

    beats_track = r"/Users/sukhbindersingh/Documents/liquidTime.txt"
    audfile = r"/Users/sukhbindersingh/Downloads/Liquid Time - Aakash Gandhi.mp3"

    # In[11]:

    song_name, new_audioclip, new_time, dur = get_audioclip_n_beats(
        audfile, beats_track, threshold=0.2)


# # Load Video files

# In[ ]:

"""
fdir=r"/Users/sukhbindersingh/Desktop/youtube/shree bhoga nandeswaraswami temple"
folder_name = os.path.basename(fdir)
print(folder_name)


# In[ ]:





# # BASH Code to change VID to img
# for f in fdir/VID_*.mp4; do mv $f IMG$f; done

# # Bash code to change resolution to img
# ffmpeg -i movie.mp4 -vf scale=640:360 movie_360p.mp4
# 

# In[ ]:


mov


# In[ ]:


len(mov)


# In[ ]:


subclips


# vc=[]
# for i in range(ntime-1):
#     while True:
#         file=np.random.choice(mov)
#         vid = vids[file]
#         if vid.duration-dur[i]>0:
#             break
#     # remove the file don't select again
#     mov.remove(file)
#     start_time=np.random.uniform(0,vid.duration-dur[i])
#     print(file, dur[i], start_time, start_time+dur[i], vid.duration)
#     clip = vid.subclip(start_time, start_time+dur[i])
#     vc.append(clip)
#     

# In[ ]:


vtype="Linear"


# In[ ]:


print(outfile)


# ## Cleanup

# In[ ]:


new_audioclip.ipython_display()


# In[ ]:


clip.audio=new_audioclip.set_duration(clip.duration)


# In[ ]:


clip.ipython_display(maxduration=230)


# In[ ]:


sc= deepcopy(subclips)


# In[ ]:


sc.sort(key=lambda x: x[0])


# In[ ]:


for file, st,et , sp in sc:
    print(os.path.basename(file), st,et)


# # Automated video for entire 1000km

# In[ ]:


folders =['arkavati-kavery-sangam', 'bambooForest_hesaragata', 
         'kolaramma_temple', 'Markandeya Dam Budikote','Model Village _ bangalore',
        'Nandi Hills','Pyramid_valley','sri_sri_aasaram', 'shree bhoga nandeswaraswami temple']


# In[ ]:


fdir=r"/Users/sukhbindersingh/Desktop/youtube"


# In[ ]:


folders=[r"arkavati-kavery-sangam"]
files = []
# i.endswith(".MOV") or
for f in folders:
    fold = os.path.join(fdir, f)
    fmov = [os.path.join(fold,i) for i in os.listdir(fold) if  i.endswith(".MOV")]
    files.extend(fmov)


# In[ ]:


len(files)


# In[ ]:


rfiles=random.sample(files, k=75)


# In[ ]:


mov=deepcopy(rfiles)


# In[ ]:


folder_name = os.path.basename(fdir)


# In[ ]:


mov


# In[ ]:


vid.duration


# In[ ]:


dur


# In[ ]:


v=vc[0]


# In[ ]:


mov


# In[ ]:


mov


# In[ ]:


vdurs = np.array([vids[file].duration for file in mov])


# In[ ]:


vdurs


# In[ ]:


vdur =vdurs[0]


# In[ ]:


np.round(vdurs/2)


# In[ ]:


dur


# In[ ]:


dur.shape


# In[ ]:


dur[:14]/2


# In[ ]:


dur.shape


# In[ ]:


np.array(vdurs)


# In[ ]:


nocfac=round(dur.mean()*2,1)


# In[ ]:


int(vdurs[0]/nocfac)


# In[ ]:


dur[:8]


# In[ ]:


vvc=[]
st=0.0
for dd in dur[:8]:
    sc = clip.subclip(st, st+dd)
    st = st+dd
    vvc.append(sc)
    


# In[ ]:


cclip = mpy.concatenate_videoclips(vvc)


# In[ ]:


cclip.ipython_display(width=640)


# In[ ]:


sclip=snd.subclip(30)


# In[ ]:


sclip.duration


# In[ ]:


snd.duration


# In[ ]:


dur


# In[ ]:


vdur=vdurs[1]


# In[ ]:


0, vdur/4, vdur/3, vdur/2, vdur


# In[ ]:


dur


# In[ ]:


len(vc)


# In[ ]:


ss =get_subclips(mov, vids, dur)


# In[ ]:


ss


# In[ ]:


fname= r"/Users/sukhbindersingh/Desktop/youtube/Leepakshi/IMG_5298.MOV"


# In[ ]:


vid = mpy.VideoFileClip(fname)


# In[ ]:


vid.duration


# In[ ]:


vid.fps


# In[ ]:


dur =3


# In[ ]:


clip = vid.subclip(0.2, 0.2+dur)


# In[ ]:


clip2= vid.subclip(0.2+dur)


# In[ ]:


clip2.duration


# In[ ]:


clip= clip.speedx(0.5)


# In[ ]:


clip2 = clip2.speedx(24)


# In[ ]:


clipc = mpy.concatenate_videoclips([clip,clip2], method="compose")


# In[ ]:


clipc.ipython_display(width=800, height=600)


# In[ ]:


clip2 = vid.fl_time( lambda t: t+ np.sin(t) , keep_duration=True)


# In[ ]:





# In[ ]:


clip2.ipython_display(width=800, height=600, maxduration=120)


# In[ ]:


"""
