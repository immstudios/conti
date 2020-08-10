Conti
=====

*FFMpeg based playout server*

About the project
-----------------

Conti is a simple linear video playout server. It enables you to broadcast
your video files with minimal configuration and hardware requirements.

Conti demo script can be modified to run simple stand-alone channels such as
lobby TVs, info channels, community TV stations, and so on.

For more complex projects, [Nebula](https://github.com/immstudios/nebula) 
broadcast automation system can be used for scheduling and playout control.

### Features

Conti has a very simple architecture allowing extensive tweaking. Most of the features
come from FFMpeg, notably:

 - Vast source format support
 - Multiple simultaneous outputs including RTP, RTMP, MPEG-TS, NDI and SDI
 - Video and audio filtering on a source, global, or output level. This includes
   on-the-fly loudness normalization, station logo burn-in, ARC and so on.
 - Up to 16 channel audio support with channels shuffling.
 - Hardware-accelerated encoding (nvenc) of selected formats (h.264, HEVC)

### Limitations

 - Most of the output formats does not support pausing. 
   It is possible to pause Decklink or SDL outputs by calling `Conti.freeze(self)` method,
   but IP streams have to run all the time.
 - It is not possible to control displayed graphics overlays during playback. 
 - There is probably no easy way to create a continuous text crawl. 
   [Prove us wrong](https://github.com/immstudios/conti/issues/new).
 - Looping is not implemented yet (but is planned) 
 - *source* and *output* filters usage differs slightly. We want to unify the behavior.

Quick start
-----------

Conti runs on Linux (no other OS has been tested) and requires Python3, FFMpeg and
nxtools.

### FFMpeg

For the most use-cases, FFMpeg build available in your favorite Linux distribution
is sufficient. 

In case you need Blackmagic Decklink or NDI I/O, you may use our build script from 
[this repository](https://github.com/immstudios/installers).

### nxtools

[nxtools](https://github.com/immstudios/nxtools) is a set of Python utilities 
we use for many tasks. Install it using `pip3 install nxtools`

### Running Conti

Clone this repository and tweak conti.py script to point to your data location
(directory with your video files)

By default, Conti streams in RTP over multicast to `rtp://224.0.0.1:2000`,
but you can change the destination as well as the encoding profile(s).

Start `./conti.py` and tune your station:
Start VLC on any machine in your network, hit ctrl+n and enter `rtp://@224.0.0.1:2000`.

Architecture
------------

Conti uses several FFMpeg processes tied together using pipes to produce a gapless stream.
Each **source** (`ContiSource` Python class) spawns an FFMpeg process with a filter-chain
which handles format and tracks layout normalization and pipes its uncompressed output to
the encoder process. Conti opens several source processes in advance, so right after one 
clip is finished, the next one can be started without delays. 

The encoder process applies *global output filter-chain* to the piped input (e.g. audio
normalization), splits the output if there is more than one output specified, applies
*per-output* filter-chains and transcode or output the result to the desired streams/devices.

Examples
--------

Feel free to tweak the sample script to meet your needs.
You can modify the `get_next` method to play different media files in
different parts of the day or to follow a playlist stored in a database.

Following `settings.json` file instruct the `conti.py` demo script to playback media files from the
chosen directory, the top-level `video_filters` parameter is applied to all outputs
(in this case, black&white conversion). Two SDL outputs (desktop windows) are defined, but the audio 
output is not used. The second output has its feed horizontally flipped.

```json
{
    "media_dir" : "/export/media.dir",
    "video_filters" : "hue=s=0",
    "outputs" : [ 
    {
        "target" : "SDL Output 1",
        "audio" : false,
        "params" : {
            "c:v" : "rawvideo",
            "f" : "sdl",
            "pix_fmt" : "yuv420p"
        }
    },
    {
        "target" : "SDL Output 2",
        "audio" : false,
        "video_filters": "hflip",
        "params" : {
            "c:v" : "rawvideo",
            "f" : "sdl",
            "pix_fmt" : "yuv420p"
        }
    }

]
}
```

 > Note: SDL is not available in the immstudios ffmpeg build (yet)

### Pipe format

The example assumes 1080p25 is used as an "intermediate" format (the format which goes thru the pipe),
but at the top level of the `settings.json` you may override the following default values.

```json
{
        "width"           : 1920,
        "height"          : 1080,
        "frame_rate"      : 25,
        "pixel_format"    : "yuv422p",
        "audio_only"      : false,
        "audio_codec"     : "pcm_s16le",
        "audio_sample_rate" : 48000,
}
```

### Decklink

Decklink cards are very picky regarding the used format, especially the interlaced flag.
In order to output 1080i50, use the default values of the pipe format and use the following values
for your output.

```json
{
    "target" : "DeckLink SDI",
    "video_filters" : "setfields=tff",
    "params" : {
        "field_order" : "tt",
        "f" : "decklink",
        "pix_fmt" : "uyvy422"
    }
}
```

### Audio

All sources are converted to 16channels audio, so in order to get a stereo output (for example for an IP stream),
use `{"audio_filters" : "pan=stereo|c0=c0|c1=c1}` or similar to get the desired channel pair.




