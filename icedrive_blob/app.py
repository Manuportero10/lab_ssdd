"""Authentication service application."""

import logging
import sys
import time

from typing import List

import Ice
Ice.loadSlice("icedrive_blob/icedrive.ice")
import IceDrive

from .blob import BlobService 

label_fin = "\n--------------------------------------[FIN]-----------------------------------------------------------\n"

class BlobApp(Ice.Application):
    """Implementation of the Ice.Application for the blob service."""

    def run(self, args: List[str]) -> int:
        """Execute the code for the BlobApp class."""
        adapter = self.communicator().createObjectAdapter("BlobAdapter")
        adapter.activate()

        servant = BlobService()
        servant_proxy = adapter.addWithUUID(servant) 
        
        logging.info("Proxy: %s", servant_proxy)

        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()

        print("fin del servidor\n")

        return 0

class ClientApp(Ice.Application):
        """Client application."""
        def run(self, args: List[str]) -> int:
            # tiene mas de un enlace (texto2.txt)
            id_blob = str("c06b6e74e0eb82cdbe517aa62896361baffb282602bbf2a338dc9475652144ac")

            # tiene solo un enlace o no esta en persistencia (texto3.txt)
            id_blob2 = str("ac1e9040b291a72aa1e818526432100391faea53ed6c33906002849d84f9fbac")

            # texto4.txt
            id_blob3 = str("5ff53f6cdf06492c46686968ebbeb0294fb6ab2f8d214765306af229e8c79f14") 
            id_blob3_mod = str("2d72e50f87e59035990929be090e27d24e92939b1362a477860e8b4571d204f5") # modificado

            # texto1.txt
            id_blob4 = str("fdd703585a9e1fdc3f7d6a79aeed0516b9092017b79e4d1e50fcb55d46c312b2")

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

            data_transfer_prx = test_download(self,blob_prx, id_blob)

            if data_transfer_prx is None:
                print("Error al descargar el archivo\n")
                return 3

            data_transfer_prx.close()

            # --------------------------PRUEBAS PARA texto2.txt--------------------------------
            print("\n--------------------------------[PRUEBAS PARA texto2.txt]--------------------------------------------\n")
            test_upload(self, blob_prx,id_blob) #upload a un archivo que ya existe en persistencia (texto2.txt)
            test_link(self,blob_prx,id_blob) #creamos un enlace a un archivo que ya tiene un enlace (texto2.txt)
            test_unlink(self,blob_prx,id_blob) # eliminamos un enlace de un archivo que tiene mas de un enlace (texto2.txt)
            # Como hacemos un link y un unlink sobre el mismo archivo, el numero de enlaces no deberia cambiar
            print(label_fin)
            #-----------------------------------------------------------------------------------


            # --------------------------PRUEBAS PARA texto3.txt--------------------------------
            print("\n--------------------------------[PRUEBAS PARA texto3.txt]--------------------------------------------\n")
            test_upload_new_file(self, blob_prx,id_blob2) #upload a un archivo que no existe en persistencia (texto3.txt)
            time.sleep(5) # simulamos complejidad
            test_link(self,blob_prx,id_blob2) # creamos un enlace a un archivo que no tiene enlaces (texto3.txt) para que no se borre por el recolector de basura
            time.sleep(5)
            test_unlink_remove(self,blob_prx,id_blob2) # eliminamos un enlace de un archivo que solo tiene un enlace (texto3.txt)
            print(label_fin)
            #-----------------------------------------------------------------------------------

            # --------------------------PRUEBAS PARA texto4.txt-------------------------------- 
            print("\n--------------------------------[PRUEBAS PARA texto4.txt]--------------------------------------------\n")
            test_upload_new_file(self, blob_prx,id_blob3_mod) #upload a un archivo que no existe en persistencia (texto4.txt)
            time.sleep(4) # simulamos complejidad
            test_link(self,blob_prx,id_blob3_mod) # creamos un enlace a un archivo que no tiene enlaces (texto4.txt) para que no se borre por el recolector de basura
            time.sleep(8)
            try:
                test_link(self,blob_prx,id_blob3) # creamos un enlace a un archivo que no tiene enlaces (texto4.txt) para que no se borre por el recolector de basura  
            except IceDrive.UnknownBlob:
                print("Error: El archivo no existe en persistencia: " + id_blob3) # este id no existe en el directorio del cliente
            
            print(label_fin)
            #-----------------------------------------------------------------------------------

            # --------------------------PRUEBAS PARA texto1.txt--------------------------------
            print("\n--------------------------------[PRUEBAS PARA texto1.txt]--------------------------------------------\n")
            test_upload(self, blob_prx,id_blob4) #upload a un archivo que no existe en persistencia (texto1.txt)
            time.sleep(13) # simulamos complejidad - 10 segundos es el tiempo de vida de un archivo en persistencia sin tener un enlace
            # Como no tenemos ningun enlace al archivo, este deberia ser borrado por el recolector de basura
            print("fin del cliente\n")

            return 0


def test_download(self, blob_prx : IceDrive.BlobServicePrx, id_blob : str):
            print("Descargando archivo a traves de su id...\n")

            prx = self.communicator().stringToProxy(str(blob_prx.download(id_blob))) #proxy para transferir datos es importante parsearlo a str?
            data_tranfer_prx = IceDrive.DataTransferPrx.checkedCast(prx)
            
            print("Tipo de datos del data_transfer_prx: " , type(data_tranfer_prx), "\n")
            print(data_tranfer_prx)

            #usamos el proxy para descargar el archivo
            size=10
            content = ""
            
            while True:
                data = data_tranfer_prx.read(size) #Llama bien a la funcion read del proxy 
                content += data.decode()
                if len(data) == 0:
                    break
            
            print("Archivo descargado correctamente\n")
            print("Contenido del archivo: \n" + content + "\n")
            print("Fin de la descarga\n")
            return data_tranfer_prx

def test_upload(self, blob_prx : IceDrive.BlobServicePrx, id_blob : str) -> None:
    print("Subiendo archivo...\n")

    prx = self.communicator().stringToProxy(str(blob_prx.download(id_blob)))
    data_transfer_prx = IceDrive.DataTransferPrx.checkedCast(prx)

    id_blob2 = blob_prx.upload(data_transfer_prx)
    if id_blob2 == id_blob:
        print("Archivo subido correctamente\n")

    print("ID: " + id_blob2) 
    

def test_upload_new_file(self, blob_prx : IceDrive.BlobServicePrx, id_blob) -> None:
    print("Subiendo un archivo que no está en persistencía\n")

    prx = self.communicator().stringToProxy(str(blob_prx.download(id_blob)))
    data_transfer_prx = IceDrive.DataTransferPrx.checkedCast(prx)

    id_blob2 = blob_prx.upload(data_transfer_prx)
    if id_blob2 == id_blob:
        print("Archivo subido correctamente\n")

    print("ID: " + id_blob2) 
    

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