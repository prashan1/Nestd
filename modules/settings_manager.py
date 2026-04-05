import json
from pathlib import Path

DEFAULT_SETTINGS = {
    "root_folder": "",
    "theme": "dark",
    "last_path": "",
    "include_date": True,
    "last_doc_type": "",
}

DEFAULT_DOC_TYPES = [
    "GST_Return",
    "GST_Annual_Return",
    "GSTR_3B",
    "GSTR_9",
    "GST_Notice_Reply",
    "ITR_1",
    "ITR_3",
    "ITR_4",
    "ITR_6",
    "Balance_Sheet",
    "Profit_Loss",
    "Audit_Report",
    "TDS_Return",
    "Form_26AS",
    "Tax_Computation",
]


class SettingsManager:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.settings_path = config_dir / "settings.json"
        self.doc_types_path = config_dir / "document_types.json"
        self.settings: dict = {}
        self.doc_types: list = []
        self._load()

    def _load(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)

        if self.settings_path.exists():
            try:
                with open(self.settings_path) as f:
                    loaded = json.load(f)
                self.settings = {**DEFAULT_SETTINGS, **loaded}
            except Exception:
                self.settings = DEFAULT_SETTINGS.copy()
        else:
            self.settings = DEFAULT_SETTINGS.copy()

        if self.doc_types_path.exists():
            try:
                with open(self.doc_types_path) as f:
                    self.doc_types = json.load(f)
            except Exception:
                self.doc_types = DEFAULT_DOC_TYPES.copy()
                self._save_doc_types()
        else:
            self.doc_types = DEFAULT_DOC_TYPES.copy()
            self._save_doc_types()

    def save(self):
        with open(self.settings_path, "w") as f:
            json.dump(self.settings, f, indent=2)

    def _save_doc_types(self):
        with open(self.doc_types_path, "w") as f:
            json.dump(self.doc_types, f, indent=2)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()
