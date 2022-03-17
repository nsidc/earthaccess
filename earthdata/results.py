import json
import uuid
from typing import Any, Dict, List

from benedict import benedict

from .formatters import _repr_granule_html


class CustomDict(benedict):
    _basic_umm_fields_: List = []
    _basic_meta_fields_: List = []

    def __init__(
        self,
        collection: Dict[str, Any],
        fields: List[str] = None,
        cloud_hosted: bool = False,
    ):
        super().__init__(collection)
        self.cloud_hosted = cloud_hosted
        self.uuid = str(uuid.uuid4())

        self.render_dict: Any
        if fields is None:
            self.render_dict = self
        elif fields[0] == "basic":
            self.render_dict = self._filter_fields_(self._basic_umm_fields_)
        else:
            self.render_dict = self._filter_fields_(fields)

    def _filter_fields_(self, fields: List[str]) -> Dict[str, Any]:
        filtered_dict = {
            "umm": dict(
                (field, self["umm"][field]) for field in fields if field in self["umm"]
            )
        }
        basic_dict = {
            "meta": dict(
                (field, self["meta"][field])
                for field in self._basic_meta_fields_
                if field in self["meta"]
            )
        }
        basic_dict.update(filtered_dict)
        return basic_dict

    def _filter_related_links(self, filter: str) -> List[str]:
        """
        Filter RelatedUrls from the UMM fields on CMR
        """
        matched_links: List = []
        if "RelatedUrls" in self["umm"]:
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
        "DirectDistributionInformation",
    ]

    def summary(self) -> Dict[str, Any]:
        # we can print only the concept-id

        summary_dict: Dict[str, Any]
        summary_dict = {
            "short-name": self.get_umm("ShortName"),
            "concept-id": self.concept_id(),
            "version": self.version(),
            "file-type": self.data_type(),
            "get-data": self.get_data(),
        }
        if "Region" in self.s3_bucket():
            summary_dict["cloud-info"] = self.s3_bucket()
        return summary_dict

    def get_umm(self, umm_field: str) -> str:
        if umm_field in self["umm"]:
            return self["umm"][umm_field]
        return ""

    def concept_id(self) -> str:
        return self["meta"]["concept-id"]

    def data_type(self) -> str:
        if "ArchiveAndDistributionInformation" in self["umm"]:
            return str(
                self["umm"]["ArchiveAndDistributionInformation"][
                    "FileDistributionInformation"
                ]
            )
        return ""

    def version(self) -> str:
        if "Version" in self["umm"]:
            return self["umm"]["Version"]
        return ""

    def abstract(self) -> str:
        return self["umm"]["Abstract"]

    def landing_page(self) -> str:
        links = self._filter_related_links("LANDING PAGE")
        if len(links) > 0:
            return links[0]
        return ""

    def get_data(self) -> List[str]:
        links = self._filter_related_links("GET DATA")
        return links

    def s3_bucket(self) -> Dict[str, Any]:
        if "DirectDistributionInformation" in self["umm"]:
            return self["umm"]["DirectDistributionInformation"]
        return {}

    def __repr__(self) -> str:
        return json.dumps(
            self.render_dict, sort_keys=False, indent=2, separators=(",", ": ")
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

    def __init__(
        self,
        collection: Dict[str, Any],
        fields: List[str] = None,
        cloud_hosted: bool = False,
    ):
        super().__init__(collection)
        self.cloud_hosted = cloud_hosted
        # TODO: maybe add area, start date and all that as an instance value
        self["size"] = self.size()
        self.uuid = str(uuid.uuid4())
        self.render_dict: Any
        if fields is None:
            self.render_dict = self
        elif fields[0] == "basic":
            self.render_dict = self._filter_fields_(self._basic_umm_fields_)
        else:
            self.render_dict = self._filter_fields_(fields)

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
        granule_html_repr = _repr_granule_html(self)
        return granule_html_repr

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

    def _derive_s3_link(self, links: List[str]) -> List[str]:
        s3_links = []
        for link in links:
            if link.startswith("s3"):
                s3_links.append(link)
            elif link.startswith("https://") and (
                "cumulus" in link or "protected" in link
            ):
                s3_links.append(f's3://{links[0].split("nasa.gov/")[1]}')
        return s3_links

    def data_links(self, s3_only: bool = False) -> List[str]:
        links = self._filter_related_links("GET DATA")
        s3_links = self._filter_related_links("GET DATA VIA DIRECT ACCESS")
        if self.cloud_hosted and s3_only:
            if len(s3_links) == 0 and len(links) > 0:
                return self._derive_s3_link(links)
            else:
                return s3_links
        links.extend(s3_links)
        return links

    def dataviz_links(self) -> List[str]:
        links = self._filter_related_links("GET RELATED VISUALIZATION")
        return links
