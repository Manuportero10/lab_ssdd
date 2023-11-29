"""Module for servants implementations."""

import Ice

Ice.loadSlice("icedrive.ice")  
import IceDrive

import hashlib

import os

import threading
from GarbageCollector import garbage_collector    

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
        self.ruta_diccionario_id_nlinks = "Sistema_directorios/tmp/historial_blob.txt" 
        self.ruta_diccionario_path_id = "Sistema_directorios/tmp/historial_rutas.txt"

    def convert_text_to_hash(self, data: str, current: Ice.Current = None) -> str:
        """Converts the text to hash."""
        hash_file = hashlib.sha256(data).hexdigest()     
        return hash_file

    #estos 2 metodos update pueden ser uno solo (o no).
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

    def update_dictionary_paths_id_changed(self, diccionario_path_id : dict, current: Ice.Current = None) -> None:
        """Updates the diccionary with a changed blobid which is stored in Sistema_directorios/tmp/historial_rutas."""
        cont_lines = 0

        if os.stat(self.ruta_diccionario_path_id).st_size != 0:
            with open(self.ruta_diccionario_path_id, "r") as file:
                lineas_diccionario = file.readlines()

                for line_file in lineas_diccionario:
                    line = line_file.split()

                    if line[1] != diccionario_path_id[line[0]]: 
                        line_changed = str(line[0] + " " + diccionario_path_id[line[0]] + "\n") 
                        lineas_diccionario[cont_lines] = line_changed

                    cont_lines += 1
              
            with open(self.ruta_diccionario_path_id, "w") as file:         
                file.writelines(lineas_diccionario)

    # ¿Puedes hacer lo mismo con paths id changed?
    def update_dictionary_links_id_changed(self, diccionario_id_nlinks : dict, current: Ice.Current = None) -> None:
        """Updates the diccionary with a changed blobid, but remaining its old number of links which is stored in Sistema_directorios/tmp/historial_blob."""
        with open(self.ruta_diccionario_id_nlinks, "w") as file:
            for key, value in diccionario_id_nlinks.items():
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
                file = self.find_file(blob_id)
                os.remove(file)
                # Eliminarlo tambien de los archivos de persistencia
                diccionario_rutas = self.recover_dictionary(self.ruta_diccionario_path_id)
                del diccionario_rutas[file]
                del diccionario_id_nlinks[blob_id]
                self.removes_entries_dictionary(diccionario_id_nlinks, diccionario_rutas)
        else:
            raise IceDrive.UnknownBlob(blob_id)      

    def find_file(self,blolbid : str) -> str:
        """Find the file with the given blobid."""
        diccionario_rutas = self.recover_dictionary(self.ruta_diccionario_path_id)
        encontrado = False

        for key, value in diccionario_rutas.items():
            if value == blolbid:
                encontrado = True
                return key
            
        if not encontrado:
            raise IceDrive.UnknownBolb(blolbid)
        

    def upload( # Es posible que no sea necesario el filename, porque nos lo tiene que pasar el cliente, pero para probar la lógica
        self, blob: IceDrive.DataTransferPrx, current: Ice.Current = None
    ) -> str:
        """Register a DataTransfer object to upload a file to the service.
            Returns the blob_id of the uploaded file."""
 
        diccionario_blobs = self.recover_dictionary(self.ruta_diccionario_id_nlinks) # necesitamos que el diccionario sea persistente entre ejecuciones
        diccionario_rutas = self.recover_dictionary(self.ruta_diccionario_path_id)
        content : str = ""

        # En el caso de que sea un archivo nuevo, tendremos que hacer el proceso de subida
        size = 10
        while True:
            # hay que tener en cuenta lo que ya haya leido el cliente (razon del bucle infinito)
            try:
                data = blob.read(size)
                content += data.decode() 
                if not data or len(data) < size:
                    blob.close()   
                    break
            except IceDrive.FailedToReadData: 
                raise IceDrive.FailedToReadData()
             
        blobid = self.convert_text_to_hash(content.encode()) # convertimos el contenido del fichero en hash

        if blob.name_file in diccionario_rutas and diccionario_rutas[blob.name_file] == blobid: # ya esta almacenado en persistencia
            return diccionario_rutas[blob.name_file]
        
        if blob.name_file not in diccionario_rutas:
            self.update_dictionary_paths(blobid, blob.name_file) # nueva entrada en la persistencia de rutas
            diccionario_rutas = self.recover_dictionary(self.ruta_diccionario_path_id) # actualizamos el diccionario de rutas 

        # Si fichero ha sido modificado, tendriamos que modificar tanto el diccionario de rutas como el de blobs y sus archivos de persistencia
        if diccionario_rutas[blob.name_file] != blobid:
            aux_nlinks = diccionario_blobs[diccionario_rutas[blob.name_file]] # guardamos el numero de links del fichero antiguo
            del diccionario_blobs[diccionario_rutas[blob.name_file]] # eliminamos la entrada del diccionario de blobs obsoleta 

            diccionario_rutas[blob.name_file] = blobid
            diccionario_blobs[blobid] = aux_nlinks

            self.update_dictionary_paths_id_changed(diccionario_rutas)
            self.update_dictionary_links_id_changed(diccionario_blobs) 
             

        # Comprobamos si el blobid ya existe en el diccionario
        if blobid not in diccionario_blobs:
            self.update_dictionary(blobid)

            # Lanzamos un hilo, a modo de temporizador del archivo, para que se elimine si no se ha enlazado
            timer_file = 10
            hilo = threading.Thread(target=garbage_collector, args=(timer_file,blobid)) 
            hilo.daemon = True
            hilo.start() # iniciamos el hilo que se encargara del recolector de basura 

        return blobid 
        
        
    def download(
        self, blob_id: str, current: Ice.Current = None 
    ) -> IceDrive.DataTransferPrx:
        """Return a DataTransfer objet to enable the client to download the given blob_id."""
        if blob_id not in self.recover_dictionary(self.ruta_diccionario_id_nlinks):
            raise IceDrive.UnknownBlob(blob_id)  
    
        fichero = self.find_file(blob_id) # encontremos el fichero en el directorio donde se almacenan los blobs
        data_transfer = DataTransfer(fichero)
        return data_transfer      

