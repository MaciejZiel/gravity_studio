from __future__ import annotations

from array import array
from math import pi, sin

import pygame


class AmbientSoundscape:
    def __init__(self, master_volume: float) -> None:
        self.enabled = master_volume > 0.0
        self.master_volume = master_volume
        self._bed_channel: pygame.mixer.Channel | None = None
        self._air_channel: pygame.mixer.Channel | None = None
        self._bed_volume = 0.0
        self._air_volume = 0.0
        self._ready = False
        self._init_channels()

    def set_enabled(self, enabled: bool, fallback_volume: float = 0.42) -> None:
        self.enabled = enabled
        self.master_volume = fallback_volume if enabled else 0.0

    def update(self, dt: float, focus_mode: bool, live_mode: bool, ui_hidden: bool) -> None:
        if not self._ready or self._bed_channel is None or self._air_channel is None:
            return

        target_bed = self.master_volume * (0.32 if live_mode else 0.26)
        target_air = self.master_volume * (0.18 if focus_mode else 0.11)
        if ui_hidden:
            target_air *= 1.18
            target_bed *= 0.92

        self._bed_volume += (target_bed - self._bed_volume) * min(1.0, dt * 2.2)
        self._air_volume += (target_air - self._air_volume) * min(1.0, dt * 2.0)
        self._bed_channel.set_volume(self._bed_volume)
        self._air_channel.set_volume(self._air_volume)

    def shutdown(self) -> None:
        if pygame.mixer.get_init() is None:
            return
        if self._bed_channel is not None:
            self._bed_channel.stop()
        if self._air_channel is not None:
            self._air_channel.stop()

    def _init_channels(self) -> None:
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except pygame.error:
            return

        bed_sound = self._build_loop((55.0, 82.5, 110.0), seconds=4.0, amplitude=0.19)
        air_sound = self._build_loop((220.0, 330.0, 440.0), seconds=4.0, amplitude=0.07)
        self._bed_channel = pygame.mixer.Channel(0)
        self._air_channel = pygame.mixer.Channel(1)
        self._bed_channel.play(bed_sound, loops=-1)
        self._air_channel.play(air_sound, loops=-1)
        self._bed_channel.set_volume(0.0)
        self._air_channel.set_volume(0.0)
        self._ready = True

    def _build_loop(self, frequencies: tuple[float, ...], seconds: float, amplitude: float) -> pygame.mixer.Sound:
        sample_rate = 22050
        sample_count = int(sample_rate * seconds)
        samples = array("h")
        for index in range(sample_count):
            t = index / sample_rate
            envelope = 0.72 + 0.28 * sin((t / seconds) * pi * 2.0)
            sample = 0.0
            for frequency_index, frequency in enumerate(frequencies):
                sample += sin(t * frequency * pi * 2.0 + frequency_index * 0.7) * (1.0 / (frequency_index + 1))
            value = int(max(-1.0, min(1.0, sample * amplitude * envelope)) * 32767)
            samples.append(value)
            samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())
