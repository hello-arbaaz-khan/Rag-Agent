from dataclasses import dataclass
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode


@dataclass
class StructuralUnit:
    unit_type: str
    content: str
    level: int = 0
    language: str | None = None
    metadata: dict[str, str] | None = None


class MarkdownParser:
    def __init__(self) -> None:
        self.parser = MarkdownIt("commonmark").enable("table")

    def parse(self, content: str) -> list[StructuralUnit]:
        if not content or not content.strip():
            return []

        tokens = self.parser.parse(content)
        root = SyntaxTreeNode(tokens)
        units: list[StructuralUnit] = []
        self._parse_children(root, units)
        return units



    def _parse_children(
        self, node: SyntaxTreeNode, units: list[StructuralUnit]
    ) -> None:
        for child in node.children:
            if child.type == "heading":
                content = self._node_text(child).strip()
                if content:
                    level = int(child.tag[1:]) if child.tag and len(child.tag) > 1 else 0
                    units.append(
                        StructuralUnit(
                            unit_type="heading",
                            content=content,
                            level=level,
                        )
                    )

            elif child.type == "paragraph":
                content = self._node_text(child).strip()
                if content:
                    units.append(
                        StructuralUnit(
                            unit_type="paragraph",
                            content=content,
                        )
                    )

            elif child.type in {"bullet_list", "ordered_list"}:
                content = self._render_list(child).strip()
                if content:
                    units.append(
                        StructuralUnit(
                            unit_type="list",
                            content=content,
                        )
                    )

            elif child.type == "table":
                content = self._render_table(child).strip()
                if content:
                    units.append(
                        StructuralUnit(
                            unit_type="table",
                            content=content,
                        )
                    )

            elif child.type == "fence":
                content = child.content.strip()
                if content:
                    units.append(
                        StructuralUnit(
                            unit_type="code",
                            content=content,
                            language=child.info.strip() or None,
                        )
                    )

            elif child.type == "code_block":
                content = child.content.strip()
                if content:
                    units.append(
                        StructuralUnit(
                            unit_type="code",
                            content=content,
                        )
                    )

            else:
                self._parse_children(child, units)

    def _render_list(self, node: SyntaxTreeNode, indent: int = 0) -> str:
        items: list[str] = []
        prefix = "  " * indent + "- "

        for item in node.children:
            if item.type != "list_item":
                continue

            item_parts: list[str] = []
            for child in item.children:
                if child.type in {"bullet_list", "ordered_list"}:
                    nested = self._render_list(child, indent + 1)
                    if nested:
                        item_parts.append(nested)
                else:
                    text = self._node_text(child).strip()
                    if text:
                        item_parts.append(text)

            if item_parts:
                first_line = f"{prefix}{item_parts[0]}"
                rest = item_parts[1:]
                items.append("\n".join([first_line] + rest))

        return "\n".join(items)

    def _render_table(self, node: SyntaxTreeNode) -> str:
        rows: list[list[str]] = []

        for child in node.children:
            if child.type in {"thead", "tbody"}:
                rows.extend(self._extract_table_rows(child))

        if not rows:
            return self._node_text(node)

        lines = ["| " + " | ".join(row) + " |" for row in rows]

        if rows:
            separator = "| " + " | ".join("---" for _ in rows[0]) + " |"
            lines.insert(1, separator)

        return "\n".join(lines)

    def _extract_table_rows(self, section: SyntaxTreeNode) -> list[list[str]]:
        rows: list[list[str]] = []

        for row in section.children:
            if row.type != "tr":
                continue

            cells: list[str] = []
            for cell in row.children:
                if cell.type in {"th", "td"}:
                    cells.append(self._node_text(cell).strip())

            if cells:
                rows.append(cells)

        return rows

    def _node_text(self, node: SyntaxTreeNode) -> str:
        if node.type == "inline":
            return node.content

        parts: list[str] = []
        for child in node.children:
            text = self._node_text(child)
            if text:
                parts.append(text)

        return " ".join(parts) if node.type != "inline" else "\n".join(parts)


@dataclass
class SplitterConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 100


class ChunkSplitter:
    def __init__(self, config: SplitterConfig | None = None) -> None:
        self.config = config or SplitterConfig()

        if self.config.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.config.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if self.config.chunk_overlap >= self.config.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

    def split(self, units: list[StructuralUnit]) -> list[str]:
        chunks: list[str] = []
        current_units: list[StructuralUnit] = []
        current_size = 0

        for unit in units:
            content = unit.content.strip()
            if not content:
                continue

            unit_size = len(content)
            separator_size = 2 if current_units else 0

            # Unit alone exceeds chunk size - push immediately
            if unit_size > self.config.chunk_size:
                if current_units:
                    chunks.append(self._join_units(current_units))
                    current_units = []
                    current_size = 0
                chunks.append(content)
                continue

            # Standard overflow check
            if (
                current_units
                and current_size + separator_size + unit_size > self.config.chunk_size
            ):
                chunks.append(self._join_units(current_units))

                # Retain overlapping units based on chunk_overlap size
                overlap_units: list[StructuralUnit] = []
                overlap_size = 0

                for prev in reversed(current_units):
                    p_len = len(prev.content.strip())
                    if overlap_size + p_len <= self.config.chunk_overlap:
                        overlap_units.insert(0, prev)
                        overlap_size += p_len + 2
                    else:
                        break

                current_units = overlap_units
                current_size = sum(len(u.content.strip()) for u in current_units)

            current_units.append(unit)
            current_size += unit_size + (2 if len(current_units) > 1 else 0)

        if current_units:
            chunks.append(self._join_units(current_units))

        return chunks

    def _join_units(self, units: list[StructuralUnit]) -> str:
        return "\n\n".join(unit.content.strip() for unit in units if unit.content.strip())