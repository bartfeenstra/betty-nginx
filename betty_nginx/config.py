"""Integrate Betty with `nginx <https://nginx.org/>`_."""

from betty.assertion import (
    OptionalField,
    assert_record,
    assert_or,
    assert_bool,
    assert_none,
    assert_setattr,
    assert_str,
)
from betty.config import Configuration
from betty.serde.dump import Dump, DumpMapping
from typing_extensions import override


class NginxConfiguration(Configuration):
    """
    Provide configuration for the :py:class:`betty_nginx.Nginx` extension.
    """

    https: bool | None
    """
    Whether the nginx server should use HTTPS.

    ``True`` to use HTTPS (and HTTP/2), ``False`` to use HTTP (and HTTP 1), ``None`` to let this behavior depend on 
    whether the project's URL uses HTTPS or not.
    """

    legacy_entity_redirects: bool
    """
    Whether to generate redirects from legacy (pre Betty 0.5) entity URLs.
    """

    www_directory_path: str | None
    """
    The nginx server's public web root directory path.
    """

    def __init__(
        self,
        *,
        www_directory_path: str | None = None,
        https: bool | None = None,
        legacy_entity_redirects: bool = False,
    ):
        super().__init__()
        self.https = https
        self.www_directory_path = www_directory_path
        self.legacy_entity_redirects = legacy_entity_redirects

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            OptionalField(
                "https",
                assert_or(assert_none(), assert_bool()) | assert_setattr(self, "https"),
            ),
            OptionalField(
                "www_directory",
                assert_str() | assert_setattr(self, "www_directory_path"),
            ),
            OptionalField(
                "legacy_entity_redirects",
                assert_bool() | assert_setattr(self, "legacy_entity_redirects"),
            ),
        )(dump)

    @override
    def dump(self) -> Dump:
        dump: DumpMapping[Dump] = {
            "https": self.https,
        }
        if self.legacy_entity_redirects:
            dump["legacy_entity_redirects"] = True
        if self.www_directory_path is not None:
            dump["www_directory"] = str(self.www_directory_path)
        return dump
