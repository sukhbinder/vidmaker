#!/usr/bin/env python
# coding: utf-8

# In[34]:


import os
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from dateutil.parser import parse


# In[35]:


def get_breaks(day, folder=r"/Users/sukhbindersingh/Desktop/200video/front", startswith="2023", stop=65):
    os.chdir(folder)
    files = os.listdir(folder)
    days= list(set(f[:8] for f in files if f.startswith(startswith)))
    dayf = [f for f in files if f.startswith(day)]
    dayf.sort()
    nov = len(dayf)
    dd = np.array([parse(d.split("_")[0]).timestamp() for d in dayf])
    ddr = np.roll(dd,-1)
    diff = ddr-dd
    breaks=[i for i, d in enumerate(diff) if d>stop]
    breaks.append(nov)
    return dayf,breaks


# In[42]:


def all_videos_by_days(folder=r"/Users/sukhbindersingh/Desktop/200video/front", startswith="2023", fileprefix="DTV_", break_at=65):
    os.chdir(folder)
    files = os.listdir(folder)
    print(len(files))
    days= list(set(f[:8] for f in files if f.startswith(startswith)))
    days.sort()
    print(days)
    
    for day in days:
        print("Working on {}".format(day))
        with ThreadPoolExecutor(max_workers=1) as exe:
            exe.submit(get_travel_video_by_day_breaks,day,folder=folder, startswith=startswith, fileprefix=fileprefix,stop=break_at)


# In[43]:


def get_travel_video_by_day_breaks(day, folder=r"/Users/sukhbindersingh/Desktop/200video/front", startswith="2023", stop=65,
                                fileprefix="daytravel_video"):
    dayf, breaks = get_breaks(day,folder, startswith,stop)
    beg =0
    print(breaks)
    for i in breaks:
        fname="{0}_{1}_{2}.mp4".format(fileprefix, day,beg)
        iret=make_video(dayf[beg:i+1],fname)
        beg=i+1


# In[44]:


def make_video(files, fname):
    with open("mylist.txt", "w") as fout:
        for f in files:
            if os.path.exists(f):
                fout.write("file {}\n".format(f))
    cmdline= "ffmpeg -f concat -safe 0 -i mylist.txt -c copy {0}".format( fname)
    print(cmdline)
    iret=os.system(cmdline)
    print(iret)
    return iret


# # All run

# In[ ]:




def combine_vides(folder, startswith="IMG", fileprefix="DayVideos"):
    #os.chdir(folder)
    files = os.listdir(folder)
    files.sort()
    files = [os.path.join(folder,f) for f in files if f.startswith(startswith)]
    fname="Combined_videos_{0}.mp4".format(fileprefix)
    make_video(files, fname)
# In[ ]:


# for pa in ["24aug"]:
#     folder = r"/Users/sukhbindersingh/Desktop/dadPhone/{}".format(pa)
#     prefix = "Dad_phone_{}_".format(pa)
#     combine_vides(folder=folder, startswith="video_", fileprefix=prefix)


#all_videos_by_days(folder=r"/Users/sukhbindersingh/Desktop/200video/front", startswith="20220828", fileprefix="KotiligeswaraTempleMarkendeyaHillDashcam")

# all_videos_by_days(folder=r"/Users/sukhbindersingh/Desktop/200video/front", startswith="20220912", fileprefix="Aman_bday_trip_")

if __name__ == "__main__":
    # fdir = r"/Users/sukhbindersingh/Desktop/youtube/GyatriMissonfoundation"
    # # files = [os.path.join(fdir, f) for f in os.listdir(fdir)]
    # # files.sort()
    # with open(os.path.join(fdir,"orderfiles.txt" ), "r") as fin:
    #     files = fin.readlines()

    # files = [os.path.join(fdir, f.strip()) for f in files]
    # make_video(files, "Combined_videos_gyatri_mission_foundations_videos.mp4")
    all_videos_by_days()