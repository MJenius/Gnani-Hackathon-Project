'use client';
import { useEffect, useRef, useState } from 'react';
import { captureWav } from './capture';
import MissionDashboard from './mission';

function SpeechConsole() {
  const signature = "I'm running late for my meeting. Tell Ananya, ask if 4:30 works, find parking, and get fuel if it doesn't add more than five minutes.";
  const [transcript, setTranscript] = useState(signature);
  const [scenario, setScenario] = useState({ contact_response: 'accepted', parking_full: false, max_detour_minutes: 5 });
  const [mission, setMission] = useState(null);
  const [status, setStatus] = useState('Ready');
  const [language, setLanguage] = useState('en-IN');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState('simulation');
  const [caps, setCaps] = useState({});
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const stopCapture = useRef(null);
  const stopTimer = useRef(null);
  const request = useRef(null);
  const recognition = useRef(null);
  useEffect(() => {
    fetch('/api/health').then(response => response.json()).then(setCaps).catch(() => {});
    return () => { clearTimeout(stopTimer.current); stopCapture.current?.(); recognition.current?.abort(); };
  }, []);
  useEffect(() => () => { if (audioUrl) URL.revokeObjectURL(audioUrl); }, [audioUrl]);

  async function microphone() {
    if (mode === 'simulation') return listen();
    if (recording) return finishRecording();
    setError(''); setMission(null); setAudioUrl(null); setBusy(true);
    try {
      stopCapture.current = await captureWav();
      setRecording(true); setStatus('Listening · maximum 15 seconds');
      stopTimer.current = setTimeout(finishRecording, 15000);
    } catch (failure) { setError(failure.message); setBusy(false); setStatus('Ready'); }
  }

  async function finishRecording() {
    const stop = stopCapture.current;
    if (!stop) return;
    stopCapture.current = null; clearTimeout(stopTimer.current); setRecording(false);
    setStatus('Transcribing and running mission');
    try {
      const audio = await stop();
      const form = new FormData();
      form.append('audio', audio, 'utterance.wav'); form.append('language', language);
      form.append('request_key', crypto.randomUUID()); form.append('authorized', 'true'); form.append('mode', mode);
      const response = await fetch('/api/voice/missions', { method: 'POST', body: form });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Voice mission failed');
      setTranscript(result.transcript); setMission(result); setStatus(result.status);
      if (result.audio_base64) {
        const bytes = Uint8Array.from(atob(result.audio_base64), value => value.charCodeAt(0));
        setAudioUrl(URL.createObjectURL(new Blob([bytes], { type: 'audio/wav' })));
      }
      if (result.speech_error) setError(`Mission result is shown below. Spoken feedback unavailable: ${result.speech_error}`);
    } catch (failure) { setError(failure.message); setStatus('Failed'); }
    finally { setBusy(false); }
  }

  async function run(text) {
    if (busy) return;
    setBusy(true); setError(''); setMission(null); setAudioUrl(null); setStatus('Working');
    if (!request.current || request.current.transcript !== text || JSON.stringify(request.current.scenario) !== JSON.stringify(scenario))
      request.current = { transcript: text, request_key: crypto.randomUUID(), authorized: true, mode: 'simulation', scenario };
    try {
      const response = await fetch('/api/missions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request.current) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'Mission failed');
      setMission(result); setStatus(result.status);
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const speech = new SpeechSynthesisUtterance(result.spoken_response);
        speech.lang = language; window.speechSynthesis.speak(speech);
      }
    } catch (failure) { setError(failure.message); setStatus('Failed'); }
    finally { setBusy(false); }
  }

  function listen() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) { setError('Voice recognition is unavailable in this browser. Use the text field.'); return; }
    setError(''); setStatus('Listening'); setBusy(true);
    const mic = new SpeechRecognition(); recognition.current = mic;
    mic.lang = language; mic.interimResults = false;
    mic.onresult = event => { const text = event.results[0][0].transcript; setTranscript(text); setBusy(false); setStatus('Review heard request'); };
    mic.onerror = event => { setError(`Microphone: ${event.error}`); setBusy(false); setStatus('Ready'); };
    mic.onend = () => { setBusy(false); setStatus(value => value === 'Listening' ? 'Ready' : value); };
    try { mic.start(); } catch (failure) { setBusy(false); setError(failure.message); }
  }

  return <main>
    <header><strong>DriveOS<span>●</span></strong><small>{mode === 'simulation' ? 'SIMULATION · BROWSER VOICE' : mode === 'live' ? 'GNANI LIVE · SIMULATED TOOLS' : 'GNANI SPEECH · DEMO PLANNER'}</small></header>
    <section className="intro"><p className="eyebrow">YOU DRIVE. IT HANDLES THE REST.</p><h1>Stay focused.<br/>Delegate the details.</h1><p>One mission. A clear outcome.</p></section>
    <section className="mission" aria-label="Mission console"><div className="heading"><h2>MISSION</h2><span role="status">{status}</span></div>
      <h3>{mission?.tasks.length ? 'Your mission outcome' : 'Handle the meeting, parking and fuel'}</h3>
      <label htmlFor="request">Your request</label><textarea id="request" value={transcript} onChange={event => {setTranscript(event.target.value); request.current = null;}} disabled={busy}/>
      <div className="controls"><label>Mode <select value={mode} disabled={busy} onChange={event => {setMode(event.target.value);setMission(null);setAudioUrl(null);setError('');setStatus('Ready');}}><option value="simulation">Demo Simulation</option><option value="speech_test" disabled={!caps.speech_configured}>Gnani speech test</option><option value="live" disabled={!caps.speech_configured || !caps.evon_configured}>Gnani Live {caps.evon_configured ? '' : '(Evon unavailable)'}</option></select></label><label>Voice language <select value={language} onChange={event => setLanguage(event.target.value)} disabled={busy}><option value="en-IN">English</option><option value="hi-IN">Hindi</option><option value="kn-IN">Kannada</option></select></label><button onClick={microphone} disabled={busy && !recording}>{recording ? 'Stop and run mission' : mode === 'simulation' ? 'Use microphone' : 'Start voice mission'}</button>{mode === 'simulation' && <button className="primary" onClick={() => run(transcript)} disabled={busy || !transcript.trim()}>Run demo mission</button>}</div>
      {mode === 'simulation' && <div className="controls" aria-label="Simulated conditions"><label>Ananya’s reply <select value={scenario.contact_response} disabled={busy} onChange={event => setScenario({ ...scenario, contact_response: event.target.value })}><option value="accepted">Accepts 4:30</option><option value="rejected">Declines 4:30</option><option value="no_answer">No answer</option></select></label><label><input type="checkbox" checked={scenario.parking_full} disabled={busy} onChange={event => setScenario({ ...scenario, parking_full: event.target.checked })}/> Office garage is full</label><label>Added route time <select value={scenario.max_detour_minutes} disabled={busy} onChange={event => setScenario({ ...scenario, max_detour_minutes: Number(event.target.value) })}><option value={5}>Up to 5 minutes</option><option value={3}>Up to 3 minutes</option></select></label><button disabled={busy} onClick={() => setTranscript(signature)}>Meeting mission</button><button disabled={busy} onClick={() => setTranscript('Tell Ananya I am 25 minutes late.')}>Simple notification</button></div>}
      <p className="note">Running a mission authorizes synthetic contact and calendar actions. MockEvon uses known demo requests. Parking and fuel are route selections; no booking or purchase occurs. Gnani speech test uses real Prisma and Timbre. Live mode requires separately verified Evon. Record only synthetic requests.</p>
      {error && <p role="alert" className="error">{error}</p>}
      {audioUrl && <audio controls autoPlay src={audioUrl} aria-label="Timbre spoken confirmation"/>}
      {mission && <><ul aria-label="Mission tasks">{mission.tasks.map(task => <li key={task.id}>{task.description} · {task.status}{task.output?.name ? ` · ${task.output.name}` : ''}</li>)}</ul><ol>{mission.events.map((event, index) => <li key={index}><span>{event.status}</span>{event.message}</li>)}</ol><p className="outcome">{mission.spoken_response}</p></>}
    </section><footer>Prisma and Timbre speech adapters connected. External tools remain simulated. Evon inference is a separate deployment.</footer>
  </main>;
}

export default function Home() { return <><MissionDashboard/><details className="legacy-console"><summary>Existing speech adapter checks</summary><SpeechConsole/></details></>; }
