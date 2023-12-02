"""Authentication service application."""

import logging
import sys
import time

from typing import List

import Ice
import IceDrive

from .blob import BlobService, DataTransfer


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
            id_blob = str("c06b6e74e0eb82cdbe517aa62896361baffb282602bbf2a338dc9475652144ac") # tiene mas de un enlace
            id_blob2 = str("2fce9849591cf214e1714dcfd45e5d6e39a3f06c3eb3a9e48a7605fae5af4707") # tiene solo un enlace o no esta en persistencia
            id_blob3 = str("12017fe97998a01c10f781d546714e6002effe42d12b1acbeb0254a8441d4b7d") # texto4.txt

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

            data_transfer_prx = prueba_download(self,blob_prx, id_blob)

            if data_transfer_prx is None:
                print("Error al descargar el archivo\n")
                return 3

            data_transfer_prx.close()

            prueba_upload(self, blob_prx,id_blob) #upload a un archivo que ya existe en persistencia (texto2.txt)
            prueba_link(self,blob_prx,id_blob) #creamos un enlace a un archivo que ya tiene un enlace (texto2.txt)
            prueba_unlink(self,blob_prx,id_blob) # eliminamos un enlace de un archivo que tiene mas de un enlace (texto2.txt)

            prueba_upload_new_file(self, blob_prx,id_blob2) #upload a un archivo que no existe en persistencia (texto3.txt)
            time.sleep(5) # simulamos complejidad
            prueba_link(self,blob_prx,id_blob2) # creamos un enlace a un archivo que no tiene enlaces (texto3.txt) para que no se borre por el recolector de basura
            time.sleep(5)
            prueba_unlink_remove(self,blob_prx,id_blob2) # eliminamos un enlace de un archivo que solo tiene un enlace (texto3.txt)

            prueba_upload_new_file(self, blob_prx,id_blob3) #upload a un archivo que no existe en persistencia (texto4.txt)
            time.sleep(12) # simulamos complejidad - ahora el recolector de basura deberia borrar el archivo Timeout = 10s
            
            print("fin del cliente\n")

            return 0


def prueba_download(self, blob_prx : IceDrive.BlobServicePrx, id_blob : str):
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

def prueba_upload(self, blob_prx : IceDrive.BlobServicePrx, id_blob : str) -> None:
    print("Subiendo archivo...\n")

    prx = self.communicator().stringToProxy(str(blob_prx.download(id_blob)))
    data_transfer_prx = IceDrive.DataTransferPrx.checkedCast(prx)

    id_blob2 = blob_prx.upload(data_transfer_prx)
    if id_blob2 == id_blob:
        print("Archivo subido correctamente\n")

    print("ID: " + id_blob2) 
    

def prueba_upload_new_file(self, blob_prx : IceDrive.BlobServicePrx, id_blob) -> None:
    print("Subiendo un archivo que no está en persistencía\n")

    prx = self.communicator().stringToProxy(str(blob_prx.download(id_blob)))
    data_transfer_prx = IceDrive.DataTransferPrx.checkedCast(prx)

    id_blob2 = blob_prx.upload(data_transfer_prx)
    if id_blob2 == id_blob:
        print("Archivo subido correctamente\n")

    print("ID: " + id_blob2) 
    print("Archivo subido correctamente\n")


def prueba_link(self,blob_prx : IceDrive.BlobServicePrx, id_blob : str):
    print("\n--------------------------------\nCreando link...\n")
    blob_prx.link(id_blob) # Tendremos que corroborarlo, mirando en los archivos de persistencia
    print("Link creado correctamente\n")

def prueba_unlink(self,blob_prx : IceDrive.BlobServicePrx, id_blob : str):
    print("\n--------------------------------\nQuitando link...\n")
    blob_prx.unlink(id_blob) # Tendremos que corroborarlo, mirando en los archivos de persistencia

    print("Links eliminado correctamente\n")

def prueba_unlink_remove(self,blob_prx,id_blob2):
    print("\n--------------------------------\nQuitando link y eliminando archivo...\n")
    blob_prx.unlink(id_blob2) # Tendremos que corroborarlo, mirando en los archivos de persistencia
    print("Link eliminado y archivo borrado correctamente\n")       