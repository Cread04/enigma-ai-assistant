from langchain_core.tools import tool
from datetime import datetime
import locale


try:
    locale.setlocale(locale.LC_TIME, 'sv_SE')
except:
    pass

@tool
def get_current_time():
    """
    Hämtar aktuell tid och datum just nu.
    """
    now = datetime.now()
    
    return now.strftime("%A, %d %B %Y, klockan %H:%M")