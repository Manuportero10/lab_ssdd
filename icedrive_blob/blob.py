"""Module for servants implementations."""

import Ice
  
import IceDrive

import hashlib

import os

import threading
from .GarbageCollector import garbage_collector     


def decorator(func):
    def wrapper(self, current=None):
        result = func(self, current=current)
        return result
    return wrapper
 
class DataTransfer(IceDrive.DataTransfer):
    """Implementation of an IceDrive.DataTransfer interface."""
    def __init__(self, file : str) -> None: 
        self.file = open(file, "r")
        self.name_file = file

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
        self.self = None



class BlobService(IceDrive.BlobService):
    """Implementation of an IceDrive.BlobService interface."""
    def __init__(self):
        self.ruta_diccionario_id_nlinks = "icedrive_blob/Sistema_directorios/tmp/historial_blob.txt" 
        self.ruta_diccionario_path_id = "icedrive_blob/Sistema_directorios/tmp/historial_rutas.txt"
        self.ruta_archivos = "icedrive_blob/Sistema_directorios/home"

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
            with open(self.ruta_diccionario_id_nlinks, "a") as file: # "a"= append --> añadimos sin sobreescribir lo que hay
                file.write(blobid + " 0\n")
            

    def update_dictionary_paths(self, blobid: str, file_name : str, current: Ice.Current = None) -> None:
        """Updates the diccionary which is stored in Sistema_directorios/tmp/historial_rutas."""
        # Comprobemos si el fichero esta vacío
        if os.stat(self.ruta_diccionario_path_id).st_size == 0:
            with open(self.ruta_diccionario_path_id, "w") as file:
                file.write(file_name + " " + blobid + "\n")
            
        else:
            with open(self.ruta_diccionario_path_id, "a") as file:
                file.write(file_name  + " " + blobid + "\n")

    def update_persistence_file(self, diccionario : dict, ruta : str, cuurent: Ice.Current = None) -> None:
        """Updates the persistence file given as a parameter."""
        with open(ruta, "w") as file:
            for key, value in diccionario.items():
                file.write(key + " " + value + "\n") 

    def update_dictionary_links(self, diccionario_id_nlinks : dict, current: Ice.Current = None) -> None:
        """Updates the links diccionary which is stored in Sistema_directorios/tmp/historial_blob.""" 
    
        cont_lines = 0

        if os.stat(self.ruta_diccionario_id_nlinks).st_size != 0:
            with open(self.ruta_diccionario_id_nlinks, "r") as file:
                lineas_diccionario = file.readlines()

                for line_file in lineas_diccionario:
                    line = line_file.split()

                    if line[1] != diccionario_id_nlinks[line[0]]: 
                        line_changed = str(line[0] + " " + diccionario_id_nlinks[line[0]] + "\n") 
                        lineas_diccionario[cont_lines] = line_changed

                    cont_lines += 1
              
            with open(self.ruta_diccionario_id_nlinks, "w") as file:         
                file.writelines(lineas_diccionario)
                

        file.close()      
        
    def removes_entries_dictionary(self, diccionario_id_nlinks : dict, diccionario_rutas : dict, current: Ice.Current = None) -> None:
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
        
        diccionario_id_nlinks = self.recover_dictionary(self.ruta_diccionario_id_nlinks) # necesitamos que el diccionario sea persistente entre ejecuciones
        if blob_id in diccionario_id_nlinks:
            cont_links = int(diccionario_id_nlinks[blob_id]) + 1 #no se actuliza el contador (es como si se cambiará el id+1)
            diccionario_id_nlinks[blob_id] = str(cont_links)
            # Actualizamos el fichero diccionario  
            self.update_dictionary_links(diccionario_id_nlinks)
        else:
            raise IceDrive.UnknownBlob(blob_id) 
        

    def unlink(self, blob_id: str, current: Ice.Current = None) -> None:
        """Mark a blob_id as unlinked (removed) from some directory."""

        diccionario_id_nlinks = self.recover_dictionary(self.ruta_diccionario_id_nlinks) # necesitamos que el diccionario sea persistente entre ejecuciones
        if blob_id in diccionario_id_nlinks:
            cont_links = int(diccionario_id_nlinks[blob_id]) - 1 #no se actuliza el contador (es como si se cambiará el id+1)
            diccionario_id_nlinks[blob_id] = str(cont_links)
            # Actualizamos el fichero diccionario
            if cont_links > 0:  
                self.update_dictionary_links(diccionario_id_nlinks)
            else: # en este caso cont_links = 0, por lo que abria que eliminarlo del diccionario y del directorio donde esta almacenado
                print("Eliminando archivo.." + blob_id + "\n")
                file = self.find_file(blob_id)
                full_path = os.path.join(self.ruta_archivos, file)

                os.remove(full_path)
                # Eliminarlo tambien de los archivos de persistencia
                diccionario_rutas = self.recover_dictionary(self.ruta_diccionario_path_id)
                del diccionario_rutas[file]
                del diccionario_id_nlinks[blob_id]
                self.removes_entries_dictionary(diccionario_id_nlinks, diccionario_rutas)
        else:
            raise IceDrive.UnknownBlob(blob_id)      


    def calcular_hash_archivo(self,ruta_archivo : str ,tamano_buffer : int, current: Ice.Current = None)-> str:
        """Calcula el hash de un archivo"""

        hash_calculado = hashlib.new("sha256")
        with open(ruta_archivo, "rb") as archivo:
            while (bloque := archivo.read(tamano_buffer)):
                hash_calculado.update(bloque)
        return hash_calculado.hexdigest()

    def find_file(self, blolbid : str) -> str:
        """Find the file with the given blobid."""

        encontrado = False
        hashes = {}

        # Recorremos el directorio donde se almacenan los blobs y calculamos el hash de cada uno de ellos
        # Para saber si el blobid que nos pasan como parametro esta almacenado en el directorio
        for elemento in os.listdir(self.ruta_archivos):
            ruta_completa = os.path.join(self.ruta_archivos, elemento)
            if os.path.isfile(ruta_completa):
                hash_archivo = self.calcular_hash_archivo(ruta_completa, 10)
                hashes[elemento] = hash_archivo

        for archivo, hash_archivo in hashes.items():
            if hash_archivo == blolbid:
                encontrado = True
                return archivo
            
        if not encontrado:
            raise IceDrive.UnknownBlob(blolbid)
        

    def upload( # Es posible que no sea necesario el filename, porque nos lo tiene que pasar el cliente, pero para probar la lógica
        self, blob: IceDrive.DataTransferPrx, current: Ice.Current = None 
    ) -> str:
        """Register a DataTransfer object to upload a file to the service.
            Returns the blob_id of the uploaded file."""
 
        diccionario_blobs = self.recover_dictionary(self.ruta_diccionario_id_nlinks) # necesitamos que el diccionario sea persistente entre ejecuciones
        content : str = "" 

        # En el caso de que sea un archivo nuevo, tendremos que hacer el proceso de subida
        size = 10
        while True:
            # hay que tener en cuenta lo que ya haya leido el cliente (razon del bucle infinito)
            try:
                data = blob.read(size)
                content += data.decode() 
                if not data or len(data) == 0:   
                    break
            except IceDrive.FailedToReadData: 
                raise IceDrive.FailedToReadData()
             
        blobid = self.convert_text_to_hash(content.encode()) # convertimos el contenido del fichero en hash
        print("blobid: ", blobid, "\n")

        # Comprobamos si el blobid ya existe en el diccionario
        if blobid not in diccionario_blobs:
            self.update_dictionary(blobid)
            file_name = self.find_file(blobid) # obtenemos el nombre del fichero
            self.update_dictionary_paths(blobid, file_name) # actualizamos el diccionario de rutas

            # Lanzamos un hilo, a modo de temporizador del archivo, para que se elimine si no se ha enlazado
            timer_file = 10
            hilo = threading.Thread(target=garbage_collector, args=(timer_file,blobid,self.ruta_diccionario_id_nlinks,self,)) 
            hilo.daemon = True
            hilo.start() # iniciamos el hilo que se encargara del recolector de basura
        else:
            return blobid 

        return blobid     
         
        
    def download(
        self, blob_id: str, current: Ice.Current = None 
    ) -> IceDrive.DataTransferPrx:
        """Return a DataTransfer objet to enable the client to download the given blob_id."""
        try:
            fichero = self.find_file(blob_id) # encontremos el fichero en el directorio donde se almacenan los blobs
        except IceDrive.UnknownBlob: # basicamente el archivo no existe, no esta en el directorio
            raise IceDrive.UnknownBlob(blob_id)
                
        full_path = os.path.join(self.ruta_archivos, fichero)

        servant = DataTransfer(full_path)
        prx = current.adapter.addWithUUID(servant)
        data_transfer_prx = IceDrive.DataTransferPrx.uncheckedCast(prx)   

        return data_transfer_prx      

