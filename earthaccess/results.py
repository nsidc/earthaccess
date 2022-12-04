import json
import uuid
from typing import Any, Dict, List, Optional, Union

from benedict import benedict

from .formatters import _repr_granule_html


class CustomDict(benedict):
    _basic_umm_fields_: List = []
    _basic_meta_fields_: List = []

    def __init__(
        self,
        collection: Dict[str, Any],
        fields: Optional[List[str]] = None,
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
        """Summary containing short_name, concept-id, file-type, and cloud-info if the dataset is cloud hosted.

        Returns:
            Returns a sumary of the collection metadata
        """
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

    def get_umm(self, umm_field: str) -> Union[str, Dict[str, Any]]:
        """
        Parameters:
            umm_field: Valid UMM item, i.e. `TemporalExtent`
        Returns:
            Returns the value of a given field inside the UMM (Unified Metadata Model)
        """
        if umm_field in self["umm"]:
            return self["umm"][umm_field]
        return ""

    def concept_id(self) -> str:
        """
        Returns:
          Retrurns a collection's `concept_id`, this id is the most relevant search field on granule queries.
        """
        return self["meta"]["concept-id"]

    def data_type(self) -> str:
        """
        Returns:
            If available, it returns the collection data type, i.e. HDF5, CSV etc
        """
        if "ArchiveAndDistributionInformation" in self["umm"]:
            return str(
                self["umm"]["ArchiveAndDistributionInformation"][
                    "FileDistributionInformation"
                ]
            )
        return ""

    def version(self) -> str:
        """
        Returns:
            returns the collection's version.
        """
        if "Version" in self["umm"]:
            return self["umm"]["Version"]
        return ""

    def abstract(self) -> str:
        """
        Returns:
            Returns the abstract of a collection
        """
        if "Abstract" in self["umm"]:
            return self["umm"]["Abstract"]
        return ""

    def landing_page(self) -> str:
        """
        Returns:
            if available it returns the first landing page for the collection, can be many.
        """
        links = self._filter_related_links("LANDING PAGE")
        if len(links) > 0:
            return links[0]
        return ""

    def get_data(self) -> List[str]:
        """
        Returns:
            Returns the GET DATA links, usually a link to a landing page, a DAAC portal or an FTP location.
        """
        links = self._filter_related_links("GET DATA")
        return links

    def s3_bucket(self) -> Dict[str, Any]:
        """
        Returns:
            Returns the S3 bucket information if the collection has it (**cloud hosted collections only**)
        """
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
        fields: Optional[List[str]] = None,
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
        Returns:
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
        Returns:
            Returns a rich representation for a data granule if we are in a Jupyter notebook.
        """
        granule_html_repr = _repr_granule_html(self)
        return granule_html_repr

    def size(self) -> float:
        """
        Returns:
            Returns the total size for the granule in MB
        """
        try:
            total_size = sum(
                [
                    float(s["Size"])
                    for s in self["umm.DataGranule.ArchiveAndDistributionInformation"]
                    if "ArchiveAndDistributionInformation" in self["umm"]["DataGranule"]
                ]
            )
        except Exception:
            total_size = 0
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

    def data_links(
        self, access: Optional[str] = None, in_region: bool = False
    ) -> List[str]:
        """Returns the data links form a granule

        Parameters:
            access: direct or external, direct means in-region access for cloud hosted collections.
            in_region: if we are running in us-west-2, meant for the store class, default is False
        Returns:
            the data link for the requested access type
        """
        https_links = self._filter_related_links("GET DATA")
        s3_links = self._filter_related_links("GET DATA VIA DIRECT ACCESS")
        if in_region:
            # we are in us-west-2
            if self.cloud_hosted and access is None:
                # this is a cloud collection and we didn't specify the access type
                # default to S3 links
                if len(s3_links) == 0 and len(https_links) > 0:
                    # This is guessing the S3 links for some cloud collections that for
                    # some reason only offered HTTPS links
                    return self._derive_s3_link(https_links)
                else:
                    # we have the s3 links so we return those
                    return s3_links
            else:
                # Even though we are in us-west-2 the user wants the HTTPS links
                # used in region they are S3 signed links from TEA
                # https://github.com/asfadmin/thin-egress-app
                return https_links
        else:
            # we are not in region
            if access == "direct":
                # maybe the user wants to collect S3 links ans use them later
                # from the cloud
                return s3_links
            else:
                # we are not in us-west-2, even cloud collections have HTTPS links
                return https_links
        return https_links

    def dataviz_links(self) -> List[str]:
        """
        Returns:
            Returns the data visualization links, usually the browse images.
        """
        links = self._filter_related_links("GET RELATED VISUALIZATION")
        return links
