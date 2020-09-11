import signal
import time
import sys
from ftpclient import FileStorage

class GracefulKiller:
  kill_now = False
  fs = FileStorage( persist = True )
  fs.restore()
  fs.kill()
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True
    fs = FileStorage( persist = True )
    print("Backing up data...")
    fs.backup(  )
    fs.kill()
    print("Backup complete\nExiting...")
    quit()
    # sys.exit( 0 )

# if __name__ == '__main__':
#   killer = GracefulKiller()
#   while not killer.kill_now:
#     time.sleep(1)
#     print("doing something in a loop ...")

  # print("End of the program. I was killed gracefully :)")