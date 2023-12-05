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
            fichero = self.find_file(blob_id,self.ruta_archivos) # encontremos el fichero en el directorio donde se almacenan los blobs
        except IceDrive.UnknownBlob: # basicamente el archivo no existe, no esta en el directorio
            print("[ERROR] El archivo no existe con [ID=" + blob_id + "] no existe\n")
            raise IceDrive.UnknownBlob(blob_id)
                
        full_path = os.path.join(self.ruta_archivos, fichero)

        servant = DataTransfer(full_path)
        prx = current.adapter.addWithUUID(servant)
        data_transfer_prx = IceDrive.DataTransferPrx.uncheckedCast(prx)   

        return data_transfer_prx 
```

Lo primero a realizar, sería encontrar el archivo dentro de donde guarde el usuario sus archivos, para saber si realmente el blob_id que le pasamos corresponde con un archivo real, una vez encontrado el archivo, lo concatenamos con su ruta y creamos un objeto **DataTransfer** con el archivo obtenido, gracias a que en el constructor le hemos pasado el archivo, el objeto DataTransfer ya tiene el descriptor del archivo, así que cuando haga las llamadas ```read()``` correspondientes, leerá el contenido del archivo en cuestión.
<br>

 - **upload**

 ```python
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
            file_name = blobid + ".txt"
            # añadimos el contenido del archivo en blobid.txt - lo creamos en nuestra persistencia
            full_path = os.path.join(self.ruta_persistencia, file_name)
            with open(full_path, "w") as file:
                file.write(content)
            
            self.update_dictionary_paths(blobid, file_name) # actualizamos el diccionario de rutas

            # Lanzamos un hilo, a modo de temporizador del archivo, para que se elimine si no se ha enlazado
            timer_file = 10
            hilo = threading.Thread(target=garbage_collector, args=(timer_file,blobid,self.ruta_diccionario_id_nlinks,self,)) 
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
```

Sabiendo los blob id's de los archivos que tenemos en nuestro directorio, el cliente hará un conjunto de pruebas, intentando abarca el mayor número de casos de uso y de causisticas posibles. para eso, sería bastante conveniente realizar cobertura de código, pero hasta la fecha desconozco como hacerlo para el cliente, ya que en local si lo hacia porque llamaba directamente al archivo test_blob.py para realizar la cobertura, ahora como lo que ejecutamos es un comando generado por el archivo .toml y le pasamos como argumento el proxy del servicio blob, desconozco cómo hacerlo (está en proceso saberlo).

Independientemente de lo útil que sería hacer cobertura de código, tengo que recalcar que el conjunto de pruebas escogido, como dije en el parrafo anterior, intenta abarcar la mayoría de casos de uso, con nuestras pruebas, realizamos llamadas a todas los métodos que proporciona nuestro BlobService de cara a que el cliente lo use (download, upload, link, unlink, read, close) y en las "PRUEBAS PARA texto4.txt" se da el caso de que el blobid no existe en el directorio del cliente, por lo que retornaría una excepción. También en "PRUEBAS PARA texto1.txt" se da la causistica de que al cliente se le olvida hacer el link al archivo que acaba de seguir, por lo que el recolector de basura actuará, borrando el archivo tanto del directorio de persistencia de nuestro servicio, como del directorio del cliente.

Para cada prueba, creamos un data_transfer_prx independiente para cada prueba, debido a que daría errores, si previamente hemos usado el proxy para leer, (por ejemplo para descargar el contenido de un archivo) a la hora de pasar el mismo objeto proxy al metodo upload, hace que como ya ha leido el archivo, a la hora de volver a leer el archivo, no genera error, sino que se generaría un blobid erroneo.


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
manuel@manuel-VivoBook-ASUSLaptop-X421EAY-K413EA:~/Desktop/Git/lab_ssdd/icedrive_blob$ icedrive-blob-client "6A5EE054-96CB-49D7-901A-8045DE735489 -t -e 1.1:tcp -h 192.168.0.24 -p 46863 -t 60000"
```

Para seguir un poco el hilo de la ejecución, en ambos roles, se mostrara algún tipo de feedback visual para saber principalmente, por la parte del servidor, con que blobid estamos trabajando y por parte del cliente, que está haciendo en este momento.

