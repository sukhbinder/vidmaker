import moviepy.editor as mpy
import os
import random
import textwrap
import numpy as np
import vidmake.app as app
import subprocess
import argparse
import moviepy.video.fx.all as vfx




_HERE = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.join(_HERE, "..", "assets")

notification_fname = os.path.join(_ASSETS, "notification.mp3")
subcribe_fname = os.path.join(_ASSETS, "subscribe.mp3")

def create_shorts_from_vid(fname, startat=0.0, crop_ratio=1):
    clip = mpy.VideoFileClip(fname)
    clip = clip.subclip(t_start=startat)
    w, h = clip.size

    # crop_ratio = 1 #  4/5 # 9/16
    crop_width = h * crop_ratio
    x1, x2 = (w-crop_width)//2, (w+crop_width)//2
    cclip = clip.crop(x1=x1, y1=0, x2=x2, y2=h)

    return cclip


def addcomment(comment, size=20):
    lines = textwrap.wrap(comment, width=size)
    nline = len(lines)
    new_comment = "\n".join(lines)
    return new_comment, nline


def zoom_in_out(t):
    """Defines a zoom in and out function based on a sin wave"""
    return 0.9 + 0.3*np.sin(t/3)


def get_text_clips_n_notification(textlist, clip_time=60, height=800, wid=688, size=20):
# def get_text_clips_n_notification(textlist, clip_time=60, height=1280, wid=720, size=20):
    colors = [ 'Green', 'NavyBlue', 'SkyBlue2', 'Purple',
              'Black', 'HotPink4', 'Red', 'OrangeRed3', 'Brown']
    
    # colors =["red",'yellow', 'Green', 'Blue', "Orange", ]

    textlist.append("Visit @humhairahi channel for full Videos!")

    text_clips = []
    notification_sounds = []
    ntext = len(textlist)
    interval = int(clip_time/ntext)
    for i, post in enumerate(textlist):
        return_comment, nline = addcomment(post, size=50)
        color = random.choice(colors)
        fontsize=30
            # color="white"
        text_hight = 60 #max(200, nline*fontsize)
        txt = mpy.TextClip(return_comment, font="Keep-Calm-Medium",  # font='Courier',
                           fontsize=fontsize, bg_color=color, size=(wid+5, text_hight+10),
                           method="caption",
                           stroke_width=2.0,
                           stroke_color="white",
                           kerning=2
                           )
        
        #txt = txt.on_color(size=(txt.w+10,txt.h-10),
        #          color=(0,0,0), pos=(6,'center'), col_opacity=0.6)
        txt = txt.on_color(col_opacity=0.4)
        txt = txt.set_position((0, 100))
        txt = txt.set_start((0, 0 + (i * interval)))
        txt = txt.set_duration(interval+1)
        txt = txt.crossfadein(0.5)
        txt = txt.crossfadeout(0.5)
        # animation
        txt = txt.resize(zoom_in_out)
        text_clips.append(txt)
        print(i, 0+(i*interval))

        notification = mpy.AudioFileClip(notification_fname)
        notification = notification.set_start((0, 0 + (i * interval)))
        notification_sounds.append(notification)
    subscribe = mpy.AudioFileClip(subcribe_fname)
    subscribe = subscribe.set_start((0, clip_time-6))
    notification_sounds.append(subscribe)
    return text_clips, notification_sounds


# fname = r"/Users/sukhbindersingh/Desktop/youtube/ThathayyaCave/IMG_MAYAN_NL_highlights_t_60.mp4"
# TEXTLIST1 = ["It is believed that Lord Rama ...", "stayed at this place during his exile.", "Thathayya Cave",
#              "Historical Place", "60km from Bangalore off the Chintamani Road"]


# fname = r"/Users/sukhbindersingh/Desktop/youtube/HALmuseum/IMG_CLEAN_NL_highlights_t_90.mp4"
# TEXTLIST = ["Do you know which is India's ..... ", "First Aerospace Museum", "HAL museum, Bangalore",
#             "Established in 2001", "showcases the growth of the Indian aviation industry"]



def main():

    MAX_CLIP_TIME = 60

    parser = argparse.ArgumentParser(description="Shorts Maker")
    
    parser.add_argument("filename", type=str, help="File containing the list of files or .mp4 file  which is used for shorts")
    parser.add_argument("-t", "--text-file",  type=str, help="Text file containing comments (default: %(default)s)", default=None)
    parser.add_argument("-i", "--input",  type=str,nargs="*",action="append", help="Text inputs (default: %(default)s)", default=[])
    parser.add_argument("-d", "--time",  type=int, help="Duration of shorts in secs (default: %(default)s)", default=MAX_CLIP_TIME)
    parser.add_argument("-st", "--startat",  type=float, help="Audio startat (default: %(default)s)", default=0.0)
    parser.add_argument("-r", "--ratio",  type=float, help="Size Ratio: ex 9/16, 4/5 or (default: %(default)s)", default=1.0)
    

    args = parser.parse_args()
    # print(args)

    fname = args.filename.strip()

    TEXTLIST=[]
    if args.text_file is not None:
        with open(args.text_file, "r") as fin:
            TEXTLIST = fin.readlines()
    else:
        TEXTLIST = [" ".join(inp) for inp in args.input]

    print(TEXTLIST)


    # print(fname)
    if not fname.endswith(".mp4"):
        choices = app._CHOICES
        cmdline = "highlights {0} -vt NL -ct 90 -t 0.1 -a {1}"
        audio = random.choice(choices)

        cmdl = cmdline.format(fname, audio)
        print(cmdl)
        op = subprocess.call(cmdl.split(" "))

        outdir = os.path.dirname(fname)
        files = os.listdir(outdir)
        files = [os.path.join(outdir,f) for f in files if f.endswith(".mp4") and "highlights" in f and f.startswith("IMG_")] 
        latest = max(files, key = os.path.getctime)
        fname = latest
    
    cclip = create_shorts_from_vid(fname, startat=args.startat, crop_ratio=args.ratio)
    # if Duration is given as negative use the entire Duration of the clip
    if args.time < 0:
        clip_time = cclip.duration
    else:
        clip_time = min(cclip.duration, args.time)
    cclip = cclip.subclip(0, clip_time)
    audio = cclip.audio

    

    # print(args)
    # return
    
    w, h = cclip.size
    texclips, notisounds = get_text_clips_n_notification(TEXTLIST, clip_time=clip_time, wid=w)
    new_audioclip = mpy.CompositeAudioClip([audio]+notisounds)

    clip = mpy.CompositeVideoClip([cclip] + texclips)
    clip.audio = new_audioclip
    clip.fadeout(1)


    dirname = os.path.dirname(fname)
    basename = os.path.basename(fname)
    outpath = os.path.join(dirname, "Shorts_{}".format(basename))
    outpath_tx = os.path.join(dirname, "Shorts.txt")


    if args.text_file is None:
        with open(outpath_tx, "w") as fout:
            fout.write("\n".join(TEXTLIST[:-1]))

    # make loopable
    clip = vfx.make_loopable(clip,1)

    clip.write_videofile(outpath, temp_audiofile="out.m4a", audio=True,  audio_codec="aac", codec='libx264')


if __name__ == "__main__":
    main()