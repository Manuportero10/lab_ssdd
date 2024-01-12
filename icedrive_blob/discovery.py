"""Servant implementations for service discovery."""

import Ice

import IceDrive
import IceStorm


class Discovery(IceDrive.Discovery):
    """Servants class for service discovery."""

    def __init__(self) -> None:
        self.lista_authentications = []
        self.lista_directories = []
        self.lista_blobs = []
        

    def announceAuthentication(self, prx: IceDrive.AuthenticationPrx, current: Ice.Current = None) -> None:
        """Receive an Authentication service announcement."""
        if prx not in self.lista_authentications: # Controlamos la redundancia de anuncios
            print("\n[AUTHENTICATION]: Anuncio recivido ", prx)
            self.lista_authentications.append(prx)

    def announceDirectoryService(self, prx: IceDrive.DirectoryServicePrx, current: Ice.Current = None) -> None:
        """Receive an Directory service announcement."""
        if prx not in self.lista_directories: # Controlamos la redundancia de anuncios
            print("\n[DIRECTORY]: Anuncio recivido ", prx)
            self.lista_directories.append(prx)

    def announceBlobService(self, prx: IceDrive.BlobServicePrx, current: Ice.Current = None) -> None:
        """Receive an Blob service announcement."""
        if prx not in self.lista_blobs: # Controlamos la redundancia de anuncios
            print("\n[BLOB]: Anuncio recivido ", prx)
            self.lista_blobs.append(prx)

    def get_BlobService(self) -> IceDrive.BlobServicePrx:
        return self.lista_blobs[0]
    
    def get_Authentication(self) -> IceDrive.AuthenticationPrx:
        return self.lista_authentications[0]
    
    def get_Directory(self) -> IceDrive.DirectoryServicePrx :
        return self.lista_directories[0]

