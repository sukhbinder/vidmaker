import os
import tempfile
from itertools import cycle

import moviepy.editor as mpy
import numpy as np

import vidmake.app as app
import vidmake.video_intro_lib as vlib
import vidmake.MakeDayVideoWithFFMPEG as flib

import argparse


import warnings

warnings.simplefilter("ignore", category=UserWarning)



def get_non_linear_subclips_VDURS(mov, vdurs, dur, ntime):
    vtype = "NL"
    subclips = []
    cc = cycle(dur)
    for i in range(ntime-1):
        span = next(cc)
        while True:
            file = np.random.choice(mov)
            try:
                duration = vdurs[file]
            except Exception as ex:
                print(file, "wrong")
                continue
            speed = 0 if duration < 0.2 and duration > 6.0 else 1
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


def get_linear_subclips(mov, vdurs, dur, ntime):
    vtype = "L"
    subclips = []
    # speeds = np.random.randint(2, size=ntime)
    cc = cycle(mov)
    nd = cycle(dur)
    for i in range(ntime-1):
        span = next(nd)
        while True:
            file = next(cc)
            try:
                duration = vdurs[file]
            except Exception as ex:
                print(file, "wrong")
                continue
            speed = 0 if span < 0.3 else 1
            if duration <= span:
                start_time=0.0 # take the whole
                span = duration
                break
            if span > 5: # if more than 10 sec video don't slow
                speed = 0 
            if speed == 1:
                span = span/2
            start_time = np.random.uniform(0, duration-span)
            if duration-span > 0:
                break
        end_time = start_time+span
        subclips.append((file, start_time, end_time, speed))
    return subclips


def trim_and_get_outfiles(sc):
    outfiles = []
    for i, clip in enumerate(sc):
        fn, st, et, speed = clip
        fna = os.path.basename(fn)
        fna,ext = os.path.splitext(fna)
        dur = et-st
        if speed == 1:
            outfile = "{0}_{1}_output_s.mp4".format(i,fna)
        else:
            outfile = "{0}_{1}_output.mp4".format(i, fna)
        app.trim_by_ffmpeg(fn, st, et, outfile, dur)
        if os.path.exists(outfile):
            outfiles.append(outfile)
    return outfiles


def create_parser():
    parser = argparse.ArgumentParser(description="Highlight Maker")
    
    parser.add_argument("filename", type=str, help="File containing the list of files")
    parser.add_argument("-ct", "--clip-time",  type=int, help="Clip Time (default: %(default)s)", default=None)
    parser.add_argument("-t", "--threshold",  type=float, help="Clip Time (default: %(default)s)", default=0.3)
    parser.add_argument("-vt", "--vtype",  type=str, help="Vtype Linear or Non Linear (default: %(default)s)",
                        choices=["L","NL"], default="L")
    parser.add_argument("-a", "--audio",  type=str, help="Audio to use (default: %(default)s)",
                        choices=app._CHOICES, default="COAST")
    parser.add_argument("-p", "--prefix",  type=str, help="Filename Prefix (default: %(default)s)", default="IMG")

    parser.add_argument("-fps", "--fps",  type=int, help="Video FPS (default: %(default)s)", default=60)
    parser.add_argument("-foout", "--fadeout",  type=float, help="Video fadeout (default: %(default)s)", default=1.0)
    parser.add_argument("-af", "--afadeout",  type=float, help="Audio FPS (default: %(default)s)", default=2.0)
    parser.add_argument("-d", "--debug", help="Debug this (default: %(default)s)", action="store_true")
    parser.add_argument("-u", "--use-ffmpeg", help="Use FFMPEG to write (default: %(default)s)", action="store_true")


    parser.add_argument("-aaf", "--audfile",  type=str, help="mp3 Audio file (default: %(default)s)", default=None)
    parser.add_argument("-bt", "--beats",  type=str, help="Beats Track (default: %(default)s)", default=None)

    return parser


def get_subclips(outfiles):
    vc = []
    for file in outfiles:
        vid = mpy.VideoFileClip(file)
        # print(vid)
        width = vid.w
        if width != 1920:
            vid = vid.resize(width=1920)
        
        if file.endswith("_s.mp4"):
            vid = vid.speedx(factor=0.5)
        try:
            dd = vid.duration
            vc.append(vid)
        except Exception as ex:
            print(ex)
            continue
    return vc

def main():

    parser = create_parser()
    args = parser.parse_args()
    audfile = args.audfile
    beats_track = args.beats
    if audfile is None and beats_track is None:
        audfile,beats_track = get_beats_tracks(args.audio)

    # ind = app._CHOICES.index(args.audio)

    # audfile = os.path.join(app._MUSICFOLDER, app._MUSIC[ind])
    # beats_track = os.path.join(app._ASSETS, app._BEATS_TRACK[ind])

    song_name, new_audioclip, new_time, dur = vlib.get_audioclip_n_beats(audfile, beats_track,threshold=args.threshold)

    mov = vlib.read_orderfile(args.filename)
    vdir = os.path.dirname(os.path.abspath(args.filename))
    vdursd = {f: app.get_length(f) for f in mov}

    clip_time=args.clip_time
    if clip_time is None:
        clip_time = len(mov)+1
    if args.vtype == "NL":
        subclips = get_non_linear_subclips_VDURS(mov, vdursd, dur, clip_time)
    else:
        subclips = get_linear_subclips(mov, vdursd, dur, clip_time)
    vlib.write_subclips_json(os.path.join(vdir, "{0}_subclips_time_{1}_{2}.json".format(args.vtype, clip_time,args.audio )), subclips)


    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tempdir:
        if args.debug:
            tempdir=cwd
        os.chdir(tempdir)
        outfiles = trim_and_get_outfiles(subclips)

        # vc = [mpy.VideoFileClip(f) for f in outfiles]
        
        outfullname = os.path.join(vdir, "{0}_{1}_{2}_highlights_t_{3}.mp4".format(args.prefix,args.audio, args.vtype, clip_time))
        if args.use_ffmpeg:
            fname="combined_withffmpeg.mp4"
            flib.make_video(outfiles, fname)
            clip = mpy.VideoFileClip(fname)
            gc = vlib.generate_video_hl([], new_audioclip, outfullname,fps=args.fps, fadeout=args.fadeout, afadeout=args.afadeout, clip=clip)
        else:
            print(len(outfiles))
            vc = get_subclips(outfiles)
            print(len(vc))
            gc = vlib.generate_video_hl(vc, new_audioclip, outfullname,fps=args.fps, fadeout=args.fadeout, afadeout=args.afadeout)
        del vc
        print(tempdir)
    os.chdir(cwd)


def create_parser2():
    parser = argparse.ArgumentParser(description="Continuous file Maker")
    
    parser.add_argument("filename", type=str, help="File containing the list of files")
    # parser.add_argument("-ct", "--clip-time",  type=int, help="Clip Time (default: %(default)s)", default=60)
    parser.add_argument("-t", "--threshold",  type=float, help="Clip Time (default: %(default)s)", default=0.3)
    # parser.add_argument("-vt", "--vtype",  type=str, help="Vtype Linear or Non Linear (default: %(default)s)",
    #                     choices=["L","NL"], default="L")
    parser.add_argument("-a", "--audio",  type=str, help="Audio to use (default: %(default)s)",
                        choices=app._CHOICES, default="COAST")
    parser.add_argument("-p", "--prefix",  type=str, help="Filename Prefix (default: %(default)s)", default="IMG")

    parser.add_argument("-fps", "--fps",  type=int, help="Video FPS (default: %(default)s)", default=60)
    parser.add_argument("-foout", "--fadeout",  type=float, help="Video fadeout (default: %(default)s)", default=1.0)
    parser.add_argument("-af", "--afadeout",  type=float, help="Audio FPS (default: %(default)s)", default=2.0)
    parser.add_argument("-d", "--debug", help="Debug this (default: %(default)s)", action="store_true")

    return parser


def trim_and_get_outfiles_for_coninous(subclips):
    inum=1
    outfiles=[]
    for item, val in subclips.items():
        if len(val) == 0:
            dur = app.get_length(item)
            st=0.0
            et = st+dur
            outfile = "{}_output_s.mp4".format(inum)
            app.trim_by_ffmpeg(item, st, et,outfile, dur)
            if os.path.exists(outfile):
                outfiles.append(outfile)
                inum = inum+1
        for st,et in val:
            dur=et-st
            if dur > 5.0:
                outfile = "{}_output.mp4".format(inum)
            else:    
                outfile = "{}_output_s.mp4".format(inum)
            app.trim_by_ffmpeg(item, st, et,outfile, dur)
            if os.path.exists(outfile):
                outfiles.append(outfile)
                inum = inum+1
    return outfiles

def get_beats_tracks(audio_tag):
    ind = app._CHOICES.index(audio_tag)

    audfile = os.path.join(app._MUSICFOLDER, app._MUSIC[ind])
    beats_track = os.path.join(app._ASSETS, app._BEATS_TRACK[ind])
    return audfile,beats_track

def con_main():
    parser = create_parser2()
    args = parser.parse_args()

    audfile,beats_track = get_beats_tracks(args.audio)
    # ind = app._CHOICES.index(args.audio)

    # audfile = os.path.join(app._MUSICFOLDER, app._MUSIC[ind])
    # beats_track = os.path.join(app._ASSETS, app._BEATS_TRACK[ind])

    song_name, new_audioclip, new_time, dur = vlib.get_audioclip_n_beats(audfile, beats_track,threshold=args.threshold)

    mov = vlib.read_orderfile(args.filename)
    vdir = os.path.dirname(os.path.abspath(args.filename))
    # vdursd = {f: app.get_length(f) for f in mov}
    vdursd = np.array([app.get_length(f) for f in mov])

    subclips = vlib.get_subclips_linear(mov, [], dur, vdurs=vdursd)
    vlib.write_subclips_json(os.path.join(vdir, "Continuous_{0}_subclips_time_{1}.json".format("Linear", len(mov))), subclips)
    
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tempdir:
        if args.debug:
            tempdir =cwd
        os.chdir(tempdir)
        outfiles = trim_and_get_outfiles_for_coninous(subclips)
        fname= os.path.join(vdir, "CONCATENATED_using_ffmpeg.mp4") # backup mp4
        iret=flib.make_video(outfiles, fname)
        # clip = mpy.VideoFileClip(fname)
        # vc = get_subclips(outfiles)
        
        outfiles = [os.path.join(tempdir, f) for f in outfiles] # Moviepy is lazy so need this fix
        # see https://stackoverflow.com/questions/72503468/exception-has-occurred-oserror-moviepy-error-failed-to-read-the-first-frame-of
        nout= len(outfiles)
        print("Length of clips: {}".format(nout))
        if nout >200:
            alist = list(range(0, nout, 200))
            alist.append(nout)
        else:
            alist=[0,nout]
        beg=0
        for istart in alist[1:]:
            prefix = "{0}_{1}".format(args.prefix, beg)
            vc = get_subclips(outfiles[beg:istart])
            outfullname = os.path.join(vdir, "continous_{0}_{1}_{2}_highlights_t_{3}.mp4".format(prefix,args.audio, "linear", len(mov)))
            gc = vlib.generate_video_hl(vc, new_audioclip, outfullname, fps=args.fps, fadeout=args.fadeout, afadeout=args.afadeout)
            beg = istart
            del vc
    os.chdir(cwd)


