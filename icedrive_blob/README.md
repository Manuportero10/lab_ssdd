# IceDrive Blob service


**Autor**: Manuel Cano García
**Correo**: Manuel.Cano3@alu.uclm.es

---

## Paso 1: implementación en local

Para comprobar el funcionamiento de mi servicio blob de forma local (Sin usar el middleware), he visto necesario crear un pequeño distema de directorios, donde la carpeta **Sistema_directorios** representaría el directorio raíz.
El directorio **home** guardaría los blobs correspondientes.
Como para este servicio se necesita persistencia, hemos visto necesario tener 2 archivos donde guardaremos la siguiente información en el directorio **tmp**

- historial_rutas.txt : guardaremos un diccionario donde la **clave** será la ruta de los archivos blob y el valor correspondiente será el identificador de ese blolb.

    > Sistema_directorios/home/texto1.txt d2626beab49bc9a63fe5507c3f7b855f79a1d6623eb937f02d6a31397bdfdf10
    Sistema_directorios/home/texto2.txt c06b6e74e0eb82cdbe517aa62896361baffb282602bbf2a338dc9475652144ac
    Sistema_directorios/home/texto3.txt ac1e9040b291a72aa1e818526432100391faea53ed6c33906002849d84f9fbac

    Ejemplo del contenido del archivo de persistencia.

<br>

- historial_blob.txt: guardaremos un diccionario donde la **clave** será el indentificador del blob y el valor el número de enlaces asociados a ese archivo.

    > d2626beab49bc9a63fe5507c3f7b855f79a1d6623eb937f02d6a31397bdfdf10 10
    c06b6e74e0eb82cdbe517aa62896361baffb282602bbf2a338dc9475652144ac 10
    ac1e9040b291a72aa1e818526432100391faea53ed6c33906002849d84f9fbac 1

    Ejemplo del contenido del archivo de persistencia.

Para realizar las pruebas correspondiente al código, he creado varios scripts, llamadaos test.sh donde realizaremos los test unitarios que estan dentro del directorio **Test**, antes de ejecutar el test/s es recomendable especificar de primera mano que test vas a querrer ejecutar antes de ejecutar propiamente el test, para esto simplemente podriamos poner el prefijo non_ para indicar al test que no ejecute este test.

```
def non_test_caso1() -> None: //el test NO lo ejecutará
def test_caso2() -> None: // el test SI lo ejecutará
```
<br>

Tambíen he creado el script coverage.sh para saber la cobertura del código, al ejecutar este comando, la cobertura se quedará almacenada en una carpeta llamada htmlcov, donde se habrá generado automaticamente una página donde puedes mirar la cobertura de código. En el archivo index.html teneis el índice para buscar los archivos .py que quieras ver la cobertura.

Si quieres ver la cobertura de un caso de uso completo, donde el test de prueba, el supuesto cliente ha llamado a todas las funciones de la interfaz propuesta, correspondería con la funcion ```test_caso2()``` del archivo ```test_blob.py```, se quedará almacenado en la carpeta **cobertura_caso2**.

**NOTA**: para poder usar estos scripts os teneis que situar en la carpeta icedrive_blob.

<br>

Para índagar mas en la implementación, visite los archivos blob.py para ver la implementación del servicio, GargabeCollector.py para comprobar la recoleción de basura implementada para el servicio y Test/test_blob.py para ver los test utilizados para comprobar la correcta implementación del servicio.