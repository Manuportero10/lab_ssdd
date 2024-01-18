"""Servant implementation for the delayed response mechanism."""

import threading
import Ice

import IceDrive


class BlobQueryResponse(IceDrive.BlobQueryResponse):
    """Query response receiver."""

    def __init__(self, future: Ice.Future):
        self.future = future
        self.thread = threading.Timer(5.0, self.timeout)
        self.thread.start()

    def timeout (self) -> None:
        """Remove an object from the adapter if exists."""
        self.future.set_exception(IceDrive.UnknownBlob())

    def downloadBlob(self, blob: IceDrive.DataTransferPrx, current: Ice.Current = None) -> None:
        """Receive a `DataTransfer` when other service instance knows the `blob_id`."""
        #Paramos el timer
        self.thread = None
        self.future.set_result(blob)
         

    def blobExists(self, current: Ice.Current = None) -> None:
        """Indicate that `blob_id` was recognised by other service instance and exists."""


    def blobLinked(self, current: Ice.Current = None) -> None:
        """Indicate that `blob_id` was recognised by other service instance and was linked."""

    def blobUnlinked(self, current: Ice.Current = None) -> None:
        """Indicate that `blob_id` was recognised by other service instance and was unlinked."""

class BlobQuery(IceDrive.BlobQuery):
    """Query receiver."""

    def __init__(self, discovery: IceDrive.Discovery):
        self.discovery = discovery
        
    def downloadBlob(self, blobId: str, response: IceDrive.BlobQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a query for downloading an archive based on `blob_id`."""
        try:
            print("===========[DOWNLOAD] : Query received for delayed response===========\n")
        except IceDrive.UnknownBlob:
            pass
    
                 
    def blobIdExists(self, blobId: str, response: IceDrive.BlobQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a response that `blob_id` exists."""
        print("=========[BLOBIDEXISTS]: Query received for delayed response ========\n")

    def linkBlob(self, blobId: str, response: IceDrive.BlobQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a query to create a link for `blob_id` archive if it exists."""
        print("=========[LINK]: Query received for delayed response ========\n")

    def unlinkBlob(self, blobId: str, response: IceDrive.BlobQueryResponsePrx, current: Ice.Current = None) -> None:
        """Receive a query to destroy a link for `blob_id` archive if it exists."""
        print("=========[UNLINK]: Query received for delayed response ========\n")