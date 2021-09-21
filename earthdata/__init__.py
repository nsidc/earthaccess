from uuid import uuid4

from .accessor import Accessor
from .auth import Auth
from .formatters import _load_static_files
from .search import DataCollections, DataGranules

__all__ = ["DataGranules", "DataCollections", "Auth", "Accessor"]

try:
    from IPython.core.display import HTML, display

    css_styles = _load_static_files()
    display(
        HTML(
            f"""
            <div id="{uuid4()}" style="height: 0px; display: none">
            {''.join([f"<style>{style}</style>" for style in css_styles])}
            </div>
            """
        )
    )
except ImportError:
    print("IPython not available, using simple representation")
    pass
