import time
import Ice
import IceDrive

def garbage_collector(timer_file : int, blobid : str,ruta_links : str, blob : IceDrive.BlobService) -> None:
    time.sleep(timer_file)
    dicionary_id_nlinks = blob.recover_dictionary(ruta_links)
    
    if blobid in dicionary_id_nlinks and dicionary_id_nlinks[blobid] == "0": 
            blob.unlink(blobid)    