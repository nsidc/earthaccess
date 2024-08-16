import os
import warnings
from collections import defaultdict
from typing import Any, Optional
from xml.etree import ElementTree as ET

import numpy as np
import xarray as xr

from virtualizarr.manifests import ChunkManifest, ManifestArray
from virtualizarr.types import ChunkKey
from virtualizarr.zarr import ZArray


class DMRParser:
    """Parser for the OPeNDAP DMR++ XML format.

    Reads groups, dimensions, coordinates, data variables, encoding, chunk manifests, and attributes.
    Highly modular to allow support for older dmrpp schema versions. Includes many utility functions to extract
    different information such as finding all variable tags, splitting hdf5 groups, parsing dimensions, and more.

    OPeNDAP DMR++ homepage: https://docs.opendap.org/index.php/DMR%2B%2B
    """

    # DAP and DMRPP XML namespaces
    _ns = {
        "dap": "http://xml.opendap.org/ns/DAP/4.0#",
        "dmr": "http://xml.opendap.org/dap/dmrpp/1.0.0#",
    }
    # DAP data types to numpy data types
    _dap_np_dtype = {
        "Byte": "uint8",
        "UByte": "uint8",
        "Int8": "int8",
        "UInt8": "uint8",
        "Int16": "int16",
        "UInt16": "uint16",
        "Int32": "int32",
        "UInt32": "uint32",
        "Int64": "int64",
        "UInt64": "uint64",
        "Url": "object",
        "Float32": "float32",
        "Float64": "float64",
        "String": "object",
    }
    # Default zlib compression value
    _default_zlib_value = 6
    # Encoding keys that should be cast to float
    _encoding_keys = {"_FillValue", "missing_value", "scale_factor", "add_offset"}

    def __init__(self, dmr: str, data_filepath: Optional[str] = None):
        """Initialize the DMRParser with the given DMR data and data file path.

        Parameters
        ----------
        dmr : str
            The DMR file contents as a string.

        data_filepath : str, optional
            The path to the actual data file that will be set in the chunk manifests.
            If None, the data file path is taken from the DMR file.
        """
        self.root = ET.fromstring(dmr)
        self.data_filepath = (
            data_filepath if data_filepath is not None else self.root.attrib["name"]
        )

    def parse_dataset(self, group=None) -> xr.Dataset:
        """Parses the given file and creates a virtual xr.Dataset with ManifestArrays.

        Parameters
        ----------
        group : str
            The group to parse. If None, and no groups are present, the dataset is parsed.
            If None and groups are present, the first group is parsed.

        Returns:
        -------
        An xr.Dataset wrapping virtualized zarr arrays.

        Examples:
        --------
        Open a sample DMR++ file and parse the dataset

        >>> import requests
        >>> r = requests.get("https://github.com/OPENDAP/bes/raw/3e518f6dc2f625b0b83cfb6e6fd5275e4d6dcef1/modules/dmrpp_module/data/dmrpp/chunked_threeD.h5.dmrpp")
        >>> parser = DMRParser(r.text)
        >>> vds = parser.parse_dataset()
        >>> vds
        <xarray.Dataset> Size: 4MB
            Dimensions:     (phony_dim_0: 100, phony_dim_1: 100, phony_dim_2: 100)
            Dimensions without coordinates: phony_dim_0, phony_dim_1, phony_dim_2
            Data variables:
                d_8_chunks  (phony_dim_0, phony_dim_1, phony_dim_2) float32 4MB ManifestA...

        >>> vds2 = open_virtual_dataset("https://github.com/OPENDAP/bes/raw/3e518f6dc2f625b0b83cfb6e6fd5275e4d6dcef1/modules/dmrpp_module/data/dmrpp/chunked_threeD.h5.dmrpp", filetype="dmrpp", indexes={})
        >>> vds2
        <xarray.Dataset> Size: 4MB
            Dimensions:     (phony_dim_0: 100, phony_dim_1: 100, phony_dim_2: 100)
            Dimensions without coordinates: phony_dim_0, phony_dim_1, phony_dim_2
            Data variables:
                d_8_chunks  (phony_dim_0, phony_dim_1, phony_dim_2) float32 4MB ManifestA...
        """
        if group is not None:
            # group = "/" + group.strip("/")  # ensure group is in form "/a/b"
            group = os.path.normpath(group).removeprefix(
                "/"
            )  # ensure group is in form "a/b/c"
        if self._is_hdf5(self.root):
            return self._parse_hdf5_dataset(self.root, group)
        if self.data_filepath.endswith(".nc"):
            return self._parse_netcdf4_dataset(self.root, group)
        raise ValueError("dmrpp file must be HDF5 or netCDF4 based")

    def _parse_netcdf4_dataset(
        self, root: ET.Element, group: Optional[str] = None
    ) -> xr.Dataset:
        """Parse the dataset from the netcdf4 based dmrpp with groups, starting at the given group. Set root to the given group.

        Parameters
        ----------
        root : ET.Element
            The root element of the DMR file.

        group : str
            The group to parse. If None, and no groups are present, the dataset is parsed.
            If None and groups are present, the first group is parsed.

        Returns:
        -------
        xr.Dataset
        """
        group_tags = root.findall("dap:Group", self._ns)
        if len(group_tags) == 0:
            if group is not None:
                # no groups found and group specified -> warning
                warnings.warn(
                    "No groups found in NetCDF4 dmrpp file; ignoring group parameter"
                )
            # no groups found and no group specified -> parse dataset
            return self._parse_dataset(root)
        all_groups = self._split_netcdf4(root)
        if group is None:
            # groups found and no group specified -> parse first group
            return self._parse_dataset(group_tags[0])
        if group in all_groups:
            # groups found and group specified -> parse specified group
            return self._parse_dataset(all_groups[group])
        else:
            # groups found and specified group not found -> error
            raise ValueError(f"Group {group} not found in NetCDF4 dmrpp file")

    def _split_netcdf4(self, root: ET.Element) -> dict[str, ET.Element]:
        """Split the input <Group> element into several <Dataset> ET.Elements by netcdf4 group. E.g. {"left": <Dataset>, "right": <Dataset>}.

        Parameters
        ----------
        root : ET.Element
            The root element of the DMR file.

        Returns:
        -------
        dict[str, ET.Element]
        """
        group_tags = root.findall("dap:Group", self._ns)
        all_groups: dict[str, ET.Element] = defaultdict(
            lambda: ET.Element(root.tag, root.attrib)
        )
        for group_tag in group_tags:
            all_groups[os.path.normpath(group_tag.attrib["name"])] = group_tag
        return all_groups

    def _is_hdf5(self, root: ET.Element) -> bool:
        """Check if the DMR file is HDF5 based."""
        if root.find(".//dap:Attribute[@name='fullnamepath']", self._ns) is not None:
            return True
        if root.find("./dap:Attribute[@name='HDF5_GLOBAL']", self._ns) is not None:
            return True
        return False

    def _parse_hdf5_dataset(
        self, root: ET.Element, group: Optional[str] = None
    ) -> xr.Dataset:
        """Parse the dataset from the HDF5 based dmrpp with groups, starting at the given group. Set root to the given group.

        Parameters
        ----------
        root : ET.Element
            The root element of the DMR file.

        group : str
            The group to parse. If None, and no groups are present, the dataset is parsed.
            If None and groups are present, the first group is parsed.

        Returns:
        -------
        xr.Dataset
        """
        all_groups = self._split_hdf5(root=root)
        if len(all_groups) == 0:
            raise ValueError("No groups found in HDF based dmrpp file")
        if group is None:
            # pick a random group if no group is specified
            group = next(iter(all_groups))
        attrs = {}
        for attr_tag in root.iterfind("dap:Attribute", self._ns):
            if attr_tag.attrib["type"] != "Container":
                attrs.update(self._parse_attribute(attr_tag))
        if group in all_groups:
            # replace aliased variable names with original names: gt1r_heights -> heights
            orignames = self._find_original_names(all_groups[group])
            vds = self._parse_dataset(all_groups[group])
            # Only one group so found attrs are global attrs
            if len(all_groups) == 1:
                vds.attrs.update(attrs)
            return vds.rename(orignames)
        raise ValueError(f"Group {group} not found in HDF5 dmrpp file")

    def _find_original_names(self, root: ET.Element) -> dict[str, str]:
        """Find the original names of variables in the DMR file. E.g. {"gt1r_heights": "heights"}.

        Parameters
        ----------
        root : ET.Element
            The root element of the DMR file.

        Returns:
        -------
        dict[str, str]
        """
        orignames: dict[str, str] = {}
        vars_tags: list[ET.Element] = []
        for dap_dtype in self._dap_np_dtype:
            vars_tags += root.findall(f"dap:{dap_dtype}", self._ns)
        for var_tag in vars_tags:
            origname_tag = var_tag.find(
                "./dap:Attribute[@name='origname']/dap:Value", self._ns
            )
            if origname_tag is not None and origname_tag.text is not None:
                orignames[var_tag.attrib["name"]] = origname_tag.text
        return orignames

    def _split_hdf5(self, root: ET.Element) -> dict[str, ET.Element]:
        """Split the input <Dataset> element into several <Dataset> ET.Elements by HDF5 group.

        E.g. {"gtr1/heights": <Dataset>, "gtr1/temperatures": <Dataset>}. Builds up new <Dataset> elements
        each with dimensions, variables, and attributes.

        Parameters
        ----------
        root : ET.Element
            The root element of the DMR file.

        Returns:
        -------
        dict[str, ET.Element]
        """
        # Add all variable, dimension, and attribute tags to their respective groups
        groups_roots: dict[str, ET.Element] = defaultdict(
            lambda: ET.Element(root.tag, root.attrib)
        )
        group_dims: dict[str, set[str]] = defaultdict(
            set
        )  # {"gt1r/heights": {"dim1", "dim2", ...}}
        vars_tags: list[ET.Element] = []
        for dap_dtype in self._dap_np_dtype:
            vars_tags += root.findall(f"dap:{dap_dtype}", self._ns)
        # Variables
        for var_tag in vars_tags:
            fullname_tag = var_tag.find(
                "./dap:Attribute[@name='fullnamepath']/dap:Value", self._ns
            )
            if fullname_tag is not None and fullname_tag.text is not None:
                # '/gt1r/heights/ph_id_pulse' -> 'gt1r/heights'
                group_name = os.path.dirname(fullname_tag.text).removeprefix("/")
                groups_roots[group_name].append(var_tag)
                dim_tags = var_tag.findall("dap:Dim", self._ns)
                dims = self._parse_multi_dims(dim_tags)
                group_dims[group_name].update(dims.keys())
        # Dimensions
        for dim_tag in root.iterfind("dap:Dimension", self._ns):
            for g, d in group_dims.items():
                if dim_tag.attrib["name"] in d:
                    groups_roots[g].append(dim_tag)
        # Attributes
        container_attr_tag = root.find("dap:Attribute[@name='HDF5_GLOBAL']", self._ns)
        if container_attr_tag is None:
            attrs_tags = root.findall("dap:Attribute", self._ns)
            for attr_tag in attrs_tags:
                fullname_tag = attr_tag.find(
                    "./dap:Attribute[@name='fullnamepath']/dap:Value", self._ns
                )
                if fullname_tag is not None and fullname_tag.text is not None:
                    group_name = os.path.dirname(fullname_tag.text).removeprefix("/")
                    # Add all attributes to the new dataset
                    groups_roots[group_name].extend(attr_tag)
        else:
            groups_roots[next(iter(groups_roots))].extend(container_attr_tag)
        return groups_roots

    def _parse_dataset(self, root: ET.Element) -> xr.Dataset:
        """Parse the dataset using the root element of the DMR file.

        Parameters
        ----------
        root : ET.Element
            The root element of the DMR file.

        Returns:
        -------
        xr.Dataset
        """
        # Dimension names and sizes
        dim_tags = root.findall("dap:Dimension", self._ns)
        dataset_dims = self._parse_multi_dims(dim_tags)
        # Data variables and coordinates
        coord_names = self._find_coord_names(root)
        # if no coord_names are found or coords don't include dims, dims are used as coords
        if len(coord_names) == 0 or len(coord_names) < len(dataset_dims):
            coord_names = set(dataset_dims.keys())
        # Seperate and parse coords + data variables
        coord_vars: dict[str, xr.Variable] = {}
        data_vars: dict[str, xr.Variable] = {}
        for var_tag in self._find_var_tags(root):
            variable = self._parse_variable(var_tag, dataset_dims)
            if var_tag.attrib["name"] in coord_names:
                coord_vars[var_tag.attrib["name"]] = variable
            else:
                data_vars[var_tag.attrib["name"]] = variable
        # Attributes
        attrs: dict[str, str] = {}
        for attr_tag in self.root.iterfind("dap:Attribute", self._ns):
            attrs.update(self._parse_attribute(attr_tag))
        return xr.Dataset(
            data_vars=data_vars,
            coords=xr.Coordinates(coords=coord_vars, indexes={}),
            attrs=attrs,
        )

    def _find_var_tags(self, root: ET.Element) -> list[ET.Element]:
        """Find all variable tags in the DMR file. Also known as array tags. Tags are labeled with the DAP data type. E.g. <Float32>, <Int16>, <String>.

        Parameters
        ----------
        root : ET.Element
            The root element of the DMR file.

        Returns:
        -------
        list[ET.Element]
        """
        vars_tags: list[ET.Element] = []
        for dap_dtype in self._dap_np_dtype:
            vars_tags += root.findall(f"dap:{dap_dtype}", self._ns)
        return vars_tags

    def _find_coord_names(self, root: ET.Element) -> set[str]:
        """Find the name of all coordinates in root. Checks inside all variables and global attributes.

        Parameters
        ----------
        root : ET.Element
            The root element of the DMR file.

        Returns:
        -------
        set[str] : The set of unique coordinate names.
        """
        # Check for coordinate names within each variable attributes
        coord_names: set[str] = set()
        for var_tag in self._find_var_tags(root):
            coord_tag = var_tag.find(
                "./dap:Attribute[@name='coordinates']/dap:Value", self._ns
            )
            if coord_tag is not None and coord_tag.text is not None:
                coord_names.update(coord_tag.text.split(" "))
            for map_tag in var_tag.iterfind("dap:Map", self._ns):
                coord_names.add(map_tag.attrib["name"].removeprefix("/"))
        # Check for coordinate names in a global attribute
        coord_tag = var_tag.find("./dap:Attribute[@name='coordinates']", self._ns)
        if coord_tag is not None and coord_tag.text is not None:
            coord_names.update(coord_tag.text.split(" "))
        return coord_names

    def _parse_dim(self, root: ET.Element) -> dict[str, int | None]:
        """Parse single <Dim> or <Dimension> tag.

        If the tag has no name attribute, it is a phony dimension. E.g. <Dim size="300"/> --> {"phony_dim": 300}
        If the tag has no size attribute, it is an unlimited dimension. E.g. <Dim name="time"/> --> {"time": None}
        If the tag has both name and size attributes, it is a regular dimension. E.g. <Dim name="lat" size="1447"/> --> {"lat": 1447}

        Parameters
        ----------
        root : ET.Element
            The root element Dim/Dimension tag

        Returns:
        -------
        dict
            E.g. {"time": 1, "lat": 1447, "lon": 2895}, {"phony_dim": 300}, {"time": None, "lat": None, "lon": None}
        """
        if "name" not in root.attrib and "size" in root.attrib:
            return {"phony_dim": int(root.attrib["size"])}
        if "name" in root.attrib and "size" not in root.attrib:
            return {os.path.basename(root.attrib["name"]): None}
        if "name" in root.attrib and "size" in root.attrib:
            return {os.path.basename(root.attrib["name"]): int(root.attrib["size"])}
        raise ValueError("Not enough information to parse Dim/Dimension tag")

    def _parse_multi_dims(
        self, dim_tags: list[ET.Element], global_dims: dict[str, int] = {}
    ) -> dict:
        """Parse multiple <Dim> or <Dimension> tags. Generally <Dim> tags are found within dmrpp variable tags.

        Returns best possible matching of {dimension: shape} present in the list and global_dims. E.g tags=(Dim("lat", None), Dim("lon", None)) and global_dims={"lat": 100, "lon": 100, "time": 5} --> {"lat": 100, "lon": 100}

        E.g. tags=(Dim("time", None), Dim("", 200)) and global_dims={"lat": 100, "lon": 100, "time": 5} --> {"time": 5, "phony_dim0": 200}

        This function is often used to fill in missing sizes from the global_dims. E.g. Variable tags may contain only dimension names and not sizes. If the {name: size} matching is known from the global_dims, it is used to fill in the missing sizes.

        Parameters
        ----------
        dim_tags : tuple[ET.Element]
            A tuple of ElementTree Elements representing dimensions in the DMR file.

        global_dims : dict
            A dictionary of dimension names and sizes. E.g. {"time": 1, "lat": 1447, "lon": 2895}

        Returns:
        -------
        dict
            E.g. {"time": 1, "lat": 1447, "lon": 2895}
        """
        dims: dict[str, int | None] = {}
        for dim_tag in dim_tags:
            dim: dict[str, int | None] = self._parse_dim(dim_tag)
            if "phony_dim" in dim:
                dims["phony_dim_" + str(len(dims))] = dim["phony_dim"]
            else:
                dims.update(dim)
        for name, size in list(dims.items()):
            if name in global_dims and size is None:
                dims[name] = global_dims[name]
        return dims

    def _parse_variable(
        self, var_tag: ET.Element, dataset_dims: dict[str, int]
    ) -> xr.Variable:
        """Parse a variable from a DMR tag.

        Parameters
        ----------
        var_tag : ET.Element
            An ElementTree Element representing a variable in the DMR file. Will have DAP dtype as tag.

        dataset_dims : dict
            A dictionary of dimension names and sizes. E.g. {"time": 1, "lat": 1447, "lon": 2895}
            Must contain at least all the dimensions used by the variable. Necessary since the variable
            metadata only contains the dimension names and not the sizes.

        Returns:
        -------
        xr.Variable
        """
        # Dimension names
        dim_tags = var_tag.findall("dap:Dim", self._ns)
        dim_shapes = self._parse_multi_dims(dim_tags, dataset_dims)
        # convert DAP dtype to numpy dtype
        dtype = np.dtype(
            self._dap_np_dtype[var_tag.tag.removeprefix("{" + self._ns["dap"] + "}")]
        )
        # Chunks and Filters
        filters = None
        shape = tuple(dim_shapes.values())
        chunks_shape = shape
        chunks_tag = var_tag.find("dmr:chunks", self._ns)
        if chunks_tag is not None:
            # Chunks
            found_chunk_dims = self._parse_chunks_dimensions(chunks_tag)
            chunks_shape = found_chunk_dims if found_chunk_dims is not None else shape
            chunkmanifest = self._parse_chunks(chunks_tag, chunks_shape)
            # Filters
            filters = self._parse_filters(chunks_tag, dtype)
        # Attributes
        attrs: dict[str, Any] = {}
        for attr_tag in var_tag.iterfind("dap:Attribute", self._ns):
            attrs.update(self._parse_attribute(attr_tag))
        # Remove attributes only used for parsing logic
        fill_value = attrs.pop("_FillValue", np.nan)
        attrs.pop("fullnamepath", None)
        attrs.pop("origname", None)
        # attrs.pop("coordinates", None)
        # create ManifestArray and ZArray
        zarray = ZArray(
            chunks=chunks_shape,
            dtype=dtype,
            fill_value=fill_value,
            filters=filters,
            order="C",
            shape=shape,
        )
        marr = ManifestArray(zarray=zarray, chunkmanifest=chunkmanifest)
        encoding = {k: attrs.get(k) for k in self._encoding_keys if k in attrs}
        return xr.Variable(
            dims=dim_shapes.keys(), data=marr, attrs=attrs, encoding=encoding
        )

    def _parse_attribute(self, attr_tag: ET.Element) -> dict[str, Any]:
        """Parse an attribute from a DMR attr tag. Converts the attribute value to a native python type.

        Parameters
        ----------
        attr_tag : ET.Element
            An ElementTree Element with an <Attr> tag.

        Returns:
        -------
        dict
        """
        attr: dict[str, Any] = {}
        values = []
        if "type" in attr_tag.attrib and attr_tag.attrib["type"] == "Container":
            return attr
        dtype = np.dtype(self._dap_np_dtype[attr_tag.attrib["type"]])
        # if multiple Value tags are present, store as "key": "[v1, v2, ...]"
        for value_tag in attr_tag:
            # cast attribute to native python type using dmr provided dtype
            val = (
                dtype.type(value_tag.text).item()
                if dtype != np.object_
                else value_tag.text
            )
            if val == "*":
                val = np.nan
            values.append(val)
        attr[attr_tag.attrib["name"]] = values[0] if len(values) == 1 else values
        return attr

    def _parse_filters(
        self, chunks_tag: ET.Element, dtype: np.dtype
    ) -> list[dict] | None:
        """Parse filters from a DMR chunks tag.

        Parameters
        ----------
        chunks_tag : ET.Element
            An ElementTree Element with a <chunks> tag.

        dtype : np.dtype
            The numpy dtype of the variable.

        Returns:
        -------
        list[dict] | None
            E.g. [{"id": "shuffle", "elementsize": 4}, {"id": "zlib", "level": 4}]
        """
        if "compressionType" in chunks_tag.attrib:
            filters: list[dict] = []
            # shuffle deflate --> ["shuffle", "deflate"]
            compression_types = chunks_tag.attrib["compressionType"].split(" ")
            if "shuffle" in compression_types:
                filters.append({"id": "shuffle", "elementsize": dtype.itemsize})
            if "deflate" in compression_types:
                level = int(
                    chunks_tag.attrib.get("deflateLevel", self._default_zlib_value)
                )
                filters.append({"id": "zlib", "level": level})
            return filters
        return None

    def _parse_chunks_dimensions(
        self, chunks_tag: ET.Element
    ) -> tuple[int, ...] | None:
        """Parse the chunk dimensions from a DMR chunks tag. Returns None if no chunk dimensions are found.

        Parameters
        ----------
        chunks_tag : ET.Element
            An ElementTree Element with a <chunks> tag.

        Returns:
        -------
        tuple[int, ...] | None

        """
        chunk_dim_tag = chunks_tag.find("dmr:chunkDimensionSizes", self._ns)
        if chunk_dim_tag is not None and chunk_dim_tag.text is not None:
            # 1 1447 2895 -> (1, 1447, 2895)
            return tuple(map(int, chunk_dim_tag.text.split()))
        return None

    def _parse_chunks(
        self, chunks_tag: ET.Element, chunks_shape: tuple[int, ...]
    ) -> ChunkManifest:
        """Parse the chunk manifest from a DMR chunks tag.

        Parameters
        ----------
        chunks_tag : ET.Element
            An ElementTree Element with a <chunks> tag.

        chunks : tuple
            Chunk sizes for each dimension. E.g. (1, 1447, 2895)

        Returns:
        -------
        ChunkManifest
        """
        chunkmanifest: dict[ChunkKey, object] = {}
        default_num: list[int] = (
            [0 for i in range(len(chunks_shape))] if chunks_shape else [0]
        )
        chunk_key_template = ".".join(["{}" for i in range(len(default_num))])
        for chunk_tag in chunks_tag.iterfind("dmr:chunk", self._ns):
            chunk_num = default_num
            if "chunkPositionInArray" in chunk_tag.attrib:
                # "[0,1023,10235]" -> ["0","1023","10235"]
                chunk_pos = chunk_tag.attrib["chunkPositionInArray"][1:-1].split(",")
                # [0,1023,10235] // [1, 1023, 2047] -> [0,1,5]
                chunk_num = [
                    int(chunk_pos[i]) // chunks_shape[i]
                    for i in range(len(chunks_shape))
                ]
            # [0,1,5] -> "0.1.5"
            chunk_key = ChunkKey(chunk_key_template.format(*chunk_num))
            chunkmanifest[chunk_key] = {
                "path": self.data_filepath,
                "offset": int(chunk_tag.attrib["offset"]),
                "length": int(chunk_tag.attrib["nBytes"]),
            }
        return ChunkManifest(entries=chunkmanifest)
