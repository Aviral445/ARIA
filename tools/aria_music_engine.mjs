/**
 * tools/aria_music_engine.mjs — High-Performance Polyglot Sound & Music Engine
 * Built with Node.js & TypedArrays for high-fidelity audio synthesis, drum generation,
 * multi-track mixing, and standard MIDI generation.
 *
 * Designed for Aria's Music Studio (The Digital Greenhouse).
 */

import fs from 'fs';
import path from 'path';

const SAMPLE_RATE = 44100;

// ─────────────────────────────────────────────────────────────────────────────
// 1. MUSIC THEORY HELPERS & FREQUENCIES
// ─────────────────────────────────────────────────────────────────────────────

export function midiToFreq(midiPitch) {
  return 440.0 * Math.pow(2.0, (midiPitch - 69) / 12.0);
}

// Pseudo-random white noise generator with seed for reproducible acoustic textures
let _seed = 1234567;
function pseudoRandom() {
  _seed = (_seed * 9301 + 49297) % 233280;
  return (_seed / 233280.0) * 2.0 - 1.0;
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. SYNTHESIZED DRUM ENGINES (KICK, SNARE, HI-HATS, RIM)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Synthesizes a punchy acoustic/lo-fi kick drum sample.
 * Frequency drops exponentially from startFreq (160 Hz) to endFreq (42 Hz).
 */
export function synthesizeKick(durationSec = 0.35, sampleRate = SAMPLE_RATE) {
  const numSamples = Math.floor(durationSec * sampleRate);
  const buffer = new Float32Array(numSamples);
  const startFreq = 160.0;
  const endFreq = 42.0;
  const sweepRate = 28.0;

  let phase = 0.0;
  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    // Exponential frequency drop
    const currentFreq = endFreq + (startFreq - endFreq) * Math.exp(-sweepRate * t);
    phase += (2.0 * Math.PI * currentFreq) / sampleRate;

    // Amplitude envelope: instant attack + exponential decay
    const amp = Math.exp(-10.0 * t);
    // Add subtle saturated sub-thump
    let val = Math.sin(phase) * amp;
    val = Math.tanh(val * 1.3); // soft clip saturation
    buffer[i] = val * 0.95;
  }
  return buffer;
}

/**
 * Synthesizes an acoustic/lo-fi snare drum.
 * Combines a resonant body tone (190 Hz) with shaped noise snap.
 */
export function synthesizeSnare(durationSec = 0.28, sampleRate = SAMPLE_RATE) {
  const numSamples = Math.floor(durationSec * sampleRate);
  const buffer = new Float32Array(numSamples);
  const bodyFreq = 190.0;

  let bodyPhase = 0.0;
  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    // Resonant body
    bodyPhase += (2.0 * Math.PI * bodyFreq) / sampleRate;
    const bodyEnv = Math.exp(-25.0 * t);
    const body = Math.sin(bodyPhase) * bodyEnv * 0.45;

    // Noise snap with fast decay
    const noise = pseudoRandom();
    const noiseEnv = Math.exp(-18.0 * t);
    const snap = noise * noiseEnv * 0.55;

    buffer[i] = (body + snap) * 0.85;
  }
  return buffer;
}

/**
 * Synthesizes a closed metallic hi-hat.
 * Fast high-pass filtered metallic transient (0.045s).
 */
export function synthesizeClosedHat(durationSec = 0.06, sampleRate = SAMPLE_RATE) {
  const numSamples = Math.floor(durationSec * sampleRate);
  const buffer = new Float32Array(numSamples);
  const ringFreq1 = 8800.0;
  const ringFreq2 = 11200.0;

  let phase1 = 0.0;
  let phase2 = 0.0;
  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    phase1 += (2.0 * Math.PI * ringFreq1) / sampleRate;
    phase2 += (2.0 * Math.PI * ringFreq2) / sampleRate;

    const ring = (Math.sin(phase1) + Math.sin(phase2)) * 0.3;
    const noise = pseudoRandom() * 0.7;
    const env = Math.exp(-55.0 * t);

    buffer[i] = (ring + noise) * env * 0.5;
  }
  return buffer;
}

/**
 * Synthesizes an open metallic hi-hat.
 * Sizzling high-frequency metallic ring with extended decay (0.35s).
 */
export function synthesizeOpenHat(durationSec = 0.35, sampleRate = SAMPLE_RATE) {
  const numSamples = Math.floor(durationSec * sampleRate);
  const buffer = new Float32Array(numSamples);
  const ringFreq = 9600.0;

  let phase = 0.0;
  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    phase += (2.0 * Math.PI * ringFreq) / sampleRate;
    const ring = Math.sin(phase) * 0.35;
    const noise = pseudoRandom() * 0.65;
    const env = Math.exp(-12.0 * t);

    buffer[i] = (ring + noise) * env * 0.5;
  }
  return buffer;
}

/**
 * Synthesizes an acoustic wooden rimshot / woodblock.
 */
export function synthesizeRimshot(durationSec = 0.08, sampleRate = SAMPLE_RATE) {
  const numSamples = Math.floor(durationSec * sampleRate);
  const buffer = new Float32Array(numSamples);
  const freq = 650.0;

  let phase = 0.0;
  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    phase += (2.0 * Math.PI * freq) / sampleRate;
    const env = Math.exp(-45.0 * t);
    const click = (i < 80 ? pseudoRandom() * 0.5 : 0.0);
    buffer[i] = (Math.sin(phase) + click) * env * 0.7;
  }
  return buffer;
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. MULTI-INSTRUMENT TIMBRE SYNTHESIS (PIANO, BASS, PAD, GUITAR, LEAD)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Synthesizes an instrument note with authentic harmonic profile and ADSR envelope.
 */
export function synthesizeInstrumentNote(instrument, freqHz, durationSec, velocity = 0.85, sampleRate = SAMPLE_RATE) {
  const releaseSec = instrument === 'ambient_pad' ? 0.45 : 0.18;
  const totalDuration = durationSec + releaseSec;
  const numSamples = Math.floor(totalDuration * sampleRate);
  const buffer = new Float32Array(numSamples);

  // ADSR Envelope Configuration per instrument
  let attack = 0.02;
  let decay = 0.1;
  let sustain = 0.6;
  if (instrument === 'warm_piano') {
    attack = 0.015;
    decay = 0.35;
    sustain = 0.45;
  } else if (instrument === 'acoustic_bass') {
    attack = 0.02;
    decay = 0.25;
    sustain = 0.55;
  } else if (instrument === 'ambient_pad') {
    attack = 0.35;
    decay = 0.2;
    sustain = 0.85;
  } else if (instrument === 'guitar_pluck') {
    attack = 0.008;
    decay = 0.28;
    sustain = 0.35;
  } else if (instrument === 'music_box') {
    attack = 0.005;
    decay = 0.4;
    sustain = 0.25;
  } else if (instrument === 'flute_lead' || instrument === 'aria_lead') {
    attack = 0.05;
    decay = 0.1;
    sustain = 0.75;
  }

  const attSamples = Math.floor(attack * sampleRate);
  const decSamples = Math.floor(decay * sampleRate);
  const sustainSamples = Math.floor(durationSec * sampleRate);
  const relSamples = Math.floor(releaseSec * sampleRate);

  let phase = 0.0;
  let phaseDetune = 0.0;

  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;

    // Envelope calculation
    let env = 0.0;
    if (i < attSamples) {
      env = i / Math.max(1, attSamples);
    } else if (i < attSamples + decSamples) {
      env = 1.0 - (1.0 - sustain) * ((i - attSamples) / Math.max(1, decSamples));
    } else if (i < sustainSamples) {
      env = sustain * Math.exp(-0.8 * (t - attack - decay));
    } else {
      const relPos = (i - sustainSamples) / Math.max(1, relSamples);
      env = Math.max(0.0, sustain * (1.0 - relPos));
    }

    // Vibrato for lead voice (starts after 0.18s)
    let currentFreq = freqHz;
    if ((instrument === 'flute_lead' || instrument === 'aria_lead') && t > 0.18) {
      const vibrato = Math.sin(2.0 * Math.PI * 5.2 * t) * (freqHz * 0.012);
      currentFreq += vibrato;
    }

    phase += (2.0 * Math.PI * currentFreq) / sampleRate;
    phaseDetune += (2.0 * Math.PI * (currentFreq * 1.0035)) / sampleRate;

    // Harmonic Spectrum Generator
    let sampleVal = 0.0;
    if (instrument === 'warm_piano') {
      sampleVal =
        Math.sin(phase) * 0.70 +
        Math.sin(2.0 * phase) * 0.20 +
        Math.sin(3.0 * phase) * 0.08 +
        Math.sin(4.0 * phase) * 0.02;
    } else if (instrument === 'acoustic_bass') {
      sampleVal =
        Math.sin(phase) * 0.82 +
        Math.sin(2.0 * phase) * 0.15 +
        Math.sin(3.0 * phase) * 0.03;
      sampleVal = Math.tanh(sampleVal * 1.2); // Warm bass saturation
    } else if (instrument === 'ambient_pad') {
      // Shimmering detuned stereo-like chorus
      sampleVal =
        (Math.sin(phase) + Math.sin(phaseDetune)) * 0.45 +
        Math.sin(2.0 * phase) * 0.15;
    } else if (instrument === 'guitar_pluck') {
      sampleVal =
        Math.sin(phase) * 0.65 +
        Math.sin(2.0 * phase) * 0.22 +
        Math.sin(3.0 * phase) * 0.10 +
        Math.sin(5.0 * phase) * 0.03;
    } else if (instrument === 'music_box') {
      sampleVal =
        Math.sin(phase) * 0.75 +
        Math.sin(2.756 * phase) * 0.18 +
        Math.sin(5.404 * phase) * 0.07;
    } else {
      // Default singing lead / flute
      sampleVal =
        Math.sin(phase) * 0.85 +
        Math.sin(2.0 * phase) * 0.12 +
        Math.sin(3.0 * phase) * 0.03;
    }

    buffer[i] = sampleVal * env * velocity;
  }

  return buffer;
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. MULTI-TRACK MIXER & PCM BUFFER ACCUMULATOR
// ─────────────────────────────────────────────────────────────────────────────

export class MultiTrackProject {
  constructor(bpm = 76, sampleRate = SAMPLE_RATE) {
    this.bpm = bpm;
    this.sampleRate = sampleRate;
    this.secPerBeat = 60.0 / bpm;
    this.tracks = {
      drums: [],      // { beatStart, type, velocity }
      bass: [],       // { beatStart, durationBeats, pitch, velocity }
      chords: [],     // { beatStart, durationBeats, pitch, velocity }
      pad: [],        // { beatStart, durationBeats, pitch, velocity }
      lead: [],       // { beatStart, durationBeats, pitch, velocity }
    };
    this.instruments = {
      bass: 'acoustic_bass',
      chords: 'warm_piano',
      pad: 'ambient_pad',
      lead: 'aria_lead'
    };
    this.trackGains = {
      drums: 0.75,
      bass: 0.80,
      chords: 0.65,
      pad: 0.42,
      lead: 0.82
    };
  }

  addDrumEvent(beatStart, type = 'kick', velocity = 0.85) {
    this.tracks.drums.push({ beatStart, type, velocity });
  }

  addNote(trackName, beatStart, durationBeats, pitch, velocity = 0.85) {
    if (this.tracks[trackName]) {
      this.tracks[trackName].push({ beatStart, durationBeats, pitch, velocity });
    }
  }

  // Pre-bake drum pattern loops across measures
  applyDrumPattern(numMeasures = 4, beatsPerMeasure = 4, grooveType = 'lofi_chill_hop') {
    for (let m = 0; m < numMeasures; m++) {
      const baseBeat = m * beatsPerMeasure;

      if (grooveType === 'lofi_chill_hop') {
        // Kick on 1 and 2.5
        this.addDrumEvent(baseBeat + 0.0, 'kick', 0.9);
        this.addDrumEvent(baseBeat + 1.5, 'kick', 0.75);
        // Snare on 2 and 4
        this.addDrumEvent(baseBeat + 1.0, 'snare', 0.85);
        this.addDrumEvent(baseBeat + 3.0, 'snare', 0.88);
        // Hi-hat 8th notes with gentle swing
        for (let b = 0; b < beatsPerMeasure; b += 0.5) {
          this.addDrumEvent(baseBeat + b, 'closed_hat', b % 1.0 === 0 ? 0.65 : 0.45);
        }
        // Occasional open hat on beat 3.5
        if (m % 2 === 1) {
          this.addDrumEvent(baseBeat + 2.5, 'open_hat', 0.55);
        }
      } else if (grooveType === 'warm_acoustic_folk') {
        // Kick on 1 and 3
        this.addDrumEvent(baseBeat + 0.0, 'kick', 0.85);
        this.addDrumEvent(baseBeat + 2.0, 'kick', 0.8);
        // Rimshot on 2 and 4
        this.addDrumEvent(baseBeat + 1.0, 'rimshot', 0.7);
        this.addDrumEvent(baseBeat + 3.0, 'rimshot', 0.75);
        // Steady hat ticks
        for (let b = 0; b < beatsPerMeasure; b += 0.5) {
          this.addDrumEvent(baseBeat + b, 'closed_hat', 0.5);
        }
      } else if (grooveType === 'gentle_afternoon_waltz') {
        // 3/4 time
        this.addDrumEvent(baseBeat + 0.0, 'kick', 0.85);
        this.addDrumEvent(baseBeat + 1.0, 'rimshot', 0.55);
        this.addDrumEvent(baseBeat + 2.0, 'rimshot', 0.55);
      }
    }
  }

  /**
   * Renders the entire project into a 44.1kHz 16-bit PCM AudioBuffer.
   */
  renderToBuffer() {
    // 1. Determine total length
    let maxBeat = 0;
    for (const [tName, events] of Object.entries(this.tracks)) {
      for (const ev of events) {
        const endBeat = ev.beatStart + (ev.durationBeats || 1.0);
        if (endBeat > maxBeat) maxBeat = endBeat;
      }
    }

    const totalDurationSec = (maxBeat * this.secPerBeat) + 1.5;
    const totalSamples = Math.ceil(totalDurationSec * this.sampleRate);
    const masterBuffer = new Float32Array(totalSamples);

    // 2. Render Drums
    const drumGain = this.trackGains.drums;
    for (const d of this.tracks.drums) {
      const startSample = Math.floor(d.beatStart * this.secPerBeat * this.sampleRate);
      let drumWave = null;
      if (d.type === 'kick') drumWave = synthesizeKick(0.35, this.sampleRate);
      else if (d.type === 'snare') drumWave = synthesizeSnare(0.28, this.sampleRate);
      else if (d.type === 'closed_hat') drumWave = synthesizeClosedHat(0.06, this.sampleRate);
      else if (d.type === 'open_hat') drumWave = synthesizeOpenHat(0.35, this.sampleRate);
      else if (d.type === 'rimshot') drumWave = synthesizeRimshot(0.08, this.sampleRate);

      if (drumWave) {
        for (let i = 0; i < drumWave.length; i++) {
          const idx = startSample + i;
          if (idx < totalSamples) {
            masterBuffer[idx] += drumWave[i] * (d.velocity || 0.8) * drumGain;
          }
        }
      }
    }

    // 3. Render Melodic Tracks (Bass, Chords, Pad, Lead)
    for (const trackName of ['bass', 'chords', 'pad', 'lead']) {
      const instName = this.instruments[trackName];
      const gain = this.trackGains[trackName];
      const notes = this.tracks[trackName];

      for (const n of notes) {
        const freq = midiToFreq(n.pitch);
        const durSec = n.durationBeats * this.secPerBeat;
        const noteWave = synthesizeInstrumentNote(instName, freq, durSec, n.velocity || 0.85, this.sampleRate);
        const startSample = Math.floor(n.beatStart * this.secPerBeat * this.sampleRate);

        for (let i = 0; i < noteWave.length; i++) {
          const idx = startSample + i;
          if (idx < totalSamples) {
            masterBuffer[idx] += noteWave[i] * gain;
          }
        }
      }
    }

    // 4. Master Normalization & Peak Limiting
    let peak = 0.0;
    for (let i = 0; i < totalSamples; i++) {
      const absVal = Math.abs(masterBuffer[i]);
      if (absVal > peak) peak = absVal;
    }

    const targetPeak = 0.95;
    const scale = peak > 0 ? (targetPeak / Math.max(peak, targetPeak)) : 1.0;

    const pcm16 = new Int16Array(totalSamples);
    for (let i = 0; i < totalSamples; i++) {
      let sample = masterBuffer[i] * scale;
      // Soft saturation limiter
      if (sample > 1.0) sample = Math.tanh(sample);
      else if (sample < -1.0) sample = Math.tanh(sample);

      pcm16[i] = Math.max(-32768, Math.min(32767, Math.floor(sample * 32767)));
    }

    return {
      pcm16,
      totalSamples,
      totalDurationSec,
      sampleRate: this.sampleRate
    };
  }

  /**
   * Encodes PCM into standard RIFF WAV buffer.
   */
  exportWavBuffer() {
    const { pcm16, totalSamples, sampleRate } = this.renderToBuffer();
    const bytesPerSample = 2; // 16-bit
    const numChannels = 1;    // Mono
    const dataSize = totalSamples * bytesPerSample * numChannels;
    const buffer = Buffer.alloc(44 + dataSize);

    // RIFF header
    buffer.write('RIFF', 0);
    buffer.writeUInt32LE(36 + dataSize, 4);
    buffer.write('WAVE', 8);

    // fmt sub-chunk
    buffer.write('fmt ', 12);
    buffer.writeUInt32LE(16, 16);             // Subchunk1Size
    buffer.writeUInt16LE(1, 20);              // PCM format = 1
    buffer.writeUInt16LE(numChannels, 22);    // Mono
    buffer.writeUInt32LE(sampleRate, 24);     // SampleRate
    buffer.writeUInt32LE(sampleRate * bytesPerSample * numChannels, 28); // ByteRate
    buffer.writeUInt16LE(bytesPerSample * numChannels, 32);              // BlockAlign
    buffer.writeUInt16LE(16, 34);             // BitsPerSample

    // data sub-chunk
    buffer.write('data', 36);
    buffer.writeUInt32LE(dataSize, 40);

    for (let i = 0; i < totalSamples; i++) {
      buffer.writeInt16LE(pcm16[i], 44 + i * 2);
    }

    return buffer;
  }

  /**
   * Generates a standard multi-channel MIDI file format 0 buffer.
   */
  exportMidiBuffer() {
    const tpq = 480;
    const events = [];

    // Tempo meta-event
    const microsec = Math.floor(60000000 / this.bpm);
    events.push({
      tick: 0,
      bytes: [0xFF, 0x51, 0x03, (microsec >> 16) & 0xFF, (microsec >> 8) & 0xFF, microsec & 0xFF]
    });

    // Helper for adding notes
    const addMidiNote = (beatStart, durBeats, pitch, velocity, channel) => {
      const startTick = Math.floor(beatStart * tpq);
      const durTicks = Math.floor(durBeats * tpq);
      events.push({
        tick: startTick,
        bytes: [0x90 | (channel & 0x0F), pitch & 0x7F, velocity & 0x7F]
      });
      events.push({
        tick: startTick + durTicks,
        bytes: [0x80 | (channel & 0x0F), pitch & 0x7F, 0]
      });
    };

    // Channel 9 (10 in 1-based indexing) is General MIDI Percussion
    const drumPitchMap = {
      kick: 36,       // Bass Drum 1
      snare: 38,      // Acoustic Snare
      closed_hat: 42, // Closed Hi-Hat
      open_hat: 46,   // Open Hi-Hat
      rimshot: 37     // Side Stick
    };

    for (const d of this.tracks.drums) {
      const pitch = drumPitchMap[d.type] || 38;
      addMidiNote(d.beatStart, 0.25, pitch, Math.floor((d.velocity || 0.8) * 127), 9);
    }

    // Chords: Channel 0
    for (const n of this.tracks.chords) {
      addMidiNote(n.beatStart, n.durationBeats, n.pitch, Math.floor((n.velocity || 0.8) * 127), 0);
    }
    // Bass: Channel 1
    for (const n of this.tracks.bass) {
      addMidiNote(n.beatStart, n.durationBeats, n.pitch, Math.floor((n.velocity || 0.8) * 127), 1);
    }
    // Pad: Channel 2
    for (const n of this.tracks.pad) {
      addMidiNote(n.beatStart, n.durationBeats, n.pitch, Math.floor((n.velocity || 0.8) * 127), 2);
    }
    // Lead: Channel 3
    for (const n of this.tracks.lead) {
      addMidiNote(n.beatStart, n.durationBeats, n.pitch, Math.floor((n.velocity || 0.8) * 127), 3);
    }

    // Sort events by absolute tick
    events.sort((a, b) => a.tick - b.tick);

    // Encode to variable-length quantity delta times
    function encodeVLQ(num) {
      const res = [num & 0x7F];
      while ((num >>= 7)) {
        res.push((num & 0x7F) | 0x80);
      }
      return res.reverse();
    }

    const trackBytes = [];
    let lastTick = 0;
    for (const ev of events) {
      const delta = ev.tick - lastTick;
      trackBytes.push(...encodeVLQ(delta));
      trackBytes.push(...ev.bytes);
      lastTick = ev.tick;
    }
    // End of track event
    trackBytes.push(...encodeVLQ(0));
    trackBytes.push(0xFF, 0x2F, 0x00);

    // MThd chunk
    const header = Buffer.alloc(14);
    header.write('MThd', 0);
    header.writeUInt32BE(6, 4);
    header.writeUInt16BE(0, 8);   // Format 0 (single multi-channel track)
    header.writeUInt16BE(1, 10);  // 1 track
    header.writeUInt16BE(tpq, 12);// Ticks per quarter note

    // MTrk chunk
    const trackHeader = Buffer.alloc(8);
    trackHeader.write('MTrk', 0);
    trackHeader.writeUInt32BE(trackBytes.length, 4);

    return Buffer.concat([header, trackHeader, Buffer.from(trackBytes)]);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. CLI INTERFACE (INVOKED BY ARIA OR PYTHON BRIDGE)
// ─────────────────────────────────────────────────────────────────────────────

if (process.argv[1] && process.argv[1].endsWith('aria_music_engine.mjs')) {
  const args = process.argv.slice(2);
  if (args.length >= 3) {
    const [scorePath, wavOutPath, midiOutPath] = args;
    try {
      const scoreData = JSON.parse(fs.readFileSync(scorePath, 'utf8'));
      const project = new MultiTrackProject(scoreData.bpm || 76);

      // Load instruments
      if (scoreData.instruments) {
        Object.assign(project.instruments, scoreData.instruments);
      }

      // Load groove
      if (scoreData.groove) {
        project.applyDrumPattern(scoreData.numMeasures || 4, 4, scoreData.groove);
      }

      // Load explicit drum events
      if (scoreData.drums) {
        for (const d of scoreData.drums) project.addDrumEvent(d.beatStart, d.type, d.velocity);
      }

      // Load tracks
      for (const tName of ['bass', 'chords', 'pad', 'lead']) {
        if (scoreData[tName]) {
          for (const n of scoreData[tName]) {
            project.addNote(tName, n.beatStart, n.durationBeats, n.pitch, n.velocity);
          }
        }
      }

      // Render WAV
      const wavBuf = project.exportWavBuffer();
      fs.mkdirSync(path.dirname(wavOutPath), { recursive: true });
      fs.writeFileSync(wavOutPath, wavBuf);

      // Render MIDI
      const midiBuf = project.exportMidiBuffer();
      fs.mkdirSync(path.dirname(midiOutPath), { recursive: true });
      fs.writeFileSync(midiOutPath, midiBuf);

      console.log(JSON.stringify({
        success: true,
        wav_path: wavOutPath,
        midi_path: midiOutPath,
        bytes_wav: wavBuf.length,
        bytes_midi: midiBuf.length,
        bpm: project.bpm,
        message: 'Aria music piece rendered successfully via Node.js Web Audio engine!'
      }));
    } catch (err) {
      console.error(JSON.stringify({ success: false, error: err.message, stack: err.stack }));
      process.exit(1);
    }
  } else {
    console.log(JSON.stringify({
      name: "Aria Multi-Track Music Engine (Node.js)",
      usage: "node aria_music_engine.mjs <score.json> <out.wav> <out.mid>"
    }));
  }
}
