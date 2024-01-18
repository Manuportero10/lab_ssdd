"""Module for servants implementations."""

import time
import hashlib
import os
import threading
import Ice
import IceDrive
from .GarbageCollector import garbage_collector
from .delayed_response import BlobQueryResponse

class DataTransfer(IceDrive.DataTransfer):
    """Implementation of an IceDrive.DataTransfer interface."""
    def __init__(self, file : str) -> None:
        self.file = open(file, "r")

    def read(self, size : int, current: Ice.Current = None) -> bytes:
        """Returns a list of bytes from the opened file with the size specified."""
        try:
            content : bytes = self.file.read(size).encode()
            return content
        except Exception:
            raise IceDrive.FailedToReadData()

    def close(self, current: Ice.Current = None) -> None:
        """Close the currently opened file."""
        self.file.close()
        current.adapter.remove(current.id) 



class BlobService(IceDrive.BlobService):
    """Implementation of an IceDrive.BlobService interface."""
    def __init__(self, query_discovery,delayed_pub) -> None:
        self.ruta_diccionario_id_nlinks = "icedrive_blob/Sistema_directorios/tmp/historial_blob.txt"
        self.ruta_diccionario_path_id = "icedrive_blob/Sistema_directorios/tmp/historial_rutas.txt"
        self.ruta_persistencia = "icedrive_blob/Sistema_directorios/bin"
        
        self.query_discovery = query_discovery
        self.delayed_pub = delayed_pub
        
        self.expected_responses = {}



    def convert_text_to_hash(self, data: str, current: Ice.Current = None) -> str:
        """Converts the text to hash."""
        hash_file = hashlib.sha256(data).hexdigest()
        return hash_file

    def update_dictionary(self, blobid: str, current: Ice.Current = None) -> None:
        """Updates the diccionary which is stored in Sistema_directorios/tmp/historial_blob."""
        # Comprobemos si el fichero esta vacío
        if os.stat(self.ruta_diccionario_id_nlinks).st_size == 0:
            with open(self.ruta_diccionario_id_nlinks, "w") as file:
                file.write(blobid + " 0\n")
        else:
            with open(self.ruta_diccionario_id_nlinks, "a") as file:
                file.write(blobid + " 0\n")


    def update_persistence_file(self, diccionario : dict,
                                ruta : str, cuurent: Ice.Current = None) -> None:
        """Updates the persistence file given as a parameter."""
        with open(ruta, "w") as file:
            for key, value in diccionario.items():
                file.write(key + " " + value + "\n")


    def removes_entries_dictionary(
        self, diccionario_id_nlinks : dict,diccionario_rutas : dict, current: Ice.Current = None
    ) -> None:
        """Removes the deleted entries due to deacrising the number of links from 1 to 0.
        Rewrite the files with the dictionaries provided."""
        with open(self.ruta_diccionario_id_nlinks, "w") as file:
            for key, value in diccionario_id_nlinks.items():
                file.write(key + " " + value + "\n")

        with open(self.ruta_diccionario_path_id, "w") as file:
            for key, value in diccionario_rutas.items():
                file.write(key + " " + value + "\n")


    def recover_dictionary(self, ruta : str, current: Ice.Current = None) -> dict:
        '''Recovers the dictionary from the file provided.'''
        diccionario = {}
        with open(ruta, "r") as file:
            for line in file:
                line = line.split()
                diccionario[line[0]] = line[1]

        return diccionario
  
    def link(self, blob_id: str, current: Ice.Current = None) -> None:
        """Mark a blob_id file as linked in some directory."""
        # necesitamos que el diccionario sea persistente entre ejecuciones
        diccionario_id_nlinks = self.recover_dictionary(self.ruta_diccionario_id_nlinks)
        if blob_id in diccionario_id_nlinks:
            cont_links = int(diccionario_id_nlinks[blob_id]) + 1 # aumentamos el contador
            # actualizamos el fichero de persistencia
            diccionario_id_nlinks[blob_id] = str(cont_links)
            self.update_persistence_file(diccionario_id_nlinks,self.ruta_diccionario_id_nlinks)
            print("==========[LINK SUCCESS:",blob_id,"]==========\n")
        else:
            raise IceDrive.UnknownBlob(blob_id)


    def unlink(self, blob_id: str, current: Ice.Current = None) -> None:
        """Mark a blob_id as unlinked (removed) from some directory."""

        diccionario_id_nlinks = self.recover_dictionary(self.ruta_diccionario_id_nlinks)
        if blob_id in diccionario_id_nlinks:
            cont_links = int(diccionario_id_nlinks[blob_id]) - 1
            diccionario_id_nlinks[blob_id] = str(cont_links)
            # Actualizamos el fichero diccionario
            if cont_links > 0:
                # actualizamos el fichero de persistencia
                self.update_persistence_file(diccionario_id_nlinks,self.ruta_diccionario_id_nlinks)
            else:
                # Eliminamos el archivo de la persistencia
                try:
                    file = self.find_file(blob_id,self.ruta_persistencia)
                    full_path = os.path.join(self.ruta_persistencia, file)
                    os.remove(full_path)

                    diccionario_rutas = self.recover_dictionary(self.ruta_diccionario_path_id)
                    del diccionario_rutas[file]
                    del diccionario_id_nlinks[blob_id]
                    self.removes_entries_dictionary(diccionario_id_nlinks, diccionario_rutas)
                    print("==========[UNLINK SUCCESS:",blob_id,"]==========\n")
                except IceDrive.UnknownBlob:
                    print("[ERROR] El archivo no existe con [ID=" + blob_id + "] no existe\n")
                    raise IceDrive.UnknownBlob(blob_id)
        else:
            raise IceDrive.UnknownBlob(blob_id)

    def calculate_file_hash(
        self,ruta_archivo : str ,tamano_buffer : int, current: Ice.Current = None
    )-> str:
        """Calculate the hash from a file"""
        hash_calculado = hashlib.new("sha256")
        with open(ruta_archivo, "rb") as archivo:
            while (bloque := archivo.read(tamano_buffer)):
                hash_calculado.update(bloque)
        return hash_calculado.hexdigest()

    def find_file(self, blolbid : str, path : str) -> str:
        """Find the file with the given blobid."""
        encontrado = False
        hashes = {}

        # Recorremos el directorio donde se almacenan los blobs y calculamos el hash de cada uno de
        # ellos para saber si el blobid que nos pasan como parametro esta almacenado
        # en el directorio

        for elemento in os.listdir(path):
            ruta_completa = os.path.join(path, elemento)
            if os.path.isfile(ruta_completa):
                hash_archivo = self.calculate_file_hash(ruta_completa, 10)
                hashes[elemento] = hash_archivo

        for archivo, hash_archivo in hashes.items():
            if hash_archivo == blolbid:
                encontrado = True
                return archivo

        if not encontrado:
            raise IceDrive.UnknownBlob(blolbid)


    def upload(
        self, user: IceDrive.UserPrx, blob: IceDrive.DataTransferPrx, current: Ice.Current = None
    ) -> str:
        """Register a DataTransfer object to upload a file to the service.
            Returns the blob_id of the uploaded file."""
        # lo primero: vamos a comprobar si el usuario esta activo
        prx_auth = self.query_discovery.get_Authentication()

        if prx_auth.verifyUser(user):
            # recuperamos los diccionarios de los archivos de persistencia
            diccionario_blobs = self.recover_dictionary(self.ruta_diccionario_id_nlinks)
            diccionario_paths = self.recover_dictionary(self.ruta_diccionario_path_id)
            content : str = ""

            # En el caso de que sea un archivo nuevo, tendremos que hacer el proceso de subida
            size = 10
            while True:
                try:
                    data = blob.read(size)
                    content += data.decode()
                    if not data or len(data) == 0:
                        blob.close()
                        break
                except IceDrive.FailedToReadData:
                    print("[ERROR] No se ha podido leer el archivo\n")
                    raise IceDrive.FailedToReadData()

            # convertimos el contenido del fichero en hash
            blobid = self.convert_text_to_hash(content.encode())
            print("blobid: ", blobid, "\n")

            # Comprobamos si el blobid ya existe en el diccionario
            if blobid not in diccionario_blobs:
                print("==========[UPLOADING]: "+blobid+"==========\n")
                self.update_dictionary(blobid)
                file_name = blobid + ".txt"
                # añadimos el contenido del archivo en blobid.txt - lo creamos en nuestra persistencia
                full_path = os.path.join(self.ruta_persistencia, file_name)
                with open(full_path, "w") as file:
                    file.write(content)

                # actualizamos el fichero de persistencia
                diccionario_paths[file_name] = blobid
                self.update_persistence_file(diccionario_paths,self.ruta_diccionario_path_id)

                # Lanzamos un hilo, a modo de temporizador del archivo
                # para que se elimine si no se ha enlazado
                timer_file = 20
                hilo = threading.Thread(target=garbage_collector,
                                        args=(timer_file,blobid,self.ruta_diccionario_id_nlinks,self,))
                hilo.daemon = True
                hilo.start() # iniciamos el hilo que se encargara del recolector de basura
            else:
                return blobid
            
            print("==========[UPLOAD SUCCESS]==========\n")
        else:
            print("[ERROR] El usuario no esta autorizado \n")
            raise IceDrive.Unauthorized()
        
        return blobid


    def download(
        self, user: IceDrive.UserPrx, blob_id: str, current: Ice.Current = None
    ) -> IceDrive.DataTransferPrx:
        
        """Return a DataTransfer objet to enable the client to download the given blob_id."""
        prx_auth = self.query_discovery.get_Authentication()
        
        # lo primero: vamos a comprobar si el usuario esta activo
        if prx_auth.verifyUser(user):
            try:
                # encontremos el fichero en el directorio donde se almacenan los blobs
                fichero = self.find_file(blob_id,self.ruta_persistencia)
                full_path = os.path.join(self.ruta_persistencia, fichero)

                servant = DataTransfer(full_path)
                prx = current.adapter.addWithUUID(servant)
                data_transfer_prx = IceDrive.DataTransferPrx.uncheckedCast(prx)
                print("==========[DOWNLOAD SUCCESS]==========\n")
                return data_transfer_prx
            except IceDrive.UnknownBlob as e: # basicamente el archivo no existe, no esta en el directorio
                # Respuesta diferida
                future = Ice.Future()
                response_servant = BlobQueryResponse(future)
                response = current.adapter.addWithUUID(response_servant)
                response_prx = IceDrive.BlobQueryResponsePrx.uncheckedCast(response)
                self.delayed_pub.downloadBlob(blob_id, response_prx) #publicamos la query
                blob_prox = self.query_discovery.get_BlobService()
                data_prx = blob_prox.download(user, blob_id)
                response_prx.downloadBlob(data_prx)
                print("==========[DELAYED DOWNLOAD SUCCESS]==========\n") 
                return future          
        else:
            print("[ERROR] El usuario no esta autorizado \n")
            raise IceDrive.Unauthorized()
            

        
