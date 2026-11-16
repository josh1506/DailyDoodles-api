from whitenoise.storage import CompressedManifestStaticFilesStorage


class ProductionStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Omit debugging source maps that vendor packages may not distribute."""

    def url_converter(self, name, hashed_files, template=None):
        if template in (
            "/*# sourceMappingURL=%(url)s */",
            "//# sourceMappingURL=%(url)s",
        ):
            return lambda match: ""
        return super().url_converter(name, hashed_files, template)
