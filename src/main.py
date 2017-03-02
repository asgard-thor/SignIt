import sys
sys.path.insert(0, "../lib")
import Leap, os, thread, time

class SampleListener(Leap.Listener):

    def on_connect(self, controller):
        print "Connected"


    def on_frame(self, controller):
        frame = controller.frame()
        #print "Frame id: %d, timestamp: %d, hands: %d, fingers: %d" % (frame.id, frame.timestamp, len(frame.hands), len(frame.fingers))
        #print frame.hands
        #print frame.fingers
        translation=frame.translation(controller.frame(10))
        if abs(translation[0])+abs(translation[1])+abs(translation[2])>10:
            print translation

def sign_to_tab()


def main():
    listener = SampleListener()
    controller = Leap.Controller()
    controller.add_listener(listener)
    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    try:
        sys.stdin.readline()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
