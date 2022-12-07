
import moviepy.editor as mpy
import os
import argparse
import numpy as np
from dateutil.parser import parse

from concurrent.futures import ThreadPoolExecutor


def makedayvideo(files, day):
    dayf = [f for f in files if f.startswith(day)]
    dayf.sort()
    nov = len(dayf)
    print("No of files :", nov )
    lls = list(range(0,nov,70))
    lls.append(nov+1)
    last=0
    for i in lls[1:]:
        dayff = dayf[last:i]
        last=i
        vc =[]
        for vid in dayff:
            a=mpy.VideoFileClip(vid)
            vc.append(a)
        clip = mpy.concatenate_videoclips(vc)
        clip.write_videofile("final_{0}_till_{1}.mp4".format(day,i), temp_audiofile="out.m4a", audio_codec="aac")
        _=[a.close() for a in vc]
        del vc, clip


def all_videos_by_days(folder=r"/Users/sukhbindersingh/Desktop/200video/front", year="2022"):
    os.chdir(folder)
    files = os.listdir(folder)
    print(len(files))
    days= list(set(f[:8] for f in files if f.startswith(year)))
    days.sort()
    print(days)
    
    for day in days:
        print("Working on {}".format(day))
        with ThreadPoolExecutor(max_workers=1) as exe:
            exe.submit(makedayvideo, files, day)


# cardfolder=r'/Volumes/NONAME/DCIM/200video/front'
# cfiles = os.listdir(cardfolder)

# cfiles = [os.path.join(cardfolder, f) for f in cfiles]

def get_travel_section(dayf, filename="travel_vid.mp4", beg_time=5, end_time=6):
    """
    # for getting sections of video out from a series of vides.

    """
    vc=[]
    for vid in dayf:
        a= mpy.VideoFileClip(vid)
        if a.duration <=beg_time:
            b=a
        else:
            b = a.subclip(beg_time,end_time)
        vc.append(b)
    print(len(vc))
    clip = mpy.concatenate_videoclips(vc)
    clip.write_videofile(filename)
    _=[a.close() for a in vc]


def get_travel_section_by_time(day, folder=r"/Users/sukhbindersingh/Desktop/200video/front", startswith="2022", stop=65,
                                fileprefix="travel_video", beg_time=5, end_time=6):
    """
    day given as YYYYMMDD
    """
    os.chdir(folder)
    files = os.listdir(folder)
    days= list(set(f[:8] for f in files if f.startswith(startswith)))
    dayf = [f for f in files if f.startswith(day)]
    dayf.sort()
    nov = len(dayf)
    print(nov)
    # dd = np.asarray([int(d[8:12]) for d in dayf])
    # dd = np.asarray([int(d[8:11])*60 + int(d[10:12]) for d in dayf])
    dd = np.array([parse(d.split("_")[0]).timestamp() for d in dayf])
    ddr = np.roll(dd,-1)
    diff = ddr-dd
    breaks=[i for i, d in enumerate(diff) if d>stop]
    breaks.append(nov)
    beg =0
    print(breaks)
    for i in breaks:
        fname="{0}_{1}_{2}.mp4".format(fileprefix, day,beg)
        get_travel_section(dayf[beg:i+1], filename=fname, beg_time=beg_time, end_time=end_time)
        beg = i+1



if __name__ == "__main__":
    # get_travel_section_by_time("20220726",folder=r"/Users/sukhbindersingh/Desktop/200video/front", fileprefix="kishoreHome")
    all_videos_by_days()

"""

get average of a frame.


def get_average(vid, outfname=None):
    ...:     if outfname is None:
    ...:         outfname = "av_frame{}_.png".format(os.path.basename(vid))
    ...:     clip = VideoFileClip(vid)
    ...:     fps= 1.0 # take one frame per second
    ...:     nframes = clip.duration*fps # total number of frames used
    ...:     total_image = sum(clip.iter_frames(fps,dtype=float,logger='bar'))
    ...:     average_image = ImageClip(total_image/ nframes)
    ...:     average_image.save_frame(outfname)


"""


"""
Making vide of pnng files

import os
import moviepy.editor as mpy

files = os.listdir(".")
len(files)

pngfiles =[f for f in files if f.endswith(".png")]
len(pngfiles)
pngfiles.sort()

clips= [ mpy.ImageClip(f).set_duration(1) for f in pngfiles]
video = mpy.concatenate(clips, method="compose")
video.write_videofile("Clips_from_dashcam.mp4", fps=24)


"""

# import moviepy.editor as mpy
# import os

# allfiles = os.listdir("path/to/video/files")
# mp4files = [f for f in allfiles if f.endswith(".mp4")]
# vc = []
# output_fname = "DashCam_day_22June2022.mp4"
# for vid in mp4files:
#     a = mpy.VideoFileClip(vid)
#     vc.append(a)
# clip = mpy.concatenate_videoclips(vc)
# clip.write_videofile(output_fname)
# # if you want the audio too use the below line
# #clip.write_videofile(output_fname, temp_audiofile="out.m4a", audio_codec="aac")
# _ = [a.close() for a in vc]
