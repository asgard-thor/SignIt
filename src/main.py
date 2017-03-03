#! /usr/bin/python
import sys
sys.path.insert(0, "../lib")
import Leap, os, thread, time

class SampleListener(Leap.Listener):
    def on_connect(self, controller):
        print "Connected"
        self.frameMatrix=[[]]
        self.listFrames=[]
        self.temps = time.time()

    def on_frame(self, controller):
        frame = controller.frame()
        temps=0.0
        timeout=1000.0
        if movement(frame, controller.frame(10)):
            #reset chrono on se donne 300 ms jusqe la prochaine frame pour considerer le mouvement continu
            temps = time.time()*1000.0 #temps en milisecondes
            self.listFrames.append(frame) #changer ici
            print len(self.listFrames)
        else:
            if time.time() >= temps+timeout and self.listFrames:  # si pas de mouvement pendant + d une seconde
                # Si on a assez de frames pour que ce soit un VRAI mouvement
                if len(self.listFrames)>35:
                    self.frameMatrix.append(self.listFrames)
                    #print self.listFrames
                    sign_to_tab(self.listFrames)
                self.listFrames=[]

    def get_frameMatrix(self):
        try:
            return self.frameMatrix
        except Exception as e:
            print "Matrice vide"


def movement(frame, frameminus10):
    translation=frame.translation(frameminus10)
    rotation_angle=frame.rotation_angle(frameminus10)
    return (abs(translation[0])+abs(translation[1])+abs(translation[2])>10) or (rotation_angle>0.26)


def sign_to_tab(frames):
    t=frames[-1].timestamp-frames[0].timestamp
    current_time=0
    simplified_frames=[]
    step=t/10
    for frame in frames:
        current_time= frame.timestamp - frames[0].timestamp
        if current_time>step*len(simplified_frames):
            simplified_frames+=[frame]

    retrun=[]
    hands=[]
    for hand in simplified_frames[0].hands:
        hands+=[hand.id]

    for i in range(len(simplified_frames)-1):
        isvalid=0
        for hand in hands:
            if not simplified_frames[i+1].hand(hand).is_valid:
                isvalid+=1
        if isvalid !=0:
            if len(hands)==1:
                if len(simplified_frames[i+1].hands)==1:
                    hands[0]=simplified_frames[i+1].hands[0].id
                else:
                    #todo fail add hand
                    pass
            elif len(hands)==2:
                if len(simplified_frames[i+1].hands)==2:
                    if isvalid==1:
                        if simplified_frames[i+1].hand(hands[0]).is_valid:
                            if simplified_frames[i+1].hands[0].id==hands[0]:
                                hands[1]=simplified_frames[i+1].hands[1].id
                            else:
                                hands[1]=simplified_frames[i+1].hands[0].id
                        else:
                            if simplified_frames[i+1].hands[1].id==hands[1]:
                                hands[0]=simplified_frames[i+1].hands[0].id
                            else:
                                hands[0]=simplified_frames[i+1].hands[1].id
                    else:
                        #todo fail total change
                        pass
                else:
                    #todo fail change number of hands
                    pass

            else:
                # todo fail too many hands
                pass


        retrun.append([])
        for j in range(len(hands)):
            retrun[i]+=[{}]
            retrun[i][j]["rotation_angle"]=simplified_frames[i+1].hand(hands[j]).rotation_angle(simplified_frames[i])
            retrun[i][j]["rotation_axis"]=simplified_frames[i+1].hand(hands[j]).rotation_axis(simplified_frames[i])
            retrun[i][j]["translation"]=simplified_frames[i+1].hand(hands[j]).translation(simplified_frames[i])
            retrun[i][j]["grab_strength"]=simplified_frames[i].hand(hands[j]).grab_strength
            retrun[i][j]["palm_normal"]=simplified_frames[i].hand(hands[j]).palm_normal
    return retrun


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
    finally:
        controller.remove_listener(listener)

if __name__ == "__main__":
    main()
