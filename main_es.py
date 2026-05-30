from __future__ import annotations

from main import PdfToolkitApp, create_root


TEXT_ES = {
    "app_title": "Kit PDF",
    "subtitle": "Unir, dividir, extraer y rotar archivos PDF",
    "files": "PDF seleccionados",
    "file_count": "{count} archivo(s) seleccionado(s)",
    "add": "Agregar PDF",
    "add_one": "Elegir PDF",
    "remove": "Quitar",
    "clear": "Limpiar",
    "move_up": "Subir",
    "move_down": "Bajar",
    "drop": "Suelta archivos PDF aqui",
    "drag_ready": "Arrastrar y soltar esta activado",
    "drag_missing": "Instala tkinterdnd2 para arrastrar y soltar",
    "preview": "Vista previa",
    "no_files": "No hay archivos seleccionados",
    "select_hint": "Selecciona una fila para quitarla o cambiar su orden.",
    "name": "Nombre",
    "pages": "Paginas",
    "size": "Tamano",
    "path": "Ruta",
    "merge": "Unir",
    "split": "Dividir por rango",
    "extract": "Extraer paginas",
    "rotate": "Rotar",
    "page_range": "Paginas",
    "page_hint": "Ejemplo: 1-3,5",
    "degrees": "Grados",
    "all_pages": "Todas las paginas",
    "all_pages_if_blank": "Todas las paginas si queda vacio",
    "selected_pages": "Paginas seleccionadas",
    "process": "Procesar",
    "ready": "Listo",
    "working": "Procesando...",
    "done": "Completado",
    "success": "PDF creado:\n{path}",
    "error": "Error",
    "pick_files": "Elegir archivos PDF",
    "pick_file": "Elige un archivo PDF",
    "save_as": "Guardar PDF de salida",
    "default_merge": "unido.pdf",
    "default_split": "dividido.pdf",
    "default_extract": "paginas_extraidas.pdf",
    "default_rotate": "rotado.pdf",
    "merge_help": "Combina los PDF seleccionados en el orden mostrado.",
    "single_help": "Elige un PDF y luego ingresa las paginas a procesar.",
    "rotate_help": "Deja las paginas en blanco para rotar todo el PDF.",
}


def main() -> None:
    root = create_root()
    PdfToolkitApp(root, TEXT_ES)
    root.mainloop()


if __name__ == "__main__":
    main()
