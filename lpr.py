import cv2
import imutils
import numpy as np
import pytesseract
from PIL import Image

from gtts import gTTS
from playsound import playsound

# sudo apt install tesseract-ocr

patenteCant = 0
patenteAnt = ''

video = cv2.VideoCapture(0)

while True:
    success, frame = video.read()

    if success:
        image = frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        camera = imutils.resize(image, width=720)
        gray = cv2.cvtColor(camera, cv2.COLOR_BGR2GRAY) #convert to grey scale
        gray = cv2.bilateralFilter(gray, 11, 17, 17) #Blur to reduce noise
        edged = cv2.Canny(gray, 30, 200) #Perform Edge detection

        try:
            # encuentramo contornos en la imagen con bordes, obtenemos solo el más grande
            # inicializamos nuestro contador
            cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]
            screenCnt = None

            # recorro el contador
            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.018 * peri, True)
             
             # si tiene aprox 4 puntos asumimos que es nuestra patente
                if len(approx) == 4:
                    screenCnt = approx
                break

            if screenCnt is None:
                detected = 0
             #print ("No contour detected")
            else:
                detected = 1

            if detected == 1:
                cv2.drawContours(camera, [screenCnt], -1, (0, 255, 0), 3)

                # Masking the part other than the number plate
                mask = np.zeros(gray.shape,np.uint8)
                new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
                #new_image = cv2.drawContours(mask, [screenCnt.astype(int)], 0, (255, 0, 0), 3)
                new_image = cv2.bitwise_and(camera,camera,mask=mask)

                #Now crop
                (x, y) = np.where(mask == 255)
                (topx, topy) = (np.min(x), np.min(y))
                (bottomx, bottomy) = (np.max(x), np.max(y))
                Cropped = gray[topx:bottomx+1, topy:bottomy+1]

                #Read the number plate
                text = pytesseract.image_to_string(Cropped, config='--psm 10 --oem 1 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                text = text.replace('\n','',4) # quitar enters
                text = text.strip() # quitar enters al inicio y final
                patente = text

                if (len(patente) > 2) :
                    print("Lectura: ",patente)
                    if (patenteAnt != patente) :
                        patenteAnt = patente
                        patenteCant = 1            

                    if patenteCant == 5:
                        print("Patente: ",patente)
                        cv2.imshow('Cropped',Cropped)
                        try:
                            tts = gTTS('Patente, '+patente, lang='es-es', slow=False)
                            NOMBRE_ARCHIVO = patente+".mp3"
                            with open(NOMBRE_ARCHIVO, "wb") as archivo:
                                tts.write_to_fp(archivo)

                            playsound(NOMBRE_ARCHIVO)
                            patenteCant = 1
                        except:
                            pass
                    else:
                        patenteCant = patenteCant + 1
                        patenteAnt = patente
        except:
            pass 

cap.release()
