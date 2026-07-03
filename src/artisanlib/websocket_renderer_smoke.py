from __future__ import annotations

import argparse
import asyncio
import json
import math
import socket
import time
from dataclasses import asdict, dataclass
from typing import Any

from dev_simulator.event_scheduler import EventScheduler
from dev_simulator.profile import RoastSpec, generate_profile
from dev_simulator.ws_server import AsyncServer

from artisanlib.plot_pyqtgraph_export import PyQtGraphWidgetPngResult, save_pyqtgraph_widget_png
from artisanlib.plot_pyqtgraph_widget import create_pyqtgraph_plot_target
from artisanlib.plot_snapshot import (
    AreaFillSnapshot,
    AxisSnapshot,
    CurveSnapshot,
    EventMarkerKind,
    EventMarkerSnapshot,
    EventValueSnapshot,
    GuideLineSnapshot,
    PhaseBandSnapshot,
    PhaseSummarySnapshot,
    RendererViewState,
    RoastPlotSnapshot,
    TimeRangeSnapshot,
)


@dataclass(frozen=True, slots=True)
class WebSocketTemperatureSample:
    time_s: float
    bt: float
    et: float


@dataclass(frozen=True, slots=True)
class WebSocketPushEvent:
    time_s: float
    label: str
    event_type: int
    color: str
    kind: EventMarkerKind = 'special'
    value: float | None = None


@dataclass(frozen=True, slots=True)
class WebSocketStreamCapture:
    samples: tuple[WebSocketTemperatureSample, ...]
    events: tuple[WebSocketPushEvent, ...]
    data_message_count: int
    push_message_count: int


@dataclass(frozen=True, slots=True)
class WebSocketRendererSmokeResult:
    sample_count: int
    data_message_count: int
    push_message_count: int
    event_count: int
    event_value_count: int
    guide_count: int
    area_count: int
    temperature_item_count: int
    ror_item_count: int
    renderer_event_item_count: int
    renderer_event_value_item_count: int
    renderer_guide_item_count: int
    renderer_area_item_count: int
    full_snapshot_count: int
    live_update_count: int
    max_update_ms: float
    avg_update_ms: float
    view_state: RendererViewState
    screenshot_file: str | None = None
    screenshot_width: int | None = None
    screenshot_height: int | None = None
    screenshot_byte_count: int | None = None
    screenshot_sampled_pixel_count: int | None = None
    screenshot_sampled_non_background_pixel_count: int | None = None


def run_websocket_pyqtgraph_validation(
        *,
        sample_count: int = 36,
        fixed_step_ms: float = 15_000.0,
        use_opengl: bool = False,
        scenario: str = 'standard',
        screenshot_file: str | None = None) -> WebSocketRendererSmokeResult:
    capture = asyncio.run(collect_websocket_stream(
        sample_count=sample_count,
        fixed_step_ms=fixed_step_ms,
        scenario=scenario,
    ))
    return render_websocket_stream_with_pyqtgraph(
        capture,
        use_opengl=use_opengl,
        screenshot_file=screenshot_file,
    )


async def collect_websocket_stream(
        *,
        sample_count: int,
        fixed_step_ms: float,
        scenario: str = 'standard') -> WebSocketStreamCapture:
    if sample_count <= 0:
        raise ValueError(f'sample_count must be positive, got {sample_count}')
    if fixed_step_ms <= 0.0:
        raise ValueError(f'fixed_step_ms must be positive, got {fixed_step_ms}')

    from websockets.asyncio.client import connect
    from websockets.asyncio.server import serve

    port = _unused_tcp_port()
    spec = RoastSpec(
        drop_t=max(840.0, (sample_count + 2) * fixed_step_ms / 1000.0),
        sample_hz=2,
        noise_model='none',
        noise_std=0.0,
    )
    server = AsyncServer(
        profile=generate_profile(spec),
        scheduler=EventScheduler(_validation_events(scenario), start_mode='auto'),
        host='127.0.0.1',
        port=port,
        path='WebSocket',
        noise_model='none',
        noise_std=0.0,
        fixed_step_ms=fixed_step_ms,
    )
    samples: list[WebSocketTemperatureSample] = []
    events: list[WebSocketPushEvent] = []
    data_message_count = 0
    push_message_count = 0

    async with (
        serve(server.handle, server.host, server.port),
        connect(f'ws://{server.host}:{server.port}/{server.path}') as websocket,
    ):
        for request_id in range(sample_count):
            current_time_s = request_id * fixed_step_ms / 1000.0
            await websocket.send(json.dumps({
                'command': 'getData',
                'id': request_id,
                'roasterID': 0,
            }))
            while True:
                message = json.loads(await asyncio.wait_for(websocket.recv(), timeout=2.0))
                if message.get('id') == request_id and isinstance(message.get('data'), dict):
                    data = message['data']
                    samples.append(WebSocketTemperatureSample(
                        time_s=current_time_s,
                        bt=float(data['BT']),
                        et=float(data['ET']),
                    ))
                    data_message_count += 1
                    break
                event = _push_event_from_message(message, current_time_s)
                if event is not None:
                    events.append(event)
                    push_message_count += 1

    return WebSocketStreamCapture(
        samples=tuple(samples),
        events=tuple(events),
        data_message_count=data_message_count,
        push_message_count=push_message_count,
    )


def render_websocket_stream_with_pyqtgraph(
        capture: WebSocketStreamCapture,
        *,
        use_opengl: bool = False,
        screenshot_file: str | None = None) -> WebSocketRendererSmokeResult:
    from PyQt6.QtWidgets import QApplication

    if not capture.samples:
        raise ValueError('capture must contain at least one sample')

    application = QApplication.instance() or QApplication([])
    target = create_pyqtgraph_plot_target(use_opengl=use_opengl, include_ror=True)
    target.configure_axes(
        time_grid=True,
        temperature_grid=True,
        time_tick_step=60.0,
        temperature_tick_step=20.0,
        ror_tick_step=5.0,
        time_label_mode='minutes',
        time_axis_start=0.0,
        grid_alpha=0.26,
        grid_width=1,
        grid_color='#A8B5AE',
        axis_color='#5E6B6E',
    )
    update_durations_ms: list[float] = []
    full_snapshot_count = 0
    live_update_count = 0
    previous_event_count = -1
    final_snapshot = build_snapshot_from_websocket_stream(capture.samples, capture.events)
    screenshot_result: PyQtGraphWidgetPngResult | None = None

    try:
        for index in range(1, len(capture.samples) + 1):
            frame_samples = capture.samples[:index]
            frame_events = tuple(
                event for event in capture.events
                if event.time_s <= frame_samples[-1].time_s
            )
            snapshot = build_snapshot_from_websocket_stream(frame_samples, frame_events)
            event_count = len(snapshot.events)
            started = time.perf_counter()
            if index == 1 or event_count != previous_event_count:
                target.renderer.set_snapshot(snapshot)
                full_snapshot_count += 1
                previous_event_count = event_count
            else:
                target.renderer.update_live_frame(snapshot)
                live_update_count += 1
            application.processEvents()
            update_durations_ms.append((time.perf_counter() - started) * 1000.0)

        target.renderer.set_snapshot(final_snapshot)
        application.processEvents()
        if screenshot_file is not None:
            screenshot_result = save_pyqtgraph_widget_png(
                target.widget,
                screenshot_file,
                application=application,
            )
        return WebSocketRendererSmokeResult(
            sample_count=len(capture.samples),
            data_message_count=capture.data_message_count,
            push_message_count=capture.push_message_count,
            event_count=len(final_snapshot.events),
            event_value_count=len(final_snapshot.event_values),
            guide_count=len(final_snapshot.guides),
            area_count=len(final_snapshot.areas),
            temperature_item_count=_plot_data_item_count(target.temperature_plot),
            ror_item_count=0 if target.ror_plot is None else _plot_data_item_count(target.ror_plot),
            renderer_event_item_count=target.renderer.event_item_count(),
            renderer_event_value_item_count=target.renderer.event_value_item_count(),
            renderer_guide_item_count=target.renderer.guide_item_count(),
            renderer_area_item_count=target.renderer.area_item_count(),
            full_snapshot_count=full_snapshot_count,
            live_update_count=live_update_count,
            max_update_ms=max(update_durations_ms),
            avg_update_ms=sum(update_durations_ms) / len(update_durations_ms),
            view_state=target.renderer.export_view_state(),
            screenshot_file=screenshot_file,
            screenshot_width=None if screenshot_result is None else screenshot_result.width,
            screenshot_height=None if screenshot_result is None else screenshot_result.height,
            screenshot_byte_count=None if screenshot_result is None else screenshot_result.byte_count,
            screenshot_sampled_pixel_count=None if screenshot_result is None else screenshot_result.sampled_pixel_count,
            screenshot_sampled_non_background_pixel_count=(
                None if screenshot_result is None else screenshot_result.sampled_non_background_pixel_count
            ),
        )
    finally:
        target.close()


def build_snapshot_from_websocket_stream(
        samples: tuple[WebSocketTemperatureSample, ...],
        events: tuple[WebSocketPushEvent, ...] = ()) -> RoastPlotSnapshot:
    if not samples:
        raise ValueError('samples must not be empty')

    x = tuple(sample.time_s for sample in samples)
    bt = tuple(sample.bt for sample in samples)
    et = tuple(sample.et for sample in samples)
    delta_bt = _ror_values(samples, channel='bt')
    delta_et = _ror_values(samples, channel='et')
    temperature_axis = _temperature_axis(bt + et)
    time_axis = AxisSnapshot(minimum=0.0, maximum=max(60.0, x[-1] + 30.0), label='Time')
    ror_axis = _ror_axis(delta_bt + delta_et)
    charge_time = _event_time(events, 100)
    event_markers = tuple(
        EventMarkerSnapshot(
            time=event.time_s,
            label=_main_event_label(event, charge_time),
            event_type=event.event_type,
            color=event.color,
            value=event.value,
            temperature=_nearest_bt(samples, event.time_s) if event.kind == 'main' else None,
            kind=event.kind,
        )
        for event in events
    ) + _turning_point_markers(samples, events)
    event_markers = tuple(sorted(event_markers, key=lambda event: (event.time, event.event_type)))
    event_values = tuple(
        EventValueSnapshot(
            time=event.time_s,
            value=event.value,
            event_type=event.event_type,
            color=event.color,
            label=event.label,
            kind=event.kind,
            opacity=0.48,
        )
        for event in events
        if event.value is not None and event.kind != 'main'
    )
    return RoastPlotSnapshot(
        curves=(
            CurveSnapshot.from_sequences(name='BT', x=x, y=bt, color='#4E7180'),
            CurveSnapshot.from_sequences(name='ET', x=x, y=et, color='#B5644F'),
            CurveSnapshot.from_sequences(name='Delta BT', x=x, y=delta_bt, color='#78905D', y_axis='ror'),
            CurveSnapshot.from_sequences(name='Delta ET', x=x, y=delta_et, color='#B98A4B', y_axis='ror'),
        ),
        temperature_axis=temperature_axis,
        time_axis=time_axis,
        ror_axis=ror_axis,
        events=event_markers,
        event_values=event_values,
        phase_bands=_phase_bands(),
        time_ranges=_development_time_ranges(events),
        phase_summaries=_phase_summaries(samples, events),
        guides=_guide_lines(),
        areas=_auc_area_fills(samples, events),
    )


def result_to_dict(result: WebSocketRendererSmokeResult) -> dict[str, object]:
    return asdict(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate PyQtGraph rendering with WebSocket virtual roast data.')
    parser.add_argument('--samples', type=int, default=36, help='Number of WebSocket getData samples to request.')
    parser.add_argument('--fixed-step-ms', type=float, default=15_000.0, help='Virtual milliseconds per request.')
    parser.add_argument('--opengl', action='store_true', help='Request PyQtGraph OpenGL rendering.')
    parser.add_argument(
        '--scenario',
        choices=('standard', 'event-heavy'),
        default='standard',
        help='Virtual roast event scenario to replay.')
    parser.add_argument('--screenshot-file', default=None, help='Optional PNG path for the rendered PyQtGraph widget.')
    args = parser.parse_args(argv)

    result = run_websocket_pyqtgraph_validation(
        sample_count=args.samples,
        fixed_step_ms=args.fixed_step_ms,
        use_opengl=args.opengl,
        scenario=args.scenario,
        screenshot_file=args.screenshot_file,
    )
    print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _validation_events(scenario: str = 'standard') -> list[tuple[float, dict[str, Any]]]:
    events = [
        (0.0, {'pushMessage': 'startRoasting'}),
        (30.0, {'pushMessage': 'addEvent', 'data': {'event': 'powerEvent', 'label': 'Power', 'value': 72.0}}),
        (60.0, {'pushMessage': 'addEvent', 'data': {'event': 'fanEvent', 'label': 'Fan', 'value': 38.0}}),
        (120.0, {'pushMessage': 'addEvent', 'data': {'event': 'colorChangeEvent'}}),
        (210.0, {'pushMessage': 'addEvent', 'data': {'event': 'firstCrackBeginningEvent'}}),
        (330.0, {'pushMessage': 'endRoasting'}),
    ]
    if scenario == 'standard':
        return events
    if scenario != 'event-heavy':
        raise ValueError(f'Unknown WebSocket renderer smoke scenario: {scenario!r}')
    return events[:5] + [
        (211.0, {'pushMessage': 'addEvent', 'data': {'event': 'powerEvent', 'label': 'Power 2', 'value': 76.0}}),
        (212.0, {'pushMessage': 'addEvent', 'data': {'event': 'fanEvent', 'label': 'Fan 2', 'value': 41.0}}),
        (213.0, {'pushMessage': 'addEvent', 'data': {'event': 'damperEvent', 'label': 'Air', 'value': 63.0}}),
        (214.0, {'pushMessage': 'addEvent', 'data': {'event': 'drumEvent', 'label': 'Drum', 'value': 58.0}}),
        (215.0, {'pushMessage': 'addEvent', 'data': {'event': 'powerEvent', 'label': 'Power 3', 'value': 70.0}}),
        (330.0, {'pushMessage': 'endRoasting'}),
    ]


def _push_event_from_message(message: dict[str, Any], time_s: float) -> WebSocketPushEvent | None:
    push_message = message.get('pushMessage')
    if push_message == 'startRoasting':
        return WebSocketPushEvent(time_s=time_s, label='CHARGE', event_type=100, color='#5E6B6E', kind='main')
    if push_message == 'endRoasting':
        return WebSocketPushEvent(time_s=time_s, label='DROP', event_type=106, color='#5E6B6E', kind='main')
    if push_message != 'addEvent':
        return None
    data = message.get('data')
    if not isinstance(data, dict):
        return None
    event_name = str(data.get('event', 'event'))
    label, event_type, color, kind = _event_descriptor(event_name)
    raw_label = data.get('label')
    if isinstance(raw_label, str) and raw_label.strip():
        label = raw_label.strip()
    value = _numeric_value(data.get('value'))
    return WebSocketPushEvent(
        time_s=time_s,
        label=label,
        event_type=event_type,
        color=color,
        kind=kind,
        value=value,
    )


def _event_descriptor(event_name: str) -> tuple[str, int, str, EventMarkerKind]:
    return {
        'powerEvent': ('Power', 1, '#B4685C', 'special'),
        'fanEvent': ('Fan', 2, '#3C7A88', 'special'),
        'damperEvent': ('Air', 3, '#78905D', 'special'),
        'drumEvent': ('Drum', 4, '#B98A4B', 'special'),
        'colorChangeEvent': ('DRY', 101, '#5E6B6E', 'main'),
        'firstCrackBeginningEvent': ('FCs', 102, '#5E6B6E', 'main'),
        'firstCrackEndEvent': ('FCe', 103, '#5E6B6E', 'main'),
        'secondCrackBeginningEvent': ('SCs', 104, '#5E6B6E', 'main'),
    }.get(event_name, (event_name, 99, '#5E6B6E', 'special'))


def _ror_values(
        samples: tuple[WebSocketTemperatureSample, ...],
        *,
        channel: str) -> tuple[float | None, ...]:
    values: list[float | None] = [None]
    for previous, current in zip(samples, samples[1:], strict=False):
        previous_value = previous.bt if channel == 'bt' else previous.et
        current_value = current.bt if channel == 'bt' else current.et
        elapsed_s = current.time_s - previous.time_s
        if elapsed_s <= 0.0:
            values.append(None)
        else:
            values.append((current_value - previous_value) * 60.0 / elapsed_s)
    return tuple(values)


def _temperature_axis(values: tuple[float, ...]) -> AxisSnapshot:
    minimum = math.floor((min(values) - 20.0) / 10.0) * 10.0
    maximum = math.ceil((max(values) + 20.0) / 10.0) * 10.0
    return AxisSnapshot(minimum=max(0.0, minimum), maximum=maximum, label='Temperature')


def _ror_axis(values: tuple[float | None, ...]) -> AxisSnapshot:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return AxisSnapshot(minimum=-10.0, maximum=25.0, label='RoR')
    return AxisSnapshot(
        minimum=math.floor((min(numeric_values) - 5.0) / 5.0) * 5.0,
        maximum=max(25.0, math.ceil((max(numeric_values) + 5.0) / 5.0) * 5.0),
        label='RoR',
    )


def _phase_bands() -> tuple[PhaseBandSnapshot, ...]:
    return (
        PhaseBandSnapshot(minimum=140.0, maximum=160.0, color='#DDE8E0', opacity=0.22, label='Drying'),
        PhaseBandSnapshot(minimum=160.0, maximum=195.0, color='#E7DEC9', opacity=0.22, label='Maillard'),
        PhaseBandSnapshot(minimum=195.0, maximum=230.0, color='#D9E4EA', opacity=0.22, label='Development'),
    )


def _development_time_ranges(events: tuple[WebSocketPushEvent, ...]) -> tuple[TimeRangeSnapshot, ...]:
    first_crack = _event_time(events, 102)
    drop = _event_time(events, 106)
    if first_crack is None or drop is None or drop <= first_crack:
        return ()
    return (
        TimeRangeSnapshot(
            start=first_crack,
            end=drop,
            color='#FFF6A8',
            opacity=0.28,
            label='Development',
            kind='development',
        ),
    )


def _phase_summaries(
        samples: tuple[WebSocketTemperatureSample, ...],
        events: tuple[WebSocketPushEvent, ...]) -> tuple[PhaseSummarySnapshot, ...]:
    charge = _event_time(events, 100)
    dry = _event_time(events, 101)
    first_crack = _event_time(events, 102)
    drop = _event_time(events, 106)
    if charge is None or dry is None or first_crack is None or drop is None:
        return ()
    if not (charge < dry < first_crack < drop):
        return ()
    total = drop - charge
    if total <= 0:
        return ()
    tp_time = _turning_point_time(samples, charge, dry)
    specs = (
        ('Drying', charge, dry, tp_time if tp_time is not None else charge, dry, '#DDE8E0'),
        ('Maillard', dry, first_crack, dry, first_crack, '#E7DEC9'),
        ('Development', first_crack, drop, first_crack, drop, '#FFF6A8'),
    )
    return tuple(
        PhaseSummarySnapshot(
            start=start,
            end=end,
            label=label,
            duration_text=_format_seconds_as_minsec(end - start),
            percent_text=f'{(end - start) / total * 100.0:.1f}%',
            delta_text=_sample_delta_text(samples, delta_start, delta_end),
            color=color,
        )
        for label, start, end, delta_start, delta_end, color in specs
    )


def _turning_point_markers(
        samples: tuple[WebSocketTemperatureSample, ...],
        events: tuple[WebSocketPushEvent, ...]) -> tuple[EventMarkerSnapshot, ...]:
    charge = _event_time(events, 100)
    dry = _event_time(events, 101)
    tp_time = _turning_point_time(samples, charge, dry)
    if charge is None or tp_time is None:
        return ()
    return (
        EventMarkerSnapshot(
            time=tp_time,
            label=f'TP {_format_seconds_as_minsec(tp_time - charge)}',
            event_type=99,
            color='#5E6B6E',
            temperature=_nearest_bt(samples, tp_time),
            kind='main',
        ),
    )


def _turning_point_time(
        samples: tuple[WebSocketTemperatureSample, ...],
        charge: float | None,
        dry: float | None) -> float | None:
    if charge is None or dry is None or dry <= charge:
        return None
    candidates = [sample for sample in samples if charge <= sample.time_s <= dry]
    if not candidates:
        return None
    return min(candidates, key=lambda sample: sample.bt).time_s


def _main_event_label(event: WebSocketPushEvent, charge_time: float | None) -> str:
    if event.kind != 'main' or event.event_type == 100 or charge_time is None:
        return event.label
    return f'{event.label} {_format_seconds_as_minsec(event.time_s - charge_time)}'


def _event_time(events: tuple[WebSocketPushEvent, ...], event_type: int) -> float | None:
    event = next((candidate for candidate in events if candidate.event_type == event_type), None)
    if event is None:
        return None
    return event.time_s


def _format_seconds_as_minsec(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    minutes, remaining_seconds = divmod(total_seconds, 60)
    return f'{minutes}:{remaining_seconds:02d}'


def _sample_delta_text(
        samples: tuple[WebSocketTemperatureSample, ...],
        start_time: float,
        end_time: float) -> str:
    start = _nearest_bt(samples, start_time)
    end = _nearest_bt(samples, end_time)
    if start is None or end is None:
        return ''
    return f'{end - start:.1f}'


def _nearest_bt(samples: tuple[WebSocketTemperatureSample, ...], time_s: float) -> float | None:
    if not samples:
        return None
    nearest = min(samples, key=lambda sample: abs(sample.time_s - time_s))
    return nearest.bt


def _guide_lines() -> tuple[GuideLineSnapshot, ...]:
    return (
        GuideLineSnapshot(position=0.0, label='BBP', color='#53756F', kind='bbp', opacity=0.42),
        GuideLineSnapshot(position=210.0, label='AUC guide', color='#8FA39C', kind='auc', line_style='-', opacity=0.5),
        GuideLineSnapshot(
            position=182.0,
            label='Charge target',
            color='#B4685C',
            orientation='horizontal',
            kind='charge_target',
            opacity=0.42,
        ),
    )


def _auc_area_fills(
        samples: tuple[WebSocketTemperatureSample, ...],
        events: tuple[WebSocketPushEvent, ...]) -> tuple[AreaFillSnapshot, ...]:
    drop_time = next((event.time_s for event in reversed(events) if event.event_type == 106), None)
    if drop_time is None:
        return ()
    drop_index = _last_sample_index_at_or_before(samples, drop_time)
    if drop_index is None or drop_index < 2:
        return ()
    tp_index = min(range(drop_index + 1), key=lambda index: samples[index].bt)
    if drop_index - tp_index < 1:
        return ()
    x_values = tuple(sample.time_s for sample in samples[tp_index:drop_index + 1])
    y_values = tuple(sample.bt for sample in samples[tp_index:drop_index + 1])
    baseline = y_values[0]
    if baseline <= 0.0:
        return ()
    return (
        AreaFillSnapshot.from_sequences(
            x=x_values,
            y=y_values,
            baseline=baseline,
            color='#767676',
            label='AUC area',
            opacity=0.28,
            kind='auc',
        ),
    )


def _last_sample_index_at_or_before(
        samples: tuple[WebSocketTemperatureSample, ...],
        time_s: float) -> int | None:
    indexes = [index for index, sample in enumerate(samples) if sample.time_s <= time_s]
    if not indexes:
        return None
    return indexes[-1]


def _plot_data_item_count(plot: object) -> int:
    list_data_items = getattr(plot, 'listDataItems', None)
    if callable(list_data_items):
        return len(list_data_items())
    return 0


def _numeric_value(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def _unused_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return int(sock.getsockname()[1])


__all__ = [
    'WebSocketPushEvent',
    'WebSocketRendererSmokeResult',
    'WebSocketStreamCapture',
    'WebSocketTemperatureSample',
    'build_snapshot_from_websocket_stream',
    'collect_websocket_stream',
    'main',
    'render_websocket_stream_with_pyqtgraph',
    'result_to_dict',
    'run_websocket_pyqtgraph_validation',
]


if __name__ == '__main__':
    raise SystemExit(main())
