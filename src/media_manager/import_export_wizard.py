"""Wizard dialogs for importing and exporting media metadata."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from .import_export_service import (
    ExportFormat,
    ExportOptions,
    ImportConflict,
    ImportExportService,
    ImportOptions,
    MergeStrategy,
)
from .logging import get_logger
from .persistence.repositories import LibraryRepository


class ExportWizard(QWizard):
    """Wizard for exporting media metadata."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._service = ImportExportService()
        self._library_repo = LibraryRepository()

        self.setWindowTitle("导出媒体元数据")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(600, 500)

        # Add wizard pages
        self.addPage(ExportFormatPage(self))
        self.addPage(ExportScopePage(self._library_repo, self))
        self.addPage(ExportFieldsPage(self))
        self.addPage(ExportProgressPage(self._service, self))

        self._logger.info("Export wizard initialized")


class ExportFormatPage(QWizardPage):
    """Page for selecting export format and destination."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle("导出格式")
        self.setSubTitle("选择导出格式和目标文件。")

        layout = QVBoxLayout()

        # Format selection
        format_group = QGroupBox("导出格式")
        format_layout = QVBoxLayout()

        self.json_radio = QRadioButton("JSON")
        self.json_radio.setChecked(True)
        self.excel_radio = QRadioButton("Excel (XLSX)")

        format_layout.addWidget(self.json_radio)
        format_layout.addWidget(self.excel_radio)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # File path selection
        file_group = QGroupBox("目标文件")
        file_layout = QHBoxLayout()

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择目标文件...")
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_file)

        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_button)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        layout.addStretch()
        self.setLayout(layout)

        # Register fields
        self.registerField("export_format", self, "format")
        self.registerField("export_file_path*", self.file_path_edit)

    def _browse_file(self) -> None:
        """Open file dialog to choose destination."""
        format_filter = (
            "JSON Files (*.json)"
            if self.json_radio.isChecked()
            else "Excel Files (*.xlsx)"
        )
        default_ext = ".json" if self.json_radio.isChecked() else ".xlsx"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存导出文件",
            "",
            format_filter,
        )

        if file_path:
            if not file_path.endswith(default_ext):
                file_path += default_ext
            self.file_path_edit.setText(file_path)

    @property
    def format(self) -> str:
        """Get selected export format."""
        return "json" if self.json_radio.isChecked() else "excel"


class ExportScopePage(QWizardPage):
    """Page for selecting export scope (libraries, media types, date range)."""

    def __init__(
        self, library_repo: LibraryRepository, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._library_repo = library_repo
        self.setTitle("导出范围")
        self.setSubTitle("选择要导出的项目。")

        layout = QVBoxLayout()

        # Library selection
        library_group = QGroupBox("媒体库")
        library_layout = QVBoxLayout()

        self.all_libraries_check = QCheckBox("所有媒体库")
        self.all_libraries_check.setChecked(True)
        self.all_libraries_check.toggled.connect(self._on_all_libraries_toggled)
        library_layout.addWidget(self.all_libraries_check)

        self.library_list = QListWidget()
        self.library_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.library_list.setEnabled(False)
        library_layout.addWidget(self.library_list)

        library_group.setLayout(library_layout)
        layout.addWidget(library_group)

        # Media type selection
        media_type_group = QGroupBox("媒体类型")
        media_type_layout = QVBoxLayout()

        self.all_types_check = QCheckBox("所有类型")
        self.all_types_check.setChecked(True)
        self.movie_check = QCheckBox("电影")
        self.tv_check = QCheckBox("电视节目")

        media_type_layout.addWidget(self.all_types_check)
        media_type_layout.addWidget(self.movie_check)
        media_type_layout.addWidget(self.tv_check)

        media_type_group.setLayout(media_type_layout)
        layout.addWidget(media_type_group)

        self.setLayout(layout)

        # Load libraries
        self._load_libraries()

    def _load_libraries(self) -> None:
        """Load available libraries."""
        libraries = self._library_repo.get_all()
        for library in libraries:
            self.library_list.addItem(library.name)
            self.library_list.item(self.library_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, library.id
            )

    def _on_all_libraries_toggled(self, checked: bool) -> None:
        """Handle all libraries checkbox toggle."""
        self.library_list.setEnabled(not checked)

    def get_selected_library_ids(self) -> list[int]:
        """Get selected library IDs."""
        if self.all_libraries_check.isChecked():
            return []

        library_ids = []
        for item in self.library_list.selectedItems():
            library_id = item.data(Qt.ItemDataRole.UserRole)
            if library_id:
                library_ids.append(library_id)
        return library_ids

    def get_selected_media_types(self) -> list[str]:
        """Get selected media types."""
        if self.all_types_check.isChecked():
            return []

        types = []
        if self.movie_check.isChecked():
            types.append("movie")
        if self.tv_check.isChecked():
            types.append("tv")
        return types


class ExportFieldsPage(QWizardPage):
    """Page for selecting which fields to include in export."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle("导出字段")
        self.setSubTitle("选择要包含在导出中的数据。")

        layout = QVBoxLayout()

        fields_group = QGroupBox("包含在导出中")
        fields_layout = QVBoxLayout()

        self.include_files_check = QCheckBox("文件路径")
        self.include_files_check.setChecked(True)

        self.include_external_ids_check = QCheckBox("外部 ID（TMDB、IMDB、TVDB）")
        self.include_external_ids_check.setChecked(True)

        self.include_artwork_check = QCheckBox("艺术作品路径")
        self.include_artwork_check.setChecked(True)

        self.include_subtitles_check = QCheckBox("字幕路径")
        self.include_subtitles_check.setChecked(True)

        fields_layout.addWidget(self.include_files_check)
        fields_layout.addWidget(self.include_external_ids_check)
        fields_layout.addWidget(self.include_artwork_check)
        fields_layout.addWidget(self.include_subtitles_check)

        fields_group.setLayout(fields_layout)
        layout.addWidget(fields_group)

        layout.addStretch()
        self.setLayout(layout)


class ExportProgressPage(QWizardPage):
    """Page showing export progress and results."""

    def __init__(
        self, service: ImportExportService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._service = service
        self.setTitle("导出进度")
        self.setSubTitle("正在导出媒体元数据...")

        layout = QVBoxLayout()

        self.status_label = QLabel("准备导出")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        self.setLayout(layout)

    def initializePage(self) -> None:
        """Initialize page and start export."""
        wizard = self.wizard()
        if not wizard:
            return

        # Get export options
        format_str = wizard.field("export_format")
        file_path = Path(wizard.field("export_file_path"))

        scope_page = wizard.page(1)
        fields_page = wizard.page(2)

        options = ExportOptions(
            format=ExportFormat.JSON if format_str == "json" else ExportFormat.EXCEL,
            library_ids=scope_page.get_selected_library_ids(),
            media_types=scope_page.get_selected_media_types(),
            include_files=fields_page.include_files_check.isChecked(),
            include_external_ids=fields_page.include_external_ids_check.isChecked(),
            include_artwork=fields_page.include_artwork_check.isChecked(),
            include_subtitles=fields_page.include_subtitles_check.isChecked(),
        )

        # Perform export
        try:
            count = self._service.export_to_file(file_path, options, self._on_progress)
            self.status_label.setText(f"导出完成：{count} 项")
            self.result_text.append(f"成功导出 {count} 项到 {file_path}")
        except Exception as e:
            self.status_label.setText("导出失败")
            self.result_text.append(f"错误：{str(e)}")

    def _on_progress(self, current: int, total: int, message: str) -> None:
        """Handle progress updates."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)


class ImportWizard(QWizard):
    """Wizard for importing media metadata."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._service = ImportExportService()
        self._library_repo = LibraryRepository()

        self.setWindowTitle("导入媒体元数据")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(700, 600)

        # Add wizard pages
        self.addPage(ImportFilePage(self._service, self))
        self.addPage(ImportMappingPage(self._service, self))
        self.addPage(ImportConflictsPage(self._service, self))
        self.addPage(ImportOptionsPage(self._library_repo, self))
        self.addPage(ImportProgressPage(self._service, self))

        self._logger.info("Import wizard initialized")


class ImportFilePage(QWizardPage):
    """Page for selecting import file."""

    def __init__(
        self, service: ImportExportService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._service = service
        self.setTitle("导入文件")
        self.setSubTitle("选择要导入的文件。")

        layout = QVBoxLayout()

        file_group = QGroupBox("源文件")
        file_layout = QHBoxLayout()

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择要导入的文件...")
        self.file_path_edit.textChanged.connect(self._on_file_changed)

        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_file)

        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_button)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Preview
        preview_group = QGroupBox("文件预览")
        preview_layout = QVBoxLayout()

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)

        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        layout.addStretch()
        self.setLayout(layout)

        self.registerField("import_file_path*", self.file_path_edit)

    def _browse_file(self) -> None:
        """Open file dialog to choose import file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开导入文件",
            "",
            "所有支持的文件 (*.json *.xlsx *.xls);;JSON 文件 (*.json);;Excel 文件 (*.xlsx *.xls)",
        )

        if file_path:
            self.file_path_edit.setText(file_path)

    def _on_file_changed(self, file_path: str) -> None:
        """Handle file path change."""
        if not file_path or not Path(file_path).exists():
            self.preview_text.clear()
            return

        try:
            path = Path(file_path)
            if path.suffix.lower() == ".json":
                with open(path, encoding="utf-8") as f:
                    content = f.read(1000)
                    self.preview_text.setPlainText(content)
            elif path.suffix.lower() in (".xlsx", ".xls"):
                headers = self._service.get_excel_headers(path)
                self.preview_text.setPlainText(
                    f"Excel file with columns:\n{', '.join(headers)}"
                )
        except Exception as e:
            self.preview_text.setPlainText(f"读取文件出错：{str(e)}")


class ImportMappingPage(QWizardPage):
    """Page for mapping columns (for Excel imports)."""

    def __init__(
        self, service: ImportExportService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._service = service
        self.setTitle("列映射")
        self.setSubTitle("将导入文件中的列映射到数据库字段。")

        layout = QVBoxLayout()

        info_label = QLabel("将文件中的列映射到预期字段：")
        layout.addWidget(info_label)

        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["文件列", "映射到"])
        layout.addWidget(self.mapping_table)

        self.setLayout(layout)

    def initializePage(self) -> None:
        """Initialize page with column mappings."""
        wizard = self.wizard()
        if not wizard:
            return

        file_path = Path(wizard.field("import_file_path"))
        if file_path.suffix.lower() not in (".xlsx", ".xls"):
            # Skip mapping for JSON files
            return

        # Load Excel headers
        try:
            headers = self._service.get_excel_headers(file_path)
            self.mapping_table.setRowCount(len(headers))

            expected_fields = [
                "title",
                "media_type",
                "year",
                "season",
                "episode",
                "description",
                "genres",
                "runtime",
                "rating",
                "library_id",
            ]

            for row, header in enumerate(headers):
                # Source column (read-only)
                source_item = QTableWidgetItem(header)
                source_item.setFlags(source_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mapping_table.setItem(row, 0, source_item)

                # Target field (combo box)
                target_combo = QComboBox()
                target_combo.addItem("（跳过）")
                target_combo.addItems(expected_fields)

                # Auto-detect mapping
                header_lower = header.lower().replace(" ", "_")
                if header_lower in expected_fields:
                    target_combo.setCurrentText(header_lower)

                self.mapping_table.setCellWidget(row, 1, target_combo)

            self.mapping_table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取文件失败：{str(e)}")

    def get_column_mapping(self) -> dict[str, str]:
        """Get the column mapping dictionary."""
        mapping = {}
        for row in range(self.mapping_table.rowCount()):
            source = self.mapping_table.item(row, 0)
            target_widget = self.mapping_table.cellWidget(row, 1)

            if source and isinstance(target_widget, QComboBox):
                target = target_widget.currentText()
                if target != "（跳过）":
                    mapping[source.text()] = target

        return mapping


class ImportConflictsPage(QWizardPage):
    """Page for previewing and handling conflicts."""

    def __init__(
        self, service: ImportExportService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._conflicts: list[ImportConflict] = []

        self.setTitle("冲突检测")
        self.setSubTitle("在导入前查看潜在冲突。")

        layout = QVBoxLayout()

        self.status_label = QLabel("正在分析导入数据...")
        layout.addWidget(self.status_label)

        self.conflicts_table = QTableWidget()
        self.conflicts_table.setColumnCount(4)
        self.conflicts_table.setHorizontalHeaderLabels(
            ["Row", "Title", "Conflict Type", "Details"]
        )
        layout.addWidget(self.conflicts_table)

        self.setLayout(layout)

    def initializePage(self) -> None:
        """Initialize page and detect conflicts."""
        wizard = self.wizard()
        if not wizard:
            return

        file_path = Path(wizard.field("import_file_path"))
        mapping_page = wizard.page(1)

        column_mapping = None
        if file_path.suffix.lower() in (".xlsx", ".xls"):
            column_mapping = mapping_page.get_column_mapping()

        try:
            data, conflicts = self._service.preview_import(file_path, column_mapping)
            self._conflicts = conflicts

            if conflicts:
                self.status_label.setText(f"发现 {len(conflicts)} 个潜在冲突")
                self.conflicts_table.setRowCount(len(conflicts))

                for row, conflict in enumerate(conflicts):
                    self.conflicts_table.setItem(
                        row, 0, QTableWidgetItem(str(conflict.row_index))
                    )
                    self.conflicts_table.setItem(
                        row, 1, QTableWidgetItem(conflict.title)
                    )
                    self.conflicts_table.setItem(
                        row, 2, QTableWidgetItem(conflict.conflict_type)
                    )
                    self.conflicts_table.setItem(
                        row, 3, QTableWidgetItem(conflict.details)
                    )

                self.conflicts_table.resizeColumnsToContents()
            else:
                self.status_label.setText("未检测到冲突。准备导入。")
                self.conflicts_table.setRowCount(0)

        except Exception as e:
            self.status_label.setText(f"分析导入时出错：{str(e)}")


class ImportOptionsPage(QWizardPage):
    """Page for selecting import options."""

    def __init__(
        self, library_repo: LibraryRepository, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._library_repo = library_repo
        self.setTitle("导入选项")
        self.setSubTitle("配置如何处理导入。")

        layout = QVBoxLayout()

        # Target library
        library_group = QGroupBox("目标媒体库")
        library_layout = QFormLayout()

        self.library_combo = QComboBox()
        self._load_libraries()
        library_layout.addRow("媒体库：", self.library_combo)

        library_group.setLayout(library_layout)
        layout.addWidget(library_group)

        # Merge strategy
        strategy_group = QGroupBox("冲突解决")
        strategy_layout = QVBoxLayout()

        self.skip_radio = QRadioButton("跳过现有项目")
        self.skip_radio.setChecked(True)
        self.replace_radio = QRadioButton("替换现有项目")
        self.update_radio = QRadioButton("更新现有项目")

        strategy_layout.addWidget(self.skip_radio)
        strategy_layout.addWidget(self.replace_radio)
        strategy_layout.addWidget(self.update_radio)

        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)

        # Additional options
        options_group = QGroupBox("其他选项")
        options_layout = QVBoxLayout()

        self.validate_files_check = QCheckBox("验证文件路径是否存在")
        self.validate_files_check.setChecked(True)

        self.create_history_check = QCheckBox("创建历史记录事件")
        self.create_history_check.setChecked(True)

        options_layout.addWidget(self.validate_files_check)
        options_layout.addWidget(self.create_history_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        layout.addStretch()
        self.setLayout(layout)

    def _load_libraries(self) -> None:
        """Load available libraries."""
        libraries = self._library_repo.get_all()
        for library in libraries:
            self.library_combo.addItem(library.name, library.id)

    def get_import_options(self) -> ImportOptions:
        """Get configured import options."""
        strategy = MergeStrategy.SKIP
        if self.replace_radio.isChecked():
            strategy = MergeStrategy.REPLACE
        elif self.update_radio.isChecked():
            strategy = MergeStrategy.UPDATE

        return ImportOptions(
            merge_strategy=strategy,
            target_library_id=self.library_combo.currentData(),
            validate_files=self.validate_files_check.isChecked(),
            create_history=self.create_history_check.isChecked(),
        )


class ImportProgressPage(QWizardPage):
    """Page showing import progress and results."""

    def __init__(
        self, service: ImportExportService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._service = service
        self.setTitle("导入进度")
        self.setSubTitle("正在导入媒体元数据...")

        layout = QVBoxLayout()

        self.status_label = QLabel("准备导入")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        self.setLayout(layout)

    def initializePage(self) -> None:
        """Initialize page and start import."""
        wizard = self.wizard()
        if not wizard:
            return

        file_path = Path(wizard.field("import_file_path"))
        mapping_page = wizard.page(1)
        options_page = wizard.page(3)

        column_mapping = None
        if file_path.suffix.lower() in (".xlsx", ".xls"):
            column_mapping = mapping_page.get_column_mapping()

        options = options_page.get_import_options()

        # Perform import
        try:
            result = self._service.import_from_file(
                file_path, options, column_mapping, self._on_progress
            )
            self.status_label.setText("导入完成")
            self.result_text.append(result.to_message())

            if result.errors:
                self.result_text.append("\nErrors:")
                for error in result.errors[:10]:
                    self.result_text.append(f"  - {error}")
                if len(result.errors) > 10:
                    self.result_text.append(f"  ... and {len(result.errors) - 10} more")

        except Exception as e:
            self.status_label.setText("导入失败")
            self.result_text.append(f"错误：{str(e)}")

    def _on_progress(self, current: int, total: int, message: str) -> None:
        """Handle progress updates."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
