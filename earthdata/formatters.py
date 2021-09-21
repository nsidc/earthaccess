from functools import lru_cache
from html import escape
from typing import Any, List

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
    style = ""
    dataviz_img = "".join(
        [
            f'<img style="{style}" class="pure-img pure-u-1-2" src="{link}" alt="Data Preview"/>'
            for link in granule.dataviz_links()[0:2]
        ]
    )
    data_links = "".join(
        [
            f'<button class="pure-button-sm"><a href="{link}" target="_blank">link</a></button>'
            for link in granule.data_links()
        ]
    )
    # TODO: probably this needs to be integrated on a list data structure
    granule_str = f"""
      <div class="pure-g">
          <div class="pure-u-2-3">
            <p>Data: {data_links}<p/>
          </div>
          <div class="pure-u-1-3">
            {dataviz_img}
          </div>
      </div>
    """
    return granule_str
