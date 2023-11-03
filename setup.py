from setuptools import find_packages, setup

setup(
    name="vidmaker",
    version="0.1",
    packages=find_packages(),
    license="Private",
    description="Video Continuous and Highlights",
    author="sukhbinder",
    author_email="sukh2010@yahoo.com",
    entry_points={
        'console_scripts': ['oldhighlights = vidmake.app:main',
                            'dashvid = vidmake.app:concat_main',
                            'section_video = vidmake.app:section_main', 
                            "concat = vidmake.app:concat_main2",
                            "trim = vidmake.app:trim_main",
                            "highlights = vidmake.vid_high_cont:main",
                            "continous = vidmake.vid_high_cont:con_main",
                            "play=vidmake.vid_high_cont:play_music",
                            "mconcat = vidmake.app:main_moviepy_concat",
                            "shorts = vidmake.shorts_experiment:main",

        ]
    },

    install_requires=["moviepy"],
)
