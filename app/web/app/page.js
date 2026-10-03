'use client';
import { useRef, useState } from 'react';

export default function Home() {
  const [transcript, setTranscript] = useState('Tell Ananya I am 25 minutes late.');
  const [mission, setMission] = useState(null);
  const [status, setStatus] = useState('Ready');
  const [language, setLanguage] = useState('en-IN');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const request = useRef(null);
  const recognition = useRef(null);

  async function run(text) {
    if (busy) return;
    setBusy(true); setError(''); setMission(null); setStatus('Working');
    if (!request.current || request.current.transcript !== text)
      request.current = { transcript: text, request_key: crypto.randomUUID(), authorized: true };
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
    <header><strong>DriveOS<span>●</span></strong><small>SIMULATION · BROWSER VOICE</small></header>
    <section className="intro"><p className="eyebrow">YOU DRIVE. IT HANDLES THE REST.</p><h1>Stay focused.<br/>Delegate the details.</h1><p>One mission. A clear outcome.</p></section>
    <section className="mission" aria-label="Mission console"><div className="heading"><h2>MISSION</h2><span role="status">{status}</span></div>
      <h3>{mission?.tasks.length ? mission.tasks[0].description : 'Let Ananya know you’re running late'}</h3>
      <label htmlFor="request">Your request</label><textarea id="request" value={transcript} onChange={event => {setTranscript(event.target.value); request.current = null;}} disabled={busy}/>
      <div className="controls"><label>Voice language <select value={language} onChange={event => setLanguage(event.target.value)} disabled={busy}><option value="en-IN">English</option><option value="hi-IN">Hindi</option><option value="kn-IN">Kannada</option></select></label><button onClick={listen} disabled={busy}>Use microphone</button><button className="primary" onClick={() => run(transcript)} disabled={busy || !transcript.trim()}>Run demo mission</button></div>
      <p className="note">Running authorizes one synthetic notification to Ananya. Nothing is sent to a real person. The current planner supports the English example above; multilingual planning comes next.</p>
      {error && <p role="alert" className="error">{error}</p>}
      {mission && <><ol>{mission.events.map((event, index) => <li key={index}><span>{event.status}</span>{event.message}</li>)}</ol><p className="outcome">{mission.spoken_response}</p></>}
    </section><footer>Mission engine first. Real Gnani integration pending credentials and verified API contracts.</footer>
  </main>;
}
