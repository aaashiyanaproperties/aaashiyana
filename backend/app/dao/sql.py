from pathlib import Path


class SqlProperties:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(__file__).with_name("sql.properties")
        self._statements = self._load()

    def _load(self) -> dict[str, str]:
        statements: dict[str, str] = {}
        current_key: str | None = None
        current_value = ""

        for raw_line in self.path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("#", "!")):
                continue
            if line.endswith("\\"):
                line = line[:-1].rstrip()
                if current_key is None:
                    key, separator, value = line.partition("=")
                    if not separator:
                        raise ValueError(f"Invalid SQL property in {self.path}: {raw_line}")
                    current_key = key.strip()
                    current_value = value.strip()
                else:
                    current_value += " " + line
                continue
            if current_key is not None:
                current_value += " " + line
                statements[current_key] = current_value.strip()
                current_key = None
                current_value = ""
                continue
            key, separator, value = line.partition("=")
            if not separator:
                raise ValueError(f"Invalid SQL property in {self.path}: {raw_line}")
            statements[key.strip()] = value.strip()

        if current_key is not None:
            raise ValueError(f"Unterminated SQL property '{current_key}' in {self.path}")
        return statements

    def get(self, key: str) -> str:
        try:
            return self._statements[key]
        except KeyError as exc:
            raise KeyError(f"SQL statement '{key}' is not defined in {self.path}") from exc


sql_properties = SqlProperties()
