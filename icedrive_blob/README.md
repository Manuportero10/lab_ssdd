# IceDrive Blob service


**Autor**: Manuel Cano García

**Correo**: Manuel.Cano3@alu.uclm.es

---

## Paso 2: implementación en ICE

Una vez comprobado que el funcionamiento en local funciona como debería, ahora pasaremos a añadirle los elementos para convertir nuestro programa en un programa distribuido con la utilización del middleware Ice. Como podemos ver en las interfaces, los elementos que devuelven objetos proxys o tienen como argumentos objetos proxys, son los métodos **download** y **upload** de la clase **BlobService**. 

- **download**
```python
    def download(
        self, blob_id: str, current: Ice.Current = None
    ) -> IceDrive.DataTransferPrx:
        """Return a DataTransfer objet to enable the client to download the given blob_id."""
        try:
            # encontremos el fichero en el directorio donde se almacenan los blobs
            fichero = self.find_file(blob_id,self.ruta_persistencia)
        except IceDrive.UnknownBlob: # basicamente el archivo no existe, no esta en el directorio
            print("[ERROR] El archivo no existe con [ID=" + blob_id + "] no existe\n")
            raise IceDrive.UnknownBlob(blob_id)

        full_path = os.path.join(self.ruta_persistencia, fichero)

        servant = DataTransfer(full_path)
        prx = current.adapter.addWithUUID(servant)
        data_transfer_prx = IceDrive.DataTransferPrx.uncheckedCast(prx)

        return data_transfer_prx
```

La lógica del método download reside en buscar, dado el id proporcionado por el cliente, en nuestra persistencia (donde almacenemos los blobs) para ver si existe algún fichero que tenga el mismo id, si es asi, eso significará que es un id valido y se creará un DataTransferPrx para que el cliente pueda descargarlo.
<br>

- **upload**
```python
    def upload(
        self, blob: IceDrive.DataTransferPrx, current: Ice.Current = None
    ) -> str:
        """Register a DataTransfer object to upload a file to the service.
            Returns the blob_id of the uploaded file."""
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
                raise IceDrive.FailedToReadData()

        # convertimos el contenido del fichero en hash
        blobid = self.convert_text_to_hash(content.encode())
        print("blobid: ", blobid, "\n")

        # Comprobamos si el blobid ya existe en el diccionario
        if blobid not in diccionario_blobs:
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
            timer_file = 10
            hilo = threading.Thread(target=garbage_collector,
                                    args=(timer_file,blobid,self.ruta_diccionario_id_nlinks,self,))
            hilo.daemon = True
            hilo.start() # iniciamos el hilo que se encargara del recolector de basura
        else:
            return blobid

        return blobid 
 ``` 

A traves del objeto proxy, realizamos un bucle para leer el contenido del archivo, después de eso, dicho contenido lo pasamos a la suma hash **sha256**. También comprobaremos si el blob obtenido esta ya guardado dentro de nuestro diccionario donde guardamos los blob_id, junto con su numero de enlaces, si ya está, simplemente devolvemos el blobid, en caso contrario, eso significará que un archivo en nuestro directorio de persistencia donde guardamos los archivos blob que el cliente ya ha subido por lo que actualizamos los diccionarios, creamos un archivo "blobid".txt donde tendrá el contenido del archivo del cliente y por ultimo creamos un hilo, que se esté ejecutando en segundo plano con la propiedad daemon.  
```python 
hilo.daemon = True
```
Al ser un archivo nuevo en nuestro directorio de persistencia, el numero de enlaces de ese archivo es de 0, por esa razón, creamos el hilo, para ver si pasado x tiempo, dicho archivo sigue teniendo 0 enlaces, para eliminarlo a traves del recolector de basura.

Mas allá de estos cambios, los demás métodos utilizados en la implementación local, no se han visto afectado por la utilización del middleware, por lo que su lógica esta intacta con respecto a local.

---

### Pruebas  
Algo nuevo a saber, es que ahora en nuestro Sistema_directorios existe un nuevo directorio /bin donde guardaremos los archivos que el cliente nos ha pasado y tienen almenos un enlace, este seria nuestro directorio de persistencia del servicio. Esto considero que es correcto, debido a que asi desacoplamos el contenido de nuestro directorio de persistencia /bin, que funciona como un almacen de archivos pasados por el cliente, mientras que el directorio /home hace referencia al directorio "real" que tiene el cliente y donde el propio cliente hace sus operaciones. A diferencia que la prueba en local, no haciamos esta distinción, pero pienso que es importante a la hora de entender el servicio BlobService. 

Para comprobar que nuestro servicio funciona correctamente, hemos creado un programa cliente que realizará las llamadas a nuestro servicio. Para ello, en nuestro archivo .toml, hemos añadido lo siguiente para poder ejecutar tanto el cliente como el servidor, tal y como hacemos en el ejemplo de la calculadora de clase:

```toml
[project.scripts]
icedrive-blob = "icedrive_blob.app:main"
icedrive-blob-client = "icedrive_blob.test_app.command_line_handlers:client"
icedrive-blob-server = "icedrive_blob.test_app.command_line_handlers:server"
```

Realmente podriamos omitir el comando icedrive-blob, ya que para probar la implementación, usaremos tanto **icedrive-blob-client** y **icedrive-blob-server** respectivamente.

Como podemos deducir, las pruebas estan integradas dentro del cliente, qué sera un Ice.Aplication para poder usar el middleware.

``` python
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
```

Sabiendo los blob id's de los archivos que tenemos en nuestro directorio, el cliente hará un conjunto de pruebas, intentando abarca el mayor número de casos de uso y de causisticas posibles. para eso, sería bastante conveniente realizar cobertura de código.

Independientemente de lo útil que sería hacer cobertura de código, tengo que recalcar que el conjunto de pruebas escogido, como dije en el parrafo anterior, intenta abarcar la mayoría de casos de uso, con nuestras pruebas, realizamos llamadas a todas los métodos que proporciona nuestro BlobService de cara a que el cliente lo use (download, upload, link, unlink, read, close). También en "PRUEBA BONUS" se da la causistica de que al cliente se le olvida hacer el link al archivo que acaba de seguir, por lo que el recolector de basura actuará, borrando el archivo tanto del directorio de persistencia de nuestro servicio, como del directorio del cliente.

Para cada prueba de upload, el cliente deberia crear un data_transfer_prx de la misma manera que creamos nosotros como servicio los proxy, para eso, el propio cliente necesitar tener su propio adaptador de objetos para crear un proxy.


**NOTA**: antes de ejecutar el cliente, tendriamos que asegurarnos que el estado de los archivos sean los siguientes en el directorio Sistema_directorios/home, correspondiente al directorio del cliente/usuario:

- texto1.txt

    >Hola, este es un texto de prueba para la implementación del servicio blolbs

- texto2.txt

    > Esto es otro texto de prueba para el servicio blob, donde trabajaremos con un archivo un poco mas grande, pero sobre todo para tener al menos 2 documentos .txt en el directorio.

- texto3.txt

    > mondongo.txt xd

- texto4.txt

    > Texto de prueba 4.
    Añado mas texto, para ver como reacciona el programa.

(correspondería con la variable id_blob3_mod, mientras que id_blob3 sería quitando la segunda línea)
<br>

Teniendo claro esto, lo siguiente sería ejecutar tanto el cliente como el servidor con los comando generador por ``pip install -e .`` dentro del directorio raiz del repositorio.

Cuando ejecutas el servidor, se mostrará por pantalla el identificador del proxy, ese id, lo tendras que pasar como parametro al cliente para que pueda acceder al servicio.

```t
manuel@manuel-VivoBook-ASUSLaptop-X421EAY-K413EA:~/Desktop/Git/lab_ssdd$ icedrive-blob-server --Ice.Config=config/blob.config
INFO:root:Proxy: 6A5EE054-96CB-49D7-901A-8045DE735489 -t -e 1.1:tcp -h 192.168.0.24 -p 46863 -t 60000:tcp -h 172.20.0.1 -p 46863 -t 60000:tcp -h 172.17.0.1 -p 46863 -t 60000
```

En estos momentos, el servicio blob esta activo y a la espera de que un cliente acceda al servicio, llamando a los metodos correspondientes del BlobService.

```t
manuel@manuel-VivoBook-ASUSLaptop-X421EAY-K413EA:~/Desktop/Git/lab_ssdd/icedrive_blob$ icedrive-blob-client --Ice.Config=config/blob.config "6A5EE054-96CB-49D7-901A-8045DE735489 -t -e 1.1:tcp -h 192.168.0.24 -p 46863 -t 60000"
```
Como para nuestras pruebas el cliente necesitar crear proxys de DataTransfer, de la misma forma que nuestro servicio, hemos necesitado añadirle al comando el fichero de configuracion para su adaptador de objetos.

Para seguir un poco el hilo de la ejecución, en ambos roles, se mostrara algún tipo de feedback visual para saber principalmente, por la parte del servidor, con que blobid estamos trabajando y por parte del cliente, que está haciendo en este momento.

