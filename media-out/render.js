const {chromium}=require('playwright');const {spawn}=require('child_process');
(async()=>{const fps=+process.env.FPS||30,dur=61,only=process.env.STILLS;
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+__dirname+'/anim.html');
if(only){for(const t of only.split(',')){await p.evaluate(t=>draw(+t),t);await p.screenshot({path:`still_${t}.png`})}await b.close();return}
const ff=spawn('ffmpeg',['-y','-f','image2pipe','-framerate',''+fps,'-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart','kidney_not_done_yet_9x16.mp4'],{stdio:['pipe','inherit','inherit']});
for(let i=0;i<fps*dur;i++){await p.evaluate(t=>draw(t),i/fps);ff.stdin.write(await p.screenshot({type:'jpeg',quality:92}))}
ff.stdin.end();ff.on('close',()=>b.close())})();
