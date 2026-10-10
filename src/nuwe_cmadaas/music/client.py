import configparser
import json
import pathlib
import warnings
import hashlib
import time
import uuid
import re
from typing import Callable, Any, Dict, Optional, Union

from .connection import Connection
from .data import (
    Array2D,
    DataBlock,
    GridArray2D,
    FilesInfo,
    GridScalar2D,
    GridVector2D,
)
from nuwe_cmadaas._log import logger
from nuwe_cmadaas.config import CMADaasConfig
from .protocol import (
    build_music_url,
    build_signature_params,
    canonical_music_param_string,
)


CONFIG_FILE_NAME = "client.config"


class CMADaaSClient:
    """
    CMADaaS 客户端

    Attributes
    ----------
    user : str
        CMADaaS用户名
    password : str
        CMADaaS用户密码
    server_ip : str
        CMADaaS服务器IP地址
    server_port : int
        CMADaaS服务器端口
    connect_timeout : float
        连接超时，单位秒
    read_timeout : float
        读取超时，单位秒
    """
    clientLanguage = "Python"
    clientVersion = "V2.0.0"

    def __init__(
            self,
            server_ip: Optional[str] = None,
            server_port: Optional[int] = None,
            server_id: Optional[str] = None,
            connection_timeout: Optional[float] = None,
            read_timeout: Optional[float] = None,
            user: Optional[str] = None,
            password: Optional[str] = None,
            config: Optional[CMADaasConfig] = None,
            config_file: Optional[Union[pathlib.Path, str]] = None,
            session=None,
            transport=None,
            log_policy: str = "full",
            max_retries: int = 2,
            retry_backoff: float = 0.1,
    ):
        """
        Notes
        -----
        连接字段只在当前值为 ``None`` 时从配置中补齐，优先级从高到低：

        1. ``__init__`` 显式参数，例如 ``server_ip``、``server_port`` 等
        2. MUSIC 原生 INI 文件 ``config_file``
        3. 配置字典 ``config``

        INI 不读取账号密码；认证字段优先使用显式 ``user``、``password``，
        再从 ``config["auth"]`` 补齐。只有显式传入 ``config_file`` 才读取 INI，
        不会自动查找当前目录的 ``client.config``。高层 YAML 查找由
        ``load_cmadaas_config`` / ``create_client`` 完成。

        Parameters
        ----------
        server_ip : str, optional
            MUSIC 主机或 IP，不含协议或 API 路径。
        server_port : int, optional
            服务端口。
        server_id : str, optional
            默认服务节点；配置字典也可提供整数节点值。
        connection_timeout : float, optional
            连接超时（秒），保存为 connect_timeout。
        read_timeout : float, optional
            读取超时（秒），不是完整请求的总耗时上限。
        user : str, optional
            账号，参数名为 user，不接受 user_id。
        password : str, optional
            账号密码。
        config : CMADaasConfig, optional
            含 auth/server 的配置字典，不含顶层 cmadaas，也不接受 YAML 路径。
        config_file : pathlib.Path or str, optional
            MUSIC 原生 INI 路径，读取 [Pb] 连接字段，不读取认证。
        session : object, optional
            提供 get() 的 HTTP session，与 transport 互斥；由调用者管理生命周期。
        transport : object, optional
            提供 get() 的请求传输对象，与 session 互斥；默认使用 requests。
        log_policy : str
            full（默认完整 URL）、redacted（遮盖认证参数）或 summary（摘要）。
        max_retries : int
            初次请求外的最多重试次数，默认 2，必须为非负整数且不能是 bool。
        retry_backoff : float
            指数退避的基础秒数，默认 0.1，必须非负。

        Raises
        ------
        ValueError
            日志策略、重试选项非法或同时传 session/transport。
        RuntimeError
            指定 INI 文件不存在。

        Notes
        -----
        构造仅初始化本地连接对象，不登录或请求服务；未提供的连接/认证字段
        可以保留 None，不自动补业务默认值。配置缺字段、错误类型或解析失败
        也可能直接抛异常，不统一包装为 CMADaaSConfigurationError。
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_id = server_id

        self.connect_timeout = connection_timeout
        self.read_timeout = read_timeout

        self.user = user
        self.password = password
        if log_policy not in {"full", "redacted", "summary"}:
            raise ValueError("log_policy must be one of full, redacted, summary")
        self.session = session
        self.transport = transport
        self.log_policy = log_policy
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self._connection = None

        # 数据读取URL
        #   http://ip:port/music-ws/api?serviceNodeId=serverId&
        self.basic_url = (
            "http://{server_ip}:{server_port}/music-ws/api?serviceNodeId={server_id}&"
        )

        if config_file is not None:
            self._load_config_from_file(config_file)

        if config is not None:
            self._load_config(config)

        self.create_connect(self.user, self.password)

    def create_connect(self, user: str, password: str):
        """Replace credentials and rebuild the local connection; return None.

        ``user`` and ``password`` replace the stored credentials. Connection
        settings and the injected session/transport are reused, without
        reloading configuration, logging in or issuing a service request.
        The caller remains responsible for an injected session's lifetime.
        """
        self.user = user
        self.password = password
        self._connection = Connection(
            connect_timeout=self.connect_timeout,
            read_timeout=self.read_timeout,
            session=self.session,
            transport=self.transport,
            max_retries=self.max_retries,
            retry_backoff=self.retry_backoff,
        )

    def callAPI_to_array2D(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ) -> Array2D:
        """Request a MUSIC table and return its raw ``Array2D`` response.

        Parameters
        ----------
        interface_id : str
            Service interface supporting the RetArray2D protobuf format.
            Availability depends on the service, dataset and user permissions.
        params : dict
            Native MUSIC parameters, for example ``dataCode``, ``time``,
            ``fcstEle`` and ``latLons``. Supply service-formatted values; this
            method does not translate high-level selectors or modify the dict.
            Authentication and request-envelope fields are built by the client.
        server_id : str, optional
            Service node for this request; defaults to the client's server_id.

        Returns
        -------
        Array2D
            Response with ``request``, ``ok``, ``element_names`` and ``data``.
            Service, transport or decode failures handled by the connection
            are recorded in ``request``; successful empty results remain valid.

        Notes
        -----
        There is no ``strict`` argument. Check ``ok`` or call
        ``raise_for_error(interface_id=interface_id, params=params)`` before
        ``to_pandas()`` to preserve error context. Failed responses cannot be
        converted; local configuration or argument errors may propagate.
        Table values and column names come from the service. Conversion keeps
        strings and adds available metadata to DataFrame.attrs; numeric/date
        conversion and missing-value handling are the caller's responsibility.
        """
        array_2d = Array2D()

        method = self.callAPI_to_array2D.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(array_2d),
            failure_handler=Connection.generate_pack_failure_handler(array_2d),
            exception_handler=Connection.generate_exception_handler(array_2d),
        )

    def callAPI_to_gridArray2D(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ) -> GridArray2D:
        """Request a MUSIC grid in the RetGridArray2D protobuf format.

        Parameters
        ----------
        interface_id : str
            Interface supporting this return format for the chosen dataset.
        params : dict
            Native MUSIC parameters such as ``dataCode``, ``fcstEle``, ``time``
            and, where supported, level, forecast-hour and rectangle fields.
            Values are not translated from high-level selectors; the dict is
            not modified. The client builds authentication/envelope fields.
        server_id : str, optional
            Service node for this request; defaults to the client's server_id.

        Returns
        -------
        GridArray2D
            Raw grid with request status, coordinates, numeric data, units
            and user_element_name. ``to_xarray()`` produces a two-dimensional
            DataArray with latitude/longitude coordinates and available attrs.

        Notes
        -----
        Check ``ok`` or use ``raise_for_error(interface_id=..., params=...)``
        before conversion. Handled service, transport and decode failures are
        recorded in request; local configuration/argument errors may propagate.
        There is no strict argument. Successful empty grids can be converted;
        failed grids raise. Names, units and coordinate order come from the
        response; conversion does not sort, interpolate or mask missing values,
        and request time/level/forecast metadata does not add dimensions.
        Interface availability and return-format support depend on the service.
        """
        data = GridArray2D()

        method = self.callAPI_to_gridArray2D.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(data),
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
        )

    def callAPI_to_fileList(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ) -> FilesInfo:
        """Request native MUSIC file metadata without downloading file bodies.

        Parameters
        ----------
        interface_id : str
            Interface supporting the RetFilesInfo protobuf return format.
        params : dict
            Native service parameters for the selected dataset and query.
            The dict is not modified and high-level selectors are not translated.
            Authentication/envelope fields are built by the client.
        server_id : str, optional
            Service node for this request; defaults to the client's server_id.

        Returns
        -------
        FilesInfo
            Response with request status and a files_info list of FileInfo
            objects. Names, URLs, suffixes, size strings, save_path and other
            fields are response metadata, not verified local files or paths.

        Notes
        -----
        No output directory or binary download is created. Successful empty
        lists remain valid. Check ok or call raise_for_error with interface_id
        and params before using the list; handled service/transport/decode
        failures are recorded in request. There is no strict argument, and local
        configuration/argument errors may propagate. FileInfo.size may be empty
        or nonnumeric; callers must validate it before using it as a byte count.
        Interface and dataset availability depend on the service and permissions.
        """
        data = FilesInfo()

        method = self.callAPI_to_fileList.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(data),
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
        )

    def callAPI_to_serializedStr(
            self,
            interface_id: str,
            params: Dict,
            data_format: str,
            server_id: str = None
    ) -> str:
        """Request UTF-8 text in a service-supported serialization format.

        Parameters
        ----------
        interface_id : str
            Interface supporting the requested output format and dataset.
        params : dict
            Native MUSIC parameters. Mutated by adding dataFormat only when
            that key is absent; an existing value takes precedence over data_format.
        data_format : str
            Service format, for example json, xml, text or html. No local format
            validation or conversion is performed.
        server_id : str, optional
            Service node for this request; defaults to the client's server_id.

        Returns
        -------
        str
            UTF-8 response text, including compatible gateway/transport error
            strings. This return has no request, ok, attrs or raise_for_error.

        Notes
        -----
        Does not write files or parse the requested format. Recognized gateway
        failures use the historical getway error prefix; handled request exceptions
        return Error retrieving data. A normal formatted business-error body can
        still be returned verbatim, so validate its status and structure. UTF-8
        decoding or unexpected failure-body parsing errors may propagate. There
        is no strict argument. Use a fresh params dict when changing formats.
        """
        if "dataFormat" not in params:
            params["dataFormat"] = data_format

        method = self.callAPI_to_serializedStr.__name__

        def handle_success(content: bytes) -> str:
            return content.decode("utf8")

        def handle_failure(content: bytes) -> str:
            getway_info = json.loads(content)
            if getway_info is None:
                return "parse getway return string error:" + content.decode("utf8")
            else:
                return "getway error: returnCode={return_code} returnMessage={return_message}".format(
                    return_code=getway_info["returnCode"],
                    return_message=getway_info["returnMessage"],
                )

        def handle_exception(exception: Exception):
            logger.warning("Error retrieving data: " + str(exception))
            return "Error retrieving data"

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=handle_success,
            failure_handler=handle_failure,
            exception_handler=handle_exception,
        )

    def callAPI_to_saveAsFile(
        self,
        interface_id: str,
        params: Dict,
        data_format: str,
        file_name: str,
        server_id: str = None,
    ) -> FilesInfo:
        """Request formatted output and download the first returned file.

        Parameters
        ----------
        interface_id : str
            Interface supporting formatted output saved as a RetFilesInfo result.
        params : dict
            Native parameters. Adds dataFormat only if absent and replaces
            savepath with file_name; both mutations remain after a failed request.
        data_format : str
            Requested service format, such as json, xml, text or html. An existing
            params dataFormat takes precedence; no local format validation occurs.
        file_name : str
            Local target filename including its directory. Used verbatim for
            savepath and downloading, independently of the returned FileInfo name.
            None returns an error response before requesting, after dataFormat
            has been added but before savepath is changed.
        server_id : str, optional
            Service node for this request; defaults to the client's server_id.

        Returns
        -------
        FilesInfo
            Response metadata and request status. Check ok or call raise_for_error
            with query context, then verify the actual target file and its format.

        Notes
        -----
        Only the first file URL is downloaded. Existing targets are replaced;
        this method has no overwrite or strict argument and imposes no output-byte
        limit. The save request disables read retries as it is not idempotent;
        subsequent downloading uses the connection's download retry policy.
        Handled service, decode, transport and download failures are recorded in
        request, but unexpected local errors can propagate. In particular, a
        successful empty file list currently raises IndexError. Formats, suffixes
        and returned metadata do not prove a valid saved file; parse or inspect it.
        """
        data = FilesInfo()

        if "dataFormat" not in params:
            params["dataFormat"] = data_format

        method = self.callAPI_to_saveAsFile.__name__

        if file_name is None:
            data.request.error_code = Connection.otherError
            data.request.error_message = (
                "error:savePath can't null, the format is dir/file.formart. "
                "For example /data/saveas.xml)")
            return data

        params["savepath"] = file_name

        def handle_success(content: bytes):
            loaded_data = Connection.generate_pack_success_handler(data)(content)
            if loaded_data.request.error_code != 0:
                return loaded_data

            result = self._connection.download_file(
                loaded_data.files_info[0].file_url, file_name
            )
            if result[0] != 0:
                loaded_data.request.error_code = result[0]
                loaded_data.request.error_message = result[1]
            return loaded_data

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=handle_success,
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
            idempotent=False,
        )

    def callAPI_to_downFile(
        self,
        interface_id: str,
        params: Dict,
        file_dir: Union[str, pathlib.Path],
        server_id: str = None,
        overwrite: bool = True,
    ) -> FilesInfo:
        """Query a MUSIC file list and download its entries into file_dir.

        Parameters
        ----------
        interface_id : str
            Interface supporting a RetFilesInfo response and downloadable URLs.
        params : dict
            Native service query parameters. The dict is not modified and
            high-level selectors are not translated.
        file_dir : str or pathlib.Path
            Local output directory. Each target is file_dir / FileInfo.file_name;
            the service's save_path field is not rewritten to the local target.
            Parent directories are created when a file download starts.
        server_id : str, optional
            Service node for the list request; defaults to the client's server_id.
        overwrite : bool, default True
            Replace existing targets. False reports a download error at the first
            existing target and stops the batch; it does not silently skip files.

        Returns
        -------
        FilesInfo
            The queried metadata and request status, not a list of local Paths.
            A failure can retain the full queried list and files already written.
            Successful empty lists create no directory or file.

        Notes
        -----
        This method makes a new callAPI_to_fileList request, then downloads files
        sequentially. A separate preflight list is not reused and may change.
        Check ok or use raise_for_error(interface_id=..., params=...) afterwards;
        there is no strict argument. Handled failures are recorded in request,
        while local configuration/argument errors may propagate. Unsafe response
        file names are rejected. Each file is streamed to a temporary sibling
        and replaced atomically; the batch has no rollback. Content-Length, when
        present, is checked against transferred bytes, not against FileInfo.size.
        No local total-byte or file-count limit is imposed by this method.
        """
        file_dir_path = file_dir
        if isinstance(file_dir_path, str):
            file_dir_path = pathlib.Path(file_dir)

        data = FilesInfo()

        method = self.callAPI_to_fileList.__name__

        def success_handler(content: bytes):
            files_info = Connection.generate_pack_success_handler(data)(content)
            if files_info.request.error_code != 0:
                return files_info

            total_count = len(files_info.files_info)
            for index, file_info in enumerate(files_info.files_info):
                logger.info(f"downloading file {index + 1}/{total_count}...")
                if not self._is_safe_file_name(file_info.file_name):
                    files_info.request.error_code = Connection.downloadError
                    files_info.request.error_message = "unsafe server file name"
                    return files_info
                result = self._connection.download_file(
                    file_info.file_url,
                    file_dir_path.joinpath(file_info.file_name),
                    overwrite=overwrite,
                )
                if result[0] != 0:
                    files_info.request.error_code = result[0]
                    files_info.request.error_message = result[1]
                    return files_info
                logger.info(f"downloading file {index + 1}/{total_count}...done")

            return files_info

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=success_handler,
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
        )

    def callAPI_to_dataBlock(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ) -> DataBlock:
        """Request an opaque MUSIC binary block in the RetDataBlock format.

        Parameters
        ----------
        interface_id : str
            Interface confirmed to return RetDataBlock for the chosen dataset.
            No live-service combination has currently been verified.
        params : dict
            Native parameters required by that interface. High-level selectors
            are not translated and the dict is not modified; authentication
            and request envelope fields are constructed by the client.
        server_id : str, optional
            Service node for this request; defaults to the client's server_id.

        Returns
        -------
        DataBlock
            Response with request status, a ``data_name`` string and opaque
            ``data`` bytes. Check ``ok`` or call ``raise_for_error`` before
            consuming the bytes. A nonzero service error can still carry a
            name and bytes; a successful response can have empty content.

        Notes
        -----
        Each call emits a UserWarning about the unverified live-service
        capability. Synthetic protobuf decoding is not online verification.
        No automatic text decoding, pandas/xarray conversion or disk writing
        is provided; inherited conversion methods raise NotImplementedError.
        The name is service metadata, not a local path. Select a reader only
        after confirming the payload format. There is no local payload-size
        limit; inspecting len(data) is a check after the response was received.
        Service, transport and decode errors normally return failed responses;
        raise_for_error accepts explicit interface/parameter error context.
        """
        warnings.warn("callAPI_to_dataBlock has no verified live-service interface")
        data_block = DataBlock()

        method = self.callAPI_to_dataBlock.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(data_block),
            failure_handler=Connection.generate_pack_failure_handler(data_block),
            exception_handler=Connection.generate_exception_handler(data_block),
        )

    def callAPI_to_gridScalar2D(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ) -> GridScalar2D:
        """Request a MUSIC scalar grid in the RetGridScalar2D protobuf format.

        Parameters
        ----------
        interface_id : str
            Interface supporting this return format for the chosen dataset.
        params : dict
            Native service parameters, including dataset, element and time
            fields required by the interface. High-level selectors are not
            translated and the dict is not modified; authentication/envelope
            fields are built by the client.
        server_id : str, optional
            Service node for this request; defaults to the client's server_id.

        Returns
        -------
        GridScalar2D
            Response whose protobuf datas field is decoded into numeric data.
            ``to_xarray()`` produces a latitude/longitude DataArray, using the
            response element name, units and available request metadata.

        Notes
        -----
        Scalar denotes a scalar field, not a single numeric return value.
        Check ``ok`` or use ``raise_for_error(interface_id=..., params=...)``
        before conversion. Handled failures are recorded in request and cannot
        be converted; successful empty grids remain valid. There is no strict
        argument; local configuration/argument errors may propagate. Coordinate
        arrays are used when supplied, otherwise inferred from the response
        start/step/count (or start/end when step is zero). Conversion does not
        sort, interpolate, mask missing values or add time/level dimensions.
        Do not assume every gridArray2D interface also supports this format.
        """
        data = GridScalar2D()

        method = self.callAPI_to_gridScalar2D.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(data),
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
        )

    def callAPI_to_gridVector2D(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ) -> GridVector2D:
        """Request a MUSIC vector grid in the RetGridVector2D protobuf format.

        Parameters
        ----------
        interface_id : str
            Interface supporting this return format for the chosen dataset.
        params : dict
            Native parameters; supported vector interfaces may use case-sensitive
            ``fcstuele``/``fcstvele`` for the U/V elements. Supply other required
            fields in service format. The dict is not modified, high-level
            selectors are not translated, and authentication is built by the client.
        server_id : str, optional
            Service node for this request; defaults to the client's server_id.

        Returns
        -------
        GridVector2D
            Response with numeric u_datas/v_datas and shared grid coordinates.
            ``to_xarray()`` returns a Dataset containing two latitude/longitude
            variables named by u_element_name/v_element_name (falling back to
            u/v when empty), with available request metadata on Dataset.attrs.

        Notes
        -----
        Conversion does not add component units, compute speed/direction,
        interpolate, rotate vectors or mask missing values. Verify the dataset's
        element definitions and units before calculations. Check ``ok`` or use
        ``raise_for_error(interface_id=..., params=...)`` before conversion;
        handled failures are recorded in request and failed conversion raises.
        Successful empty grids remain valid. There is no strict argument;
        local configuration/argument errors may propagate. Return-format support
        depends on the service and dataset, not just the method's availability.
        """
        # warnings.warn("callAPI_to_gridVector2D is not tested")
        data = GridVector2D()

        method = self.callAPI_to_gridVector2D.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(data),
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
        )

    def _load_config_from_file(self, config_file: Optional[Union[pathlib.Path, str]] = None):
        if config_file is not None:
            config_file = pathlib.Path(config_file)
            if not config_file.exists():
                raise RuntimeError(f"config file is not exist: {config_file.absolute()}")
        else:
            config_file = pathlib.Path(CONFIG_FILE_NAME)
            if not config_file.exists():
                raise RuntimeError(f"default config file is not exist: {config_file.absolute()}")

        cf = configparser.ConfigParser()
        cf.read(config_file)

        if self.server_ip is None:
            self.server_ip = cf.get("Pb", "music_server")

        if self.server_port is None:
            self.server_port = cf.getint("Pb", "music_port")

        if self.server_id is None:
            self.server_id = cf.get("Pb", "music_ServiceId")

        if self.connect_timeout is None:
            self.connect_timeout = int(cf.get("Pb", "music_connTimeout"))

        if self.read_timeout is None:
            self.read_timeout = int(cf.get("Pb", "music_readTimeout"))

    def _load_config(self, config: Dict):
        auth_config = config["auth"]
        server_config = config["server"]

        if self.user is None:
            self.user = auth_config["user"]
        if self.password is None:
            self.password = auth_config["password"]

        if self.server_ip is None:
            self.server_ip = server_config["music_server"]

        if self.server_port is None:
            self.server_port = server_config["music_port"]

        if self.server_id is None:
            self.server_id = server_config["music_ServiceId"]

        if self.connect_timeout is None:
            self.connect_timeout = server_config["music_connTimeout"]

        if self.read_timeout is None:
            self.read_timeout = server_config["music_readTimeout"]

    def _get_fetch_url(
            self,
            interface_id: str,
            method: str,
            params: Dict,
            server_id: str = None,
    ) -> str:
        if server_id is None:
            server_id = self.server_id

        basic_url = self.basic_url.format(
            server_ip=self.server_ip, server_port=self.server_port, server_id=server_id
        )

        timestamp = str((round(time.time() * 1000)))
        nonce = str(uuid.uuid1())
        sign_params = build_signature_params(
            params,
            service_node_id=server_id,
            method=method,
            user=self.user,
            interface_id=interface_id,
            timestamp=timestamp,
            nonce=nonce,
            password=self.password,
        )
        sign = CMADaaSClient._get_sign(sign_params)
        return build_music_url(
            basic_url,
            method=method,
            user=self.user,
            interface_id=interface_id,
            params=params,
            timestamp=timestamp,
            nonce=nonce,
            sign=sign,
        )

    def _do_request(
            self,
            interface_id: str,
            method: str,
            params: Dict,
            server_id: str,
            success_handler: Callable[[bytes], Any],
            failure_handler: Callable[[bytes], Any],
            exception_handler: Callable[[Exception], Any],
            idempotent: bool = True,
    ):
        fetch_url = self._get_fetch_url(
            interface_id, method, params, server_id
        )
        request_id = uuid.uuid4().hex
        if self.log_policy == "full":
            logger.info(f"fetch url: {fetch_url}")
        elif self.log_policy == "redacted":
            logger.info(f"fetch url: {self._redact_url(fetch_url)}")

        started = time.monotonic()
        result = self._connection.make_request(
            fetch_url,
            success_handler,
            failure_handler,
            exception_handler,
            idempotent=idempotent,
        )
        self._attach_output_metadata(result, interface_id, params)
        if self.log_policy == "summary":
            request = getattr(result, "request", None)
            result_code = getattr(request, "error_code", "unknown")
            logger.info(
                f"request summary interface={interface_id} "
                f"service_node={server_id or self.server_id} request_id={request_id} "
                f"elapsed_ms={(time.monotonic() - started) * 1000:.1f} "
                f"result_code={result_code} retries={self._connection.last_retries}"
            )
        return result

    @staticmethod
    def _attach_output_metadata(result, interface_id: str, params: Dict) -> None:
        metadata = getattr(result, "metadata", None)
        if not isinstance(metadata, dict):
            return
        metadata["interface_id"] = interface_id
        parameter_names = {
            "time": "time",
            "timeRange": "time_range",
            "validTime": "valid_time",
            "levelType": "level_type",
            "fcstLevel": "level",
            "fcstMember": "member",
        }
        for source_name, metadata_name in parameter_names.items():
            if source_name in params:
                metadata[metadata_name] = params[source_name]

    @staticmethod
    def _redact_url(fetch_url: str) -> str:
        return re.sub(
            r"([?&](?:userId|sign|pwd|password|passwd)=)[^&]*",
            r"\1<redacted>",
            fetch_url,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def _is_safe_file_name(file_name: str) -> bool:
        if not file_name or file_name in {".", ".."}:
            return False
        if "\\" in file_name or "/" in file_name:
            return False
        return pathlib.Path(file_name).name == file_name

    @staticmethod
    def _get_sign(sign_params: Dict) -> str:
        """
        计算一次性签名值

        Parameters
        ----------
        sign_params

        Returns
        -------
        str
        """
        sign_params = dict(sign_params)
        if "params" in sign_params:
            params_val = sign_params.pop("params")
            key_val_list = params_val.split("&")
            for keyVal in key_val_list:
                key, value = keyVal.split("=", 1)
                sign_params[key] = value
        param_string = canonical_music_param_string(sign_params)
        return hashlib.md5(param_string.encode(encoding="UTF-8")).hexdigest().upper()
