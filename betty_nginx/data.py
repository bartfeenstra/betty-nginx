"""Integrate Betty with `nginx <https://nginx.org/>`_."""

from typing import final

from betty.data import Data
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.bool import BoolDefinition
from betty.data.str import StrDefinition
from betty.locale.localizable.gettext import _
from betty.property import Optional, Property


@final
@ObjectDefinition(
    label=_("Nginx configuration"),
)
class NginxConfiguration(Data):
    """
    Provide configuration for the :py:class:`betty_nginx.Nginx` extension.
    """

    https = Optional(
        Property(
            BoolDefinition(label="HTTPS"),
            omit_load=True,
            omit_dump=lambda data: data is None,
        )
    )
    """
    Whether the nginx server should use HTTPS.

    ``True`` to use HTTPS (and HTTP/2), ``False`` to use HTTP (and HTTP 1), ``None`` to let this behavior depend on 
    whether the project's URL uses HTTPS or not.
    """

    legacy_entity_redirects = Property(
        BoolDefinition(label=_("Legacy entity redirects")),
        omit_load=True,
        omit_dump=lambda data: data is False,
    )
    """
    Whether to generate redirects from legacy (pre Betty 0.5) entity URLs.
    """

    www_directory = Optional(
        Property(
            StrDefinition(
                label=_("WWW directory"),
            ),
            omit_load=True,
            omit_dump=lambda data: data is None,
        )
    )
    """
    The nginx server's public web root directory path.
    """

    def __init__(
        self,
        *,
        www_directory: str | None = None,
        https: bool | None = None,
        legacy_entity_redirects: bool = False,
    ):
        super().__init__()
        self.https = https
        self.www_directory = www_directory
        self.legacy_entity_redirects = legacy_entity_redirects
