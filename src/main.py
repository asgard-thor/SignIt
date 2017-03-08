#! /usr/bin/python
# coding=utf-8
from operator import itemgetter
import sys
sys.path.insert(0, "../lib")
import Leap, os, thread, time, json, pprint, marshal
import pyttsx

TAUX_REDISTRIBUTION=2#1/TAUX_REDISTRIBUTION=%gardé à chaque pas de match

class SampleListener(Leap.Listener):
    mode="p"

    def set_mode(self, mode):
        self.mode=mode

    def on_connect(self, controller):
        print "Connected"
        self.listFrames=[]
        self.temps = time.time()
        self.sign_table=[]

    def on_frame(self, controller):
        frame = controller.frame()
        temps=0.0
        timeout=500.0
        if movement(frame, controller.frame(10)):
            #reset chrono on se donne 300 ms jusqe la prochaine frame pour considerer le mouvement continu
            temps = time.time()*1000.0 #temps en milisecondes
            self.listFrames.append(frame)
            print "\r"+str(len(self.listFrames))
        else:
            if time.time() >= temps+timeout and self.listFrames:  # si pas de mouvement pendant timeout secondes
                # Si on a assez de frames pour que ce soit un VRAI signe
                if len(self.listFrames)>35:
                    if(self.mode.lower()!="r\n"):  # mode reconnaissance de signe
                        word= match(sign_to_tab(self.listFrames), get_saved_signs())
                        print word
                        engine = pyttsx.init()
                        engine.setProperty('rate',70)
                        engine.say(word)
                        engine.runAndWait()
                        self.sign_table = []
                    if(self.mode.lower()=="r\n"):       # mode enregistrement de signe
                        self.sign_table.append(sign_to_tab(self.listFrames))
                        # au bout de 3 signes, on les moyenne et enregistre dans la DB
                        if len(self.sign_table) >= 3:
                            recordSign(self.sign_table)
                            self.sign_table = []

                # vide la liste de frames une fois utilisée.
                self.listFrames=[]


    def get_frameMatrix(self):
        try:
            return self.frameMatrix
        except:
            print "Matrice vide"


def recordSign(signTable):
    mean_sign_table = signTable[0]
    name = raw_input("veuillez entrer le nom de votre signe\n")
    # parcours les 3 tables de signes
    for tableIndex, signTable in enumerate(signTable, 1):
        # parcours les 10 signes significatifs de chaque table
        for signIndex, sign in enumerate(signTable):
            for handIndex, hand in enumerate(sign):
                for index, key in enumerate(hand):
                    # on peut effectuer des opérations sur les vecteurs (mul, div) comme des flottants (cf la doc)
                    mean(mean_sign_table[signIndex][handIndex][key], tableIndex, hand[key], 1)
    mean_sign_table.append({"name":name})
    save_sign(mean_sign_table)
    print "signe enregistré !"

def mean(val1, weight1, val2, weight2):
    return (val1*weight1 + val2*weight2) / (weight1+weight2)

def vectorToFloat(data):
    for sign in data:
        for hand in sign:
            for index, key in enumerate(hand):
                if key in ['palm_normal', 'translation', 'rotation_axis']:
                    hand[key] = hand[key].to_float_array()
    return data

def floatToVector(data):
    for signs in data:
        for sign in signs:
            for hand in sign:
                for index, key in enumerate(hand):
                    if key in ['palm_normal', 'translation', 'rotation_axis']:
                        hand[key] = Leap.Vector(hand[key][0],hand[key][1],hand[key][2])
    return data

# ajout un signe sign à la liste de signes signs
def add_sign(sign, signs):
    signs.append(vectorToFloat(sign))

def load_signs():
    try:
        retrun = marshal.load(file("./signs.db", 'rba'))
    except Exception as e:
        retrun=[]
    return retrun

def store_signs(signs):
    marshal.dump(signs, file("./signs.db", 'wba'))

def save_sign(sign):
    signs=load_signs()
    add_sign(sign, signs)
    store_signs(signs)

def save_signs(list_sign):
    signs=load_signs()
    for sign in list_sign:
        add_sign(sign, signs)
    store_signs(signs)

def get_saved_signs():
    retrun = floatToVector(load_signs())
    return retrun

# renvoie true tant que l'on maintient un mouvement de main.
def movement(frame, frameminus10):
    translation=frame.translation(frameminus10)
    rotation_angle=frame.rotation_angle(frameminus10)
    return (abs(translation[0])+abs(translation[1])+abs(translation[2])>10) or (rotation_angle>0.26)


def distance(mvt1,mvt2):
    retrun=0
    for key in mvt1.keys():
        if type(mvt1[key])==float:
            retrun+=((mvt1[key]-mvt2[key])*3)**2#le coefficient 3 est là pour éviter que les vecteurs prennent trop d'importance sur les floats
        elif type(mvt1[key])==tuple:
            for i in range(len(mvt1[key])):
                retrun+=(mvt1[key][i]-mvt2[key][i])**2
        elif type(mvt1[key])==Leap.Vector:
            m1=mvt1[key].to_tuple()
            m2=mvt2[key].to_tuple()
            for i in range(len(m1)):
                retrun+=(m1[i]-m2[i])**2
        else:
            print "distance() : type non reconnu dans le calcul de distance : %s" % str(type(mvt1[key]))
    return retrun


def ressemblance(base,entree):
    retrun=0
    if len(base)!=len(entree):
        return None
    else:
        if len(base)==1:
            retrun+=distance(base[0],entree[0])
        else:
            tmp1=distance(base[0],entree[0])+distance(base[1],entree[1])
            tmp2=distance(base[0],entree[1])+distance(base[1],entree[0])
            retrun+=tmp1 if tmp1<tmp2 else tmp2
    return retrun

def match(signed,signs):
    tab=[]
    for i in range(len(signed)):
        for j in range(len(signs)):
            if i ==0:
                signs[j]+=[0]

            signs[j][-1]+=ressemblance(signed[i],signs[j][i])
        signs=sorted(signs, key=itemgetter(-1))
        signs[:len(signs)//TAUX_REDISTRIBUTION]
        if len(signs)==1:
            return signs[0][-2]["name"]
    return signs[0][-2]["name"]





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
            retrun[i][j]["pinch_strength"]=simplified_frames[i].hand(hands[j]).pinch_strength#float
            retrun[i][j]["palm_normal"]=simplified_frames[i].hand(hands[j]).palm_normal
    return retrun


def main():
    print "Press (q) to quit, (r) to record (default), (p) to play"

    mode = sys.stdin.readline()
    # print mode
    if mode != "q\n":
        try:
            listener = SampleListener()
            listener.set_mode(mode if mode in ["r\n", "p\n"] else "r\n")
            controller = Leap.Controller()
            controller.add_listener(listener)
            while(True):
                pass
        except KeyboardInterrupt:
            controller.remove_listener(listener)

    print "bye bye"

if __name__ == "__main__":
    main()
