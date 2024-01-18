# IceDrive Blob service


**Autor**: Manuel Cano García

**Correo**: Manuel.Cano3@alu.uclm.es

---

## Entrega 2: IceStorm

En esta segunda entrega, tendremos que comunicarnos con otros servicios gracias al descubrimiento de servicio al mismo tiempo que nuestro servicio aplica la resolución diferida cuando no tengamos lo necesario para poder ejecutar los metodos de nuestro servicio, en ese caso se lo pediremos a otro y nosotros actuaremos como intermediarios.

### Descubrimiento de servicios

Para que funcione el descubrimiento de servicios, es necesario tener 2 cosas:

- Un **publisher** del topico correspondiente (en nuestro caso seria el topico discover):

```python
    properties = self.communicator().getProperties()
    topic_name = properties.getProperty("Discovery.Topic")
    topic_manager = IceStorm.TopicManagerPrx.checkedCast(
        self.communicator().propertyToProxy("IceStorm.Proxy")
    )

    try:
        topic = topic_manager.retrieve(topic_name)
    except IceStorm.NoSuchTopic:
        topic = topic_manager.create(topic_name)
```

- Una instancia de la clase Discovery que esté suscrita al topico discovery

```python
    discovery_servant = Discovery() #sirviente del servicio de descubrimiento receptor
    discovery = adapter.addWithUUID(discovery_servant)
    discovery_proxy = IceDrive.DiscoveryPrx.checkedCast(discovery) # Creamos el proxy del servicio de descubrimiento
        
    topic.subscribeAndGetPublisher({},discovery_proxy) # es el que recibe los anuncios de los otros servicios

```

Una vez entendido esto, pasaremos a la especificación de la clase **Discovery**, pero para adelantarnos, la función que tendra los metodos de esta clase es ir almacenando los servicios que se van anunciando con el topic.

```python
    class Discovery(IceDrive.Discovery):
    """Servants class for service discovery."""

    def __init__(self) -> None:
        self.lista_authentications = []
        self.lista_directories = []
        self.lista_blobs = []

    def announceAuthentication(self, prx: IceDrive.AuthenticationPrx, current: Ice.Current = None) -> None:
        """Receive an Authentication service announcement."""
        if prx not in self.lista_authentications: # Controlamos la redundancia de anuncios
            print("\n[AUTHENTICATION]: Anuncio recibido ", prx)
            self.lista_authentications.append(prx)

    def announceDirectoryService(self, prx: IceDrive.DirectoryServicePrx, current: Ice.Current = None) -> None:
        """Receive an Directory service announcement."""
        if prx not in self.lista_directories: # Controlamos la redundancia de anuncios
            print("\n[DIRECTORY]: Anuncio recibido ", prx)
            self.lista_directories.append(prx)

    def announceBlobService(self, prx: IceDrive.BlobServicePrx, current: Ice.Current = None) -> None:
        """Receive an Blob service announcement."""
        if prx not in self.lista_blobs: # Controlamos la redundancia de anuncios
            print("\n[BLOB]: Anuncio recibido ", prx)
            self.lista_blobs.append(prx)

    def get_BlobService(self) -> IceDrive.BlobServicePrx:
        return self.lista_blobs[0]
    
    def get_Authentication(self) -> IceDrive.AuthenticationPrx:
        return self.lista_authentications[0]
    
    def get_Directory(self) -> IceDrive.DirectoryServicePrx :
        return self.lista_directories[0]
```

También tenemos métodos auxiliares que nos serviran para ir rescatando los servicios que hemos descubierto, esto lo veremos mas adelante a la hora de explicar las modificaciones de los metodos **upload** y **download**

Sabremos que hemos hecho el descubrimiento de servicios bien, cuando nosotros estemos recibiendo los servicios que se anuncian y viceversa. Para ver si nos anunciamos bien lo podemos ver con el comando ```tail -f nohup.out | less``` para ver las últimas entradas del log.

### Modificaciones

Al tener ahora un objeto user, lo primero que tenemos que comprobar es si esta activo con la función verifyUser de un servicio Authentication que recibamos. Esto pasa tanto para el método **upload** como en el **download**

```python
    # lo primero: vamos a comprobar si el usuario esta activo
    prx_auth = self.query_discovery.get_Authentication()

    if prx_auth.verifyUser(user):
        # ejecucion del codigo normal
    else:
        print("[ERROR] El usuario no esta autorizado \n")
        raise IceDrive.Unauthorized() 
```
---

### Pruebas  

Para probar nuestro servicio, lo primero que tenemos que hacer es arrancarlo, para esto ejecutamos el comando **icedrive-blob-server** pasandle el archivo de configuración:

> Teniendo claro esto, lo siguiente sería ejecutar el servidor con los comando generador por ``pip install -e .`` dentro del directorio raiz del repositorio.

Para seguir un poco el hilo de la ejecución, en nuestro servicio, se mostrará algún tipo de feedback visual para saber principalmente, por la parte del servidor, con que blobid estamos trabajando y por parte del cliente, que está haciendo en este momento...

También necesitaremos tener la máquina virtual encendida, haciendo el setup estandar de iniciar icedrive con ./run_icedrive dentro de /opt/icedrive y posteriormente ejecutar el cliente con ./run_client.

Es importante recalcar la necesidad de cambiar las ip's conforme a tu conexión, ya que puede dar problemas de conexión si no se toman estas medidas tanto para los archivos de configuración de nuestro servicio como los del cliente.








