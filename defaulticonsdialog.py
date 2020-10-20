# -*- coding: utf-8 -*-

import os
from functools import partial

from PyQt5.QtCore import QResource, Qt, QSettings, QSize, QModelIndex
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QDialog,
    QToolButton,
    QAction,
    QLabel,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QFontDialog,
)

from qgis.core import Qgis, QgsLayerTree
from qgis.utils import iface

from .resourcebrowserimpl import ResourceBrowser


class DefaultIconsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = QSettings()
        self.settings.beginGroup("plugins/layertreeicons")

        self.setWindowTitle(self.tr("Default layer tree properties"))
        self.setMinimumSize(QSize(250, 0))
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        hlayout = QHBoxLayout()
        self.group_font_label = QLabel("")
        group_font_button = QToolButton(self)
        group_font_button.setText("...")
        hlayout.addWidget(self.group_font_label)
        hlayout.addWidget(group_font_button)
        form_layout.addRow(self.tr("Group node font"), hlayout)
        group_font_button.setToolTip("Select font")
        group_font_button.clicked.connect(self.select_group_font)

        hlayout = QHBoxLayout()
        self.layer_font_label = QLabel("")
        layer_font_button = QToolButton(self)
        layer_font_button.setText("...")
        hlayout.addWidget(self.layer_font_label)
        hlayout.addWidget(layer_font_button)
        form_layout.addRow(self.tr("Layer node font"), hlayout)
        layer_font_button.setToolTip("Select font")
        layer_font_button.clicked.connect(self.select_layer_font)

        self.icon_size_combo = QComboBox(self)
        self.icon_size_combo.addItem(self.tr("default"), -1)
        for val in (16, 24, 32, 48, 64):
            self.icon_size_combo.addItem(f"{val} px", val)

        idx = self.icon_size_combo.findData(self.settings.value("iconsize", -1, int))
        self.icon_size_combo.setCurrentIndex(idx)
        self.icon_size_combo.currentIndexChanged.connect(self.on_icon_size_changed)

        form_layout.addRow(self.tr("Icon Size"), self.icon_size_combo)

        layout.addLayout(form_layout)
        group_box = QGroupBox(self)
        group_box.setTitle("Default Icons")
        self.form_layout = QFormLayout(group_box)
        layout.addWidget(group_box)
        self.reset_button = QPushButton(self.tr("Reset default icons"))
        layout.addWidget(self.reset_button)

        self.reset_button.clicked.connect(self.reset_all)

        self.resource_browser = ResourceBrowser(parent)

        self.source_data = {
            "group": (self.tr("Group"), ":/images/themes/default/mActionFolder.svg",),
            "raster": (self.tr("Raster"), ":/images/themes/default/mIconRaster.svg",),
            "point": (self.tr("Point"), ":/images/themes/default/mIconPointLayer.svg",),
            "line": (self.tr("Line"), ":/images/themes/default/mIconLineLayer.svg",),
            "polygon": (
                self.tr("Polygon"),
                ":/images/themes/default/mIconPolygonLayer.svg",
            ),
            "nogeometry": (
                self.tr("No Geometry"),
                ":/images/themes/default/mIconTableLayer.svg",
            ),
        }

        if Qgis.QGIS_VERSION_INT > 30200:

            self.source_data["mesh"] = (
                self.tr("Mesh Layer"),
                ":/images/themes/default/mIconMeshLayer.svg",
            )

        for settings_key, (text, default_icon) in self.source_data.items():

            button = QToolButton(self)
            button.setObjectName(settings_key)
            button.setPopupMode(QToolButton.MenuButtonPopup)
            button.setIconSize(QSize(24, 24))
            button.setIcon(QIcon(default_icon))
            label = QLabel(text, self)
            label.setMinimumSize(QSize(label.minimumSize().width(), 38))
            self.form_layout.addRow(label, button)

            action_from_qgis = QAction("Set from QGIS ressources", button)
            action_from_qgis.triggered.connect(
                partial(self.set_icon_from_ressources, settings_key)
            )
            button.addAction(action_from_qgis)
            button.clicked.connect(action_from_qgis.trigger)

            action_from_file = QAction("Set from file", button)
            action_from_file.triggered.connect(
                partial(self.set_icon_from_file, settings_key)
            )
            button.addAction(action_from_file)

            action_reset = QAction("Reset", button)
            action_reset.triggered.connect(partial(self.reset, settings_key))
            button.addAction(action_reset)

        f = QFont()
        if f.fromString(self.settings.value("defaulticons/group_font")) and f.family():
            iface.layerTreeView().model().setLayerTreeNodeFont(
                QgsLayerTree.NodeGroup, f
            )
        f = QFont()
        if f.fromString(self.settings.value("defaulticons/layer_font")) and f.family():
            iface.layerTreeView().model().setLayerTreeNodeFont(
                QgsLayerTree.NodeLayer, f
            )
        self.update_font_labels()

    def set_icon_from_ressources(self, settings_key):
        res = self.resource_browser.exec()
        if res == QDialog.Accepted:
            button = self.findChild(QToolButton, settings_key)
            button.setIcon(QIcon(self.resource_browser.icon))
            self.settings.setValue(
                f"defaulticons/{settings_key}", self.resource_browser.icon
            )
        iface.layerTreeView().model().dataChanged.emit(QModelIndex(), QModelIndex())

    def set_icon_from_file(self, settings_key):

        iconpath = self.settings.value("iconpath", "")
        icon, _ = QFileDialog.getOpenFileName(
            caption=self.tr("Select Icon"),
            filter=self.tr("Image Files (*.svg *.png *.gif);;All files (*)"),
            directory=iconpath,
        )
        if not icon:
            return

        button = self.findChild(QToolButton, settings_key)
        button.setIcon(QIcon(icon))
        self.settings.setValue(f"defaulticons/{settings_key}", icon)
        iface.layerTreeView().model().dataChanged.emit(QModelIndex(), QModelIndex())

    def reset(self, settings_key):
        button = self.findChild(QToolButton, settings_key)
        button.setIcon(QIcon(self.source_data[settings_key][1]))
        self.settings.setValue(f"defaulticons/{settings_key}", "")
        iface.layerTreeView().model().dataChanged.emit(QModelIndex(), QModelIndex())

    def reset_all(self):
        for settings_key, (_, default_icon) in self.source_data.items():
            button = self.findChild(QToolButton, settings_key)
            button.setIcon(QIcon(default_icon))
            self.settings.setValue(f"defaulticons/{settings_key}", "")
        iface.layerTreeView().model().dataChanged.emit(QModelIndex(), QModelIndex())
        self.icon_size_combo.setCurrentIndex(0)

    def on_icon_size_changed(self):
        val = self.icon_size_combo.currentData()
        iface.layerTreeView().setIconSize(QSize(val, val))
        self.settings.setValue("iconsize", val)

    def select_group_font(self):

        dialog = QFontDialog(iface.mainWindow())
        dialog.setCurrentFont(
            iface.layerTreeView().model().layerTreeNodeFont(QgsLayerTree.NodeGroup)
        )
        res = dialog.exec()
        if res != QDialog.Accepted:
            return

        iface.layerTreeView().model().setLayerTreeNodeFont(
            QgsLayerTree.NodeGroup, dialog.currentFont()
        )
        self.update_font_labels()
        self.settings.setValue(
            f"defaulticons/group_font", dialog.currentFont().toString()
        )
        dialog.deleteLater()

    def select_layer_font(self):

        dialog = QFontDialog(iface.mainWindow())
        dialog.setCurrentFont(
            iface.layerTreeView().model().layerTreeNodeFont(QgsLayerTree.NodeLayer)
        )
        res = dialog.exec()
        if res != QDialog.Accepted:
            return

        iface.layerTreeView().model().setLayerTreeNodeFont(
            QgsLayerTree.NodeLayer, dialog.currentFont()
        )
        self.update_font_labels()
        self.settings.setValue(
            f"defaulticons/layer_font", dialog.currentFont().toString()
        )
        dialog.deleteLater()

    def update_font_labels(self):
        layer_font = (
            iface.layerTreeView().model().layerTreeNodeFont(QgsLayerTree.NodeLayer)
        )
        self.layer_font_label.setText(
            f"{layer_font.family()}, {layer_font.pointSize()}"
        )
        self.layer_font_label.setFont(layer_font)

        group_font = (
            iface.layerTreeView().model().layerTreeNodeFont(QgsLayerTree.NodeGroup)
        )
        self.group_font_label.setText(
            f"{group_font.family()}, {group_font.pointSize()}"
        )
        self.group_font_label.setFont(group_font)
