#! /usr/bin/python
# coding=utf-8

import sys
sys.path.insert(0, "../lib")
import Leap, os, thread, time, json, pprint, marshal

class SampleListener(Leap.Listener):

    def on_connect(self, controller):
        print "Connected"
        self.listFrames=[]
        self.temps = time.time()
        self.indice_sign_table=0
        self.sign_table=[]

    def on_frame(self, controller):
        frame = controller.frame()
        temps=0.0
        timeout=500.0
        if movement(frame, controller.frame(10)):
            #reset chrono on se donne 300 ms jusqe la prochaine frame pour considerer le mouvement continu
            temps = time.time()*1000.0 #temps en milisecondes
            self.listFrames.append(frame) # changer ici
            print "\r"+str(len(self.listFrames))
        else:
            if time.time() >= temps+timeout and self.listFrames:  # si pas de mouvement pendant timeout secondes
                # Si on a assez de frames pour que ce soit un VRAI signe
                if len(self.listFrames)>35:
                    #penser a une file de sign_table
                    #print self.listFrames
                    self.sign_table.append(sign_to_tab(self.listFrames))
                    self.listFrames=[]
                    # on a 3 signes, on les moyene et affiche le JSON
                    if len(self.sign_table) >= 3:
                        mean_sign_table = self.sign_table[0]
                        # parcours les 3 tables de signes
                        for tableIndex, signTable in enumerate(self.sign_table, 1):
                            # parcours les 10 signes significatifs de chaque table
                            for signIndex, sign in enumerate(signTable):
                                for handIndex, hand in enumerate(sign):
                                    for index, key in enumerate(hand):
                                        # on peut effectuer des opérations sur les vecteurs (mul, div) comme des flottants (cf la doc)
                                        mean(mean_sign_table[signIndex][handIndex][key], tableIndex, hand[key], 1)
                        self.sign_table = []
                        print("your sign : ")
                        pprint.pprint(toJSON(mean_sign_table))
                        addSign(mean_sign_table)#gery tu as un beau tshirt


    def get_frameMatrix(self):
        try:
            return self.frameMatrix
        except:
            print "Matrice vide"

    def get_sign_table(self):
        if self.indice_sign_table<= len(self.sign_table):
            self.indice_sign_table+=1
            return self.sign_table[indice_sign_table-1]
        else:
            return None

def mean(val1, weight1, val2, weight2):
    return (val1*weight1 + val2*weight2) / (weight1+weight2)

def addSign(sign):
    signs = getSigns()
    signs.append(sign)
    saveSigns(signs)

def saveSigns(signs):
    fiel = open("./signs.db", 'w+b')
    pprint.pprint(signs)
    try:
        marshal.dump(signs, fiel)
    except:
        print "l'erreur est ici"
    fiel.close()

def getSigns():
    fiel = open("./signs.db", 'r+b')
    retrun = []
    try:
        retrun = marshal.load(fiel)
    except:
        print "ou la"
    fiel.close()
    return retrun


# renvoie true tant que l'on maintient un mouvement de main.
def movement(frame, frameminus10):
    translation=frame.translation(frameminus10)
    rotation_angle=frame.rotation_angle(frameminus10)
    return (abs(translation[0])+abs(translation[1])+abs(translation[2])>10) or (rotation_angle>0.26)


def sign_to_tab(frames):
    t=frames[-1].timestamp-frames[0].timestamp
    current_time=0
    simplified_frames=[]
    step=t/10

    # recupere 10 frames significatives permettant de decrire un signe
    for frame in frames:
        current_time= frame.timestamp - frames[0].timestamp
        if current_time>step*len(simplified_frames):
            simplified_frames+=[frame]

    retrun=[]
    hands=[]
    for hand in simplified_frames[0].hands:
        hands+=[hand.id]

    for i in range(len(simplified_frames)-1):
        print "i : "+str(i)
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
            retrun[i][j]["rotation_angle"]=simplified_frames[i+1].hand(hands[j]).rotation_angle(simplified_frames[i])#float
            retrun[i][j]["rotation_axis"]=simplified_frames[i+1].hand(hands[j]).rotation_axis(simplified_frames[i])
            retrun[i][j]["translation"]=simplified_frames[i+1].hand(hands[j]).translation(simplified_frames[i])
            retrun[i][j]["grab_strength"]=simplified_frames[i].hand(hands[j]).grab_strength#float
            retrun[i][j]["palm_normal"]=simplified_frames[i].hand(hands[j]).palm_normal
    return retrun


def main():
    listener = SampleListener()
    controller = Leap.Controller()
    controller.add_listener(listener)
    # Keep this process running until Enter is pressed

    print "Press Q to quit, R to record (default), P to play"
    try:
        choice = sys.stdin.readline()
    except KeyboardInterrupt:
        pass
    finally:
        controller.remove_listener(listener)

if __name__ == "__main__":
    main()
