"""Pruebas unitarias para validar la existencia y consistencia de artefactos de Origin."""

from __future__ import annotations

from pathlib import Path

from automations.inventario_funciones import resolver_raiz

BASE_DIR = resolver_raiz(Path(__file__))
DOCS = BASE_DIR / "docs"


class TestArtefactosOrigin:
    def test_skills_y_prompts_existen(self):
        skill_c = BASE_DIR / ".cursor" / "skills" / "analisis-complejidad" / "SKILL.md"
        skill_h = BASE_DIR / ".cursor" / "skills" / "hotspots-propuestas" / "SKILL.md"
        prompt_c = DOCS / "prompts-origin" / "complejidad-temporal.txt"
        prompt_h = DOCS / "prompts-origin" / "hotspots-propuestas.txt"
        guia = DOCS / "automatizaciones-origin.md"
        for ruta in (skill_c, skill_h, prompt_c, prompt_h, guia):
            assert ruta.is_file(), ruta
            contenido = ruta.read_text(encoding="utf-8")
            assert "automations.ejecutar" in contenido
            assert "español" in contenido.lower() or "Español" in contenido

    def test_prompts_prohíben_aplicar_codigo(self):
        prompt = (DOCS / "prompts-origin" / "hotspots-propuestas.txt").read_text(encoding="utf-8")
        assert "NO apliques" in prompt or "No apliques" in prompt
        assert "src/" in prompt
