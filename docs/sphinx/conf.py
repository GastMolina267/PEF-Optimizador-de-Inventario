"""Configuración de Sphinx para la documentación de Optimizador de Inventario y Pedidos."""

from __future__ import annotations

import os
import sys

# Agregar la raíz del repositorio a sys.path para autodoc
sys.path.insert(0, os.path.abspath("../.."))

# Metadatos del proyecto
project = "Optimizador de Inventario y Pedidos"
copyright = "2026, Programación Eficiente — Universidad Blas Pascal"
author = "Gastón Molina, Edgar"
release = "2.0.0"

# Idioma y sufijos de archivo
language = "es"
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Extensiones de Sphinx
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

# Configuración de Napoleon para Google Style con secciones en español
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_attr_annotations = True
napoleon_custom_sections = [
    ("Argumentos", "params_style"),
    ("Retorna", "returns_style"),
    ("Lanza", "raises_style"),
    ("Ejemplo", "admonition"),
    ("Nota", "admonition"),
]

# Configuración de MyST Parser
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "html_admonition",
    "html_image",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3

# Supresión de advertencias toleradas para archivos Markdown incluidos y bloques mermaid
suppress_warnings = [
    "myst.header",
    "myst.xref_missing",
    "misc.highlighting_failure",
]

# Configuración de Autodoc
autodoc_mock_imports = [
    "flet",
    "flet_desktop",
    "flet.core",
    "flet.core.control",
    "flet.core.page",
]
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# Tema visual y opciones HTML
html_theme = "furo"
html_title = "Optimizador de Inventario y Pedidos v2.0"
html_static_path = ["_static"]

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "light_css_variables": {
        "color-brand-primary": "#2563EB",
        "color-brand-content": "#1D4ED8",
    },
    "dark_css_variables": {
        "color-brand-primary": "#3B82F6",
        "color-brand-content": "#60A5FA",
    },
}
