import json
import uuid
from typing import Any, Dict, List

from IPython.display import HTML, display


class CustomDict(dict):
    _basic_umm_fields_: List = []
    _basic_meta_fields_: List = []

    def __init__(self, collection: Dict[str, Any], fields: List[str] = None):
        super().__init__(collection)
        self.uuid = str(uuid.uuid4())
        if fields is None:
            self.render_dict = self._filter_fields_(self._basic_umm_fields_)
        elif fields[0] == "*":
            self.render_dict = self
        else:
            self.render_dict = self._filter_fields_(fields)

    def _filter_fields_(self, fields: List[str]) -> Dict[str, Any]:

        filtered_dict = dict(
            (field, self["umm"][field]) for field in fields if field in self["umm"]
        )
        basic_dict = dict(
            (field, self["meta"][field])
            for field in self._basic_meta_fields_
            if field in self["meta"]
        )
        basic_dict.update(filtered_dict)
        return basic_dict

    def _filter_related_links(self, filter: str) -> List[str]:
        """
        Filter RelatedUrls from the UMM fields on CMR
        """
        matched_links: List = []
        for link in self["umm"]["RelatedUrls"]:
            if link["Type"] == filter:
                matched_links.append(link["URL"])
        return matched_links


class DataCollection(CustomDict):
    """
    Dictionary-like object to represent a data collection from CMR
    """

    _basic_meta_fields_ = [
        "concept-id",
        "granule-count",
        "provider-id",
    ]

    _basic_umm_fields_ = [
        "ShortName",
        "Abstract",
        "SpatialExtent",
        "TemporalExtents",
        "DataCenters",
        "RelatedUrls",
        "ArchiveAndDistributionInformation",
    ]

    def concept_id(self) -> str:
        return self["meta"]["concept-id"]

    def landing_page(self) -> str:
        links = self._filter_related_links("LANDING PAGE")
        return links[0]

    def __repr__(self) -> str:
        return json.dumps(
            self.render_dict, sort_keys=False, indent=2, separators=(",", ": ")
        )

    def _ipython_display_(self) -> None:
        display(
            HTML(
                '<div id="{}" style="height: auto; width:100%;"></div>'.format(
                    self.uuid
                )
            )
        )
        display(
            HTML(
                """<script>
        require(["https://rawgit.com/caldwell/renderjson/master/renderjson.js"], function() {
          renderjson.set_show_to_level(1)
          document.getElementById('%s').appendChild(renderjson(%s))
        });</script>
        """
                % (self.uuid, json.dumps(self.render_dict))
            )
        )


class DataGranule(CustomDict):
    """
    Dictionary-like object to represent a granule from CMR
    """

    _basic_meta_fields_ = [
        "concept-id",
        "provider-id",
    ]

    _basic_umm_fields_ = [
        "GranuleUR",
        "SpatialExtent",
        "TemporalExtent",
        "RelatedUrls",
        "DataGranule",
    ]

    def __repr__(self) -> str:
        """
        returns a basic representation of a data granule
        """
        data_links = [link for link in self.data_links()]
        rep_str = f"""
        Collection: {self['umm']['CollectionReference']}
        Spatial coverage: {self['umm']['SpatialExtent']}
        Temporal coverage: {self['umm']['TemporalExtent']}
        Size(MB): {self.size()}
        Data: {data_links}\n\n
        """.strip().replace(
            "  ", ""
        )
        return rep_str

    def _repr_html_(self) -> str:
        """
        Returns a rich representation for a data granule.
        """
        dataviz_img = "".join(
            [
                f'<img src="{link}" width="240px" />'
                for link in self.dataviz_links()[0:2]
            ]
        )
        data_links = "".join(
            [
                f'<a href="{link}" target="_blank">{link}</a><BR>'
                for link in self.data_links()
            ]
        )
        granule_str = f"""
        <p>
          <b>Collection</b>: {self['umm']['CollectionReference']}<BR>
          <b>Spatial coverage</b>: {self['umm']['SpatialExtent']}<BR>
          <b>Temporal coverage</b>: {self['umm']['TemporalExtent']}<BR>
          <b>Size(MB):</b> {self.size()} <BR>
          <b>Data</b>: {data_links}<BR>
          <span>{dataviz_img}</span>
        </p>
        """
        return granule_str

    def size(self) -> float:
        """
        returns the total size for the granule in MB
        """
        total_size = sum(
            [
                float(s["Size"])
                for s in self["umm"]["DataGranule"]["ArchiveAndDistributionInformation"]
            ]
        )
        return total_size

    def data_links(self, only_s3: bool = False) -> List[str]:
        links = self._filter_related_links("GET DATA")
        s3_links = [link for link in links if link.startswith("s3")]
        if only_s3 is True:
            return s3_links
        return links

    def dataviz_links(self) -> List[str]:
        links = self._filter_related_links("GET RELATED VISUALIZATION")
        return links
