"""Module for servants implementations."""

import Ice

Ice.loadSlice("icedrive.ice")  
import IceDrive

import hashlib

import os

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
        self.self = None
        


class BlobService(IceDrive.BlobService):
    """Implementation of an IceDrive.BlobService interface."""
    def __init__(self, ruta_archivo : str, ruta_diccionario_id_nlinks : str, ruta_diccionario_path_id : str):
        self.ruta_archivo = ruta_archivo
        self.ruta_diccionario_id_nlinks = ruta_diccionario_id_nlinks
        self.ruta_diccionario_path_id = ruta_diccionario_path_id 


    def convert_text_to_hash(self, data: str, current: Ice.Current = None) -> str:
        """Converts the text to hash."""
        hash_file = hashlib.sha256(data).hexdigest()
        return hash_file

    #estos 2 metodos update pueden ser uno solo.
    def update_dictionary(self, blobid: str, current: Ice.Current = None) -> None:
        """Updates the diccionary which is stored in Sistema_directorios/tmp/historial_blob."""
        # Comprobemos si el fichero esta vacío
        if os.stat(self.ruta_diccionario_id_nlinks).st_size == 0:
            with open(self.ruta_diccionario_id_nlinks, "w") as file:
                file.write(blobid + " 0\n")
            file.close()
        else:
            with open(self.ruta_diccionario_id_nlinks, "a") as file: # "a"= append --> añadimos sin sobreescribir lo que hay
                file.write(blobid + " 0\n")
            file.close()


    def update_dictionary_paths(self, blobid: str, current: Ice.Current = None) -> None:
        """Updates the diccionary which is stored in Sistema_directorios/tmp/historial_rutas."""
        # Comprobemos si el fichero esta vacío
        if os.stat(self.ruta_diccionario_path_id).st_size == 0:
            with open(self.ruta_diccionario_path_id, "w") as file:
                file.write(self.ruta_archivo + " " + blobid + "\n")
            file.close()
        else:
            with open(self.ruta_diccionario_path_id, "a") as file:
                file.write(self.ruta_archivo  + " " + blobid + "\n")


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
        
    
    def recover_dictionary_links(self, current: Ice.Current = None) -> dict:
        """Recovers the diccionary which is stored in Sistema_directorio/tmp/historial_blob.txt"""
        diccionario_id_nlinks = {}

        with open(self.ruta_diccionario_id_nlinks, "r") as file: 
            for line in file:
                line = line.split()
                diccionario_id_nlinks[line[0]] = line[1] 
        file.close()

        return diccionario_id_nlinks

    # estos metodos pueden ser uno solo.
    def recover_dictionary_paths(self, current: Ice.Current = None) -> dict:
        """Recovers the diccionary which is stored in Sistema_directorio/tmp/historial_rutas.txt"""
        diccionario_path_id = {}

        with open(self.ruta_diccionario_path_id, "r") as file:    
            for line in file:
                line = line.split()
                diccionario_path_id[line[0]] = line[1] 
        file.close()

        return diccionario_path_id
    

    def link(self, blob_id: str, current: Ice.Current = None) -> None:
        """Mark a blob_id file as linked in some directory."""
        
        diccionario_id_nlinks = self.recover_dictionary_links() # necesitamos que el diccionario sea persistente entre ejecuciones
        if blob_id in diccionario_id_nlinks:
            cont_links = int(diccionario_id_nlinks[blob_id]) + 1 #no se actuliza el contador (es como si se cambiará el id+1)
            diccionario_id_nlinks[blob_id] = str(cont_links)
            # Actualizamos el fichero diccionario  
            self.update_dictionary_links(diccionario_id_nlinks)
        else:
            raise IceDrive.UnknownBlob(blob_id) 
        

    def unlink(self, blob_id: str, current: Ice.Current = None) -> None:
        """Mark a blob_id as unlinked (removed) from some directory."""

        diccionario_id_nlinks = self.recover_dictionary_links() # necesitamos que el diccionario sea persistente entre ejecuciones
        if blob_id in diccionario_id_nlinks:
            cont_links = int(diccionario_id_nlinks[blob_id]) - 1 #no se actuliza el contador (es como si se cambiará el id+1)
            diccionario_id_nlinks[blob_id] = str(cont_links)
            # Actualizamos el fichero diccionario
            if cont_links >= 0:  
                self.update_dictionary_links(diccionario_id_nlinks)
            else: # en este caso cont_links = -1, por lo que abria que eliminarlo del diccionario y del directorio donde esta almacenado
                pass
        else:
            raise IceDrive.UnknownBlob(blob_id)      

    def find_file(self,blolbid : str) -> str:
        """Find the file with the given blobid."""
        diccionario_rutas = self.recover_dictionary_paths()
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
 
        diccionario_blobs = self.recover_dictionary_links() # necesitamos que el diccionario sea persistente entre ejecuciones
        diccionario_rutas = self.recover_dictionary_paths()
        content : str = ""
         
        size = 10
        blob = DataTransfer(self.ruta_archivo) # este seria seria blob
        while True:
            # hay que tener en cuenta lo que ya haya leido el cliente (razon del bucle infinito)
            try:
                data = blob.read(size)
                content += data.decode() 
                if not data or len(data) < size:   
                    break
            except IceDrive.FailedToReadData: 
                raise IceDrive.FailedToReadData()
            
        blob.close()        
         
        blobid = self.convert_text_to_hash(content.encode()) # convertimos el contenido del fichero en hash

        if self.ruta_archivo not in diccionario_rutas:
            self.update_dictionary_paths(blobid)

        # Comprobamos si el blobid ya existe en el diccionario
        if blobid not in diccionario_blobs:
            self.update_dictionary(blobid)

        return blobid 
        
        
    def download(
        self, blob_id: str, current: Ice.Current = None 
    ) -> IceDrive.DataTransferPrx:
        """Return a DataTransfer objet to enable the client to download the given blob_id."""
        if blob_id not in self.recover_dictionary_links():
            raise IceDrive.UnknownBlob(blob_id)  
    
        fichero = self.find_file(blob_id) # encontremos el fichero en el directorio donde se almacenan los blobs
        data_transfer = DataTransfer(fichero)
        return data_transfer

