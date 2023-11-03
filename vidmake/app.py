import vidmake.video_intro_lib as vlib
import vidmake.MakeDayVideoWithFFMPEG as flib
import vidmake.dashcam_days_video as dlib
import argparse
from concurrent.futures import ProcessPoolExecutor
import subprocess
import os
import moviepy.editor as mpy

import json

import warnings

warnings.simplefilter("ignore", category=UserWarning)

"""
vil.generate_highlights_with_mov(
    mov,
    audfile,
    beats_track,
    clip_time=60,
    vtype='L',
    starts_with='IMG',
    fps=30,
    fadeout=1,
    afadeout=2,
    folder_name=None,
)


"""
_HERE = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.join(_HERE, "..", "assets")
_MUSICFOLDER = os.path.join(_ASSETS, "music")
_BEATSFILE =os. path.join(_ASSETS, "beatsnmusic.json")

with open(_BEATSFILE, "r") as fin:
    beats = json.load(fin)

_CHOICES = beats["0"]
_BEATS_TRACK = beats["1"]
_MUSIC = beats["2"]


def create_parser():
    parser = argparse.ArgumentParser(description="Video Maker")
    
    parser.add_argument("filename", type=str, help="File containing the list of files")
    parser.add_argument("-ct", "--clip-time",  type=int, help="Clip Time (default: %(default)s)", default=60)
    parser.add_argument("-vt", "--vtype",  type=str, help="Vtype Linear or Non Linear (default: %(default)s)",
                        choices=["L","NL"], default="L")
    parser.add_argument("-p", "--prefix",  type=str, help="Filename Prefix (default: %(default)s)", default="IMG")

    parser.add_argument("-fps", "--fps",  type=int, help="Video FPS (default: %(default)s)", default=60)
    parser.add_argument("-foout", "--fadeout",  type=float, help="Video fadeout (default: %(default)s)", default=1.0)
    parser.add_argument("-af", "--afadeout",  type=float, help="Audio FPS (default: %(default)s)", default=2.0)
    parser.add_argument("-f", "--folder-name",  type=str, help="Folder Name (default: %(default)s)", default=None)

    # parser.add_argument("-a", "--audio",  type=str, help="Vtype Linear or Non Linear",
    #                     choices=["L","NL"], default="L")

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    mov = vlib.read_orderfile(args.filename)

    alist = list(range(0,len(mov), 100))
    alist.append(len(mov))
    print(alist)

    
    with ProcessPoolExecutor(max_workers=1) as executor:
    # future = executor.submit(pow, 323, 1235)
    # print(future.result())
        istart =0
        i=0
        # for i in alist[1:]:
        prefix ="{0}_{1}".format(i, args.prefix) 
        audfile = os.path.join(_MUSICFOLDER,_MUSIC[13])
        beats_track = os.path.join(_ASSETS ,_BEATS_TRACK[13])
        
        # future = executor.submit(vlib.generate_highlights_with_mov,mov[istart:i],audfile,beats_track,
        future = executor.submit(vlib.generate_highlights_with_mov,mov,audfile,beats_track,
        clip_time=args.clip_time,
        vtype=args.vtype,
        starts_with=prefix,
        fps=args.fps,
        fadeout=args.fadeout,
        afadeout=args.afadeout,
        folder_name=args.folder_name )

        istart = i
            
            # print(future.result())
            # vc = vlib.generate_highlights_with_mov(mov[istart:i], vlib.audfile,
            # vlib.beats_track,
            # clip_time=args.clip_time,
            # vtype=args.vtype,
            # starts_with=prefix,
            # fps=args.fps,
            # fadeout=args.fadeout,
            # afadeout=args.afadeout,
            # folder_name=args.folder_name)
            
            # del vc
        
        
    


def create_parser_concat():
    # all_videos_by_days(folder=r"/Users/sukhbindersingh/Desktop/200video/front", startswith="2022", fileprefix="DTV_", break_at=65)
    parser = argparse.ArgumentParser( description="Concat Videos using FFMPEG")
    
    parser.add_argument("-f", "--folder", type=str, help="Folder Path (default: %(default)s)", default=r"/Users/sukhbindersingh/Desktop/200video/front")
    parser.add_argument("-p", "--prefix",  type=str, help="Filename Starts with (default: %(default)s)", default="2023")
    parser.add_argument("-op", "--output-prefix",  type=str,  help="Output Filename prefix (default: %(default)s)", default="DIV_")
    parser.add_argument("-b", "--break-at",  type=int,  help="File Break in Seconds (default: %(default)s)", default=65)
    
    return parser


def concat_main():
    parser = create_parser_concat()
    args = parser.parse_args()
    flib.all_videos_by_days(folder=args.folder, startswith=args.prefix, fileprefix=args.output_prefix, break_at=args.break_at)


def create_parser_section():
    # get_travel_section_by_time(day, folder=r"/Users/sukhbindersingh/Desktop/200video/front", startswith="2022", stop=65,
    # fileprefix="travel_video", beg_time=5, end_time=6)
    parser = argparse.ArgumentParser( description="DASHCAM section videos")
    
    parser.add_argument("day", type=str, help="Day in YYYYMMDD")
    parser.add_argument("-f", "--folder",  type=str, help="Folder location (default: %(default)s)", default=r"/Users/sukhbindersingh/Desktop/200video/front")
    parser.add_argument("-p", "--prefix",  type=str, help="Filename Starts with (default: %(default)s)", default="2023")
    parser.add_argument("-op", "--output-prefix",  type=str,  help="Output Filename prefix (default: %(default)s)", default="travel_video")
    parser.add_argument("-b", "--break-at",  type=int,  help="File Break in Seconds (default: %(default)s)", default=65)
    
    parser.add_argument("-bt", "--beg_time",  type=int,  help="Time from where to take video clip (default: %(default)s)", default=5)
    parser.add_argument("-et", "--end_time",  type=int,  help="End time  (default: %(default)s)", default=6)
    return parser

def section_main():
    parser = create_parser_section()
    args = parser.parse_args()

    dlib.get_travel_section_by_time(args.day, folder=args.folder, startswith=args.prefix, stop=args.break_at, 
                            fileprefix=args.output_prefix, beg_time=args.beg_time, end_time=args.end_time)



def concat(inputfile:str, fname:str = None):
    inputfile = os.path.abspath(inputfile)
    folder = os.path.dirname(inputfile)
    with open(inputfile, "r") as fin:
        files = fin.readlines()

    if fname is None:
        fname= "combined_{0}.mp4".format(files[0]) 
    
    fname= os.path.join(folder, fname)
    print(files)
    files = [os.path.join(folder, f.strip()) for f in files]
    
    print(files)
    iret= flib.make_video(files, fname )
    return fname


def create_parser_concat2():
    parser = argparse.ArgumentParser( description="Concat Videos using FFMPEG given a filename")
    parser.add_argument("inputfile", type=str, help="Inputfiles to concatenate")
    parser.add_argument("-o", "--outfilename", type=str, help="Folder where files are (default: %(default)s)", default=None )
    return parser


def concat_main2():
    parser = create_parser_concat2()
    args = parser.parse_args()
    fname= concat(args.inputfile, args.outfilename)
    print("{} created".format(fname) )


def create_parser_trim():
    parser = argparse.ArgumentParser( description="Trim Video Using FFMPEG")
    parser.add_argument("inputfile", type=str, help="Single file name")
    parser.add_argument("-st", "--starttime", type=str, help="Start time in the format hh:mm:ss" )
    parser.add_argument("-et", "--endtime", type=str, help="End time in the format hh:mm:ss" )
    parser.add_argument("-o", "--outputfile", type=str, help="Output file (default: %(default)s)", default="output.mp4" )
    parser.add_argument("-d", "--duration", type=float, help="Duration time in seconds (default: %(default)s)", default=None )

    return parser


def trim_main():
    parser = create_parser_trim()
    args = parser.parse_args()
    iret = trim_by_ffmpeg(args.inputfile, args.starttime, args.endtime, args.outputfile, args.duration)
    print("{} created.".format(args.outputfile))

def get_seconds(ts):
    secs = sum(int(x) * 60 ** i for i, x in enumerate(reversed(ts.split(':'))))
    return secs


def trim_by_ffmpeg(inputfile, starttime, endtime, outputfile,duration =None):
    if isinstance(starttime, str):
        if ":" in starttime:
            starttime = get_seconds(starttime)
    if isinstance(endtime,str):
        if ":" in endtime:
            endtime = get_seconds(endtime)
    
    if duration is not None:
        cmdline = "ffmpeg -y -ss {starttime:0.4f} -i {inputfile} -t {duration:0.4f} -c copy {outputfile}".format(
            starttime=float(starttime),
            inputfile=inputfile,
            duration=float(duration),
            outputfile=outputfile
        )
    else:
        cmdline = "ffmpeg -y -ss {starttime:0.4f} -i {inputfile} -to {endtime:0.4f} -map 0 -vcodec copy -acodec copy  {outputfile}".format(
            starttime=float(starttime),
            inputfile=inputfile,
            endtime=float(endtime),
            outputfile=outputfile
        )
    cmdlist = cmdline.split()
    iret = subprocess.call(cmdlist)
    return iret


def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return float(result.stdout)



def create_concat_movie(fname, onlyaudio=False):
    #fname=r"/Users/sukhbindersingh/Desktop/youtube/aadiyogi_/orderfiles.txt"
    fpath = os.path.dirname(fname)
    
    with open(fname, "r") as fin:
        files = fin.readlines()
    # get folder name
    iname = os.path.basename(fpath).lower()
    print(iname)

    files =[os.path.join(fpath, file.strip()) for file in files]
    clips = [mpy.VideoFileClip(file) for file in files]
    
    
    clip = mpy.concatenate_videoclips(clips)

    # Write out only audio file also
    audio = clip.audio
    aoutput_path = os.path.join(fpath, "total_{0}.mp3".format(iname))
    audio=audio.set_fps(44100)
    audio.write_audiofile(aoutput_path)
    print("{} mp3 created".format(aoutput_path))

    # write out video
    if not onlyaudio:
        output_path = os.path.join(fpath, "total_vid_{0}.mp4".format(iname))
        clip.write_videofile(output_path, temp_audiofile="out.m4a", audio=True,  audio_codec="aac", codec='libx264', fps=60)
        print("{} mp4 created".format(output_path))
    
    
    _=[clip.close() for clip in clips]

    

def create_parser_moviepy_concat():
    parser = argparse.ArgumentParser( description="Concat files using moviepy")
    parser.add_argument("inputfile", type=str, help="orderfiles that has list of files to concat")
    parser.add_argument("-oa", "--onlyaudio", help="Only audio (default: %(default)s)", action="store_true")
    return parser

def main_moviepy_concat():
    parser = create_parser_moviepy_concat()
    args = parser.parse_args()
    fname = os.path.abspath(args.inputfile)
    create_concat_movie(fname, args.onlyaudio)
