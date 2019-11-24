#
#  SamplerBox
#
#  author:    Joseph Ernest (twitter: @JosephErnest, mail: contact@samplerbox.org)
#  url:       http://www.samplerbox.org/
#  license:   Creative Commons ShareAlike 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)
#
#  samplerbox.py: Main file
#


#########################################
# LOCAL
# CONFIG
#########################################

AUDIO_DEVICE_ID = 0                     # change this number to use another soundcard
SAMPLES_DIR = "."                       # The root directory containing the sample-sets. Example: "/media/" to look for samples on a USB stick / SD card
HW_SERIAL_MIDI = False                  # Set to True to enable MIDI commands via Scene_Board device connected in USB port (message: "@MIDI:<Status>,<Data0>,<Data1>")
HW_SERIAL_MIDI_ON_JSON = True


#########################################
# IMPORT
# MODULES
#########################################
import time
import re
import threading
import numpy
import struct
import os
import sys
import pygame as pg
import json

main_dir = os.path.split(os.path.abspath(__file__))[0]

samples = {}
channels = []
globalvolume = 10 ** (-12.0/20)  # -12dB default global volume




#########################################
# LOAD SAMPLES
#
#########################################
def LoadSamples():
    global preset
    global samples
    global globalvolume
    samples = {}
    globalvolume = 10 ** (-12.0/20)  # -12dB default global volume
    
    samplesdir = SAMPLES_DIR if os.listdir(SAMPLES_DIR) else '.'      # use current folder (containing 0 Saw) if no user media containing samples has been found

    basename = next((f for f in os.listdir(samplesdir) if f.startswith("%d " % preset)), None)      # or next(glob.iglob("blah*"), None)
    if basename:
        dirname = os.path.join(samplesdir, basename)
    if not basename:
        print 'Preset empty: %s' % preset
        return
    print 'Preset loading: %s (%s)' % (preset, basename)

    definitionfname = os.path.join(dirname, "definition.txt")
    if os.path.isfile(definitionfname):
        with open(definitionfname, 'r') as definitionfile:
            for i, pattern in enumerate(definitionfile):
                try:
                    if r'%%volume' in pattern:        # %%paramaters are global parameters
                        globalvolume *= 10 ** (float(pattern.split('=')[1].strip()) / 20)
                        continue
                    if r'%%transpose' in pattern:
                        continue
                    defaultparams = {'midinote': '0', 'velocity': '127', 'notename': ''}
                    if len(pattern.split(',')) > 1:
                        defaultparams.update(dict([item.split('=') for item in pattern.split(',', 1)[1].replace(' ', '').replace('%', '').split(',')]))
                    pattern = pattern.split(',')[0]
                    pattern = re.escape(pattern.strip())
                    pattern = pattern.replace(r"\%midinote", r"(?P<midinote>\d+)").replace(r"\%velocity", r"(?P<velocity>\d+)")\
                                     .replace(r"\%notename", r"(?P<notename>[A-Ga-g]#?[0-9])").replace(r"\*", r".*?").strip()    # .*? => non greedy
                    for fname in os.listdir(dirname):
                        m = re.match(pattern, fname)
                        if m:
                            info = m.groupdict()
                            midinote = int(info.get('midinote', defaultparams['midinote']))
                            velocity = int(info.get('velocity', defaultparams['velocity']))
                            notename = info.get('notename', defaultparams['notename'])
                            print midinote
                            samples[midinote] = pg.mixer.Sound(os.path.join(dirname, fname))
                except:
                    print "Error in definition file, skipping line %s." % (i+1)

    else:
        print "Definition file not found"

    initial_keys = set(samples.keys())
    if len(initial_keys) > 0:
        print 'Preset loaded: ' + str(preset)
    else:
        print 'Preset empty: ' + str(preset)

    
def InitializeChannels(nChannels):
    global channels
    channels=[]
    pg.mixer.set_num_channels(nChannels)
    print "Initialize ",nChannels," channels"
    for ch in range(nChannels):
        channels.append(pg.mixer.Channel(ch))


if HW_SERIAL_MIDI_ON_JSON:
    import serial

    def MidiPPCallback():
        CONNECT=0
        RESUME=1
        state=CONNECT
        while True:
            if state==CONNECT:
                for dev in os.listdir('/dev'):
                    if dev.startswith('ttyUSB'):
                        print("Connecting to %s" % dev)
                        try:
                            ser = serial.Serial(os.path.join('/dev', dev), baudrate=115200)
                            print("Success")
                            state=RESUME
                            ser.flush()
                        except:
                            print("Fail")
                            pass
                time.sleep(2)
            if state==RESUME:
                message = [0, 0, 0]
                try:
                    line = ser.read_until('\n')  # read a line. Expected something like "@MIDI:244,100,127"
                except:
                    print("Lost connection")
                    if pg.mixer.get_busy():
                        pg.mixer.stop()
                    state=CONNECT
                if line.startswith("@MIDI:"):
                    line=line.replace('@MIDI:', '')
                    line=line.replace('\r', '')
                    line=line.replace('\n', '')
                    print line
                    try:
                        messageJ=json.loads(line)
                        MidiCallbackJSON(messageJ)
                    except:
                        pass
                        
            
    MidiThread = threading.Thread(target=MidiPPCallback)
    MidiThread.daemon = True
    MidiThread.start()


    # root["command"] = MIDI_CONTROL_CHANGE;
    # root["channel"] = this->channelNumber;
    # root["note"] = MIDI_CONTROL_CHANGE_RESET;
    # root["velocity"] = 0;
    # root["panning"] = 0;
    # root["isLoop"] = 0;

def MidiCallbackJSON(message):

    messagetype = message['command']
    messagechannel = message['channel']
    note = message['note']
    velocity = message['velocity']
    panning = message['panning']
    isLoop = message['isLoop']

    if messagetype == 9:    # Note on
        # Get Pan
        pan=(panning*90*3.14/(127*180)) #Scale to 0 pi/2 rads
        sinA=numpy.sin(pan)
        cosA=numpy.cos(pan)
        # Get Loops
        if isLoop:
            nLoops=-1
        else:
            nLoops=0
        # Stop Previous Sound
        channels[messagechannel].stop()
        # Set Playback Attributes
        channels[messagechannel].set_volume(sinA, cosA)
        # Play sample
        channels[messagechannel].play(samples[note], loops=nLoops)

    elif messagetype == 8:  # Note off
        for ch in channels:
            if ch.get_sound()==samples[note]:
                ch.stop()


    elif messagetype == 11:  # Control Change
        if note == 50:
            if pg.mixer.get_busy():
                pg.mixer.stop()



#########################################
# OPEN AUDIO DEVICE
#
#########################################

pg.mixer.init(frequency=44100, size=-16, channels=2)

#########################################
# LOAD FIRST SOUNDBANK
#
#########################################

preset = 1
LoadSamples()
InitializeChannels(32)

#########################################
# MAIN LOOP
#########################################

while True:
    time.sleep(2)
