from functools import lru_cache
from html import escape
from typing import Any, List
from uuid import uuid4

import pkg_resources

STATIC_FILES = ["css/pure-min.css"]


@lru_cache(None)
def _load_static_files() -> List[str]:
    """Load styles"""
    return [
        pkg_resources.resource_string("earthdata", fname).decode("utf8")
        for fname in STATIC_FILES
    ]


def _repr_collection_html() -> str:
    return "<div></div>"


def _repr_granule_html(granule: Any) -> str:
    css_styles = _load_static_files()
    css_inline = f"""<div id="{uuid4()}" style="height: 0px; display: none">
            {''.join([f"<style>{style}</style>" for style in css_styles])}
            </div>"""
    style = "max-height: 120px;"
    class_img = "pure-img pure-u-1-2"
    dataviz_img = "".join(
        [
            f'<a href="{link}"><img style="{style}" class="{class_img}" src="{link}" alt="Data Preview"/></a>'
            for link in granule.dataviz_links()[0:2]
        ]
    )
    data_links = "".join(
        [
            f'<button class="pure-button-sm"><a href="{link}" target="_blank">link</a></button>'
            for link in granule.data_links()
        ]
    )
    granule_size = granule.size()
    # TODO: probably this needs to be integrated on a list data structure
    granule_str = f"""
      {css_inline}
      <div class="pure-g">
          <div class="pure-u-2-3">
            <p><b>Data</b>: {data_links}<p/>
            <p><b>Size</b>: {granule_size} MB</p>
            <p><b>Spatial</b>: <span class="pure-u sm">{granule["umm.SpatialExtent"]}</span></p>
          </div>
          <div class="pure-u-1-3">
            {dataviz_img}
          </div>
      </div>
    """
    return granule_str
