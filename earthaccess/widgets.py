import re
from typing import Any, Dict, List, Tuple, Union

import geopandas
import ipyleaflet
import ipywidgets
import pandas
import shapely

from .results import DataGranule

# geopandas.options.io_engine = "pyogrio"


class SearchWidget:
    def __init__(
        self, params: Dict[str, Any] = {}, projection: str = "global", map: Any = None
    ):
        self.current_geometry = None
        self.active_layers: Any = []
        self.roi: Any = []
        self.overview = None
        self.map = map
        self.default_fields = [
            "size",
            "concept_id",
            "dataset-id",
            "native-id",
            "provider-id",
            "_related_urls",
            "_beginning_date_time",
            "_ending_date_time",
            "geometry",
        ]
        self.html = ipywidgets.HTML(
            """
          <h4>File Info</h4>
          Hover over a file footprint
        """
        )
        self.html.layout.margin = "0px 20px 20px 20px"

        self._build_widget(params, projection)

    def _build_widget(
        self, params: Dict[str, Any] = {}, projection: str = "global"
    ) -> None:
        self.map_projection = projection
        self.search_params = params

        if "polygon" not in self.search_params:
            self.search_params["polygon"] = ""
        self.dc = ipyleaflet.DrawControl(
            marker={"shapeOptions": {"color": "#0000FF"}},
            circlemarker={},
            rectangle={"shapeOptions": {"color": "#0000FF"}},
        )
        self.dc.on_draw(self._handle_draw)
        proj_dict = {
            "global": {
                "basemap": ipyleaflet.basemaps.Esri.WorldImagery,
                "crs": ipyleaflet.projections.EPSG3857,
                "map_center": [0, 0],
            },
            "south": {
                "basemap": ipyleaflet.basemaps.NASAGIBS.BlueMarble3031,
                "crs": ipyleaflet.projections.EPSG3031.NASAGIBS,
                "map_center": [-90, 0],
            },
            "north": {
                "basemap": ipyleaflet.basemaps.NASAGIBS.BlueMarble3413,
                "crs": ipyleaflet.projections.EPSG3413.NASAGIBS,
                "map_center": [90, 0],
            },
        }
        if self.map is None:
            self.m = ipyleaflet.Map(
                center=proj_dict[self.map_projection]["map_center"],
                zoom=3,
                prefer_canvas=True,
                basemap=proj_dict[self.map_projection]["basemap"],
                crs=proj_dict[self.map_projection]["crs"],
            )
        else:
            self.m = self.map
            self.m.clear_controls()
            self.m.add(ipyleaflet.ZoomControl())

        self.m.add(ipyleaflet.LayersControl())
        self.m.add(ipyleaflet.FullScreenControl())
        self.m.add_control(
            ipyleaflet.MeasureControl(
                position="topleft",
                active_color="orange",
                primary_length_unit="kilometers",
            )
        )
        self.m.layout.height = "600px"

        self.m.add(self.dc)

        return None

    def _flattent_column_names(self, df: pandas.DataFrame) -> pandas.DataFrame:
        df.columns = [
            re.sub("([A-Z]+)", r"_\1", col.split(".")[-1]).lower() for col in df.columns
        ]
        return df

    def to_geopandas(
        self, results: List[DataGranule], fields: List[str] = []
    ) -> geopandas.GeoDataFrame:
        results_df = pandas.json_normalize(list(results), errors="ignore")
        # results_df = results_df.loc[:,~results_df.columns.duplicated()].copy()
        results_df = self._flattent_column_names(results_df)
        if len(fields) == 0:
            fields = self.default_fields

        results_df = results_df.drop(
            columns=[col for col in results_df.columns if col not in fields]
        )

        # results_df["_related_urls"] = results_df["_related_urls"].apply( lambda r: [l["URL"] for l in r._related_urls if l["Type"] == "GET DATA"])
        results_df["_related_urls"] = results_df["_related_urls"].apply(
            lambda links: [
                link
                for link in links
                if link["Type"]
                in [
                    "GET DATA",
                    "GET DATA VIA DIRECT ACCESS",
                    "GET RELATED VISUALIZATION",
                ]
            ]
        )

        # Create shapely polygons for result
        geometries = [
            self._get_shapely_object(results[index])
            for index in results_df.index.to_list()
        ]
        # Convert to GeoDataframe
        gdf = geopandas.GeoDataFrame(results_df, geometry=geometries, crs="EPSG:4326")
        return gdf

    def _orient_polygon(
        self, coords: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        polygon = shapely.geometry.polygon.orient(shapely.geometry.Polygon(coords))
        return list(polygon.exterior.coords)

    def _extract_geometry_info(self, geometry: Dict[str, Any]) -> Any:
        geometry_type = geometry["type"]
        coordinates = geometry["coordinates"]

        if geometry_type in ["Polygon"]:
            coords = self._orient_polygon(coordinates[0])
            self.search_params["polygon"] = coords
            return coords
        elif geometry_type in ["Point"]:
            self.search_params["point"] = coordinates
            return coordinates
        elif geometry_type in ["LineString"]:
            self.search_params["line"] = coordinates
            return coordinates
        else:
            print("Unsupported geometry type:", geometry_type)
            return None

    def _handle_draw(
        self, target: Dict[str, Any], action: Dict[str, Any], geo_json: Dict[str, Any]
    ) -> None:
        for layer in self.active_layers:
            self.m.remove_layer(layer)

        self.active_layers = []

        self.dc.clear()
        if self.current_geometry:
            self.m.remove_layer(self.current_geometry)

        self.current_geometry = ipyleaflet.GeoJSON(
            name="ROI",
            data=geo_json,
            style={"color": "red", "opacity": 0.9, "fillOpacity": 0.1},
        )

        self.roi = self._extract_geometry_info(geo_json["geometry"])

        self.m.add(self.current_geometry)

    def _get_shapely_object(
        self, result: DataGranule
    ) -> Union[shapely.geometry.base.BaseGeometry, None]:
        shape = None
        try:
            geo = result["umm"]["SpatialExtent"]["HorizontalSpatialDomain"]["Geometry"]
            keys = geo.keys()
            if "BoundingRectangles" in keys:
                bounding_rectangle = geo["BoundingRectangles"][0]
                # Create bbox tuple
                bbox_coords = (
                    bounding_rectangle["WestBoundingCoordinate"],
                    bounding_rectangle["SouthBoundingCoordinate"],
                    bounding_rectangle["EastBoundingCoordinate"],
                    bounding_rectangle["NorthBoundingCoordinate"],
                )
                # Create shapely geometry from bbox
                shape = shapely.geometry.box(*bbox_coords, ccw=True)
            elif "GPolygons" in keys:
                points = geo["GPolygons"][0]["Boundary"]["Points"]
                # Create shapely geometry from polygons
                shape = shapely.geometry.Polygon(
                    [[p["Longitude"], p["Latitude"]] for p in points]
                )
            else:
                raise ValueError(
                    "Provided result does not contain bounding boxes/polygons or is incompatible."
                )

        except Exception as e:
            pass

        return shape

    def display(self) -> ipyleaflet.Map:
        return self.m

    def update_html(self, feature: Dict[str, Any], **kwargs: Any) -> None:
        native_id = feature["properties"]["native-id"]
        start = feature["properties"]["_beginning_date_time"]
        end = feature["properties"]["_ending_date_time"]
        size = feature["properties"]["size"]
        url = [
            f"<a href={link['URL']}>link</a>"
            for link in feature["properties"]["_related_urls"]
            if link["Type"] == "GET DATA" and link["URL"].startswith("https")
        ]
        preview = [
            f"<img src={link['URL']} width='200px'/>"
            for link in feature["properties"]["_related_urls"]
            if link["Type"] == "GET RELATED VISUALIZATION"
            and link["URL"].startswith("https")
        ]
        if len(preview) > 1:
            browse = "".join(preview[0:2])
        else:
            browse = "".join(preview)

        self.html.value = """
            <h4>{}</h4>
            Size: {} MB<br>
            Start: {}<br>
            End: {}<br>
            Url: {}<br>
            <div>{}</div>
        """.format(native_id, round(size, 2), start, end, url, browse)
        if self.overview:
            self.m.remove_control(self.overview)
        self.overview = ipyleaflet.WidgetControl(
            widget=self.html, position="bottomright"
        )
        self.m.add(self.overview)

    def explore(
        self, results: List[DataGranule], roi: Dict[str, Any]
    ) -> ipyleaflet.Map:
        gdf = self.to_geopandas(results)
        dataset_ids = list(gdf["dataset-id"].unique())
        # matplotlib tb10
        colors = [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
        ]

        for p, c in zip(dataset_ids, colors):
            df = gdf.loc[gdf["dataset-id"] == p]
            total_size = round(df["size"].sum() / 1024, 2)
            total_granules = len(df)
            g = ipyleaflet.GeoData(
                geo_dataframe=df,
                style={
                    "color": c,
                    "fillColor": c,
                    "opacity": 0.15,
                    "weight": 0.04,
                    "fillOpacity": 0.1,
                    "stroke-width": 0.05,
                },
                hover_style={"fillColor": "red", "fillOpacity": 0.6},
                name=f"{p} [Count: {total_granules:,} | Size: {total_size} GB]",
            )
            g.on_click(self.update_html)
            self.active_layers.append(g)
            self.m.add(g)

        geo_json = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[c[0], c[1]] for c in roi["polygon"]]],
                    },
                }
            ],
        }

        roi_layer = ipyleaflet.GeoJSON(
            name="ROI",
            data=geo_json,
            style={"color": "red", "opacity": 0.9, "fillOpacity": 0.1},
        )

        self.active_layers.append(roi_layer)
        self.m.add(roi_layer)
        self.m.add(
            ipyleaflet.SearchControl(
                position="topleft",
                url="https://nominatim.openstreetmap.org/search?format=json&q={s}",
                zoom=8,
                marker=None,
            )
        )

        self.m._send({"redraw"})

        return self.m
