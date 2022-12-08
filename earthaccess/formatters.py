from typing import Any, List
from uuid import uuid4

import pkg_resources

STATIC_FILES = ["css/iso_bootstrap4.0.0min.css", "css/styles.css"]


def _load_static_files() -> List[str]:
    """Load styles"""
    return [
        pkg_resources.resource_string("earthaccess", fname).decode("utf8")
        for fname in STATIC_FILES
    ]


def _repr_collection_html() -> str:
    return "<div></div>"


def _repr_granule_html(granule: Any) -> str:
    css_styles = _load_static_files()
    css_inline = f"""<div id="{uuid4()}" style="height: 0px; display: none">
            {''.join([f"<style>{style}</style>" for style in css_styles])}
            </div>"""
    style = "max-height: 140px;"
    dataviz_img = "".join(
        [
            f'<a href="{link}"><img style="{style}" src="{link}" alt="Data Preview"/></a>'
            for link in granule.dataviz_links()[0:2]
            if link.startswith("http")
        ]
    )
    data_links = "".join(
        [
            f'<a href="{link}" target="_blank" class="btn btn-secondary btn-sm">{link}</a>'
            for link in granule.data_links()
        ]
    )
    granule_size = round(granule.size(), 2)
    # TODO: probably this needs to be integrated on a list data structure
    granule_str = f"""
    {css_inline}
    <div class="bootstrap">
      <div class="container-fluid border">
        <div class="row border">
          <div class="col-6">
            <p><b>Data</b>: {data_links}<p/>
            <p><b>Size</b>: {granule_size} MB</p>
            <p><b>Spatial</b>: <span>{granule["umm.SpatialExtent"]}</span></p>
          </div>
          <div class="col-2 offset-sm-3 pull-right">
            {dataviz_img}
          </div>
        </div>
      </div>
    </div>
    """
    return granule_str
