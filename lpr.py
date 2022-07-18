import cv2
import imutils
import numpy as np
import pytesseract
from PIL import Image


img = cv2.imread('patente3.jpg',cv2.IMREAD_COLOR)

img = cv2.resize(img, (620,480) )

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #convierte a escala de grises
gray = cv2.bilateralFilter(gray, 11, 17, 17)
edged = cv2.Canny(gray, 30, 200) #

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
 print ("No contour detected")
else:
 detected = 1

if detected == 1:
 cv2.drawContours(img, [screenCnt], -1, (0, 255, 0), 3)

# Enmascaramos la parte que no sea la placa de matrícula
mask = np.zeros(gray.shape,np.uint8)
new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
new_image = cv2.bitwise_and(img,img,mask=mask)

# recortamos
(x, y) = np.where(mask == 255)
(topx, topy) = (np.min(x), np.min(y))
(bottomx, bottomy) = (np.max(x), np.max(y))
Cropped = gray[topx:bottomx+1, topy:bottomy+1]

# leemos el numero de patente
text = pytesseract.image_to_string(Cropped, config='--psm 11')
print("Detected Number is:",text)

cv2.imshow('image',img)
cv2.imshow('Cropped',Cropped)

#mostramos en pantalla
cv2.waitKey(0)
cv2.destroyAllWindows()
