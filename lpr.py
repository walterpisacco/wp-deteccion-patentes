import cv2
import imutils
import numpy as np
import pytesseract
from PIL import Image
#from vidgear.gears import CamGear
from gtts import gTTS
from playsound import playsound
#pip3 install flask-mysql
from flaskext.mysql import MySQL
from flask import Flask, render_template, json, request
from datetime import datetime

# sudo apt-get update
# sudo apt-get install tesseract-ocr
# para RASPI: sudo apt install python3-gst-1.0

mysql = MySQL()

app = Flask(__name__ , template_folder= "modulos")
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

from config import config
configuracion = config()

# MySQL configurations
app.config['UPLOAD_FOLDER'] = configuracion.pathUpload
app.config['MYSQL_DATABASE_USER'] = configuracion.usuario
app.config['MYSQL_DATABASE_PASSWORD'] = configuracion.password
app.config['MYSQL_DATABASE_DB'] = configuracion.base
app.config['MYSQL_DATABASE_HOST'] = configuracion.servidor
app.cliente = configuracion.cliente
app.lista = 0

patenteCant = 0
lecturaAnt = ''
patenteAnt = ''

mysql.init_app(app)

#video = cv2.VideoCapture(2)
#video = CamGear(source="https://www.youtube.com/watch?v=7SZuhEfjEZk", stream_mode = True, logging=True).start()

#video = cv2.VideoCapture("rtsp://admin:0000@192.168.0.51:80/live/h264/ch01")

#******* SON LO MISMO PARA KIKVISION ********
#video = cv2.VideoCapture("rtsp://admin:admin1234@192.168.0.52:554/h264/ch01/sub/av_stream")
video = cv2.VideoCapture("rtsp://admin:admin1234@192.168.0.52:554/Streaming/Channels/902")
#*****************************

#video = cv2.VideoCapture("rtsp://admin:Global*3522@192.168.0.108:554/cam/realmonitor?channel=1&subtype=1")

while True:
    success, image = video.read()
    cv2.imshow('image', image)
    if cv2.waitKey(1) == ord('q'):
        break

    if success:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        #image = imutils.resize(image, width=720)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) #convert to grey scale
        gray = cv2.bilateralFilter(gray, 11, 17, 17) #Blur to reduce noise
        edged = cv2.Canny(gray, 30, 200) #Perform Edge detection

        try:
            # encuentramo contornos en la imagen con bordes, obtenemos solo el m\u00e1s grande
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
                cv2.drawContours(image, [screenCnt], -1, (0, 255, 0), 3)

                # Masking the part other than the number plate
                mask = np.zeros(gray.shape,np.uint8)
                #new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
                new_image = cv2.drawContours(mask, [screenCnt.astype(int)], 0, (255, 0, 0), 3)
                new_image = cv2.bitwise_and(image,image,mask=mask)

                #Now crop
                (x, y) = np.where(mask == 255)
                (topx, topy) = (np.min(x), np.min(y))
                (bottomx, bottomy) = (np.max(x), np.max(y))
                Cropped = gray[topx:bottomx+1, topy:bottomy+1]

                #Read the number plate
                text = pytesseract.image_to_string(Cropped,lang="eng", config='--psm 10 --oem 1 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                text = text.replace('\n','',4) # quitar enters
                text = text.strip() # quitar enters al inicio y final
                #patente = text.replace("%","").replace("|","").replace("!","").replace("\u2018","").replace(".","").replace(" ","").replace("`","").replace("[","").replace("]","").replace(",","").replace("'","").replace("(","").replace(")","").replace("{","").replace("","")
                patente = ''.join(char for char in text if char.isalnum())

                if (len(patente) > 2) :
                    print(patente)
                    if (lecturaAnt != patente) :
                        lecturaAnt = patente

                    else:
                        #espero que lea 5 veces seguidas la misma patente para verificar que no es un error (mejorar)
                        patenteCant = patenteCant + 1
                        #print(patenteCant, patenteAnt, patente)
                        if patenteCant == 5:
                            patenteCant = 1
                            if patenteAnt != patente:
                                lecturaAnt = patente
                                patenteAnt = patente

                                dia = str(datetime.now())[:-7]

                                try:
                                    conn = mysql.connect()
                                    cursor = conn.cursor()

                                    query = "select id from dx_ingresos.tipoLista where cliente = "+app.cliente+ " limit 1"
                                    cursor.execute(query)
                                    conn.commit()
                                    results = cursor.fetchall()
                                    if len(results) > 0:
                                        for row in results:
                                            app.lista = row[0]

                                    query = "update dx_ingresos.listaBlancaVehiculos set"
                                    campos = " estado = 0, deleted_at = '"+dia+"'"
                                    where = " where estado = 1 and idCliente = "+app.cliente+" and patente = '"+patente+"'"
                                    cursor.execute(query+campos+where)                                

                                    query = "INSERT INTO dx_ingresos.listaBlancaVehiculos(idCliente,patente,fechaDesde,fechaHasta,fecha,estado,lista,created_at)"
                                    valores = " VALUES("+app.cliente+",'"+patente+"','"+dia+"','"+dia+"','"+dia+"',1,"+str(app.lista)+",'"+dia+"')"

                                    cursor.execute(query+valores)

                                    query = "INSERT INTO dx_ingresos.lecturaPatentes(idCliente,idEquipo,camara,patente,fecha,idListaBlanca,estado)"
                                    valores = " VALUES("+app.cliente+",1,'Ingreso','"+patente+"','"+dia+"',"+str(app.lista)+",1)"
                                    cursor.execute(query+valores)

                                    conn.commit()
                                except:
                                    pass
                                
                                print('grabado: '+patente)
                                cv2.imshow('Cropped',Cropped)                                

                                try:
                                    tts = gTTS('Patente, '+patente, lang='es-es', slow=False)
                                    NOMBRE_ARCHIVO = "sonido.mp3"
                                    with open(NOMBRE_ARCHIVO, "wb") as archivo:
                                        tts.write_to_fp(archivo)

                                    playsound(NOMBRE_ARCHIVO)
                                except:
                                    pass
                
        except OSError as error:
            #print(error)
            pass

video.release()
cv2.destroyAllWindows()

