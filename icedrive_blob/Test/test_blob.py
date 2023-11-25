
import pytest
import sys
from blob import BlobService, DataTransfer

import Ice

Ice.loadSlice("icedrive.ice")  
import IceDrive

'''Estas son los test unitarios para el modulo blob.py'''

ruta_archivo1 = "Sistema_directorios/home/texto1.txt"
ruta_archivo2 = "Sistema_directorios/home/texto2.txt"
ruta_diccionario_blob = "Sistema_directorios/tmp/historial_blob.txt"
ruta_diccionario_path = "Sistema_directorios/tmp/historial_rutas.txt" 

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

    blob_service1 = BlobService(ruta_archivo1,ruta_diccionario_blob,ruta_diccionario_path)
    blob_service2 = BlobService(ruta_archivo2,ruta_diccionario_blob,ruta_diccionario_path)
    data_transfer1 = DataTransfer(ruta_archivo1)
    data_transfer2 = DataTransfer(ruta_archivo2)
    
    blobid1 = blob_service1.upload(data_transfer1) 
    blobid2 = blob_service2.upload(data_transfer2) 

    print("blobid: " + blobid1 + "\n") 

    assert(blobid1 == "d2626beab49bc9a63fe5507c3f7b855f79a1d6623eb937f02d6a31397bdfdf10")
    assert(blobid2 == "c06b6e74e0eb82cdbe517aa62896361baffb282602bbf2a338dc9475652144ac") 

    # Caso de error - El fichero ya se ha cerrado (FailedToReadData)
    excepcion = False
    try:
      blob_service1.upload(data_transfer1) 
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



def test_download() -> None: 
    
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

    blob_service = BlobService(ruta_archivo1,ruta_diccionario_blob,ruta_diccionario_path)
    blob_id1 = "d2626beab49bc9a63fe5507c3f7b855f79a1d6623eb937f02d6a31397bdfdf10"
    data_transfer = blob_service.download(blob_id1)

    # Seguimos con la descarga como si fueramos el cliente del servicio
    size = 10
    content = ""

    while True:
        data = data_transfer.read(size) 
        content += data.decode()
        if len(data) < size:
            break
   
   # Creamos el archivo llamado prueba.txt
    with open("Sistema_directorios/home/prueba.txt", "w") as file:
        file.write(content)
        file.close()

    data_transfer2 = DataTransfer("Sistema_directorios/home/prueba.txt")   
    blob_id2 = blob_service.upload(data_transfer2)

    assert( blob_id2 == blob_id1) # Comprobamos que el contenido del archivo prueba.txt es el mismo que el texto1.txt

