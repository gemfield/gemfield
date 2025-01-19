# 背景
Gemfield最近尝试使用python封装的ffmpeg库（PyAV）来进行mp4文件、rtmp协议及其它协议的decode，具体来说就是将mp4文件（或者rtmp协议的数据，下同）进行demux并逐帧decode。然而在这期间发现了一些decode的性能问题。这些问题概括起来就是2点：python封装的ffmpeg是否能够利用到多核CPU的并发优势？不同的编译参数能带来ffmpeg性能怎样的提升？gemfield本文就是从这2个角度出发来进行各种性能测试，并最终得出一个结论。

本文使用的测试程序是remux.py。该程序已经开源在了：https://github.com/CivilNet/Gemfield/blob/master/src/python/ffmpeg/remux.py。

# 多线程
可以从下面的输出看到，程序是1个进程8个线程（Linux上称之为轻量级进程），其中，python程序本身只有一个线程，在import numpy之后，多了3个线程，而在ffmpeg开始decode之后，线程数量又增加了4个。至此，整个程序的线程数量为8个。
```bash
gemfield@ThinkPad-X1C:~/github/tmp$ ps -eL -o %cpu,%mem,lwp,pid,ppid,cmd | grep remux | grep -v code | grep -v watch | grep -v grep
 104  1.4 16595 16595 19441 python remux.py
 1.8  1.4 16596 16595 19441 python remux.py
 1.8  1.4 16597 16595 19441 python remux.py
 1.6  1.4 16598 16595 19441 python remux.py
 0.0  1.4 16599 16595 19441 python remux.py
 0.0  1.4 16600 16595 19441 python remux.py
 0.0  1.4 16601 16595 19441 python remux.py
 0.0  1.4 16602 16595 19441 python remux.py
```
在程序执行的时候，自始至终都只有一个线程在使用CPU，并且cpu使用率基本是100%，因此可以说，程序在decode的过程中并没有利用到多核的并发优势。众所周知，Python自身的字节码在执行的时候由于GIL的机制，是无法同时利用多CPU的计算资源的；但是对于python封装的C库、并且线程是在C库中创建并维护的、并且线程并不需要callback Python的代码的情况下，还是能利用的多核的并发优势的。因此，这里尚不清楚是否是python封装的原因。不过没关系，和编译参数比起来，这里只能算是开胃菜。

# 编译参数的调试
## 1，安装依赖
```bash
sudo apt-get update -qq && sudo apt-get -y install \
  autoconf \
  automake \
  build-essential \
  cmake \
  git \
  libass-dev \
  libfreetype6-dev \
  libsdl2-dev \
  libtool \
  libva-dev \
  libvdpau-dev \
  libvorbis-dev \
  libxcb1-dev \
  libxcb-shm0-dev \
  libxcb-xfixes0-dev \
  pkg-config \
  texinfo \
  wget \
  zlib1g-dev \
  nasm
```
## 2，PyAV选用的默认ffmpeg编译参数
```bash
./configure --disable-static --enable-shared --disable-doc --enable-libx264 --enable-gpl --disable-optimizations --disable-mmx --enable-debug=3 --disable-stripping
install prefix            /home/gemfield/test/PyAV/vendor/build/ffmpeg-4.0
source path               .
C compiler                gcc
C library                 glibc
ARCH                      x86 (generic)
big-endian                no
runtime cpu detection     yes
standalone assembly       no
x86 assembler             nasm
MMX enabled               no
MMXEXT enabled            no
3DNow! enabled            no
3DNow! extended enabled   no
SSE enabled               no
SSSE3 enabled             no
AESNI enabled             no
AVX enabled               no
AVX2 enabled              no
AVX-512 enabled           no
XOP enabled               no
FMA3 enabled              no
FMA4 enabled              no
i686 features enabled     yes
CMOV is fast              yes
EBX available             yes
EBP available             no
debug symbols             yes
strip symbols             no
optimize for size         no
optimizations             no
static                    no
shared                    yes
postprocessing support    yes
network support           yes
threading support         pthreads
safe bitstream reader     yes
texi2html enabled         no
perl enabled              yes
pod2man enabled           yes
makeinfo enabled          no
makeinfo supports HTML    no

External libraries:
iconv                   libx264                 lzma                    xlib                    zlib

External libraries providing hardware acceleration:
v4l2_m2m

Libraries:
avcodec                 avfilter                avformat                avutil                  postproc                swresample              swscale
avdevice

Programs:
ffmpeg                  ffprobe

Enabled decoders:
aac                     asv2                    eacmv                   jv                      pcm_bluray              roq_dpcm                v210x
aac_fixed               atrac1                  eamad                   kgv1                    pcm_dvd                 rpza                    v308
aac_latm                atrac3                  eatgq                   kmvc                    pcm_f16le               rscc                    v408
aasc                    atrac3al                eatgv                   lagarith                pcm_f24le               rv10                    v410
ac3                     atrac3p                 eatqi                   loco                    pcm_f32be               rv20                    vb
ac3_fixed               atrac3pal               eightbps                m101                    pcm_f32le               rv30                    vble
adpcm_4xm               aura                    eightsvx_exp            mace3                   pcm_f64be               rv40                    vc1
adpcm_adx               aura2                   eightsvx_fib            mace6                   pcm_f64le               s302m                   vc1_v4l2m2m
adpcm_afc               avrn                    escape124               magicyuv                pcm_lxf                 sami                    vc1image
adpcm_aica              avrp                    escape130               mdec                    pcm_mulaw               sanm                    vcr1
adpcm_ct                avs                     evrc                    metasound               pcm_s16be               sbc                     vmdaudio
adpcm_dtk               avui                    exr                     microdvd                pcm_s16be_planar        scpr                    vmdvideo
adpcm_ea                ayuv                    ffv1                    mimic                   pcm_s16le               screenpresso            vmnc
adpcm_ea_maxis_xa       bethsoftvid             ffvhuff                 mjpeg                   pcm_s16le_planar        sdx2_dpcm               vorbis
adpcm_ea_r1             bfi                     ffwavesynth             mjpegb                  pcm_s24be               sgi                     vp3
adpcm_ea_r2             bink                    fic                     mlp                     pcm_s24daud             sgirle                  vp5
adpcm_ea_r3             binkaudio_dct           fits                    mmvideo                 pcm_s24le               sheervideo              vp6
adpcm_ea_xas            binkaudio_rdft          flac                    motionpixels            pcm_s24le_planar        shorten                 vp6a
adpcm_g722              bintext                 flashsv                 movtext                 pcm_s32be               sipr                    vp6f
adpcm_g726              bitpacked               flashsv2                mp1                     pcm_s32le               smackaud                vp7
adpcm_g726le            bmp                     flic                    mp1float                pcm_s32le_planar        smacker                 vp8
adpcm_ima_amv           bmv_audio               flv                     mp2                     pcm_s64be               smc                     vp8_v4l2m2m
adpcm_ima_apc           bmv_video               fmvc                    mp2float                pcm_s64le               smvjpeg                 vp9
adpcm_ima_dat4          brender_pix             fourxm                  mp3                     pcm_s8                  snow                    vp9_v4l2m2m
adpcm_ima_dk3           c93                     fraps                   mp3adu                  pcm_s8_planar           sol_dpcm                vplayer
adpcm_ima_dk4           cavs                    frwu                    mp3adufloat             pcm_u16be               sonic                   vqa
adpcm_ima_ea_eacs       ccaption                g2m                     mp3float                pcm_u16le               sp5x                    wavpack
adpcm_ima_ea_sead       cdgraphics              g723_1                  mp3on4                  pcm_u24be               speedhq                 webp
adpcm_ima_iss           cdxl                    g729                    mp3on4float             pcm_u24le               srgc                    webvtt
adpcm_ima_oki           cfhd                    gdv                     mpc7                    pcm_u32be               srt                     wmalossless
adpcm_ima_qt            cinepak                 gif                     mpc8                    pcm_u32le               ssa                     wmapro
adpcm_ima_rad           clearvideo              gremlin_dpcm            mpeg1_v4l2m2m           pcm_u8                  stl                     wmav1
adpcm_ima_smjpeg        cljr                    gsm                     mpeg1video              pcm_zork                subrip                  wmav2
adpcm_ima_wav           cllc                    gsm_ms                  mpeg2_v4l2m2m           pcx                     subviewer               wmavoice
adpcm_ima_ws            comfortnoise            h261                    mpeg2video              pgm                     subviewer1              wmv1
adpcm_ms                cook                    h263                    mpeg4                   pgmyuv                  sunrast                 wmv2
adpcm_mtaf              cpia                    h263_v4l2m2m            mpeg4_v4l2m2m           pgssub                  svq1                    wmv3
adpcm_psx               cscd                    h263i                   mpegvideo               pictor                  svq3                    wmv3image
adpcm_sbpro_2           cyuv                    h263p                   mpl2                    pixlet                  tak                     wnv1
adpcm_sbpro_3           dca                     h264                    msa1                    pjs                     targa                   wrapped_avframe
adpcm_sbpro_4           dds                     h264_v4l2m2m            mscc                    png                     targa_y216              ws_snd1
adpcm_swf               dfa                     hap                     msmpeg4v1               ppm                     tdsc                    xan_dpcm
adpcm_thp               dirac                   hevc                    msmpeg4v2               prores                  text                    xan_wc3
adpcm_thp_le            dnxhd                   hnm4_video              msmpeg4v3               prores_lgpl             theora                  xan_wc4
adpcm_vima              dolby_e                 hq_hqa                  msrle                   psd                     thp                     xbin
adpcm_xa                dpx                     hqx                     mss1                    ptx                     tiertexseqvideo         xbm
adpcm_yamaha            dsd_lsbf                huffyuv                 mss2                    qcelp                   tiff                    xface
aic                     dsd_lsbf_planar         iac                     msvideo1                qdm2                    tmv                     xl
alac                    dsd_msbf                idcin                   mszh                    qdmc                    truehd                  xma1
alias_pix               dsd_msbf_planar         idf                     mts2                    qdraw                   truemotion1             xma2
als                     dsicinaudio             iff_ilbm                mvc1                    qpeg                    truemotion2             xpm
amrnb                   dsicinvideo             imc                     mvc2                    qtrle                   truemotion2rt           xsub
amrwb                   dss_sp                  indeo2                  mxpeg                   r10k                    truespeech              xwd
amv                     dst                     indeo3                  nellymoser              r210                    tscc                    y41p
anm                     dvaudio                 indeo4                  nuv                     ra_144                  tscc2                   ylc
ansi                    dvbsub                  indeo5                  on2avc                  ra_288                  tta                     yop
ape                     dvdsub                  interplay_acm           opus                    ralf                    twinvq                  yuv4
apng                    dvvideo                 interplay_dpcm          paf_audio               rawvideo                txd                     zero12v
aptx                    dxa                     interplay_video         paf_video               realtext                ulti                    zerocodec
aptx_hd                 dxtory                  jacosub                 pam                     rl2                     utvideo                 zlib
ass                     dxv                     jpeg2000                pbm                     roq                     v210                    zmbv
asv1                    eac3                    jpegls                  pcm_alaw

Enabled encoders:
a64multi                avrp                    h261                    msvideo1                pcm_s64le               rawvideo                v210
a64multi5               avui                    h263                    nellymoser              pcm_s8                  roq                     v308
aac                     ayuv                    h263_v4l2m2m            opus                    pcm_s8_planar           roq_dpcm                v408
ac3                     bmp                     h263p                   pam                     pcm_u16be               rv10                    v410
ac3_fixed               cinepak                 h264_v4l2m2m            pbm                     pcm_u16le               rv20                    vc2
adpcm_adx               cljr                    huffyuv                 pcm_alaw                pcm_u24be               s302m                   vorbis
adpcm_g722              comfortnoise            jpeg2000                pcm_f32be               pcm_u24le               sbc                     vp8_v4l2m2m
adpcm_g726              dca                     jpegls                  pcm_f32le               pcm_u32be               sgi                     wavpack
adpcm_g726le            dnxhd                   libx264                 pcm_f64be               pcm_u32le               snow                    webvtt
adpcm_ima_qt            dpx                     libx264rgb              pcm_f64le               pcm_u8                  sonic                   wmav1
adpcm_ima_wav           dvbsub                  ljpeg                   pcm_mulaw               pcx                     sonic_ls                wmav2
adpcm_ms                dvdsub                  magicyuv                pcm_s16be               pgm                     srt                     wmv1
adpcm_swf               dvvideo                 mjpeg                   pcm_s16be_planar        pgmyuv                  ssa                     wmv2
adpcm_yamaha            eac3                    mlp                     pcm_s16le               png                     subrip                  wrapped_avframe
alac                    ffv1                    movtext                 pcm_s16le_planar        ppm                     sunrast                 xbm
alias_pix               ffvhuff                 mp2                     pcm_s24be               prores                  svq1                    xface
amv                     fits                    mp2fixed                pcm_s24daud             prores_aw               targa                   xsub
apng                    flac                    mpeg1video              pcm_s24le               prores_ks               text                    xwd
aptx                    flashsv                 mpeg2video              pcm_s24le_planar        qtrle                   tiff                    y41p
aptx_hd                 flashsv2                mpeg4                   pcm_s32be               r10k                    truehd                  yuv4
ass                     flv                     mpeg4_v4l2m2m           pcm_s32le               r210                    tta                     zlib
asv1                    g723_1                  msmpeg4v2               pcm_s32le_planar        ra_144                  utvideo                 zmbv
asv2                    gif                     msmpeg4v3               pcm_s64be

Enabled hwaccels:

Enabled parsers:
aac                     cook                    dvbsub                  h261                    mpeg4video              rv30                    vorbis
aac_latm                dca                     dvd_nav                 h263                    mpegaudio               rv40                    vp3
ac3                     dirac                   dvdsub                  h264                    mpegvideo               sbc                     vp8
adx                     dnxhd                   flac                    hevc                    opus                    sipr                    vp9
bmp                     dpx                     g729                    mjpeg                   png                     tak                     xma
cavsvideo               dvaudio                 gsm                     mlp                     pnm                     vc1

Enabled demuxers:
aa                      caf                     gdv                     image_webp_pipe         mtv                     rawvideo                tedcaptions
aac                     cavsvideo               genh                    image_xpm_pipe          musx                    realtext                thp
ac3                     cdg                     gif                     ingenient               mv                      redspark                threedostr
acm                     cdxl                    gsm                     ipmovie                 mvi                     rl2                     tiertexseq
act                     cine                    gxf                     ircam                   mxf                     rm                      tmv
adf                     codec2                  h261                    iss                     mxg                     roq                     truehd
adp                     codec2raw               h263                    iv8                     nc                      rpl                     tta
ads                     concat                  h264                    ivf                     nistsphere              rsd                     tty
adx                     data                    hevc                    ivr                     nsp                     rso                     txd
aea                     daud                    hls                     jacosub                 nsv                     rtp                     ty
afc                     dcstr                   hnm                     jv                      nut                     rtsp                    v210
aiff                    dfa                     ico                     live_flv                nuv                     s337m                   v210x
aix                     dirac                   idcin                   lmlm4                   ogg                     sami                    vag
amr                     dnxhd                   idf                     loas                    oma                     sap                     vc1
amrnb                   dsf                     iff                     lrc                     paf                     sbc                     vc1t
amrwb                   dsicin                  ilbc                    lvf                     pcm_alaw                sbg                     vivo
anm                     dss                     image2                  lxf                     pcm_f32be               scc                     vmd
apc                     dts                     image2_alias_pix        m4v                     pcm_f32le               sdp                     vobsub
ape                     dtshd                   image2_brender_pix      matroska                pcm_f64be               sdr2                    voc
apng                    dv                      image2pipe              mgsts                   pcm_f64le               sds                     vpk
aptx                    dvbsub                  image_bmp_pipe          microdvd                pcm_mulaw               sdx                     vplayer
aptx_hd                 dvbtxt                  image_dds_pipe          mjpeg                   pcm_s16be               segafilm                vqf
aqtitle                 dxa                     image_dpx_pipe          mjpeg_2000              pcm_s16le               shorten                 w64
asf                     ea                      image_exr_pipe          mlp                     pcm_s24be               siff                    wav
asf_o                   ea_cdata                image_j2k_pipe          mlv                     pcm_s24le               sln                     wc3
ass                     eac3                    image_jpeg_pipe         mm                      pcm_s32be               smacker                 webm_dash_manifest
ast                     epaf                    image_jpegls_pipe       mmf                     pcm_s32le               smjpeg                  webvtt
au                      ffmetadata              image_pam_pipe          mov                     pcm_s8                  smush                   wsaud
avi                     filmstrip               image_pbm_pipe          mp3                     pcm_u16be               sol                     wsd
avr                     fits                    image_pcx_pipe          mpc                     pcm_u16le               sox                     wsvqa
avs                     flac                    image_pgm_pipe          mpc8                    pcm_u24be               spdif                   wtv
bethsoftvid             flic                    image_pgmyuv_pipe       mpegps                  pcm_u24le               srt                     wv
bfi                     flv                     image_pictor_pipe       mpegts                  pcm_u32be               stl                     wve
bfstm                   fourxm                  image_png_pipe          mpegtsraw               pcm_u32le               str                     xa
bink                    frm                     image_ppm_pipe          mpegvideo               pcm_u8                  subviewer               xbin
bintext                 fsb                     image_psd_pipe          mpjpeg                  pjs                     subviewer1              xmv
bit                     g722                    image_qdraw_pipe        mpl2                    pmp                     sup                     xvag
bmv                     g723_1                  image_sgi_pipe          mpsub                   pva                     svag                    xwma
boa                     g726                    image_sunrast_pipe      msf                     pvf                     swf                     yop
brstm                   g726le                  image_svg_pipe          msnwc_tcp               qcp                     tak                     yuv4mpegpipe
c93                     g729                    image_tiff_pipe         mtaf                    r3d

Enabled muxers:
a64                     data                    gsm                     md5                     nut                     pcm_u32be               stream_segment
ac3                     daud                    gxf                     microdvd                oga                     pcm_u32le               sup
adts                    dirac                   h261                    mjpeg                   ogg                     pcm_u8                  swf
adx                     dnxhd                   h263                    mkvtimestamp_v2         ogv                     psp                     tee
aiff                    dts                     h264                    mlp                     oma                     rawvideo                tg2
amr                     dv                      hash                    mmf                     opus                    rm                      tgp
apng                    eac3                    hds                     mov                     pcm_alaw                roq                     truehd
aptx                    f4v                     hevc                    mp2                     pcm_f32be               rso                     tta
aptx_hd                 ffmetadata              hls                     mp3                     pcm_f32le               rtp                     uncodedframecrc
asf                     fifo                    ico                     mp4                     pcm_f64be               rtp_mpegts              vc1
asf_stream              fifo_test               ilbc                    mpeg1system             pcm_f64le               rtsp                    vc1t
ass                     filmstrip               image2                  mpeg1vcd                pcm_mulaw               sap                     voc
ast                     fits                    image2pipe              mpeg1video              pcm_s16be               sbc                     w64
au                      flac                    ipod                    mpeg2dvd                pcm_s16le               scc                     wav
avi                     flv                     ircam                   mpeg2svcd               pcm_s24be               segafilm                webm
avm2                    framecrc                ismv                    mpeg2video              pcm_s24le               segment                 webm_chunk
bit                     framehash               ivf                     mpeg2vob                pcm_s32be               singlejpeg              webm_dash_manifest
caf                     framemd5                jacosub                 mpegts                  pcm_s32le               smjpeg                  webp
cavsvideo               g722                    latm                    mpjpeg                  pcm_s8                  smoothstreaming         webvtt
codec2                  g723_1                  lrc                     mxf                     pcm_u16be               sox                     wtv
codec2raw               g726                    m4v                     mxf_d10                 pcm_u16le               spdif                   wv
crc                     g726le                  matroska                mxf_opatom              pcm_u24be               spx                     yuv4mpegpipe
dash                    gif                     matroska_audio          null                    pcm_u24le               srt

Enabled protocols:
async                   data                    gopher                  icecast                 pipe                    rtp                     tee
cache                   ffrtmphttp              hls                     md5                     prompeg                 srtp                    udp
concat                  file                    http                    mmsh                    rtmp                    subfile                 udplite
crypto                  ftp                     httpproxy               mmst                    rtmpt                   tcp                     unix

Enabled filters:
abench                  asendcmd                cover_rect              flanger                 lutyuv                  realtime                split
abitscope               asetnsamples            crop                    floodfill               mandelbrot              remap                   spp
acompressor             asetpts                 cropdetect              format                  maskedclamp             removegrain             ssim
acontrast               asetrate                crossfeed               fps                     maskedmerge             removelogo              stereo3d
acopy                   asettb                  crystalizer             framepack               mcdeint                 repeatfields            stereotools
acrossfade              ashowinfo               curves                  framerate               mcompand                replaygain              stereowiden
acrusher                asidedata               datascope               framestep               mergeplanes             reverse                 streamselect
adelay                  asplit                  dcshift                 fspp                    mestimate               rgbtestsrc              super2xsai
adrawgraph              astats                  dctdnoiz                gblur                   metadata                roberts                 superequalizer
aecho                   astreamselect           deband                  geq                     midequalizer            rotate                  surround
aemphasis               atadenoise              decimate                gradfun                 minterpolate            sab                     swaprect
aeval                   atempo                  deconvolve              haas                    mix                     scale                   swapuv
aevalsrc                atrim                   deflate                 haldclut                movie                   scale2ref               tblend
afade                   avectorscope            deflicker               haldclutsrc             mpdecimate              select                  telecine
afftfilt                avgblur                 dejudder                hdcd                    mptestsrc               selectivecolor          testsrc
afifo                   bandpass                delogo                  headphone               negate                  sendcmd                 testsrc2
afir                    bandreject              deshake                 hflip                   nlmeans                 separatefields          threshold
aformat                 bass                    despill                 highpass                nnedi                   setdar                  thumbnail
agate                   bbox                    detelecine              hilbert                 noformat                setfield                tile
ahistogram              bench                   dilation                histeq                  noise                   setpts                  tinterlace
aiir                    biquad                  displace                histogram               normalize               setrange                tlut2
ainterleave             bitplanenoise           doubleweave             hqdn3d                  null                    setsar                  tonemap
alimiter                blackdetect             drawbox                 hqx                     nullsink                settb                   transpose
allpass                 blackframe              drawgraph               hstack                  nullsrc                 showcqt                 treble
allrgb                  blend                   drawgrid                hue                     oscilloscope            showfreqs               tremolo
allyuv                  boxblur                 drmeter                 hwdownload              overlay                 showinfo                trim
aloop                   bwdif                   dynaudnorm              hwmap                   owdenoise               showpalette             unpremultiply
alphaextract            cellauto                earwax                  hwupload                pad                     showspectrum            unsharp
alphamerge              channelmap              ebur128                 hysteresis              palettegen              showspectrumpic         uspp
amerge                  channelsplit            edgedetect              idet                    paletteuse              showvolume              vaguedenoiser
ametadata               chorus                  elbg                    il                      pan                     showwaves               vectorscope
amix                    chromakey               entropy                 inflate                 perms                   showwavespic            vflip
amovie                  ciescope                eq                      interlace               perspective             shuffleframes           vfrdet
anequalizer             codecview               equalizer               interleave              phase                   shuffleplanes           vibrato
anoisesrc               color                   erosion                 join                    pixdesctest             sidechaincompress       vignette
anull                   colorbalance            extractplanes           kerndeint               pixscope                sidechaingate           vmafmotion
anullsink               colorchannelmixer       extrastereo             lenscorrection          pp                      sidedata                volume
anullsrc                colorkey                fade                    life                    pp7                     signalstats             volumedetect
apad                    colorlevels             fftfilt                 limiter                 premultiply             signature               vstack
aperms                  colormatrix             field                   loop                    prewitt                 silencedetect           w3fdif
aphasemeter             colorspace              fieldhint               loudnorm                pseudocolor             silenceremove           waveform
aphaser                 compand                 fieldmatch              lowpass                 psnr                    sine                    weave
apulsator               compensationdelay       fieldorder              lumakey                 pullup                  smartblur               xbr
arealtime               concat                  fifo                    lut                     qp                      smptebars               yadif
aresample               convolution             fillborders             lut2                    random                  smptehdbars             yuvtestsrc
areverse                convolve                find_rect               lut3d                   readeia608              sobel                   zoompan
aselect                 copy                    firequalizer            lutrgb                  readvitc                spectrumsynth

Enabled bsfs:
aac_adtstoasc           eac3_core               h264_mp4toannexb        hevc_mp4toannexb        mov2textsub             noise                   trace_headers
chomp                   extract_extradata       h264_redundant_pps      imx_dump_header         mp3_header_decompress   null                    vp9_raw_reorder
dca_core                filter_units            hapqa_extract           mjpeg2jpeg              mpeg2_metadata          remove_extradata        vp9_superframe
dump_extradata          h264_metadata           hevc_metadata           mjpega_dump_header      mpeg4_unpack_bframes    text2movsub             vp9_superframe_split

Enabled indevs:
fbdev                   lavfi                   oss                     v4l2

Enabled outdevs:
fbdev                   oss                     v4l2
```
总结下来就是以下几点：

1，启用了几个输入输出设备；启用了（很）多个bsfs、protocol、filter、muxer、demuxer、parser、encoder、decoder；

2，没有启用hwaccels；

3，编译完要产出的库：avcodec、avfilter、avformat、avutil 、postproc、swresample、swscale、avdevice；要产出的可执行文件：ffmpeg、ffprobe；

4，使用了这些三方库：iconv、libx264、lzma、xlib、zlib；

5，因为要使用libx264编码库，所以加上了--enable-libx264；又因为libx264是GPL条款，比ffmpeg的LGPL更加严格，所以还需要加上--enable-gpl。

6，启用了pthreads线程支持；没有去掉符号表；禁用了编译优化；禁用了大量x86之上的强大指令集（编译时间因此而大大减少）：
```bash
MMX enabled               no
MMXEXT enabled            no
3DNow! enabled            no
3DNow! extended enabled   no
SSE enabled               no
SSSE3 enabled             no
AESNI enabled             no
AVX enabled               no
AVX2 enabled              no
AVX-512 enabled           no
XOP enabled               no
FMA3 enabled              no
FMA4 enabled              no
i686 features enabled     yes
CMOV is fast              yes
EBX available             yes
EBP available             no
debug symbols             yes
strip symbols             no
optimize for size         no
optimizations             no
static                    no
shared                    yes
postprocessing support    yes
network support           yes
threading support         pthreads
```
基于此编译参数，gemfield得出了一个初步的性能报告。注意，下面的结果只具有参考意义（因为不同的硬件平台等，Gemfield使用的CPU是Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz）：
```bash
gemfield@ThinkPad-X1C:~/test/PyAV$ python remux.py 
try to open stream /home/gemfield/gemfield.mp4
before av open
after av open
('start_time: ', 1527351675.136291)
('end_time: ', 1527351717.412348)
(4554, 2398, 2153, 42.27605700492859)
('time per video frame: ', 0.017629715181371387)
('video frames per second: ', 56.722413817363304)
```
一秒中大约decode 56个视频帧。

## 3，更改ffmpeg的编译参数

去掉configure中任何不利于性能提升的参数，得到新的编译参数：
```bash
 ./configure --disable-static --enable-shared --disable-doc --enable-libx264 --enable-gpl
......
MMX enabled               yes
MMXEXT enabled            yes
3DNow! enabled            yes
3DNow! extended enabled   yes
SSE enabled               yes
SSSE3 enabled             yes
AESNI enabled             yes
AVX enabled               yes
AVX2 enabled              yes
AVX-512 enabled           yes
XOP enabled               yes
FMA3 enabled              yes
FMA4 enabled              yes
i686 features enabled     yes
CMOV is fast              yes
EBX available             yes
EBP available             yes
debug symbols             yes
strip symbols             yes
optimize for size         no
optimizations             yes
static                    no
shared                    yes
postprocessing support    yes
network support           yes
threading support         pthreads
```
基于此编译参数，gemfield得出了又一个初步的性能报告。注意，下面的结果只具有参考意义（因为不同的硬件平台等，Gemfield使用的CPU是Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz）：
```bash 
gemfield@ThinkPad-X1C:~/test/PyAV$ python remux.py 
try to open stream /home/gemfield/gemfield.mp4
before av open
after av open
('start_time: ', 1527384957.096571)
('end_time: ', 1527384963.782417)
(4554, 2398, 2153, 6.6858460903167725)
('time per video frame: ', 0.0027880926148109975)
('video frames per second: ', 358.66814276102843)
```
一秒中大约decode 358个视频帧。

## 4，启用--enable-static

不可以，python封装需要动态库。

## 5，让ffmpeg只静态链接第三方库

configure的时候添加--pkg-config-flags="--static" 和 --extra-libs="-lpthread -lm"（如果能检测pthreads，默认就有）：
```bash
./configure \
    --disable-static \
    --enable-shared \
    --disable-doc \
    --enable-libx264 \
    --enable-gpl \
    --pkg-config-flags="--static"\
    --extra-libs="-lpthread -lm" \
......
```
测试效果：没有什么变化。

## 6，使用官方提供的优化tips

configure的时候添加 --extra-cflags="-march=native" 和 --enable-hardcoded-tables
```bash
./configure \
    --disable-static \
    --enable-shared \
    --disable-doc \
    --enable-libx264 \
    --enable-gpl \
    --pkg-config-flags="--static" \
    --extra-libs="-lpthread -lm" \
    --extra-cflags="-march=native" \
    --enable-hardcoded-tables \
......
```
测试效果：没有什么变化。

# 网友评论
Zuxy：
```bash
3DNow!/FMA4/XOP 等针对 AMD 的优化可以禁掉，生成的二进制文件会小一点。
```
gemfield:
```bash
默认的configure选项是 ./configure --disable-static --enable-shared --disable-doc --disable-optimizations --disable-mmx --enable-debug=3 --enable-gpl --enable-libx264 --disable-stripping --prefix=/opt/PyAV/vendor/build/ffmpeg-4.0，可以看到禁止掉了各种优化
```
wlgqa:
```bash
我用conda安装pyav，conda会自动安装ffmpeg，运行ffmpeg看到的编译选项是--disable-doc --disable-openssl --enable-shared --enable-static --extra-cflags='-Wall -g -m64 -pipe -O3 -march=x86-64 -fPIC' --extra-cxxflags='-Wall -g -m64 -pipe -O3 -march=x86-64 -fPIC' --extra-libs='-lpthread -lm -lz' --enable-zlib --enable-pic --enable-pthreads --enable-gpl --enable-version3 --enable-hardcoded-tables --enable-avresample --enable-libfreetype --enable-gnutls --enable-libx264 --enable-libopenh264
```
