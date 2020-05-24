
from collections import deque
from masonry import Brick,Stack
from math import floor

import cv2
import glob
import itertools
import json
import math
import mimetypes
import numpy as np
import os
import random
import requests
import statistics
import subprocess as sp
import sys
import time

def isVideoFile(filename):
  g = mimetypes.guess_type(filename)
  return g is not None and g[0] is not None and 'video' in g[0]

urls = sys.argv[1:]

if len(urls)==0:
  print('NoInput')
  exit()

print(urls)
inputNameList = []
inputdims = []
alignments = []

hasaudio  = []
bricks=[]
images=[]
durations=[]
starts=[]
megMult = 1024*1024

otuputWidth=1440
maxHeight=1440
minAllowedArea=200*200
layoutPermutationCount=200
targetDuration=60
postMoveScrollBack=1

maxSize = 4.0*megMult
minsize = 3.5*megMult
targetSize = (maxSize+minsize)/2

crf=4
br=2000000
threads=4
maxPerGrid=9

outputFormats = ['webm','hqwebm']
outputFormat  = ''

basepath=int(time.time())

os.path.exists('tempwebms') or os.mkdir(('tempwebms'))
countTempfolders=str(len(os.listdir('tempwebms'))+2)

while outputFormat not in outputFormats:
  outputFormat = input('outputFormat?[{}]>'.format(','.join(outputFormats)))
  if outputFormat == '':
    outputFormat = outputFormats[-1]

outbanner = input('banner?>')
outfilename = input('filename?>')

try:
  targetDuration = int(input('targetDuration>'))
except:
  pass

try:
  postMoveScrollBack = int(input('postMoveScrollBack>'))
except:
  pass


try:
  maxPerGrid = int(input('maxPerGrid (max{})>'.format(len(urls))))
except:
  pass


print(urls,urls[0],os.path.isfile(urls[0]),os.path.isfile(urls[0]))

if os.path.isfile(urls[0]) or os.path.isdir(urls[0]) or '*' in urls[0]:

  if input('cut?').upper()=='Y':

    outurls=[]

    if len(urls)==1 and os.path.isdir(urls[0]):
      urls = [os.path.join(urls[0],f) for f in os.listdir(urls[0]) if isVideoFile(f)]
    elif '*' in urls[0]:
      urls = [f for f in glob.glob(urls[0]) if isVideoFile(f)]

    urls = sorted(urls,key=lambda x:os.stat(x).st_size,reverse=True)
    random.shuffle(urls)


    extractQeueue = []
    exitEarly=False
    for file in urls:
      ic = input(file).upper()
      if ic=='Q':
        exit()
      elif ic=='S':
        continue

      if exitEarly:
        break

      basename = os.path.basename(file)

      proc = sp.Popen(['mpv','--script','easycrop.lua','--script-opts=easyCrop-windowWidth={},easyCrop-postMoveOffset={}'.format(targetDuration,postMoveScrollBack),file],stdout=sp.PIPE)
      outs,errs=proc.communicate()

      x,y,w,h = 0,0,0,0

      for line in outs.split(b'\n'):
        
        if b'easycrop coords' in line:
          x,y,w,h = line.strip().split(b' ')[-4:]
          x,y,w,h = int(x),int(y),int(w),int(h)
          print(x,y,w,h)

        if b'HKEY' in line:
          exitEarly=True
          break

        if b'easycrop range' in line:
          start,end,r = line.strip().split(b' ')[-3:]
          start = float(start)
          end   = float(end)
          outname = os.path.join('tempwebms',countTempfolders,str(start)+'_'+basename+'.mp4')
          extractQeueue.append( (file,start,end,x,y,w,h,outname) )


    for i,(filename,start,end,x,y,w,h,outname) in enumerate(extractQeueue):
      os.path.exists(os.path.join('tempwebms',countTempfolders)) or os.mkdir(os.path.join('tempwebms',countTempfolders))

      print('cut',filename,start,end,i,'/',len(extractQeueue))
      if sum([x,y,w,h])==0:
        proc = sp.Popen(['ffmpeg', '-y'
                        ,'-ss', str(start)
                        ,'-i', filename
                        ,'-t', str(targetDuration)
                        ,'-c:v', 'libx264'
                        ,'-crf', '0'
                        ,'-ac', '1' ,outname],stdin=sp.DEVNULL,stdout=sp.DEVNULL,stderr=sp.DEVNULL)
      else:
        proc = sp.Popen(['ffmpeg','-y'
                        ,'-ss', str(start)
                        ,'-i', filename
                        ,'-t', str(targetDuration)
                        ,'-vf', 'crop={}:{}:{}:{}'.format(x,y,w,h)
                        ,'-c:v', 'libx264'
                        ,'-crf', '0'
                        ,'-ac', '1',outname],stdin=sp.DEVNULL,stdout=sp.DEVNULL,stderr=sp.DEVNULL)

      proc.communicate()
      outurls.append(outname)

    urls=outurls

for i,url in enumerate(urls):

  basename = url.split('/')[-1]
  
  if not os.path.isfile(url):
    localname = os.path.join('tempwebms',basename)
  else:
    localname = url
  

  if not os.path.exists(localname):
    content = requests.get(url).content
    with open(localname,'wb') as of:
      of.write(content)


  inputNameList.append(localname)
  dimensions = sp.Popen(['ffprobe'
                        ,'-v'
                        ,'error'
                        ,'-select_streams'
                        ,'v:0'
                        ,'-show_entries'
                        ,'stream=height,width'
                        ,'-of'
                        ,'csv=s=x:p=0',localname],stdout=sp.PIPE).communicate()[0].strip()


  duration = sp.Popen(['ffprobe' 
                      ,'-v', 'error' 
                      ,'-show_entries'
                        ,'format=duration'
                      ,'-of'
                      ,'default=noprint_wrappers=1:nokey=1'
                      ,localname],stdout=sp.PIPE).communicate()[0].strip()
  duration = float(duration)
  durations.append(duration)

  audio = sp.Popen(['ffprobe'
                        ,'-v'
                        ,'error'
                        ,'-select_streams'
                        ,'a','-show_entries', 'stream=codec_type',localname],stdout=sp.PIPE).communicate()[0]
  cap = cv2.VideoCapture(localname)
  while(cap.isOpened()):
    ret, frame = cap.read()
    images.append(frame)
    break
  cap.release()
  cv2.destroyAllWindows()


  w,h = dimensions.split(b'x')
  vh=int(h)
  vw=int(w)
  inputdims.append((vw,vh))
  hasaudio.append(len(audio)>0)
  bricks.append(Brick(i,vw,vh))

if len(bricks)==0:
  exit()

minDuration = min(durations)-0.5

startTimes=[]

for name,duration in zip(inputNameList,durations):
  startTimes.append(str((duration/2)-(minDuration/2) ))


print(inputdims)
print(hasaudio)


n=0
from itertools import permutations,combinations_with_replacement


def encodeRun(run):
  global br


  run=sorted(run,key=lambda x:(x[1]))
  runIndex=0

  passedRun = []

  lastresizeScale=0
  fftoresizescaledrop=False



  while 1:
    key,resizeScale,w,h,logger,layout,coords = run[runIndex%len(run)]

    canvas = np.zeros((int(h),int(w),3),np.uint8)
    for k,(xo,yo,cw,ch,ar,ow,oh) in sorted(logger.items(),key=lambda x:int(x[0])):
      rimg = cv2.resize(images[k],(int(floor(cw)),int(floor(ch))))
      try:
        canvas[int(yo):int(yo)+int(floor(ch)),int(xo):int(xo)+int(floor(cw)),:]=rimg[:int(floor(ch)),:int(floor(cw)),:]
      except Exception as e:
        print(e)

    print(layout,'resizeScale:',resizeScale)
    cv2.imshow('plan',canvas)


    k = cv2.waitKey(0)
    if k ==ord('y'):
      passedRun.append( (key,resizeScale,w,h,logger,layout,coords) )
    elif k == ord('q'):
      break
    elif k == ord('a'):
      runIndex-=1
    elif k == ord('d'):
      runIndex+=1
    elif k == ord('A'):
      runIndex-= max(10,int(len(run)*0.005))
    elif k == ord('D'):
      runIndex+= max(10,int(len(run)*0.005))
    elif k == ord('e'):
      exit()
    else:
      continue
  cv2.destroyAllWindows()

  for _,std,vow,voh,logger,layout,coords in passedRun:
    layout = layout.replace('|','_')
    ffmpegFilterCommand = "color=s={w}x{h}:c=black[base],".format(w=int(vow),h=int(voh))

    inputScales=[]
    
    inputAudio  = []
    outputsAudio = []

    overlays   =[]

    audioSizeRatios = []
    keys = []

    vols={}
    klookup={}
    streropos={}
    name=[]
    for i,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
        
      streropos[k] = (((xo+w/2)/vow)-0.5)

      klookup[k]=i
      file = inputNameList[k]
      name.append( os.path.basename(file) )
      print(file)
      proc = sp.Popen(['ffprobe', '-f', 'lavfi'
                      ,'-i','amovie=\'{}\',astats=metadata=1:reset=1'.format(file.replace('\\','/').replace(':','\\:').replace('\'','\\\\\''))
                      ,'-show_entries', 'frame=pkt_pts_time:frame_tags=lavfi.astats.Overall.RMS_level,lavfi.astats.1.RMS_level,lavfi.astats.2.RMS_level'
                      ,'-of', 'csv=p=0'],stdout=sp.PIPE,stderr=sp.DEVNULL)
      outs,errs = proc.communicate()
      minvol=float('inf')
      maxvol=float('-inf')
      for line in outs.decode('utf8').split('\n'):
        if line.strip() != '':
          ts,vol1,vol2 = line.strip().split(',')
          vol= -((float(vol1)+float(vol2))/2)
          minvol = min(minvol,vol)
          maxvol = max(maxvol,vol)
      for line in outs.decode('utf8').split('\n'):
        if line.strip() != '':
          ts,vol1,vol2 = line.strip().split(',')
          vol= -((float(vol1)+float(vol2))/2)
          vol = (vol-minvol)/(maxvol-minvol)
          vols.setdefault(round(float(ts),1),{}).setdefault(k,[]).append(vol)

    name = ','.join(name)
    if len(outbanner)==0:
      name = outbanner

    loudSeq=[]

    for k,v in sorted(vols.items()):

      loudest=None
      loudLevel=None

      for fn,vl in v.items():
        mv = statistics.mean(vl)
        if loudLevel is None or loudLevel<mv:
          loudest = fn
          loudLevel = mv

      loudSeq.append( (k,klookup[loudest],loudLevel) )

    from collections import deque

    selection=None
    hist=deque([],20)

    selectedSections=[]

    for second,index,_ in loudSeq:
      if selection is None:
        selection = index
      hist.append(index)
      try:
        selection=statistics.mode(list(hist)+[selection] )
      except:
        pass
      selectedSections.append( (second,selection) )

    for second,selection in selectedSections:
      print(second,selection)

    volcommands = {}
    for i,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
      onSections = []
      for keybool,group in itertools.groupby(selectedSections,key=lambda x:x[1]==i):
        if keybool:
          gl = [x[0] for x in group]
          onSections.append( (min(gl),max(gl)) )
      if len(onSections)>0:
        volcommands[k] = '+'.join([ '(between(t,{s},{e}) + ( between(t,{s}-1,{s}+1)*cos(t-{s}) ) + ( between(t,{e}-1,{e}+1)*cos(t-{e}) ))'.format(s=x[0],e=x[1]) for x in onSections])
        
        print(k,volcommands[k])

    print(volcommands)

    print(ow,oh)
    inputList = []
  
    for snum,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
      
      inputList.extend(['-i',inputNameList[k]])

      print([k,xo,yo,w,h,ar,ow,oh])

      inputScales.append('[{k}:v]setpts=PTS-STARTPTS+{st},scale={w}:{h}[vid{k}]'.format(k=snum,w=int(w),h=int(h),st=0))

      if hasaudio[k]:
        inputAudio.append('[{k}:a]loudnorm=I=-16:TP=-1.5:LRA=11,atrim=duration={mindur},volume=\'1.0*min(1,{vol})\':eval=frame,pan=stereo|c0=c0|c1=c0,stereotools=balance_out={panpos}[aud{k}]'.format(k=snum,mindur=minDuration,panpos=streropos.get(k,0),vol=volcommands.get(k,'0.0')))
        outputsAudio.append('[aud{k}]'.format(k=snum))
      

      srcLayer='[tmp{k}]'.format(k=snum)
      if snum==0:
        srcLayer='[base]'
      destLayer='[tmp{k}]'.format(k=int(snum)+1)
      overlay = '[vid{k}]overlay=shortest=1:x={x}:y={y}'.format(k=snum,x=int(xo),y=int(yo))

      overlays.append(srcLayer+overlay+destLayer )

    if len(inputAudio)>0:
      ffmpegFilterCommand += ','.join(inputAudio) + ','

    ffmpegFilterCommand += ','.join(inputScales)
    ffmpegFilterCommand += ',' + ','.join(overlays)
    if len(outbanner)==0:
      ffmpegFilterCommand += ',[tmp{k}]null,pad=ceil(iw/2)*2:ceil(ih/2)*2[videoOut]'.format(k=snum+1)
    else:
      ffmpegFilterCommand += ',[tmp{k}]null,pad=ceil(iw/2)*2:ceil(ih/2)*2,'.format(k=snum+1)
      ffmpegFilterCommand +=  "drawtext=text='"+outbanner+"':fontsize=16:shadowcolor=black:shadowx=2:shadowy=2:fontcolor=white:x=5:y='(h-text_h)-5+(gte(t,2)*((t-2)*50))'"
      ffmpegFilterCommand += '[videoOut]'

    


    
    if len(inputAudio)>1:
      ffmpegFilterCommand +=  ',{}amix=inputs={}:duration=shortest[audioOut]'.format(''.join(outputsAudio),len(outputsAudio))
    if len(inputAudio)==1:
      ffmpegFilterCommand +=  ',{}anull[audioOut]'.format(''.join(outputsAudio),len(outputsAudio))
  
    print('')
    print(ffmpegFilterCommand)
    print('')


    cmd_pre = ["ffmpeg",'-y']+inputList+['-filter_complex',ffmpegFilterCommand]
    cmd_pre += ['-metadata', 'title="{}"'.format(name.replace('"',''))]

    cmd_pre += ['-map','[videoOut]'] 
    if len(inputAudio)>0:
      cmd_pre += ['-map','[audioOut]']

    print('len(inputAudio)',len(inputAudio))
    if outputFormat == 'webm':
      cmd_pre += [  "-shortest" 
               ,"-lag-in-frames", "16" 
               ,"-slices", "8"
               ,"-cpu-used", "0"
               ,"-copyts"
               ,"-start_at_zero"
               ,"-c:v","libvpx" 
               ,"-c:a"  ,"libvorbis"
               ,"-stats"
               ,"-pix_fmt","yuv420p"
               ,"-bufsize", "3000k"
               ,"-threads", str(threads)
               ,"-quality", "best"]
    elif outputFormat == 'hqwebm':
      cmd_pre += [  "-shortest" 
               ,"-slices", "8"
               ,"-copyts"
               ,"-start_at_zero"
               ,"-c:v","libvpx" 
               ,"-c:a"  ,"libvorbis"
               ,"-stats"
               ,"-pix_fmt","yuv420p"
               ,"-bufsize", "3000k"
               ,"-threads", str(threads)]
    encodingpassN=0
    while 1:
      encodingpassN+=1
      if outputFormat == 'webm':
        cmd = cmd_pre + ["-crf"  ,str(crf)
                        ,"-b:v",str(br)
                        ,"-ac"   ,"2"
                        ,"-sn",'{}_{}_{}.{}'.format(basepath,outfilename,layout,'webm')]
      elif outputFormat == 'hqwebm':
        cmd = cmd_pre + ["-crf"  ,'4'
                        ,"-b:v","16M"
                        ,"-qmin","0"
                        ,"-qmax","10"
                        ,"-ac"   ,"2"
                        ,"-sn",'{}_{}_{}.{}'.format(basepath,outfilename,layout,'webm')]

      print('encodingpassN',encodingpassN,br)
      print(' '.join(cmd))
      proc = sp.Popen(cmd,stdin=sp.DEVNULL)
      proc.communicate()

      finalSize = os.stat('{}_{}_{}.{}'.format(basepath,outfilename,layout,'webm')).st_size

      if outputFormat == 'webm':
        print('finalSize',finalSize,'tooBig:',finalSize > maxSize,abs(finalSize-maxSize),'tooSmall:',finalSize < minsize,abs(finalSize-minsize))
        if finalSize > maxSize:
          brn =  br * (1/(finalSize/targetSize))
          if brn==br:
            br=br*0.9
          else:
            br=brn
        elif  finalSize < minsize and encodingpassN<5:
          brn =  br * (1/(finalSize/targetSize))
          if brn==br:
            br=br*1.1
          else:
            br=brn
        else:
          break
      else:
        break





seenLayouts={}

def generateActionCombinations(head,targetInserts,stackDepth):

  joinedHead = ''.join(head)

  badSubstringMap = {
  #  'haha':'haa',
  #  'vaavaa':'vaaaa',
  #  'haaahaaa':'haaaaaa',
  #  'vaaavaaa':'vaaaaaa',

  }

  if joinedHead in badSubstringMap:
    head = list(badSubstringMap.get(joinedHead,joinedHead))
    stackDepth-=1


  if len(head)==0:
    for r in generateActionCombinations(head+['v'],targetInserts,stackDepth+1):
      yield r
    for r in generateActionCombinations(head+['h'],targetInserts,stackDepth+1):
      yield r
  else:
    insertCount = head.count('a')
    if insertCount>=targetInserts:
      if stackDepth>1:
        for r in generateActionCombinations(head+['V'],targetInserts,1):
          yield r
        for r in generateActionCombinations(head+['H'],targetInserts,1):
          yield r
      else:
        yield ''.join(head)
    else:
      if head[-1] == 'V':
        for r in generateActionCombinations(head+['h'],targetInserts,stackDepth+1):
          yield r
      if head[-1] == 'H':
        for r in generateActionCombinations(head+['v'],targetInserts,stackDepth+1):
          yield r
      else:
        seen=[]
        lastsubStack=None
        for e in head[::-1]:
          seen.append(e)
          if e in 'vh':
            lastsubStack=e
            break
        lastStackMayBeClosed = (('v' in seen) or ('h' in seen)) and seen.count('a')>1 and (stackDepth-head.count('a'))<2 and (not  (('V' in seen) or ('H' in seen)))

        if lastStackMayBeClosed:
          
          if lastsubStack=='h':
            for r in generateActionCombinations(head+['V'],targetInserts,1):
              yield r
            for r in generateActionCombinations(head+['v'],targetInserts,stackDepth+1):
              yield r

          if lastsubStack=='v':
            for r in generateActionCombinations(head+['H'],targetInserts,1):
              yield r  
            for r in generateActionCombinations(head+['h'],targetInserts,stackDepth+1):
              yield r

        for r in generateActionCombinations(head+['a'],targetInserts,stackDepth):
          yield r


def rotate(l, n):
    return l[-n:] + l[:-n]

stackSize = min(len(bricks),maxPerGrid)

runnumber=0
while stackSize <= len(bricks) or runnumber==0:
  runs=[]
  if runnumber>0:
    stackSize+=1
  if stackSize>len(bricks):
    exit()

  runnumber+=1

  print('Action gen start')
  allactionlistCombs = list(generateActionCombinations([],stackSize,1))
  print('Action gen end')
  random.shuffle(allactionlistCombs)

  alltempbricksPerm = []
  for i in range(layoutPermutationCount):
    random.shuffle(bricks)
    if bricks[:stackSize] not in alltempbricksPerm:
      alltempbricksPerm.append(bricks[:stackSize])

  random.shuffle(alltempbricksPerm)

  passn=0
  passReal=0
  for permInd,tempbricksPerm in enumerate(alltempbricksPerm,start=1):
    for actionInd,tempactionlist in enumerate(allactionlistCombs,start=1):
      passn+=1
      passReal+=1
      tempbricks = list(tempbricksPerm)
      actionlist= list(tempactionlist)

      state = ''.join(list( [str(x.identifier) for x in tempbricks]+['|']+[x[0] for x in actionlist] ))

      logger={}

      tempStack=[]
      while len(tempbricks)>0 or len(tempStack)>1:

        action = actionlist.pop(0)

        if action == 'V':
          tempStack = [Stack(tempStack,'vertical')]
        elif action == 'H':
          tempStack = [Stack(tempStack,'horizontal')]
        elif action == 'a':
          tempStack[-1].append(tempbricks.pop())
        elif action == 'h':
          tempStack.append(Stack([],'horizontal'))
        elif action == 'v':
          tempStack.append(Stack([],'vertical'))

      w,h = tempStack[0].getSizeWithContstraint('width',otuputWidth,logger,0,0)

      coords = []

      areasCropped=[]
      areasOriginal=[]


      for k,v in sorted(logger.items()):
        areasCropped.append(int(v[2])*int(v[3]))
        owm,ohm = int(v[5]),int(v[6])
        mult = min( 100/owm,100/ohm )
        areasOriginal.append( owm*mult*ohm*mult  )
        coords.extend([k,int(v[0]),int(v[1]),int(v[2]),int(v[3])])


      coords = tuple(coords)

      minArea = min(areasCropped)

      if minArea<minAllowedArea or h>maxHeight:
        passReal-=1
        continue

      if coords in seenLayouts:
        passReal-=1
        seenLayouts.setdefault(coords,set()).add(state.split('|')[1] )


        print("{:<6} {:<6} {:<30}  {:<25}  {:<11%} {:<11%} {:} {:<6}".format(passn,passReal,
                                                      state,
                                                      w/h,
                                                      (passn/(len(alltempbricksPerm)*len(allactionlistCombs)) ), 
                                                      (passReal/(len(alltempbricksPerm)*len(allactionlistCombs)) ), 
                                                      len(seenLayouts.get(coords)),
                                                      str(list(seenLayouts.get(coords))[:8]) ))
        
        continue
      else:
        print("{:<6} {:<6} {:<30}  {:<25}  {:<11%} {:<11%}".format(passn,passReal,
                                                    state,
                                                    w/h,
                                                    (passn/(len(alltempbricksPerm)*len(allactionlistCombs)) ), 
                                                    (passReal/(len(alltempbricksPerm)*len(allactionlistCombs)) ) ))

      seenLayouts.setdefault(coords,set()).add(state.split('|')[1])



      sumcropped = sum(areasCropped)
      sumOriginal = sum(areasOriginal)
      sizeChange = 0

      for cropped,orig in zip(areasCropped,areasOriginal):
        tempVariance = ((orig/sumOriginal) / (cropped/sumcropped))
        if tempVariance<1:
          tempVariance = 1/tempVariance
        
        sizeChange+=tempVariance

      if sizeChange != 0 :
        sizeChange = (sizeChange/len(areasOriginal))

      runs.append( (abs((w/h)-(16/9)),sizeChange, w,h,logger,state,coords) )
      if len(runs)>150:
        print('stackSize:',stackSize,'<=','len bricks:', len(bricks))
        encodeRun(runs)
        runs=[]

  print('stackSize:',stackSize,'<=','len bricks:', len(bricks))
  if len(runs)>0:
    encodeRun(runs)
  else:
    break


