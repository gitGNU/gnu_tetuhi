#!/usr/bin/python
# Copyright (C) 2008 Douglas Bagnall
#
# This file is part of Te Tuhi Video Game System, or Te Tuhi for short.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import sys, traceback, time
from optparse import OptionParser
import random
from vg import config

PROFILE_FILE = '/tmp/tetuhi.prof'

def go(fn, mode='play'):
    """parse an image and make a game"""
    try:
        bf = BlobFinder(fn, window=window)
        if config.DETERMINISTIC:
            random.seed(bf.entropy[0])
        gm = GameMaker(bf, window)
        game = gm.find_game()
        
        if mode == 'play':
            game.intro()
            game.play()
            
    except GameEscape:
        pass # abandoning play for some reason
    return game


def cycle():
    #XXX a little dodgy
    attractor = Attractor(window)
    game = None
    while True:
        try:
            fn = attractor.attract()
            game = go(fn)
        except GameReplay:
            game.play()
        except Exception, e:
            traceback.print_exc()
            attractor.apologise(e)
        
        attractor.remember_game(game)

def present(filename):
    window.presentation(filename)
        

def get_opts():
    parser = OptionParser()
    parser.add_option("-c", "--capture", dest="capture",
                      help="capture to DIRECTORY", metavar="DIRECTORY", default=None)
    parser.add_option("-d", "--display-everything", action="store_true",
                      help="display more steps", default=False)
    parser.add_option("-f", "--fake-parse", dest="fake_parse", action="store_true",
                      help="don't really parse - use fake images", default=False)
    parser.add_option("-p", "--profile", dest="profile", action="store_true",
                      help="run the profiler", default=False)
    parser.add_option("-n", "--nopsyco", action="store_true",
                      help="stop psyco", default=False)
    parser.add_option("-t", "--train", dest="train", action="store_true",
                      help="train players with no video", default=False)
    parser.add_option("-e", "--exhibition-mode", dest="exhibit", action="store_true",
                      help="go into an endless exhibition cycle", default=False)
    parser.add_option("-s", "--fullscreen", dest="fullscreen", action="store_true",
                      help="try to take up the whole screen", default=False)
    parser.add_option("-r", "--really-capture", action="store_true",
                      help="really capture, don't just copy", default=False)
    parser.add_option("-b", "--bias", metavar="FRIENDLY|NASTY",
                      help="bias game in one direction", default=None)
    parser.add_option("-o", "--processes", metavar="NUMBER",
                      help="how many processes to start", default=None)
    parser.add_option("-y", "--presentation", metavar="FILE",
                      help="play yaml presentation", default=None)
    parser.add_option("-S", "--sound", metavar="FILE",
                      help="use sound description file FILE", default=None)

    return parser.parse_args()



if __name__ == '__main__':
    options, files = get_opts()
    if not files:
        files = [config.TEST_IMAGE]

    
    if options.profile:
        print "profiling"
        try:
            import cProfile as profile
        except ImportError:
            print "don't have cProfile in this old ancient python"
            import profile
        import pstats

    #options can alter config
    if options.display_everything:
        config.DISPLAY_EVERYTHING = True
        config.DISPLAY = True
    if options.fullscreen:
        config.FULLSCREEN = True
        #XXX a lot of stuff here to set the sizes right
        #config.WORKING_SIZE = (1024, 768)
        #config.WINDOW_SIZE = (1024, 768)
    if options.really_capture:
        config.CAMERA_SCRIPT = config.CAPTURE_SCRIPT
    if options.sound:
        #fragile (added late for release)
        config.SOUND = True
        config.SOUND_YAML = options.sound
        config.SOUND_DIR = os.path.dirname(options.sound)        
    
    if options.bias and options.bias.lower() == 'friendly':
        config.FRIENDLY_ONLY = True
    elif options.bias and options.bias.lower() == 'nasty':
        config.NASTY_ONLY = True

    if options.processes:        
        _p = config.PROCESSES
        config.PROCESSES = int(options.processes)
        config.RULE_GROWING_TIMEOUT *= float(config.PROCESSES) / _p
        config.RULE_GROWING_PARENT_TIMEOUT = config.RULE_GROWING_TIMEOUT * config.RULE_GROWING_TIMEOUT / 4
        print "children have %s secs, parent %s" % (config.RULE_GROWING_TIMEOUT,
                                                    config.RULE_GROWING_PARENT_TIMEOUT)

    # now that config is settled, import other modules.
    from vg.display import Window
    from vg.maker import GameMaker
    from vg.misc import GameEscape, GameReplay, SpriteError, ParseError
    from vg.attract import Attractor
    from vg import utils
    if options.fake_parse:
        from vg.fakeblobdetect import BlobFinder
    else:
        from vg.cblobdetect import BlobFinder

    if not options.profile and not options.nopsyco:
        #pyscoise
        try:
            import psyco
            psyco.full()
        except ImportError:
            print "running without Psyco!"


    #NOW stuff actually happens    
    window = Window(config.WINDOW_SIZE, capture=options.capture)

    if options.exhibit:
        cycle()
    elif options.presentation:
        present(options.presentation)
    else:
        for fn in files:
            if options.profile:
                profile.run('go(fn, mode="noplay")', PROFILE_FILE)
            else:
                go(fn)


    if options.profile:
        p = pstats.Stats(PROFILE_FILE)
        p.sort_stats('cumulative').print_stats(30)
        
