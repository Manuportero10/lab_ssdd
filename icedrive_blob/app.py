"""Authentication service application."""

import logging
import sys
import time
import threading
from typing import List

import Ice
import IceDrive
import IceStorm

from .blob import BlobService, DataTransfer
from .delayed_response import BlobQueryResponse, BlobQuery
from .discovery import Discovery

class BlobApp(Ice.Application):
    """Implementation of the Ice.Application for the blob service."""

    def run(self, args: List[str]) -> int:
        """Execute the code for the BlobApp class."""
        print("Iniciando servidor...\n")

        properties = self.communicator().getProperties()
        topic_name = properties.getProperty("Discovery.Topic")
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            self.communicator().propertyToProxy("IceStorm.Proxy")
        )
        topic_delayed_response_name = properties.getProperty("Blob.DeferredResolution.Topic")

        try:
            topic = topic_manager.retrieve(topic_name)
            topic_delayed_response = topic_manager.retrieve(topic_delayed_response_name)
        except IceStorm.NoSuchTopic:
            topic = topic_manager.create(topic_name)
            topic_delayed_response = topic_manager.create(topic_delayed_response_name)
            
        print("Topic name: ", topic_name, "\nObject: ", topic, "\n")
        print("Topic name (delayed response): ", topic_delayed_response_name, "\nObject: ", topic_delayed_response, "\n")
        
        discovery_pub = IceDrive.DiscoveryPrx.uncheckedCast(topic.getPublisher())  # es el que envia los anuncios de los otros servicios
        delayed_query_pub = IceDrive.BlobQueryPrx.uncheckedCast(topic_delayed_response.getPublisher()) # es el que envia las peticiones de los otros servicios
        print("Publisher: ", discovery_pub, "\n")
        
        adapter = self.communicator().createObjectAdapter("BlobAdapter")
        adapter.activate()

        
        discovery_servant = Discovery() #sirviente del servicio de descubrimiento receptor

        #delay_response_servant = BlobQueryResponse() #sirviente del servicio de respuesta diferida receptor
        
        servant = BlobService(discovery_servant,delayed_query_pub)
        
        servant_proxy = adapter.addWithUUID(servant) # Creamos el proxy del servicio
        discovery = adapter.addWithUUID(discovery_servant)

        #delay_response = adapter.addWithUUID(delay_response_servant)
        #delayed_query = adapter.addWithUUID(delayed_query_servant)

        discovery_proxy = IceDrive.DiscoveryPrx.checkedCast(discovery) # Creamos el proxy del servicio de descubrimiento

        #delay_response_proxy = IceDrive.BlobQueryResponsePrx.checkedCast(delay_response) # Creamos el proxy del servicio de respuesta diferida
        #delayed_query_proxy = IceDrive.BlobQueryPrx.checkedCast(delayed_query)
        
        topic.subscribeAndGetPublisher({},discovery_proxy) # es el que recibe los anuncios de los otros servicios

        #topic_delayed_response.subscribeAndGetPublisher({},delay_response_proxy) # es el que recibe las peticiones de los otros servicios
        #topic_delayed_response.subscribeAndGetPublisher({},delayed_query_proxy) # es el que envia las peticiones de los otros servicios
        
                    
        logging.info("Proxy: %s", servant_proxy)
        blob_prx = IceDrive.BlobServicePrx.checkedCast(servant_proxy)

        # Una vez obtenido el proxy del servicio, lo registramos en el servicio de descubrimiento cada 5 secs
        
        hilo = threading.Thread(target=descubrimiento,
                                args=(blob_prx,discovery_pub,))
        hilo.daemon = True
        hilo.start() # iniciamos el hilo que se encargara del recolector de basura
        
        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()
        
        print("\n ======Servicios elegidos===== \n","[BLOB]",discovery_servant.get_BlobService(),"\n[DISCOVERY]",discovery_servant.get_Authentication(),
              "\n[DIRECTORY]",discovery_servant.get_Directory())
        print("fin del servidor\n")

        return 0

def descubrimiento(proxy : IceDrive.BlobServicePrx, discovery_pub : IceDrive.Discovery):
    while True:
        time.sleep(5)
        discovery_pub.announceBlobService(proxy)
        print("Anuncio enviado\n")


class ClientApp(Ice.Application):
        """Client application."""
        def run(self, args: List[str]) -> int:
            # texto2.txt
            adapter = self.communicator().createObjectAdapter("BlobAdapter")
            adapter.activate()

            id_blob = str("c06b6e74e0eb82cdbe517aa62896361baffb282602bbf2a338dc9475652144ac")

            # texto3.txt
            id_blob2 = str("ac1e9040b291a72aa1e818526432100391faea53ed6c33906002849d84f9fbac")
            

            # texto4.txt
            id_blob3 = str("5ff53f6cdf06492c46686968ebbeb0294fb6ab2f8d214765306af229e8c79f14") 
            id_blob3_mod = str("2d72e50f87e59035990929be090e27d24e92939b1362a477860e8b4571d204f5") # modificado

            # texto1.txt
            id_blob4 = str("fdd703585a9e1fdc3f7d6a79aeed0516b9092017b79e4d1e50fcb55d46c312b2")

            #Recordatorio: estos id anteriores todos son validos menos id_blob3

            ruta_texto1 = str("/home/manuel/Desktop/Git/lab_ssdd/icedrive_blob/Sistema_directorios/home/texto1.txt")
            ruta_texto2 = str("/home/manuel/Desktop/Git/lab_ssdd/icedrive_blob/Sistema_directorios/home/texto2.txt")
            ruta_texto3 = str("/home/manuel/Desktop/Git/lab_ssdd/icedrive_blob/Sistema_directorios/home/texto3.txt")
            ruta_texto4 = str("/home/manuel/Desktop/Git/lab_ssdd/icedrive_blob/Sistema_directorios/home/texto4.txt")

            """Code to be run by the application."""
            if len(args) != 2:
                print("Error: a proxy, and only one proxy, should be passed")
                return 1
            
            print("Creando proxy blob...\n")
            proxy = self.communicator().stringToProxy(args[1])
            blob_prx = IceDrive.BlobServicePrx.checkedCast(proxy)

            if not blob_prx:
                print(f"Proxy {blob_prx} is not available.")
                return 2
            
            print("Proxy blob: ", blob_prx, " creado correctamente\n")

            print("---------PRUEBA 1: Un cliente puede subir un blolb (texto1.txt)--------\n")
            time.sleep(5)
            superado = test_upload(self,blob_prx,id_blob4,ruta_texto1,adapter)
            if superado:
                print("Prueba 1 superada\n")

            print("Prueba 5: Un cliente puede incrementar los enlaces con un id valido (texto1.txt)--------\n")
            time.sleep(3)
            test_link(self,blob_prx,id_blob4)
            print("-----------------Prueba 5 finalizada------------------\n")

            print("---------PRUEBA 6: Un cliente intenta incrementar un enlace a un blobid invalido--------\n")
            time.sleep(5)
            try:
                test_link(self,blob_prx,id_blob3)
            except IceDrive.UnknownBlob:
                print("-------------Salio la excepcion esperada --> Prueba 6 superada--------------\n")


            print("-------------Prueba 7: Un cliente puede decrementar los enlaces con un id valido (texto1.txt)--------\n")
            time.sleep(5)
            test_link(self,blob_prx,id_blob4) # no querremos que se elimine en esta prueba
            time.sleep(2)
            test_unlink(self,blob_prx,id_blob4)
            print("-------------Prueba 7 finalizada--------------\n")

            print("---------------Prueba 8: Un cliente intenta decrementar los enlaces de un id invalido --------\n")
            time.sleep(5)
            try:
                test_unlink(self,blob_prx,id_blob3)
            except IceDrive.UnknownBlob:
                print("------------Salio la excepcion esperada --> Prueba 8 superada--------------\n")

            print("------------Prueba 9: Un blob que pasa de 1 a 0 pasa a ser destruido (texto4.txt)--------\n")
            time.sleep(5)
            test_upload(self,blob_prx,id_blob3_mod,ruta_texto4,adapter) # primero tiene que estar en la persistencia
            test_link(self,blob_prx,id_blob3_mod)
            time.sleep(2)
            test_unlink_remove(self,blob_prx,id_blob3_mod)
            print("-----------Si no está " + id_blob3_mod + " en la persistencia de enlaces --> Prueba 9 superada--------\n")

            print("---------PRUEBA 2 y 10: Un cliente puede descargar un blob con un id valido (texto1.txt)--------\n")
            time.sleep(5)
            test_download(self,blob_prx,id_blob4)
            print("----------Prueba 2 superada. Si sale el mismo contenido --> Prueba 10 superada----------\n")

            print("---------PRUEBA 4: Un cliente intenta descargar un blob con un id invalido recibe la excepcion UnknownBlob--------\n")
            time.sleep(5)
            try:
                test_download(self,blob_prx,id_blob3)
            except IceDrive.UnknownBlob:
                print("Salio la excepcion esperada --> Prueba 4 superada\n")

            print("---------PRUEBA 12: el blobid de un blob coincide con el hexidigest de la suma hash sha256 (texto3.txt)--------\n")
            time.sleep(5)
            superado = test_upload(self,blob_prx,id_blob2,ruta_texto3,adapter)
            test_link(self,blob_prx,id_blob2)
            if superado:
                print("----------Prueba 12 superada-----------\n")

            print("--------- PRUEBA BONUS: Un cliente sube un archivo y el recolector de basura lo elimina (texto2.txt)--------\n")
            time.sleep(5)
            superado = test_upload(self,blob_prx,id_blob,ruta_texto2,adapter)
            time.sleep(12)
            print("-------------Si no esta " + id_blob + " en la persistencia de enlaces --> Prueba BONUS superada-------------\n")

            return 0


def test_download(self, blob_prx : IceDrive.BlobServicePrx, id_blob : str):
            print("Descargando archivo a traves de su id...\n")
            # Un cliente puede descargar un blob con un id valido
            prx = self.communicator().stringToProxy(str(blob_prx.download(id_blob)))
            data_tranfer_prx = IceDrive.DataTransferPrx.checkedCast(prx)
            
            if data_tranfer_prx is not None:
                print("Proxy DataTransfer: ", data_tranfer_prx, " creado correctamente\n")

            #usamos el proxy para descargar el archivo
            size=10
            content = ""
            
            while True:
                data = data_tranfer_prx.read(size) #Llama bien a la funcion read del proxy 
                content += data.decode()
                if len(data) == 0:
                    data_tranfer_prx.close()
                    break
            
            print("Archivo descargado correctamente\n")
            print("Contenido del archivo: \n" + content + "\n")
            print("Fin de la descarga\n")

def test_upload(self, blob_prx : IceDrive.BlobServicePrx, id_blob : str, ruta : str, adapter) -> bool:
    print("Subiendo archivo...\n")

    servant = DataTransfer(ruta)
    prx = adapter.addWithUUID(servant)
    data_transfer = IceDrive.DataTransferPrx.uncheckedCast(prx)
    data_transfer_prx = IceDrive.DataTransferPrx.checkedCast(data_transfer)
    
    id_blob2 = blob_prx.upload(data_transfer_prx)
    if id_blob2 == id_blob:
        print("Archivo subido correctamente\n")
        print("ID: " + id_blob2)
        return True
    else:
        print("Archivo no subido correctamente\n")
        return False
       
def test_link(self,blob_prx : IceDrive.BlobServicePrx, id_blob : str):
    print("\n--------------------------------\nCreando link...\n")
    blob_prx.link(id_blob) # Tendremos que corroborarlo, mirando en los archivos de persistencia
    print("Link creado correctamente\n")

def test_unlink(self,blob_prx : IceDrive.BlobServicePrx, id_blob : str):
    print("\n--------------------------------\nQuitando link...\n")
    blob_prx.unlink(id_blob) # Tendremos que corroborarlo, mirando en los archivos de persistencia

    print("Links eliminado correctamente\n")

def test_unlink_remove(self,blob_prx,id_blob2):
    print("\n--------------------------------\nQuitando link y eliminando archivo...\n")
    blob_prx.unlink(id_blob2) # Tendremos que corroborarlo, mirando en los archivos de persistencia
    print("Link eliminado y archivo borrado correctamente\n")       