Conti
=====

*FFMpeg based playout server*

About the project
-----------------

Conti is a simple linear video playout server. It enables you to broadcast 
your video files with minimal configuration and hardware requirements.

With a little help of our other tools, Conti can run regional info channels,
loby TVs, you can use in your hotel, restaurant or just run a pirate-punk-whatever
channel for fun as [we do](https://nxtv.cz).

It is also possible to switch to live sources (capture card, webcam
or another IP video stream).

Quick start
-----------

Install [ffmpeg](https://www.ffmpeg.org) on a Linux box.
If you are using Debian based distribution, you may use
install.ffmpeg.sh script from our
[installers repository](https://github.com/immstudios/installers).

Clone this repository and tweak conti.py script to point to your data location
(directory with your video files)

By default, Conti streams in RTP over multicast to `rtp://224.0.0.1:2000`,
but you can change the destination as well as the encoding profile(s).

Start `./conti.py` and tune your station:
Start VLC on any machine in your network, hit ctrl+n and enter `rtp://@224.0.0.1:2000`.

If you wish, you can use RTMP output to stream - for
example - to YouTube Live or NGINX with RTMP module, create HLS or MPEG DASH segments
and manifest and run your own web TV.

Additionaly you can use our [Streampunk](https://streampunk.cz) service and
[WarpPlayer](http://player.warp.rocks).
[Contact us](mailto:info@nebulabroadcast.com) for more information


Do you want more?
-----------------

Feel free to tweak the sample script to meet your needs.
You can modify the `get_next` method to play different media in
different part of the day. You can apply audio and video filters both to each
source clip and output.

Limitations
-----------

`ContiSource` is work in progress... more features coming soon.

Real-time graphics will be limited to elements supported by ffmpeg filters.
You will be able to burn-in station logo, clock and simple news ticker though.
