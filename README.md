# Media Streaming Server

Open-source media streaming server for use with OBS or other RTMP/RTMPS compatible streaming client

## Introduction

Released under the Apache 2.0 License except where third-party code is used, which remains licensed under each as appropriate. No warranty or other liability is provided.

This guide provides documentation and some code on assembling a media streaming server from open-source components. The use case for which this project was assembled was for a friend's band wanting to livestream their music and videos to a select fanbase using the Open Broadcaster Software ("OBS"), without having to use a public and ad-sponsored service like YouTube or Twitch, and with the ability to manage and restrict the fan club with basic authentication. Other examples of use might include livestreaming yourself playing video games, or streaming your own live journalism or adventures around the world to a select audience. Or potentially many more use cases. This media streaming server can handle multiple RTMP streams and many viewers concurrently.

In short, this media streaming server setup is a repeater of whatever media you send it.

## Dependencies

Most of the functionality documented here is based on the following awesome open-source projects:

* nginx [https://nginx.org] - high-performance web server
* nginx-rtmp-module [https://github.com/arut/nginx-rtmp-module] - powerful rtmp streaming module for nginx (notable thanks to Roman Arutyunyan for developing this powerful module)
* OBS Studio [https://obsproject.com] - remarkable open-source video recording and live streaming software
* HLS video client [https://github.com/video-dev/hls.js/] - open-source video player for playing HLS in a JavaScript-compatible browser
* DASH video client [https://github.com/Dash-Industry-Forum/dash.js] - open-source video player for playing MPEG DASH in a JavaScript-compatible browser

## Overview of System Setup

* OS of choice - using Ubuntu 22.04 with a Linux 5.15 kernel but this setup should run on any relatively recent Linux system. May run on Windows also, not testing and thus not at all sure
* Hosted node of choice - a single cloud host at AWS/GCS/Azure or wherever should be able to support a significant number of viewers, assuming appropriate bandwidth and to a lesser degree CPU/memory. A modern 4GB-16GB should be well sufficient
* web files: files reference /www for path simplicity
* Depends on your OS in use - nginx typically runs with a default lower-permission user:group of for example: www-default:www-default

## Directories and Files

* /www/html/ - web file directory
  * /www/html/index.html - HTML landing page for entering streamkey or viewing available streams
* /www/html/css/ - CSS directory
  * /www/html/css/styles.css - basic CSS styles, provides a method for transparent background images on the index.html landing page
* /www/html/images/ - directory for your images of choice for favicon and foreground/background images
* /www/html/play/ - directory to temporarily store media files during stream
  * /www/html/play/index-play.html - HTML page that identifies viewer browser type and selects the appropriate player
  * /www/html/play/hls/ - HLS media files tmp directory, must be writable by nginx user
  * /www/html/play/dash/ - DASH media files tmp directory, must be writable by nginx user
  * /www/html/play/air - this part is a bit of a hack, but this is just a symlink to /www/html/play/hls/ to access the HLS media files without requiring authentication (AirPlay devices cannot assume the authentication of the device sending the airplay, for some rather insecure reason). The nginx.conf default file will apply different access permissions to this symlinked directory
* /www/html/js/ - JavaScript directory
  * /www/html/js/hls/ - HLS video player
  * /www/html/js/dash/ - DASH video player
* /www/auth/htpasswd - htpasswd authentication file for basic auth
* /www/rtmp/ - directory for nginx rtmp module statistics
  * /www/rtmp/counts/ - directory for writing viewer counts
* /www/scripts/ - directoy for script files for operation, currently just capturing viewer count with viewer-count.py
* /etc/nginx - default Ubuntu location for nginx configuration
  * /etc/nginx/sites-enabled - virtual host configuration for nginx, just using /etc/nginx/sites-enabled/default in this example
* /var/log/nginx/access.log - nginx access log and used for collecting viewer information via viewer-count.py
* /var/log/nginx/rtmp_access.log - rtmp nginx access log

## Server Inbound Network Ports

* 1935: the default RTMPS port is used for encrypted media streaming - the nginx server simply proxies and streams the media to the nginx-rtmp-module
* 1936: localhost-only port used by nginx-rtmp-module to process the media stream and write the media files temporarily to the filesystem
* 443: default HTTPS server port for viewing the media streams via the video players listed here

## Encryption

While this README is not going to go into configuring encryption, there are many good articles on using Let's Encrypt with certbot for certificate management and configured with Nginx:

* https://letsencrypt.org/getting-started/
* https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/

## Install Nginx with nginx-rtmp-module

Not going to provide extensive instructions here on installing nginx, as there are better guides available: https://www.nginx.com/resources/wiki/start/topics/tutorials/install/

For whatever your flavor of operating system, you'll need these components:
* nginx
* nginx-rtmp-module

On Ubuntu, the install would simply be the following:

```apt install nginx
add-apt-repository universe
apt install libnginx-mod-rtmp
```

## Configure Nginx

### nginx.conf

location: this file is included in this repository at ngnix/nginx.conf and would generally be placed at /etc/nginx/nginx.conf

configuration: Replace the sections that reference [URL] with your URL to reference the letsencrypt certificates. There are many other options for performance and limits - not going to catalog those here so you'll find those references at the nginx.org website if you need detailed tuning

### sites-enabled/default

location: this file is included in this repository at nginx/sites-enabled/default and would generally be placed at /etc/nginx/sites-enabled/default

configuration: Replace the sections that reference [URL] with your URL for server_name and letsencrypt certificates

### htpasswd

location: /www/auth/htpasswd

configuration: build this file using the htpasswd tool (part of the Apache httpd project at https://httpd.apache.org/docs/current/programs/htpasswd.html) for managing user viewing access

## Configure viewer-count.py

The script can be installed at /www/scripts/viewer-count.py or wherever you prefer. The script uses python3 with a few standard modules and reads the log file /var/log/nginx/access.log to gather (approximate) viewer counts. Would recommend just running it out of cron per minute:

```
* * * * *   /www/scripts/viewer-count.py
```

There are some configuration options for the timerange, formats, debug info, directories, and number of lines to read each run from access.log

## HTML files

The HTML files currently just have the JavaScript directly in the files. Should probably be moved out into separate loaded .js files at some point

* html/index.html - configure this as the landing page for entering a streamkey or viewing the available streams. Replace the [TITLE] with yours, and the [BACKGROUND] and [BOTTOM-IMAGE] with yours, as well as the [URL] references
* html/play/index-play.html - replace the [TITLE] and [URL] references to your environment
* css/styles.css - replace [IMAGE] references with yours

## RTMP stat.xsl file

This file is originally provided with the nginx-rtmp-module and has been customized to display the available streams and pull in the viewer counts. Replace the [URL] references with yours. Also will display a "click me to stream!" option to make it easier for viewers to find available streams and start playing them

## Build HLS player

```apt install npm
git clone https://github.com/Dash-Industry-Forum/dash.js.git
npm install ci
npm run dev
npm run sanity-check
npm run build
mkdir /www/html/js/hls
cp -p *js /www/html/js/hls
```

## Build DASH player

```apt install npm
git clone https://github.com/video-dev/hls.js.git
npm install ci
npm run dev
npm run sanity-check
npm run build
mkdir /www/html/js/hls
cp -p *js /www/html/js/dash
```

## AirPlay Directory
This is just a simple symlink to the hls/ directory, but the nginx config for permissions allows for AirPlay to access directly. This is an unfortunate workaround hack for the fact that AirPlay source devices cannot pass their authentication to the AirPlay target device:

```
$ ln -s /www/html/play/hls /www/html/play/air
```

## Using OBS

OBS is a flexible, powerful piece of software, with many options. This guide is not intended to provide full coverage of its possibilities. Use the OBJ documentation for full instructions [https://obsproject.com/wiki/]. The simple instructions for use are the following:

### OBS Configuration

* Settings->Stream: configure for the media streaming server, e.g.:
* Server: rtmps://example.com:1935/stream
* Stream Key: a key of choice chosen by the streamer to uniquely identify the stream. The javascript code included here requires that this must be ASCII characters >127, no spaces. Not sure what OBS allows otherwise

### Media Sources

OBS can stream media direct from camera, video/audio media files, desktop display, browser display, or many other sources. Check the OBS documentation for full instructions.

### Media Quality

Will depend on your bandwidth and that of the server as well as the quality of the original source and the CPU/memory capabilities of your laptop/desktop/mobile. The media streaming server is essentially just a proxy for whatever media is sent to it, so the quality of the stream is determined by the streamer via OBS. This media streaming server does no transcoding of any sort - transcoding requires significant CPU resources on the server and is likely to lead to latency or buffering. The server will report the media stream quality in the RTMP stats. High quality streams include the following settings in OBS:

* Settings->Output: Video Bitrate at 5200 Kpbs and Audio Bit at 320 for high quality, or lower if dictated by bandwidth or CPU
* Settings->Audio: Sample Rate 44.1 kHz or better yet 48 kHz
* Settings->Video: Base Resolution and Output Resolution of 1920x1080 or higher for HD, can use Common FPS values of 30 or higher quality at 60

Resulting media streams should be in H.264 High quality or better.

One note about OBS on macOS - audio capture can be quite difficult on macOS, due to additional security restrictions in the kernel on the audio interfaces. You may want to use the BlackHole plugin on MacOS to properly capture audio - more details here: https://github.com/ExistentialAudio/BlackHole

## Known Issues

* RTMP media stream not currently requiring authentication. It is possible but requires some additional development. Here is a good reference implementation: https://github.com/Nesseref/nginx-rtmp-auth
* Nginx media RTMP statistics are per process. This can create inconsistency in viewing media statistics if using more than 1 nginx worker. Since nginx is so high performant, While a single nginx worker should be able to sustain tens and possibly hundreds of concurrent viewer - at some perfomance threshhold - additional workers will be required. Roman Arutyunyan has developed a "per-worker-listener" that allows these RTMP stats to be gathered individually per worker [https://github.com/arut/nginx-patches]; however, there is still a requirement to ensure that each stream is only allocated to a single worker to gather consistent stats for that stream. Better solution not yet found. Since this current implementation only requires a small number of viewers, using 1 nginx worker is the simplest solution

Hope this works for you. Feel free to submit suggestions or pull requests.
