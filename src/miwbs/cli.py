"""CLI and Textual entrypoints — zero-point surface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from . import PRODUCT_NAME, format as fmt
from .commands import dispatch
from .db import connect, get_meta, init_schema, migrate_schema
from .history import CommandHistory
from .seed import seed_world
from .world import World

DEFAULT_WORLD = (
    Path(__file__).resolve().parents[2] / "worlds" / "day-of-days.world.db"
)
console = Console(highlight=False)

TUI_BG = "#0a0a0c"
TUI_SURFACE = "#0e0e12"
TUI_PANEL = "#121218"
TUI_BORDER = "#3d3d48"
TUI_BORDER_ACCENT = "#5ec8d8"
TUI_INPUT_BG = "#0c0c10"


def ensure_world(path: Path, reseed: bool = False, seed: str = "mentalor") -> World:
    if reseed and path.exists():
        path.unlink()
    is_new = not path.exists()
    conn = connect(path)
    if is_new or reseed:
        seed_world(conn, flavor=seed)
        console.print(fmt.hint(f"Seeded world ({seed}) · {path}"))
    else:
        init_schema(conn)
        migrate_schema(conn)
    return World(conn)


def run_repl(world: World, world_path: Path) -> None:
    history = CommandHistory()
    session = None
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.history import InMemoryHistory

        class _LinkedPtkHistory(InMemoryHistory):
            def store_string(self, string: str) -> None:  # type: ignore[override]
                history.push(string)
                super().store_string(string)

        session = PromptSession(history=_LinkedPtkHistory())
    except ImportError:
        session = None

    def read_prompt(prefix: str = ">|") -> str:
        if session is not None:
            return session.prompt(HTML(f"<ansiyellow><b>{prefix}</b></ansiyellow> "))
        return console.input(f"[bold yellow]{prefix}[/bold yellow] ")

    while True:
        try:
            line = read_prompt(">|")
        except (EOFError, KeyboardInterrupt):
            console.print(fmt.hint("Until the next shelf."))
            break
        line = (line or "").strip()
        if not line:
            continue

        from .multiline_open import (
            commit_multiline_session,
            parse_multiline_opener,
        )
        from .text_editor import run_text_editor

        ml = parse_multiline_opener(line)
        if ml is not None:
            history.push(line)
            edited = run_text_editor(
                initial="",
                title=ml.title,
                studio=ml.studio,
            )
            if edited is None:
                console.print(fmt.hint("Editor cancelled."))
                continue
            result = commit_multiline_session(world, ml, edited.body)
            if result.message:
                console.print()
                console.print(result.message)
            if result.quit:
                break
            continue

        history.push(line)
        result = dispatch(world, line)
        if result.clear_log:
            console.print("\n" * 5)
        if result.message:
            console.print()
            console.print(result.message)
        if result.quit:
            break


def run_textual(world: World, world_path: Path) -> None:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal
    from textual.selection import Selection
    from textual.widgets import Footer, Input, RichLog, Static

    from .history import CommandHistory

    class SelectableWorldLog(RichLog):
        ALLOW_SELECT = True

        @staticmethod
        def _stylize_char_range(strip, start: int, end: int, style) -> object:
            from rich.segment import Segment
            from textual.strip import Strip

            if end < 0:
                end = sum(len(seg.text) for seg in strip)
            if start >= end:
                return strip
            out: list = []
            pos = 0
            for segment in strip:
                text, seg_style, control = segment
                n = len(text)
                if n == 0:
                    out.append(segment)
                    continue
                seg_start, seg_end = pos, pos + n
                if seg_end <= start or seg_start >= end:
                    out.append(segment)
                else:
                    if seg_start < start:
                        cut = start - seg_start
                        out.append(Segment(text[:cut], seg_style, control))
                        text = text[cut:]
                        seg_start = start
                    if text and seg_start < end:
                        cut = min(len(text), end - seg_start)
                        mid_style = style if seg_style is None else seg_style + style
                        out.append(Segment(text[:cut], mid_style, control))
                        text = text[cut:]
                    if text:
                        out.append(Segment(text, seg_style, control))
                pos = seg_end
            return Strip(out, strip.cell_length)

        def get_selection(self, selection: Selection) -> tuple[str, str] | None:
            if not self.lines:
                return None
            text = "\n".join(strip.text for strip in self.lines)
            if not text:
                return None
            return selection.extract(text), "\n"

        def selection_updated(self, selection: Selection | None) -> None:
            try:
                self._line_cache.clear()
            except Exception:
                pass
            self.refresh()

        def render_line(self, y: int):
            from rich.style import Style as RichStyle
            from textual.strip import Strip

            scroll_x, scroll_y = self.scroll_offset
            content_y = scroll_y + y
            width = self.scrollable_content_region.width
            rich_style = self.rich_style
            if content_y >= len(self.lines):
                return Strip.blank(width, rich_style)
            line = self.lines[content_y]
            selection = self.text_selection
            if selection is not None:
                span = selection.get_span(content_y)
                if span is not None:
                    start, end = span
                    if end < 0:
                        end = len(line.text)
                    try:
                        sel_style = self.screen.get_component_rich_style(
                            "screen--selection"
                        )
                    except Exception:
                        sel_style = RichStyle(reverse=True)
                    line = self._stylize_char_range(line, start, end, sel_style)
            line = line.crop_extend(scroll_x, scroll_x + width, rich_style)
            line = line.apply_offsets(scroll_x, content_y)
            return line.apply_style(rich_style)

    class HistoryInput(Input):
        BINDINGS = [
            Binding("up", "hist_up", "Prev cmd", show=False, priority=True),
            Binding("down", "hist_down", "Next cmd", show=False, priority=True),
        ]

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.cmd_history = CommandHistory()

        def action_hist_up(self) -> None:
            nxt = self.cmd_history.up(self.value)
            if nxt is not None:
                self.value = nxt
                self.cursor_position = len(self.value)

        def action_hist_down(self) -> None:
            nxt = self.cmd_history.down(self.value)
            if nxt is not None:
                self.value = nxt
                self.cursor_position = len(self.value)

    class StudioApp(App[None]):
        CSS = f"""
        Screen {{ background: {TUI_BG}; }}
        #body {{ height: 1fr; background: {TUI_BG}; }}
        #log {{
            width: 1fr; height: 1fr;
            border: solid {TUI_BORDER};
            padding: 1 2;
            background: {TUI_SURFACE};
            color: #e8e8ec;
            scrollbar-background: {TUI_BG};
            scrollbar-color: {TUI_BORDER};
        }}
        #cmd-bar {{
            dock: bottom; height: 3; margin: 0 0;
            border: solid {TUI_BORDER_ACCENT};
            background: {TUI_INPUT_BG};
            layout: horizontal;
            align: left middle;
        }}
        #cmd-prompt {{
            width: 4; min-width: 4; height: 1fr;
            content-align: right middle;
            color: #ffd84a; text-style: bold;
            background: {TUI_INPUT_BG};
            padding: 0 1 0 1;
        }}
        #cmd {{
            width: 1fr; height: 1fr; margin: 0 0;
            border: none; background: {TUI_INPUT_BG};
            color: #e8e8ec; padding: 0 1;
        }}
        #studio-header {{
            dock: top; height: 3;
            background: {TUI_PANEL};
            border-bottom: solid {TUI_BORDER_ACCENT};
            padding: 0 1; layout: horizontal;
        }}
        #header-left, #header-right {{
            height: 3; content-align: center middle; color: #c8c8d0;
        }}
        #header-left {{
            width: 1fr; content-align: left middle;
            text-style: bold; color: #e8e8ec;
        }}
        #header-right {{
            width: 4fr; content-align: right middle; color: #c8c8d0;
        }}
        Footer {{
            background: {TUI_BG}; color: #888890;
            border-top: solid {TUI_BORDER};
        }}
        """
        BINDINGS = [
            Binding("ctrl+c", "copy_or_quit", "Copy / Quit", show=False),
            Binding("ctrl+q", "quit", "Quit", show=True),
            Binding("f1", "inline_help", "Help"),
        ]

        def __init__(self) -> None:
            super().__init__()
            self._turn = 0

        def action_copy_or_quit(self) -> None:
            selected = self.screen.get_selected_text()
            if selected:
                self.copy_to_clipboard(selected)
                self.notify("Copied.", severity="information", timeout=1.5)
                return
            self.exit()

        def compose(self) -> ComposeResult:
            class ChromeStatic(Static):
                ALLOW_SELECT = False

            with Horizontal(id="studio-header"):
                yield ChromeStatic("", id="header-left", markup=True)
                yield ChromeStatic("", id="header-right", markup=True)
            with Horizontal(id="body"):
                yield SelectableWorldLog(
                    id="log",
                    highlight=False,
                    markup=True,
                    wrap=True,
                    auto_scroll=True,
                )
            with Horizontal(id="cmd-bar"):
                yield Static(
                    "[bold #ffd84a]>[/bold #ffd84a][bold #ffd84a]|[/bold #ffd84a]",
                    id="cmd-prompt",
                    markup=True,
                )
                yield HistoryInput(placeholder="", id="cmd")
            yield Footer()

        def on_mount(self) -> None:
            self.title = "miwbs"
            self.sub_title = ""
            self._refresh_studio_header()
            log = self.query_one("#log", SelectableWorldLog)
            log.clear()
            self._turn = 0
            log.write("")
            self.query_one("#cmd", HistoryInput).focus()

        def _refresh_studio_header(self) -> None:
            from . import chronicle as ch
            from . import cycle as cycle_mod
            from .ids import display_name

            left = self.query_one("#header-left", Static)
            right = self.query_one("#header-right", Static)
            left.update("[bold]miwbs[/bold]")

            wname = get_meta(world.conn, "world_name", "Day of Days") or "Day of Days"
            title = wname
            hid = ch.herenow_id(world)
            if hid:
                inst = world.get_instance(hid)
                if inst is not None:
                    title = display_name(inst.name)
            face = ""
            if cycle_mod.is_mentalor(world):
                face = cycle_mod.current_face(cycle_mod.load_state(world))
            right.update(
                f"{fmt.safe(wname)}  [dim]|[/dim]  {fmt.safe(title)}  "
                f"[dim]@[/dim]  [{TUI_BORDER_ACCENT}]{fmt.safe(face or '—')}"
                f"[/{TUI_BORDER_ACCENT}]"
            )

        def action_inline_help(self) -> None:
            log = self.query_one("#log", SelectableWorldLog)
            result = dispatch(world, "help")
            self._write_world_turn(log, "help", result.message or None)

        def _write_world_turn(
            self,
            log: RichLog,
            line: str,
            message: str | None,
            *,
            clear_log: bool = False,
        ) -> None:
            if clear_log:
                log.clear()
                self._turn = 0
                if not (message or "").strip():
                    self._refresh_studio_header()
                    return
            if self._turn > 0:
                log.write(fmt.turn_separator())
            self._turn += 1
            log.write(f"[bold yellow]>|[/bold yellow] {fmt.safe(line)}")
            if message:
                log.write("")
                log.write(message)
            self._refresh_studio_header()

        def on_input_submitted(self, event: Input.Submitted) -> None:
            log = self.query_one("#log", SelectableWorldLog)
            cmd = self.query_one("#cmd", HistoryInput)
            line = event.value.strip()
            event.input.value = ""
            if not line:
                return

            from .multiline_open import (
                commit_multiline_session,
                parse_multiline_opener,
            )
            from .text_editor import StudioBufferResult, make_studio_buffer_screen

            ml = parse_multiline_opener(line)
            if ml is not None:
                cmd.cmd_history.push(line)
                screen = make_studio_buffer_screen(
                    initial="",
                    title=ml.title,
                    studio=ml.studio,
                    page_title=None,
                )

                def _on_editor_done(edited: StudioBufferResult | None) -> None:
                    if edited is None:
                        self._write_world_turn(
                            log, line, fmt.hint("Editor cancelled.")
                        )
                    else:
                        result = commit_multiline_session(
                            world, ml, edited.body
                        )
                        self._write_world_turn(
                            log, line, result.message or None
                        )
                        if result.quit:
                            self.exit()
                    try:
                        self.query_one("#cmd", HistoryInput).focus()
                    except Exception:  # noqa: BLE001
                        pass

                self.push_screen(screen, _on_editor_done)
                return

            cmd.cmd_history.push(line)
            result = dispatch(world, line)
            self._write_world_turn(
                log,
                line,
                result.message or None,
                clear_log=result.clear_log,
            )
            if result.quit:
                self.exit()

    StudioApp().run()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="miwbs",
        description="MIWBS — Day of Days zero point (consider · HERENOW · crates)",
    )
    p.add_argument(
        "world",
        nargs="?",
        type=Path,
        default=DEFAULT_WORLD,
        help="Path to world.db",
    )
    p.add_argument("--reseed", action="store_true", help="Wipe and reseed")
    p.add_argument(
        "--seed",
        default="mentalor",
        help="Seed flavor (only mentalor / day-of-days)",
    )
    p.add_argument(
        "--textual",
        "-t",
        action="store_true",
        help="Textual TUI (default if no flag: also TUI)",
    )
    p.add_argument(
        "--repl",
        action="store_true",
        help="Plain REPL instead of Textual",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    path = Path(args.world)
    path.parent.mkdir(parents=True, exist_ok=True)
    world = ensure_world(path, reseed=args.reseed, seed=args.seed)
    if args.repl:
        run_repl(world, path)
    else:
        run_textual(world, path)


if __name__ == "__main__":
    main()
