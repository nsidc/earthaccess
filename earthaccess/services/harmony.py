# import earthaccess as ea
#
# ea.login()
#
# results = ea.search_data(**params)
# job_id = ea.services.harmony.request(results, **kwargs) # internally the API will use only the concept-id and pass the kwargs
# status= ea.services.harmony.status(job_id)
#
# if status is "COMPLETED": # or an enum of it
#     files  = ea.services.harmony.results(job_id)
#
# ds = xr.open_mfdataset(files)
from enum import Enum


def request(results: list[dict], **kwargs) -> str:
    """

    Args:
        results: Results from an earthaccess search
        **kwargs: Stuff to give to harmony

    returns:
        the harmony job_id for your request
    """
    pass

# TODO: Define enum for possible statuses
HyP3 = ['PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED']
Harmony = ['failed', 'cancelled', 'paused']
def status(job_id) -> Enum['']:
    pass
