
import pytest
import sys
import time
from blob import BlobService, DataTransfer


import Ice

Ice.loadSlice("icedrive.ice")  
import IceDrive

'''Estas son los test unitarios para el modulo blob.py'''

ruta_archivo1 = "Sistema_directorios/home/texto1.txt"
ruta_archivo2 = "Sistema_directorios/home/texto2.txt"
ruta_archivo3 = "Sistema_directorios/home/texto3.txt"

ruta_diccionario_blob = "Sistema_directorios/tmp/historial_blob.txt"
ruta_diccionario_path = "Sistema_directorios/tmp/historial_rutas.txt" 

# ----------------------------------------TESTs BASICOS------------------------------------------------------------ #

def non_test_data_transfer_read() -> bytes:
    print("---------------------------------TEST DATA_TRANSFER_READ---------------------------------\n")
    
    size1 = 1
    size100 = 100 
    data_transfer = DataTransfer(ruta_archivo1)
    #abrimos el fichero
    print("Leemos archivo conocido: " + ruta_archivo1 + " con tamaño pequeño - Prueba 1" )
    #Comprobamos un caso normal, si el tamaño del dato leido es igual al tamaño que le hemos pasado
    assert (len(data_transfer.read(size1)) == size1)
    print("Prueba 1 superada")
    

    print("Leemos archivo conocido: " + ruta_archivo1 + " con tamaño mas grande que el archivo - Prueba 2" )
    
    # Comprobamos el caso de que el tamaño del dato leido sea menor que el tamaño que le hemos pasado
    assert (len(data_transfer.read(size100)) < size100) 
    print("Prueba 2 superada")
    data_transfer.close()

    # CASOS DE ERROR - El fichero ya se ha cerrado
    data_transfer2 = DataTransfer(ruta_archivo1)
    data_transfer2.close()
    excepcion = False

    try:
        data_transfer2.read(200)
    except IceDrive.FailedToReadData:
        excepcion = True
    finally:
        assert(excepcion == True)
        
def non_test_blobservice_recover_dicionary() -> dict:
    blolb_service = BlobService()
    print("---------------------------------TEST RECOVER_DICIONARY---------------------------------\n")
    diccionario = blolb_service.recover_dicionary()
    assert(diccionario != {})
    assert(diccionario != None)

def non_test_blobservice_upload() -> str:
    print("---------------------------------TEST UPLOAD---------------------------------\n")

    blob_service = BlobService(ruta_diccionario_blob,ruta_diccionario_path)
    
    data_transfer1 = DataTransfer(ruta_archivo1)
    data_transfer2 = DataTransfer(ruta_archivo2)
    data_transfer3 = DataTransfer(ruta_archivo3)
    
    # Estos blobid ya estan en los archivos de consistencia
    blobid1 = blob_service.upload(data_transfer1) 
    blobid2 = blob_service.upload(data_transfer2) 
    blobid3 = blob_service.upload(data_transfer3)

    assert(blobid1 == "d2626beab49bc9a63fe5507c3f7b855f79a1d6623eb937f02d6a31397bdfdf10")
    assert(blobid2 == "889a7030089bc32cf31d1b641844f45cb27087e671225bcb78ec046affb08ebf")
    # para probar un fichero nuevo, hemos creado el texto3.txt y hemos comprobado que el blobid es el correcto
    # a traves de un generador de SHA256 online
    assert(blobid3 == "12ba5fd54f58a3ca363a77919189984deefd801db9d0b691c42c4f164b0820d0")


    # Caso de error - El fichero ya se ha cerrado (FailedToReadData)
    excepcion = False
    try:
      blob_service.upload(data_transfer1) 
    except IceDrive.FailedToReadData:
        excepcion = True
        assert(excepcion == True)

def non_test_blobservice_link() -> None:
    print("---------------------------------TEST LINK---------------------------------\n")
    blob_service1 = BlobService(ruta_archivo1,ruta_diccionario_blob,ruta_diccionario_path)
    blob_service2 = BlobService(ruta_archivo2,ruta_diccionario_blob,ruta_diccionario_path)

    blob_id1 = "d2626beab49bc9a63fe5507c3f7b855f79a1d6623eb937f02d6a31397bdfdf10"
    blob_id2 = "c06b6e74e0eb82cdbe517aa62896361baffb282602bbf2a338dc9475652144ac"   

    blob_service1.link(blob_id1)
    blob_service2.link(blob_id2)

    # Caso de error - El blobid no existe (UnknownBolb)
    excepcion = False
    try:
        blob_service1.link("blobid1")
    except IceDrive.UnknownBlob:
        excepcion = True
        assert(excepcion == True) 
    
def non_test_blobservice_unlink() -> None:
    print("---------------------------------TEST UNLINK---------------------------------\n")
    blob_service1 = BlobService(ruta_archivo1,ruta_diccionario_blob,ruta_diccionario_path)
    blob_service2 = BlobService(ruta_archivo2,ruta_diccionario_blob,ruta_diccionario_path) 

    blob_id1 = "d2626beab49bc9a63fe5507c3f7b855f79a1d6623eb937f02d6a31397bdfdf10"
    blob_id2 = "c06b6e74e0eb82cdbe517aa62896361baffb282602bbf2a338dc9475652144ac"  

    blob_service1.unlink(blob_id1)
    blob_service2.unlink(blob_id2)

    # caso de error - El blobid no existe (UnknownBlob)
    excepcion = False
    try:
        blob_service1.unlink("blobid1")
    except IceDrive.UnknownBlob:
        excepcion = True
        assert(excepcion == True)

def non_test_download() -> None: 
    
    blob_service1 = BlobService(ruta_archivo1,ruta_diccionario_blob,ruta_diccionario_path)
    blob_service2 = BlobService(ruta_archivo2,ruta_diccionario_blob,ruta_diccionario_path) 

    blob_id1 = "d2626beab49bc9a63fe5507c3f7b855f79a1d6623eb937f02d6a31397bdfdf10"
    blob_id2 = "c06b6e74e0eb82cdbe517aa62896361baffb282602bbf2a338dc9475652144ac"  

    data_transfer1 = blob_service1.download(blob_id1)
    data_transfer2 = blob_service2.download(blob_id2)

    assert(data_transfer1 != None)
    assert(data_transfer2 != None)

    # Caso de error - El blobid no existe (UnknownBlob)
    excepcion = False
    try:
        blob_service1.download("blobid1")
    except IceDrive.UnknownBlob:
        excepcion = True
        assert(excepcion == True) 

def non_test_download_upload() -> None:
    # El objetivo de este test es comprobar que el archivo que se sube y se descarga es el mismo
    # El fichero que descargaremos, lo vamos a llamar prueba.txt y su contenido será el mismo que el texto1.txt

    blob_service = BlobService(ruta_diccionario_blob,ruta_diccionario_path)
    blob_id1 = "d2626beab49bc9a63fe5507c3f7b855f79a1d6623eb937f02d6a31397bdfdf10"
    blob_id2 = "c06b6e74e0eb82cdbe517aa62896361baffb282602bbf2a338dc9475652144ac"
    blob_id3 = "435394610d65f20d74567c6fafe062134e8dfa2fab6554275d5c6cdae6569fe9"

    data_transfer = blob_service.download(blob_id1)
    data_transfer2 = blob_service.download(blob_id2)
    data_transfer3 = blob_service.download(blob_id3)
    

    # Seguimos con la descarga como si fueramos el cliente del servicio
    size = 10
    content = ""

    while True:
        data = data_transfer3.read(size) 
        content += data.decode()
        if len(data) < size:
            break
   
   # Creamos el archivo llamado prueba.txt
    with open("Sistema_directorios/home/prueba.txt", "w") as file: 
        file.write(content)
        file.close()
   
    blob_id_prueba = blob_service.upload(data_transfer3)

    assert( blob_id_prueba == blob_id3) # Comprobamos que el contenido del archivo prueba.txt es el mismo que el texto1.txt


# ----------------------------------------TESTs MAS AVANZADOS------------------------------------------------------------ #

def non_test_upload1_text4() -> None:
    # El usuario creara un objeto de tipo DataTransfer y lo pasara como parametro al metodo upload
    blob_service = BlobService()
    data_transfer = DataTransfer("Sistema_directorios/home/texto4.txt")

    blob_id = blob_service.upload(data_transfer)
    assert (blob_id == "12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d")
    time.sleep(6)
    # El usuario se queda sin enlazar el archivo que ha hecho el upload durante mas tiempo que el timer_file 
    # (5 segundos por ejmplo)

    error = False
    try:
        blob_id = blob_service.upload(data_transfer) # debería dar error, ya que el data transfer se ha cerrado
    except IceDrive.FailedToReadData:
        error = True
        assert (error == True) # Comprobamos que el error es el esperado   

def non_test_upload2_text3_4() -> None:
    # El usuario creara un objeto de tipo DataTransfer y lo pasara como parametro al metodo upload
    # Esta prueba consiste en que se cree un hilo por cada objeto que el usuario hacer el upload y no esté anteriormente enlazado

    
    data_transfer4 = DataTransfer("Sistema_directorios/home/texto4.txt")
    data_transfer3 = DataTransfer("Sistema_directorios/home/texto3.txt")

    blob_id = BlobService().upload(data_transfer4)
    assert (blob_id == "12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d")
    time.sleep(3) 
    blob_id2 = BlobService().upload(data_transfer3)
    assert (blob_id2 == "ac1e9040b291a72aa1e818526432100391faea53ed6c33906002849d84f9fbac")
    time.sleep(11)
    # Despues del sleep, se debería haber borrado texto4 y texto3, si el usuario no ha hecho link (Trabajamos con time out de 10s)

def non_test_upload3_text4() -> None:
    data_transfer4 = DataTransfer("Sistema_directorios/home/texto4.txt")
    data_transfer3 = DataTransfer("Sistema_directorios/home/texto3.txt")

    # ahora, el usuario hace link al texto 4 pero se le olvida de crearlo al texto 3
    blob_id = BlobService().upload(data_transfer4)
    assert (blob_id == "12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d")
    time.sleep(3)
    BlobService().link(blob_id) 
    blob_id2 = BlobService().upload(data_transfer3)
    assert (blob_id2 == "ac1e9040b291a72aa1e818526432100391faea53ed6c33906002849d84f9fbac")
    time.sleep(11)
    # Despues del sleep, se debería haber borrado texto3.txt y texto4 debería tener 1 link (Trabajamos con time out de 10s)

def non_test_upload4_text4() -> None:
    data_transfer4 = DataTransfer("Sistema_directorios/home/texto4.txt")
    data_transfer3 = DataTransfer("Sistema_directorios/home/texto3.txt")

    # ahora, el usuario hace link al texto 4 y al texto 3. 
    # (partimos de la base de que no estan en nuestros archivos de persistencia inicialmente)

    blob_id = BlobService().upload(data_transfer4)
    assert (blob_id == "12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d")
    time.sleep(3)
    BlobService().link(blob_id) 
    blob_id2 = BlobService().upload(data_transfer3)
    assert (blob_id2 == "ac1e9040b291a72aa1e818526432100391faea53ed6c33906002849d84f9fbac")
    time.sleep(2)
    BlobService().link(blob_id2)
    time.sleep(11)
    # Despues del sleep, no se debería haber borrado texto3.txt y texto4 y texto3 debería tener 1 link (Trabajamos con time out de 10s)
 
def non_test_download_text4() -> None:
    id_prueba = str("12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d")

    data_transfer1 = BlobService().download(id_prueba)
    assert(data_transfer1 != None)  
    
    size = 10
    content = ""

    while True:
        data = data_transfer1.read(size) 
        content += data.decode()
        if len(data) < size:
            break
   
   # Creamos el archivo llamado prueba.txt
    with open("Sistema_directorios/home/prueba.txt", "w") as file: 
        file.write(content)
        file.close()

    blob_id_prueba = BlobService().upload(data_transfer1)
    assert( blob_id_prueba == id_prueba) # Comprobamos que el contenido del archivo prueba.txt es el mismo que el texto1.txt

def non_text_upload_download_text4() -> None: # en proceso
    pass

def non_test_link_text4() -> None:
    id_prueba = str("12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d")
    BlobService().link(id_prueba)

def non_test_unlink_text4() -> None:
    id_prueba = str("12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d")
    BlobService().unlink(id_prueba)
    # Hay que ver, como se modificaría los archivos de persistencia. 

def non_test_unlink_text3() -> None:    
    id_prueba = str("ac1e9040b291a72aa1e818526432100391faea53ed6c33906002849d84f9fbac")
    BlobService().unlink(id_prueba)
    # Hay que ver, como se modificaría los archivos de persistencia. 

#-----------------------------------CASOS DE USO COMPLETOS DEL SERVICIO BLOB----------------------------------#

def non_test_caso1() -> None:
    # El usuario sube un archivo que no existe en los archivos de persistencia (texto4.txt), lo enlaza para que no se borre
    # y lo descarga para comprobar que es el mismo que el que ha subido (para este caso, el nuevo archivo se llamaría
    # txCaso1.txt y su contenido sería el mismo que el texto4.txt, por lo que si subimos el txCaso1.txt, debería tener el mismo id)
    # No se debería borrar ni texto4.txt ni txCaso1.txt porque los enlazamos a tiempo.

    # Funciones participantes de este caso - numero de veces ejecutadas:
    # 1. upload - 2 (uno para texto4.txt y otro para txCaso1.txt)
    # 2. link - 2 (uno por cada archivo)
    # 3. download - 1

    data_transfer = DataTransfer("Sistema_directorios/home/texto4.txt")
    id_blob = BlobService().upload(data_transfer)

    assert(id_blob == "12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d")
    time.sleep(5) # esperamos 5 segundos simulando complejidad
    BlobService().link(id_blob)

    data_transfer2 = BlobService().download(id_blob)
    assert(data_transfer2 != None)

    # Simulamos la descarga del cliente    
    size = 10
    content = ""

    while True:
        data = data_transfer2.read(size) 
        content += data.decode()
        if len(data) < size:
            break
   
   # Creamos el archivo llamado prueba.txt
    with open("Sistema_directorios/home/txCaso1.txt", "w") as file: # debería tener el mismo contenido que el texto4.txt 
        file.write(content)
        file.close()

    # procedemos a subir el archivo que hemos descargado (en teoria deberia tener el mismo id que el texto4.txt)
    data_transfer3 = DataTransfer("Sistema_directorios/home/txCaso1.txt")
    id_blob2 = BlobService().upload(data_transfer3)
    assert(id_blob2 == id_blob)
    time.sleep(5) # esperamos 5 segundos simulando complejidad
    BlobService().link(id_blob2) 

def non_test_caso2() -> None:
    # El usuario sube un archivo que no existe en los archivos de persistencia (texto4.txt), lo enlaza para que no se borre
    # y lo descarga para comprobar que es el mismo que el que ha subido (para este caso, el nuevo archivo se llamaría
    # txCaso2.txt. Borramos el enlace de texto4.txt, por lo que se debería borrar texto4.txt, pero no txCaso2.txt.
    # Más tarde, subimos txCaso2.txt, pero no lo enlazamos, por lo que se debería borrar txCaso2.txt por el recolector de basura
    # No debería estan en persistencia ni texto4.txt ni txCaso2.txt.

    # Flujo de ejecucion:
    # texto4.txt esta en persistencia gracias a upload
    # texto4.txt se enlaza, por lo que debería tener 1 link
    # Se sube otra vez texto4.txt, como ya está en persistencia, devolverá directamente el id
    # Se enlaza otra vez texto4.txt (llevaría 2 enlaces)
    # texto4.txt se descarga y se crea un nuevo archivo llamado txCaso2.txt
    # texto4.txt le quitamos los 2 enlaces, por lo que debería tener 0 links y se borra de persistencia
    # txCaso2.txt se sube y esta en persistencia
    # pasa el timeout del archivo txCaso2.txt, por lo que se borra, gracias a la recoleción de basura.
    # Conclusión: texto4.txt y txCaso2.txt se borran, no estan en persistencia

    # Funciones participantes de este caso - numero de veces ejecutadas:
    # 1. upload - 3 (uno para texto4.txt y otro para txCaso2.txt)
    # 2. link - 2
    # 3. download - 1
    # 4. unlink - 2
    # 5. garbage_collector - 1

    data_transfer = DataTransfer("Sistema_directorios/home/texto4.txt")
    id_blob = BlobService().upload(data_transfer)

    assert(id_blob == "12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d")
    time.sleep(5) # esperamos 5 segundos simulando complejidad
    BlobService().link(id_blob)

    time.sleep(3) # esperamos 3 segundos simulando complejidad

    data_transfer = DataTransfer("Sistema_directorios/home/texto4.txt")
    id_blob = BlobService().upload(data_transfer)

    assert(id_blob == "12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d")
    time.sleep(2) # esperamos 5 segundos simulando complejidad
    BlobService().link(id_blob) #Segundo enlace a texto4.txt
    time.sleep(2)

    data_transfer2 = BlobService().download(id_blob)
    assert(data_transfer2 != None)

    # Simulamos la descarga del cliente    
    size = 10
    content = ""

    while True:
        data = data_transfer2.read(size) 
        content += data.decode()
        if len(data) < size:
            break
   
   # Creamos el archivo llamado prueba.txt
    with open("Sistema_directorios/home/txCaso2.txt", "w") as file: # debería tener el mismo contenido que el texto4.txt 
        file.write(content)
        file.close()

    # Eliminamos el enlace de texto4.txt
    BlobService().unlink(id_blob) 
    time.sleep(3) # esperamos 3 segundos simulando complejidad
    BlobService().unlink(id_blob)
    time.sleep(2)
    # procedemos a subir el archivo que hemos descargado (en teoria deberia tener el mismo id que el texto4.txt)
    data_transfer3 = DataTransfer("Sistema_directorios/home/txCaso2.txt")
    id_blob2 = BlobService().upload(data_transfer3)
    assert(id_blob2 == id_blob)
    time.sleep(14) # esperamos 14 segundos simulando complejidad, eliminando txCaso2.txt por el timeout

def non_test_caso3() -> None:

    # El usuario subirá texto4.txt que no está en persistencia, lo enlazará para que no se borre y lo descargará
    # Una vez descargado, modificará el contenido del archivo y lo subirá de nuevo.

    data_transfer = DataTransfer("Sistema_directorios/home/texto4.txt")
    id_blob = BlobService().upload(data_transfer) # Como no está en persistencia, se guarda en persistencia y se devuelve el id

    assert(id_blob == "12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d")
    time.sleep(5) # esperamos 5 segundos simulando complejidad
    BlobService().link(id_blob)
    time.sleep(3) # esperamos 3 segundos simulando complejidad

    data_transfer2 = BlobService().download(id_blob)
    assert(data_transfer2 != None)

    # Simulamos la descarga del cliente    
    size = 10
    content = ""

    while True:
        data = data_transfer2.read(size) 
        content += data.decode()
        if len(data) < size:
            break
   
    with open("Sistema_directorios/home/texto4.txt", "w") as file: # debería tener el mismo contenido que el texto4.txt 
        file.write(content)

    time.sleep(4)    
    # El cliente modifica el archivo texto4.txt y lo sube de nuevo
    with open("Sistema_directorios/home/texto4.txt", "a") as file:
        file.write("Añadimos contenido al archivo")

    data_transfer_bis = DataTransfer("Sistema_directorios/home/texto4.txt")
    id_blob = BlobService().upload(data_transfer_bis) #Deberia verse la entrada modificada de los archivos de persistencia
    time.sleep(5) # esperamos 5 segundos simulando complejidad
    assert(id_blob == "17b0494d6fdcadf68781e5b9af3bb65590063da0645a8d98f90323204f8e007e")


