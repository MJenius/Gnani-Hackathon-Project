// Native browser PCM capture → mono WAV, sent to backend Prisma only on submission.
export async function captureWav() {
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia)
    throw new Error('Microphone capture requires localhost or HTTPS in a supported browser.');
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
  let context;
  try {
    context = new AudioContext({ sampleRate: 16000 });
    await context.resume();
    const source = context.createMediaStreamSource(stream);
    // ponytail: ScriptProcessor is widely supported but deprecated; move to AudioWorklet for streaming.
    const processor = context.createScriptProcessor(4096, 1, 1);
    const mute = context.createGain(); mute.gain.value = 0;
    const samples = [];
    processor.onaudioprocess = event => samples.push(new Float32Array(event.inputBuffer.getChannelData(0)));
    source.connect(processor); processor.connect(mute); mute.connect(context.destination);
    let stopped = false;
    return async function stop() {
      if (stopped) return null;
      stopped = true;
      processor.disconnect(); source.disconnect(); mute.disconnect();
      stream.getTracks().forEach(track => track.stop());
      const rate = context.sampleRate;
      await context.close();
      const count = samples.reduce((total, chunk) => total + chunk.length, 0);
      if (!count) throw new Error('No audio captured. Record the full request before stopping.');
      const buffer = new ArrayBuffer(44 + count * 2);
      const view = new DataView(buffer);
      const string = (offset, value) => [...value].forEach((letter, i) => view.setUint8(offset + i, letter.charCodeAt(0)));
      string(0, 'RIFF'); view.setUint32(4, 36 + count * 2, true); string(8, 'WAVE'); string(12, 'fmt ');
      view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
      view.setUint32(24, rate, true); view.setUint32(28, rate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
      string(36, 'data'); view.setUint32(40, count * 2, true);
      let offset = 44;
      samples.forEach(chunk => chunk.forEach(sample => { const value = Math.max(-1, Math.min(1, sample)); view.setInt16(offset, value < 0 ? value * 32768 : value * 32767, true); offset += 2; }));
      return new Blob([buffer], { type: 'audio/wav' });
    };
  } catch (error) {
    stream.getTracks().forEach(track => track.stop());
    if (context) await context.close();
    throw error;
  }
}
