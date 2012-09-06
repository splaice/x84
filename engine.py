#!/usr/bin/env python2.6
"""
Scripting and session engine
"""
__author__ = 'Jeffrey Quast <dingo@1984.ws>'
__license__ = 'ISC'
__maintainer__ = 'Jeffrey Quast'
__email__ = 'dingo@1984.ws'
__status__ = 'Alpha'
__version__ = '3.0rc0'
# version 1, unnamed? 2001 johannes, 2003 jeff
# version 2, PRSV, 2008 johannes, 2010 jeff
# version 3, x84, 2011 jeff

import bbs.ini

def main (logger, logHandler, cfgFile='default.ini'):
  """
  x84 main entry point. The system begins and ends here.
  """
  import terminal
  terminal.logger.addHandler (logHandler)
  logger.addHandler (logHandler)

  import bbs.session
  bbs.session.logger.addHandler (logHandler)
  logger.addHandler (logHandler)

  # load .ini file
  bbs.ini.init (cfgFile)

  # initialize scripting subsystem
  import bbs.scripting
  bbs.scripting.init (bbs.ini.cfg.get('system', 'scriptpath'))

  # initialize telnet server
  import telnet
  telnet_port = int(bbs.ini.cfg.get('system', 'telnet_port'))
  telnet_addr = bbs.ini.cfg.get('system', 'telnet_addr')

  server = telnet.TelnetServer \
      (port=telnet_port, address=telnet_addr,
       on_connect=terminal.on_connect,
       on_disconnect=terminal.on_disconnect,
       timeout=0.01)

  logger.info ('[telnet:%s] listening tcp', telnet_port)

  # main event loop
  eof_pipes = set()
  while True:
    event = server.poll()
    for client, pipe in terminal.CHANNELS:
      # poll for keyboard input, send to session channel monitor
      if client.input_ready:
        inp = client.get_input()
        pipe.send (('input', inp))

      # poll for events received on child process pipe
      if pipe.poll():
        try:
          event, data = pipe.recv()
          if event == 'output':
            client.send (data)
          elif event == 'global':
            for (c,p) in terminal.CHANNELS:
              if c != client:
                c.send (('global', data))
          elif event.startswith ('db-'):
            t = db.DBHandler(pipe, event, data)
            t.start ()
          else:
            assert 0, 'Unhandled event: %s (data=%s)' % (event,)
        except EOFError:
          eof_pipes.add ((client, pipe))
    while 0 != len(eof_pipes):
      terminal.CHANNELS.remove (eof_pipes.pop())


if __name__ == '__main__':
  import sys
  import logging
  import log
  logger = logging.getLogger(__name__)
  logger.setLevel(logging.DEBUG)
  sys.stdout.write ('x/84 bbs ')
  log_level = logging.INFO
  cfgFile = 'default.ini'
  if '-v' in sys.argv:
    sys.argv.remove('-v')
    log_level = logging.DEBUG
  if '-cfg' in sys.argv:
    cfgFile = sys.argv[sys.argv.index('-cfg')+1]
    sys.argv.remove(cfgFile)
    sys.argv.remove('-cfg')
  logHandler = log.get_stderr(level=log_level)
  sys.stdout.flush()
  main (logger, logHandler, cfgFile)
