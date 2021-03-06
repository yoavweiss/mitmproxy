"""
This module handles the import of mitmproxy flows generated by old versions.
"""

from typing import Any

from mitmproxy import version
from mitmproxy.utils import strutils


def convert_011_012(data):
    data[b"version"] = (0, 12)
    return data


def convert_012_013(data):
    data[b"version"] = (0, 13)
    return data


def convert_013_014(data):
    data[b"request"][b"first_line_format"] = data[b"request"].pop(b"form_in")
    data[b"request"][b"http_version"] = b"HTTP/" + ".".join(
        str(x) for x in data[b"request"].pop(b"httpversion")).encode()
    data[b"response"][b"http_version"] = b"HTTP/" + ".".join(
        str(x) for x in data[b"response"].pop(b"httpversion")).encode()
    data[b"response"][b"status_code"] = data[b"response"].pop(b"code")
    data[b"response"][b"body"] = data[b"response"].pop(b"content")
    data[b"server_conn"].pop(b"state")
    data[b"server_conn"][b"via"] = None
    data[b"version"] = (0, 14)
    return data


def convert_014_015(data):
    data[b"version"] = (0, 15)
    return data


def convert_015_016(data):
    for m in (b"request", b"response"):
        if b"body" in data[m]:
            data[m][b"content"] = data[m].pop(b"body")
    if b"msg" in data[b"response"]:
        data[b"response"][b"reason"] = data[b"response"].pop(b"msg")
    data[b"request"].pop(b"form_out", None)
    data[b"version"] = (0, 16)
    return data


def convert_016_017(data):
    data[b"server_conn"][b"peer_address"] = None
    data[b"version"] = (0, 17)
    return data


def convert_017_018(data):
    # convert_unicode needs to be called for every dual release and the first py3-only release
    data = convert_unicode(data)

    data["server_conn"]["ip_address"] = data["server_conn"].pop("peer_address")
    data["marked"] = False
    data["version"] = (0, 18)
    return data


def convert_018_019(data):
    # convert_unicode needs to be called for every dual release and the first py3-only release
    data = convert_unicode(data)

    data["request"].pop("stickyauth", None)
    data["request"].pop("stickycookie", None)
    data["client_conn"]["sni"] = None
    data["client_conn"]["alpn_proto_negotiated"] = None
    data["client_conn"]["cipher_name"] = None
    data["client_conn"]["tls_version"] = None
    data["server_conn"]["alpn_proto_negotiated"] = None
    data["mode"] = "regular"
    data["metadata"] = dict()
    data["version"] = (0, 19)
    return data


def convert_019_100(data):
    data["version"] = (1, 0, 0)
    return data


def convert_100_200(data):
    data["version"] = (2, 0, 0)
    return data


def _convert_dict_keys(o: Any) -> Any:
    if isinstance(o, dict):
        return {strutils.always_str(k): _convert_dict_keys(v) for k, v in o.items()}
    else:
        return o


def _convert_dict_vals(o: dict, values_to_convert: dict) -> dict:
    for k, v in values_to_convert.items():
        if not o or k not in o:
            continue
        if v is True:
            o[k] = strutils.always_str(o[k])
        else:
            _convert_dict_vals(o[k], v)
    return o


def convert_unicode(data: dict) -> dict:
    """
    This method converts between Python 3 and Python 2 dumpfiles.
    """
    data = _convert_dict_keys(data)
    data = _convert_dict_vals(
        data, {
            "type": True,
            "id": True,
            "request": {
                "first_line_format": True
            },
            "error": {
                "msg": True
            }
        }
    )
    return data


converters = {
    (0, 11): convert_011_012,
    (0, 12): convert_012_013,
    (0, 13): convert_013_014,
    (0, 14): convert_014_015,
    (0, 15): convert_015_016,
    (0, 16): convert_016_017,
    (0, 17): convert_017_018,
    (0, 18): convert_018_019,
    (0, 19): convert_019_100,
    (1, 0): convert_100_200,
}


def migrate_flow(flow_data):
    while True:
        flow_version = tuple(flow_data.get(b"version", flow_data.get("version")))
        if flow_version[:2] == version.IVERSION[:2]:
            break
        elif flow_version[:2] in converters:
            flow_data = converters[flow_version[:2]](flow_data)
        else:
            v = ".".join(str(i) for i in flow_version)
            raise ValueError(
                "{} cannot read files serialized with version {}.".format(version.MITMPROXY, v)
            )
    return flow_data
