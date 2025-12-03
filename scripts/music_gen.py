#!/usr/bin/env python3
import sys
import os
import glob
import math
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

def read_varlen(data, pos):
    value = 0
    while True:
        b = data[pos]
        pos += 1
        value = (value << 7) | (b & 0x7F)
        if (b & 0x80) == 0:
            break
    return value, pos

def midi_note_name(n):
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (n // 12) - 1
    return f"{names[n % 12]}{octave}"

def midi_note_freq(n):
    return int(round(440.0 * (2 ** ((n - 69) / 12.0))))

def parse_midi(path):
    with open(path, "rb") as f:
        data = f.read()

    pos = 0
    if data[pos:pos+4] != b"MThd":
        raise ValueError("MIDI header not found")
    pos += 4
    header_len = int.from_bytes(data[pos:pos+4], "big")
    pos += 4
    fmt = int.from_bytes(data[pos:pos+2], "big")
    pos += 2
    ntrks = int.from_bytes(data[pos:pos+2], "big")
    pos += 2
    division = int.from_bytes(data[pos:pos+2], "big", signed=True)
    pos += 2
    if header_len > 6:
        pos += (header_len - 6)

    if division < 0:
        raise ValueError("SMPTE timecode not supported")
    tpqn = division

    tracks = []
    for _ in range(ntrks):
        if data[pos:pos+4] != b"MTrk":
            raise ValueError("Track chunk not found")
        pos += 4
        trk_len = int.from_bytes(data[pos:pos+4], "big")
        pos += 4
        trk_data = data[pos:pos+trk_len]
        pos += trk_len
        tracks.append(trk_data)

    tempo_us_per_qn = 500000
    melody_track_index = 0
    note_on_counts = []
    parsed_tracks = []

    for ti, tdata in enumerate(tracks):
        tpos = 0
        tick = 0
        running = None
        notes_active = {}
        events = []
        local_note_on = 0
        local_tempos = []

        while tpos < len(tdata):
            delta, tpos = read_varlen(tdata, tpos)
            tick += delta

            status = tdata[tpos]
            if status < 0x80:
                if running is None:
                    raise ValueError("Running status without previous status")
                status = running
                # position stays; data bytes will be read using current tpos
            else:
                tpos += 1
                running = status

            if status == 0xFF:
                if tpos >= len(tdata):
                    break
                meta_type = tdata[tpos]
                tpos += 1
                length, tpos = read_varlen(tdata, tpos)
                meta_data = tdata[tpos:tpos+length]
                tpos += length
                if meta_type == 0x51 and length == 3:
                    us = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
                    local_tempos.append((tick, us))
            elif status == 0xF0 or status == 0xF7:
                length, tpos = read_varlen(tdata, tpos)
                tpos += length
            else:
                etype = status & 0xF0
                if etype in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    b1 = tdata[tpos]
                    b2 = tdata[tpos+1]
                    tpos += 2
                    if etype == 0x90:
                        if b2 > 0:
                            local_note_on += 1
                            notes_active.setdefault(b1, []).append(tick)
                        else:
                            lst = notes_active.get(b1)
                            if lst:
                                start_tick = lst.pop(0)
                                events.append((start_tick, tick, b1))
                    elif etype == 0x80:
                        lst = notes_active.get(b1)
                        if lst:
                            start_tick = lst.pop(0)
                            events.append((start_tick, tick, b1))
                elif etype in (0xC0, 0xD0):
                    tpos += 1
                else:
                    break

        for pitch, starts in list(notes_active.items()):
            while starts:
                s = starts.pop(0)
                events.append((s, s + tpqn // 4, pitch))

        parsed_tracks.append({"events": events, "tempos": local_tempos})
        note_on_counts.append(local_note_on)

    if note_on_counts:
        melody_track_index = max(range(len(note_on_counts)), key=lambda i: note_on_counts[i])

    chosen = parsed_tracks[melody_track_index]
    evs = sorted(chosen["events"], key=lambda e: e[0])
    global_tempo = None
    if parsed_tracks and parsed_tracks[0]["tempos"]:
        global_tempo = parsed_tracks[0]["tempos"][0][1]
    if global_tempo is None:
        for tr in parsed_tracks:
            if tr["tempos"]:
                tempo_0 = next((us for tick, us in tr["tempos"] if tick == 0), None)
                global_tempo = tempo_0 if tempo_0 is not None else tr["tempos"][0][1]
                break
    if global_tempo is not None:
        tempo_us_per_qn = global_tempo

    pieces = []
    last_end = 0
    used_notes = {}
    for s, e, p in evs:
        if s > last_end:
            gap_ticks = s - last_end
            if gap_ticks > 0:
                pieces.append(("SILENCE", gap_ticks))
        dur_ticks = max(1, e - s)
        freq = midi_note_freq(p)
        name = midi_note_name(p)
        used_notes[name] = freq
        pieces.append((name, dur_ticks))
        last_end = e

    notes_dict = {"SILENCE": 0}
    for k, v in used_notes.items():
        notes_dict[k] = v

    tick_ms = max(1, int(round(tempo_us_per_qn / tpqn / 1000)))
    tempo_ms_qn = max(1, int(round(tempo_us_per_qn / 1000)))
    return notes_dict, pieces, tick_ms, tpqn, tempo_ms_qn

def write_song_module(notes, pieces, out_path, tempo_ms_qn, tpqn):
    lines = []
    lines.append("NOTES = {")
    for k in sorted(notes.keys(), key=lambda x: (x != "SILENCE", x)):
        lines.append(f"    '{k}': {notes[k]},")
    lines.append("}")
    lines.append(f"TEMPO = {tempo_ms_qn}")
    lines.append(f"SUBDIV = {tpqn}")
    lines.append("PIECE = [")
    for name, ticks in pieces:
        dur_expr = "TEMPO // SUBDIV" if int(ticks) == 1 else f"TEMPO * {int(ticks)} // SUBDIV"
        lines.append(f"    (NOTES['{name}'], {dur_expr}),")
    lines.append("]")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))

def main():
    console = Console()
    console.print(Panel("MIDI files available in 'assets/':", title="[bold cyan]Music Generator[/bold cyan]"))
    midi_files = glob.glob("assets/*.mid") + glob.glob("assets/*.midi")
    names = [os.path.basename(f) for f in midi_files]
    if not names:
        console.print("[bold red]Error:[/bold red] No MIDI files found in 'assets/'.")
        sys.exit(1)
    for i, name in enumerate(names):
        console.print(f"  [yellow]{i+1}[/yellow]. {name}")
    choice = Prompt.ask("\n[bold]Choose a MIDI to convert[/bold]", choices=[str(i+1) for i in range(len(names))])
    selected = names[int(choice) - 1]
    src_path = os.path.join("assets", selected)
    out_name = os.path.splitext(selected)[0] + ".py"
    out_path = os.path.join(os.getcwd(), out_name)
    console.print(Panel(f"  - Source: {src_path}\n  - Output: {out_name}", title="[bold cyan]Processing[/bold cyan]"))
    try:
        notes, pieces, tick_ms, tpqn, tempo_ms_qn = parse_midi(src_path)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    write_song_module(notes, pieces, out_path, tempo_ms_qn, tpqn)
    console.print(f"\n[bold green]✓ Successfully generated '{out_name}' ({len(pieces)} events).[/bold green]")

if __name__ == "__main__":
    main()
