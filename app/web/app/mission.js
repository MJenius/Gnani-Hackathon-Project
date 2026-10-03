'use client';
import { useEffect, useRef, useState } from 'react';
import { captureWav } from './capture';

const GOAL="I'm running late for my meeting. Tell Ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn't add more than five minutes.";
const labels={PLANNED:'Queued',READY:'Ready',EXECUTING:'Checking',WAITING_ON_EXTERNAL:'Waiting on Ananya',REPLANNING:'Replanning',AWAITING_CONFIRMATION:'Needs approval',COMPLETED:'Done',BLOCKED:'Needs attention',SKIPPED:'Omitted',CANCELLED:'Cancelled',FAILED:'Failed'};
const time=value => { if (!value) return '—'; const [h,m]=value.split(':').map(Number); return `${h%12 || 12}:${String(m).padStart(2,'0')} ${h>=12?'PM':'AM'}`; };

export default function MissionDashboard() {
  const [goal,setGoal]=useState(GOAL);
  const [mission,setMission]=useState(null);
  const [playing,setPlaying]=useState(false);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [heard,setHeard]=useState('');
  const [capabilities,setCapabilities]=useState(null),[voiceMode,setVoiceMode]=useState('speech_test'),[language,setLanguage]=useState('en-IN'),[recording,setRecording]=useState(false),[audioUrl,setAudioUrl]=useState('');
  const stopCapture=useRef(null),captureTimer=useRef(null),audioPlayer=useRef(null),voiceRequest=useRef(null);
  const state=useRef(null),lock=useRef(false),recognition=useRef(null),lastSpoken=useRef(0),startRequest=useRef(null);
  const waiters=useRef([]);
  function accept(value) { state.current=value;setMission(value);localStorage.setItem('driveos-mission',value.id); }
  useEffect(() => {
    fetch('/api/health').then(response=>response.json()).then(setCapabilities).catch(()=>setError('API unavailable.'));
    const id=localStorage.getItem('driveos-mission');
    if (id) fetch('/api/missions/'+encodeURIComponent(id)).then(response => response.ok?response.json():null).then(value => {
      if (value) { accept(value);lastSpoken.current=value.events.length;setPlaying(value.status==='EXECUTING' && localStorage.getItem('driveos-running')!=='false'); }
    }).catch(() => setError('Could not restore the saved mission.'));
    return () => { recognition.current?.abort();clearTimeout(captureTimer.current);stopCapture.current?.(); };
  },[]);
  useEffect(() => { localStorage.setItem('driveos-running',String(playing)); },[playing]);
  useEffect(() => {
    if (!playing) return;
    const timer=setInterval(() => {
      const value=state.current;
      if (value?.status==='EXECUTING') send('advance');
      else setPlaying(false);
    },1100);
    return () => clearInterval(timer);
  },[playing]);
  useEffect(() => {
    if (!mission) return;
    const fresh=mission.events.filter(event => event.id>lastSpoken.current && ['REPLANNING','COMPLETED','ESCALATED','AWAITING_CONFIRMATION'].includes(event.status));
    lastSpoken.current=mission.events.length;
    if (fresh.length && mission.mode!=='simulation') {
      if (['COMPLETED','ESCALATED','AWAITING_CONFIRMATION'].includes(mission.status))
        speakResult(mission);
    } else if (fresh.length && 'speechSynthesis' in window) { window.speechSynthesis.cancel();window.speechSynthesis.speak(new SpeechSynthesisUtterance(fresh[fresh.length-1].message)); }
  },[mission]);

  async function speakResult(current=state.current) {
    try {
      const response=await fetch(`/api/missions/${current.id}/speech`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_revision:current.revision})});
      const value=await response.json();if (!response.ok) throw new Error(value.detail || 'Speech unavailable');
      if(state.current?.id===current.id && state.current?.revision===current.revision) {setError('');playAudio(value);}
    } catch(failure) {if(state.current?.id===current.id && state.current?.revision===current.revision) setError('Mission saved. Timbre: '+failure.message);}
    finally {fetch('/api/health').then(response=>response.json()).then(setCapabilities).catch(()=>{});}
  }

  function playAudio(value) {
    if (value.audio_base64) {setAudioUrl('data:audio/wav;base64,'+value.audio_base64);}
    if (value.speech_error) setError('Mission saved. Timbre: '+value.speech_error);
  }
  useEffect(()=>{if (audioUrl) audioPlayer.current?.play().catch(()=>setError('Press play to hear the Timbre response.'));},[audioUrl]);
  async function submitVoice() {
    const request=voiceRequest.current;if (!request || lock.current) return;
    lock.current=true;setBusy(true);setError('');
    try {
      const form=new FormData();form.append('audio',request.audio,'mission.wav');
      for (const [key,value] of Object.entries(request.fields)) form.append(key,value);
      const response=await fetch('/api/voice/missions',{method:'POST',body:form});const value=await response.json();
      if (!response.ok) throw new Error(typeof value.detail==='string'?value.detail:'Voice mission rejected');
      setHeard(value.transcript);lastSpoken.current=value.events.length;accept(value);playAudio(value);voiceRequest.current=null;setPlaying(value.status==='EXECUTING');
    } catch(failure) {setError(failure.message);} finally {lock.current=false;setBusy(false);waiters.current.shift()?.();fetch('/api/health').then(response=>response.json()).then(setCapabilities).catch(()=>{});}
  }
  async function voice() {
    if (stopCapture.current) {
      clearTimeout(captureTimer.current);setRecording(false);const stop=stopCapture.current;stopCapture.current=null;
      try {
        const audio=await stop();voiceRequest.current={audio,fields:{request_key:crypto.randomUUID(),authorized:'true',mode:voiceMode,language,persistent_mission:'true',demo:'parking-change'}};
        await submitVoice();
      } catch(failure) {setError(failure.message);} return;
    }
    setBusy(true);
    setPlaying(false);window.speechSynthesis?.cancel();audioPlayer.current?.pause();setAudioUrl('');
    try {stopCapture.current=await captureWav();setRecording(true);captureTimer.current=setTimeout(()=>voice(),15000);} catch(failure) {setError(failure.message);} finally {setBusy(false);}
  }

  async function send(operation,extra={}) {
    if (!state.current) return false;
    if (lock.current) {
      if (operation==='advance') return false;
      await new Promise(resolve => waiters.current.push(resolve));
      return send(operation,extra);
    }
    lock.current=true;setBusy(true);setError('');
    const current=state.current;
    try {
      const response=await fetch(`/api/missions/${current.id}/${operation}`,{
        method:['world','requirements'].includes(operation)?'PATCH':'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({request_key:crypto.randomUUID(),expected_revision:current.revision,...extra})});
      const value=await response.json();
      if (response.status===409) {
        const latest=await fetch('/api/missions/'+current.id);if (latest.ok) accept(await latest.json());
        throw new Error('The mission changed. Review the current state and retry.');
      }
      if (!response.ok) throw new Error(typeof value.detail==='string'?value.detail:'Mission update was rejected.');
      accept(value);return true;
    } catch (failure) { setError(failure.message);setPlaying(false);return false; }
    finally { lock.current=false;setBusy(false);waiters.current.shift()?.(); }
  }
  async function start(text=goal,demo='none') {
    if (lock.current) return;
    lock.current=true;setBusy(true);setError('');
    // Retain a start key across network retries, never create two missions accidentally.
    if (!startRequest.current || startRequest.current.transcript!==text || startRequest.current.demo!==demo)
      startRequest.current={transcript:text,request_key:crypto.randomUUID(),authorized:true,demo};
    try {
      const response=await fetch('/api/missions/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(startRequest.current)});
      const value=await response.json();if (!response.ok) throw new Error(typeof value.detail==='string'?value.detail:'Could not start mission.');
      lastSpoken.current=0;accept(value);startRequest.current=null;setPlaying(value.status==='EXECUTING');
    } catch (failure) { setError(failure.message); }
    finally {lock.current=false;setBusy(false);waiters.current.shift()?.();}
  }
  async function change(operation,changes) {
    if (await send(operation,{changes})) setPlaying(true);
  }
  async function confirm(approved) {
    const pending=state.current?.confirmation;if (!pending) return;
    if (await send('confirm',{confirmation_id:pending.id,approved})) setPlaying(true);
  }
  function listen() {
    const Recognizer=window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognizer) {setError('Browser voice is unavailable; use the mission controls.');return;}
    window.speechSynthesis?.cancel();
    const mic=new Recognizer();recognition.current=mic;mic.lang='en-IN';mic.interimResults=false;
    mic.onresult=event => {
      const text=event.results[0][0].transcript;setHeard(text);
      const normalized=text.toLowerCase().replace(/[.!?]/g,'').trim();
      if (!state.current) {setGoal(text);start(text);return;}
      if (['skip fuel','no fuel','remove fuel'].includes(normalized)) change('requirements',{include_fuel:false});
      else if (['limit detour to three minutes','limit detour to 3 minutes'].includes(normalized)) change('requirements',{max_detour_minutes:3});
      else if (['approve four forty five','approve 4:45'].includes(normalized) && state.current.confirmation?.arguments.time==='16:45') confirm(true);
      else setError('Say “skip fuel”, “limit detour to three minutes”, or “approve four forty five” when that action is shown.');
    };
    mic.onerror=event => setError('Voice input: '+event.error);
    try {mic.start();} catch (failure) {setError(failure.message);}
  }

  const active=mission?.engine_version===2;
  const call=mission?.world.contact.call_state || 'IDLE';
  const replans=mission?.events.filter(event => event.status==='REPLANNING') || [];
  const voiceCalls=voiceMode==='live'?4:3;
  const budgetBlocked=capabilities?.request_budget?.remaining<voiceCalls;
  return <main className="v2">
    <header><strong>DriveOS<span>●</span></strong><small>MISSION ENGINE V2 · SYNTHETIC WORLD</small></header>
    <section className="intro"><p className="eyebrow">KEEP DRIVING. THE MISSION CONTINUES.</p><h1>One mission.<br/>Ready for change.</h1><p>Meeting, parking and fuel, handled together.</p></section>
    <section className="mission" aria-label="Active mission">
      <div className="heading"><h2>YOUR MISSION</h2><span role="status">{mission?.status.replaceAll('_',' ') || 'READY'}</span></div>
      <h3>{active?mission.goal:'Get to the meeting with the details handled'}</h3>
      {!active && <><label htmlFor="v2goal">Mission goal</label><textarea id="v2goal" value={goal} onChange={event => {setGoal(event.target.value);startRequest.current=null;}} disabled={busy}/></>}
      <div className="controls"><button className="primary" disabled={busy || recording} onClick={() => start(goal)}>Start mission</button><button disabled={busy || recording} onClick={() => start(GOAL,'parking-change')}>Run changing-world demo</button><button onClick={listen} disabled={busy || recording}>Browser voice {active?'change':'mission'}</button>{active && <button onClick={() => setPlaying(!playing)} disabled={busy || mission.status!=='EXECUTING'}>{playing?'Pause demo':'Continue mission'}</button>}</div>
      <p className="note">Deterministic simulation. Starting authorizes the requested demo contact and calendar actions. The changing-world demo fills the garage after selection, then replans autonomously. No real calls, purchases or reservations. Closing this console pauses progression; mission state is saved.</p>
      <div className="controls" aria-label="Gnani voice mission"><label>Planner <select disabled={recording || busy} value={voiceMode} onChange={event=>setVoiceMode(event.target.value)}><option value="speech_test">Prisma / MockEvon / Timbre</option><option value="live" disabled={!capabilities?.evon_configured}>Prisma / Evon / Timbre {capabilities?.evon_configured?'':'(unavailable)'}</option></select></label><label>Speech language <select disabled={recording || busy} value={language} onChange={event=>setLanguage(event.target.value)}><option value="en-IN">English</option><option value="kn-IN">Kannada</option><option value="hi-IN">Hindi / Hinglish</option></select></label><button className="primary" disabled={busy || !capabilities?.speech_configured || (!recording && budgetBlocked)} onClick={voice}>{recording?'Stop and run voice mission':'Start Gnani voice mission'}</button>{voiceRequest.current && <button disabled={busy} onClick={submitVoice}>Retry same recording</button>}</div>
      <p className="note" role="status">{recording?'Microphone recording · up to 15 seconds':capabilities?.speech_configured?'Real Prisma and Timbre; synthetic external actions. MockEvon supports documented fixtures only.':'Configure backend Gnani credentials to enable real speech.'}</p>
      {capabilities?.request_budget && <p className="note" role="status">Local request allowance: {capabilities.request_budget.remaining} calls left ({capabilities.request_budget.used} used of {capabilities.request_budget.maximum}). {budgetBlocked?`A new voice mission needs ${voiceCalls} calls. Voice start is paused until the free-credit balance is checked and the local allowance is updated.`:'This allowance counts requests, not provider credits.'}</p>}
      {audioUrl && <audio ref={audioPlayer} src={audioUrl} controls aria-label="Timbre mission response"/>}
      {active && mission.mode!=='simulation' && ['COMPLETED','ESCALATED','AWAITING_CONFIRMATION'].includes(mission.status) && <button disabled={busy} onClick={()=>speakResult()}>Speak current result with Timbre</button>}
      {error && <p className="error" role="alert">{error}</p>}{heard && <p className="note">Heard: {heard}</p>}
      {active && <>
        <div className="mission-metrics"><div><span>Current action</span><strong>{mission.current_action}</strong></div><div><span>Call with Ananya</span><strong>{call.replaceAll('_',' ')}</strong></div><div><span>Simulated ETA</span><strong>{time(mission.eta.arrival)}</strong><small>+{mission.eta.added_minutes} min route detour</small></div></div>
        {mission.confirmation && <aside className="confirmation" aria-label="Action confirmation"><h4>Decision needed</h4><p>{mission.confirmation.label}. {mission.confirmation.action==='plan.review'?'No action runs until the proposed plan is approved.':'This is outside the original meeting-time mandate.'}</p><button className="primary" disabled={busy} onClick={() => confirm(true)}>Approve exact action</button> <button disabled={busy} onClick={() => confirm(false)}>Decline</button></aside>}
        <section aria-label="Task timeline"><h2>TASK TIMELINE</h2><ol className="tasks">{mission.tasks.map((task,index) => <li key={task.id} data-state={task.status}><span className="task-number">{index+1}</span><div><strong>{task.description}</strong><p>{labels[task.status]}{task.output?.name?` · ${task.output.name}`:''}</p>{task.dependencies.length>0 && <small>After {task.dependencies.map(id => mission.tasks.find(item => item.id===id)?.description).join(', ')}</small>}<details><summary>Progress history</summary>{task.history.map((item,i) => <p key={i}>{item.message}</p>)}</details></div><span className="task-state">{labels[task.status]}</span></li>)}</ol></section>
        <div className="route-summary"><h2>ROUTE & MEETING</h2><p>Meeting: {time(mission.world.calendar.time)} · Parking: {mission.route.parking?.name || 'Not selected'} · Fuel: {mission.route.fuel?.name || 'Not selected'}</p></div>
        <section aria-label="Mid-mission requirements"><h2>CHANGE A REQUIREMENT</h2><div className="controls"><label>Maximum added route time <select value={mission.requirements.max_detour_minutes} disabled={busy} onChange={event => change('requirements',{max_detour_minutes:Number(event.target.value)})}><option value={5}>5 minutes</option><option value={3}>3 minutes</option><option value={2}>2 minutes</option><option value={0}>No detour</option></select></label><label><input type="checkbox" checked={mission.requirements.include_fuel} disabled={busy} onChange={event => change('requirements',{include_fuel:event.target.checked})}/> Include fuel stop</label></div><p className="note">You can also say “skip fuel” or “limit detour to three minutes”. Completed calls and calendar actions are retained.</p></section>
        <section aria-label="Replanning events"><h2>REPLANNING</h2>{replans.length?<ol>{replans.map(event => <li key={event.id}><span>REPLAN</span>{event.message}</li>)}</ol>:<p className="note">The mission is following the current plan.</p>}</section>
        <details className="world-controls"><summary>Change the simulated external world</summary><div className="controls"><button disabled={busy} onClick={() => change('world',{parking_full:true})}>Garage becomes full</button><button disabled={busy} onClick={() => change('world',{contact_response:'rejected'})}>Ananya declines 4:30</button><button disabled={busy} onClick={() => change('world',{contact_response:'no_answer'})}>Ananya does not answer</button><button disabled={busy} onClick={() => change('world',{fuel_detour_minutes:8})}>Fuel adds 8 minutes</button><button disabled={busy} onClick={() => change('world',{base_travel_minutes:28})}>Traffic slows route</button></div><p className="note">Use these during execution. The demo clock advances one persisted transition each second. Changing completed routing can reopen those tasks without repeating contact or calendar effects.</p></details>
        <details><summary>Mission action log</summary><ol>{mission.events.map(event => <li key={event.id}><span>{event.status}</span>{event.message}</li>)}</ol></details>
        {['COMPLETED','ESCALATED','CANCELLED'].includes(mission.status) && <p className="outcome" aria-label="Completion outcome">{mission.spoken_response}</p>}
      </>}
    </section><footer>{mission?.planner || 'MockEvon'} · Frozen planning contract · Deterministic policy · Persistent mission state</footer>
  </main>;
}
