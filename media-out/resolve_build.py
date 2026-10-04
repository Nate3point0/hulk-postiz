#!/usr/bin/env python3
"""Build the 'You're Not Done Yet' timeline in DaVinci Resolve via its scripting API.

Run on the Mac with Resolve open (Preferences > General > External scripting: Local):
  export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
  export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
  export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
  python3 resolve_build.py [--render]

V1 = video, A1 = voice-over, A2 = music bed (-20 dB), A3 = empty for your SFX.
Markers on the timeline show where the whoosh, ding and pop sounds go.
"""
import os, sys
import DaVinciResolveScript as dvr

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
VIDEO, VO, MUSIC = (os.path.join(HERE, f) for f in
                    ("kidney_not_done_yet_9x16.mp4", "kidney_vo.wav", "kidney_music_bed.wav"))
SFX = ([(t, "Blue", "WHOOSH") for t in (4, 14, 30, 48, 57)]
       + [(14.8 + i * 2.4, "Green", f"DING {i + 1}") for i in range(6)]
       + [(t, "Yellow", "POP") for t in (38, 39.2, 40.4)])

resolve = dvr.scriptapp("Resolve")
pm = resolve.GetProjectManager()
proj = pm.CreateProject("Kidney_NotDoneYet") or pm.LoadProject("Kidney_NotDoneYet")
for k, v in {"timelineResolutionWidth": "1080", "timelineResolutionHeight": "1920",
             "timelineFrameRate": str(FPS), "timelinePlaybackFrameRate": str(FPS)}.items():
    proj.SetSetting(k, v)

pool = proj.GetMediaPool()
v, vo, mus = pool.ImportMedia([VIDEO, VO, MUSIC])
tl = pool.CreateEmptyTimeline("NotDoneYet_9x16")
proj.SetCurrentTimeline(tl)
tl.AddTrack("audio", "stereo")
tl.AddTrack("audio", "stereo")
start = tl.GetStartFrame()
pool.AppendToTimeline([{"mediaPoolItem": v, "trackIndex": 1, "mediaType": 1, "recordFrame": start}])  # video is silent
pool.AppendToTimeline([{"mediaPoolItem": vo, "trackIndex": 1, "mediaType": 2, "recordFrame": start}])
pool.AppendToTimeline([{"mediaPoolItem": mus, "trackIndex": 2, "mediaType": 2, "recordFrame": start}])
for item in tl.GetItemListInTrack("audio", 2):
    item.SetProperty("Volume", -20.0)

for sec, color, name in SFX:
    tl.AddMarker(int(sec * FPS), color, name, "Drop SFX on A3 here", 1)

print("Timeline built. Sidechain-duck A2 under A1 in Fairlight, add SFX on A3 at markers.")

if "--render" in sys.argv:
    proj.SetRenderSettings({"TargetDir": HERE, "CustomName": "kidney_not_done_yet_FINAL",
                            "FormatWidth": 1080, "FormatHeight": 1920, "FrameRate": FPS})
    proj.SetCurrentRenderFormatAndCodec("mp4", "H264")
    proj.AddRenderJob()
    proj.StartRendering()
    print("Rendering to", HERE)
