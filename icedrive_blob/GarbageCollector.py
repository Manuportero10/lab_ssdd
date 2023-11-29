import time
import blob

def garbage_collector(timer_file : int, blobid : str) -> None:
    time.sleep(timer_file)
    dicionary_id_nlinks = blob.BlobService().recover_dictionary_links()
    
    if blobid in dicionary_id_nlinks and dicionary_id_nlinks[blobid] == "0":
            blob.BlobService().unlink(blobid)    