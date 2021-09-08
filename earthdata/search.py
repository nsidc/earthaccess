from cmr import CollectionQuery, GranuleQuery
from IPython.core.display import HTML
from IPython.display import display
from requests import exceptions


class DataCollections(CollectionQuery):
    def cloud_hosted(self, cloud_hosted=True):
        """
        Only match granules that are hosted in the cloud.
        :param cloud_only: True to require granules only be online
        :returns: Query instance
        """

        if not isinstance(cloud_hosted, bool):
            raise TypeError("Online_only must be of type bool")

        self.params["cloud_hosted"] = cloud_hosted
        return self


class DataGranule(object):
    def __init__(self, granule):
        self._data = granule

    def _filter_related_links(self, filter: str):
        """
        Filter RelatedUrls from the UMM fields on CMR
        """
        matched_links = []
        for link in self._data["umm"]["RelatedUrls"]:
            if link["Type"] == filter:
                matched_links.append(link["URL"])
        return matched_links

    def __repr__(self):
        data_links = [link for link in self.data_links()]
        rep_str = f"""
        Collection: {self._data['umm']['CollectionReference']}
        Spatial coverage: {self._data['umm']['SpatialExtent']}
        Temporal coverage: {self._data['umm']['TemporalExtent']}
        Size(MB): {self.size()}
        Data: {data_links}\n\n
        """.strip().replace(
            "  ", ""
        )
        return rep_str

    def _repr_html_(self):
        dataviz_img = "".join(
            [
                f'<img src="{link}" width="340px" />'
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
          <b>Collection</b>: {self._data['umm']['CollectionReference']}<BR>
          <b>Spatial coverage</b>: {self._data['umm']['SpatialExtent']}<BR>
          <b>Temporal coverage</b>: {self._data['umm']['TemporalExtent']}<BR>
          <b>Size(MB):</b> {self.size()} <BR>
          <b>Data</b>: {data_links}<BR>
          <span>{dataviz_img}</span>
        </p>
        """
        return granule_str

    def size(self):
        total_size = sum(
            [
                float(s["Size"])
                for s in self._data["umm"]["DataGranule"][
                    "ArchiveAndDistributionInformation"
                ]
            ]
        )
        return total_size

    def data_links(self, only_s3=False):
        links = self._filter_related_links("GET DATA")
        s3_links = [link for link in links if link.startswith("s3")]
        if only_s3 is True:
            return s3_links
        return links

    def dataviz_links(self):
        links = self._filter_related_links("GET RELATED VISUALIZATION")
        return links


class DataGranules(GranuleQuery):

    _format = "umm_json"
    _valid_formats_regex = [
        "json",
        "xml",
        "echo10",
        "iso",
        "iso19115",
        "csv",
        "atom",
        "kml",
        "native",
        "umm_json",
    ]

    def _valid_state(self):

        # spatial params must be paired with a collection limiting parameter
        spatial_keys = ["point", "polygon", "bounding_box", "line"]
        collection_keys = ["short_name", "entry_title", "concept_id"]

        if any(key in self.params for key in spatial_keys):
            if not any(key in self.params for key in collection_keys):
                return False

        # all good then
        return True

    def get(self, limit=2000):
        """
        Get all results up to some limit, even if spanning multiple pages.
        :limit: The number of results to return
        :returns: query results as a list
        """

        page_size = min(limit, 2000)
        url = self._build_url()

        results = []
        page = 1
        while len(results) < limit:
            params = {"page_size": page_size, "page_num": page}
            if self._token is not None:
                params["token"] = self._token

            response = self.session.get(url, params=params)

            try:
                response.raise_for_status()
            except exceptions.HTTPError as ex:
                raise RuntimeError(ex.response.text)

            if self._format == "json":
                latest = response.json()["feed"]["entry"]
            elif self._format == "umm_json":
                latest = [DataGranule(granule) for granule in response.json()["items"]]
            else:
                latest = [response.text]

            if len(latest) == 0:
                break

            results.extend(latest)
            page += 1

        return results

    def download(self):
        return None
