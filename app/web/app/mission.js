'use client';
import { useEffect, useRef, useState } from 'react';
import { captureWav } from './capture';
import HumanValidation from './validation';

const GOAL="I'm running late for my meeting. Tell Ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn't add more than five minutes.";
const FIXTURES={'en-IN':GOAL,'kn-IN':'ನಾನು ಸಭೆಗೆ ತಡವಾಗುತ್ತಿದ್ದೇನೆ. ಅನನ್ಯ ಅವರಿಗೆ ತಿಳಿಸಿ, ನಾಲ್ಕೂವರೆಗೆ ಆಗುತ್ತದೆಯೇ ಕೇಳಿ, ಅವರ ಕಚೇರಿ ಬಳಿ ಪಾರ್ಕಿಂಗ್ ಹುಡುಕಿ, ಐದು ನಿಮಿಷಕ್ಕಿಂತ ಹೆಚ್ಚು ಆಗದಿದ್ದರೆ ಇಂಧನ ತುಂಬಿಸಿ.','hi-IN':'Meeting ke liye late ho raha hoon. Ananya ko batao, 4:30 works poochho, office ke paas parking dhundo, aur fuel agar five minutes se zyada detour nahi hota.'};
const SCENARIOS=[['parking-change','Parking disappears'],['counter-offer','Ananya offers 4:45'],['no-answer','No answer · two attempts'],['fuel-budget','Fuel exceeds budget'],['requirement-change','User removes fuel'],['service-failure','Fuel service fails'],['late-arrival','Traffic makes arrival too late']];
const labels={PLANNED:'Queued',READY:'Ready',EXECUTING:'Checking',WAITING_ON_EXTERNAL:'Waiting on Ananya',REPLANNING:'Replanning',AWAITING_CONFIRMATION:'Needs approval',COMPLETED:'Done',BLOCKED:'Needs attention',SKIPPED:'Omitted',CANCELLED:'Cancelled',FAILED:'Failed'};
const time=value => { if (!value) return '—'; const [h,m]=value.split(':').map(Number); return `${h%12 || 12}:${String(m).padStart(2,'0')} ${h>=12?'PM':'AM'}`; };
const canonical=value=>Array.isArray(value)?value.map(canonical):value && typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])])):value;

export default function MissionDashboard() {
  const [goal,setGoal]=useState(GOAL);
  const [mission,setMission]=useState(null);
  const [playing,setPlaying]=useState(false);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [scenario,setScenario]=useState('parking-change'),[replayRequest,setReplayRequest]=useState(null),[guardResult,setGuardResult]=useState('');
  const [heard,setHeard]=useState('');
  const [voiceMissionId,setVoiceMissionId]=useState(null);
  const [captureStatus,setCaptureStatus]=useState('Not recorded'),[playbackStatus,setPlaybackStatus]=useState('Waiting for Timbre');
  const [capabilities,setCapabilities]=useState(null),[voiceMode,setVoiceMode]=useState('speech_test'),[language,setLanguage]=useState('en-IN'),[recording,setRecording]=useState(false),[audioUrl,setAudioUrl]=useState('');
  const stopCapture=useRef(null),captureTimer=useRef(null),audioPlayer=useRef(null),voiceRequest=useRef(null);
  const state=useRef(null),lock=useRef(false),recognition=useRef(null),lastSpoken=useRef(0),startRequest=useRef(null);
  const waiters=useRef([]);
  const staleConfirmation=useRef(null);
  function accept(value) {
    if (state.current?.id!==value.id) staleConfirmation.current=null;
    else if (state.current.confirmation && state.current.confirmation.id!==value.confirmation?.id) staleConfirmation.current=state.current.confirmation.id;
    state.current=value;setMission(value);localStorage.setItem('driveos-mission',value.id);
  }
  useEffect(() => {
    fetch('/api/health').then(response=>response.json()).then(setCapabilities).catch(()=>setError('API unavailable.'));
    const id=localStorage.getItem('driveos-mission');
    if (id) fetch('/api/missions/'+encodeURIComponent(id)).then(response => response.ok?response.json():null).then(value => {
      if (value) {
        accept(value);lastSpoken.current=value.events.length;setPlaying(value.status==='EXECUTING' && localStorage.getItem('driveos-running')!=='false');
        if (value.mode!=='simulation') {setHeard(value.transcript);setVoiceMissionId(value.id);setCaptureStatus('Saved voice mission restored · recording was completed');setPlaybackStatus('Use Speak current result with Timbre to restore audio');}
      }
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
    setPlaybackStatus('Requesting Timbre response');
    try {
      const response=await fetch(`/api/missions/${current.id}/speech`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_revision:current.revision})});
      const value=await response.json();if (!response.ok) throw new Error(value.detail || 'Speech unavailable');
      if(state.current?.id===current.id && state.current?.revision===current.revision) {setError('');playAudio(value);}
    } catch(failure) {if(state.current?.id===current.id && state.current?.revision===current.revision) {setPlaybackStatus('Timbre unavailable · retry saved result');setError('Mission saved. Timbre: '+failure.message);}}
    finally {fetch('/api/health').then(response=>response.json()).then(setCapabilities).catch(()=>{});}
  }

  function playAudio(value) {
    if (value.audio_base64) {setPlaybackStatus('Timbre audio ready');setAudioUrl('data:audio/wav;base64,'+value.audio_base64);}
    if (value.speech_error) {setPlaybackStatus('Timbre unavailable · retry saved result');setError('Mission saved. Timbre: '+value.speech_error);}
  }
  useEffect(()=>{if (audioUrl) audioPlayer.current?.play().catch(()=>{setPlaybackStatus('Autoplay blocked · press play');setError('Press play to hear the Timbre response.');});},[audioUrl]);
  async function submitVoice() {
    const request=voiceRequest.current;if (!request || lock.current) return;
    lock.current=true;setBusy(true);setError('');
    try {
      const form=new FormData();form.append('audio',request.audio,'mission.wav');
      for (const [key,value] of Object.entries(request.fields)) form.append(key,value);
      const response=await fetch('/api/voice/missions',{method:'POST',body:form});const value=await response.json();
      if (!response.ok) throw new Error(typeof value.detail==='string'?value.detail:'Voice mission rejected');
      setCaptureStatus('Recording completed · Prisma returned transcript');setHeard(value.transcript);setVoiceMissionId(value.id);lastSpoken.current=value.events.length;accept(value);playAudio(value);voiceRequest.current=null;setPlaying(value.status==='EXECUTING');
      if (['COMPLETED','ESCALATED','AWAITING_CONFIRMATION'].includes(value.status)) speakResult(value);
    } catch(failure) {setError(failure.message);} finally {lock.current=false;setBusy(false);waiters.current.shift()?.();fetch('/api/health').then(response=>response.json()).then(setCapabilities).catch(()=>{});}
  }
  async function voice() {
    if (lock.current) return;
    if (stopCapture.current) {
      lock.current=true;setBusy(true);clearTimeout(captureTimer.current);setRecording(false);setCaptureStatus('Recording stopped · sending WAV to Prisma');const stop=stopCapture.current;stopCapture.current=null;
      try {
        const audio=await stop();voiceRequest.current={audio,fields:{request_key:crypto.randomUUID(),authorized:'true',mode:voiceMode,language,persistent_mission:'true',demo:'parking-change'}};
        lock.current=false;
        await submitVoice();
      } catch(failure) {setCaptureStatus('Recording failed');setError(failure.message);lock.current=false;setBusy(false);waiters.current.shift()?.();} return;
    }
    lock.current=true;setBusy(true);setError('');setCaptureStatus('Waiting for microphone permission');
    setPlaying(false);window.speechSynthesis?.cancel();audioPlayer.current?.pause();setAudioUrl('');
    try {stopCapture.current=await captureWav();setHeard('');setVoiceMissionId(null);setCaptureStatus('Recording started · microphone permission granted');setPlaybackStatus('Waiting for Timbre');setRecording(true);captureTimer.current=setTimeout(()=>voice(),15000);} catch(failure) {setCaptureStatus('Capture failed');setError(failure.message);} finally {lock.current=false;setBusy(false);waiters.current.shift()?.();}
  }

  async function send(operation,extra={}) {
    if (!state.current || stopCapture.current) return false;
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
  async function start(text=goal,demo='none',run=true) {
    if (lock.current) return;
    setPlaying(false);window.speechSynthesis?.cancel();audioPlayer.current?.pause();setAudioUrl('');setHeard('');setCaptureStatus('Not recorded');setVoiceMissionId(null);
    lock.current=true;setBusy(true);setError('');
    // Retain a start key across network retries, never create two missions accidentally.
    if (!startRequest.current || startRequest.current.transcript!==text || startRequest.current.demo!==demo)
      startRequest.current={transcript:text,request_key:crypto.randomUUID(),authorized:true,demo};
    try {
      const response=await fetch('/api/missions/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(startRequest.current)});
      const value=await response.json();if (!response.ok) throw new Error(typeof value.detail==='string'?value.detail:'Could not start mission.');
      lastSpoken.current=0;accept(value);setReplayRequest({...startRequest.current});setGuardResult('');startRequest.current=null;setPlaying(run && value.status==='EXECUTING');
    } catch (failure) { setError(failure.message); }
    finally {lock.current=false;setBusy(false);waiters.current.shift()?.();}
  }
  async function resetDemo() {
    if (lock.current) return;
    setPlaying(false);state.current=null;setMission(null);setGoal(GOAL);setError('');setHeard('');setVoiceMissionId(null);setCaptureStatus('Not recorded');setPlaybackStatus('Waiting for Timbre');setAudioUrl('');setReplayRequest(null);setGuardResult('');voiceRequest.current=null;startRequest.current=null;lastSpoken.current=0;
    window.speechSynthesis?.cancel();audioPlayer.current?.pause();localStorage.removeItem('driveos-mission');
    await start(GOAL,'parking-change',false);
  }
  async function checkGuard(kind) {
    if (lock.current || !state.current) return;
    lock.current=true;setBusy(true);setGuardResult('');
    const current=state.current;
    try {
      const duplicate=kind==='duplicate';
      const body=duplicate?replayRequest:{request_key:crypto.randomUUID(),expected_revision:kind==='revision'?current.revision-1:current.revision,...(kind==='confirmation'?{confirmation_id:staleConfirmation.current,approved:true}:{})};
      const url=duplicate?'/api/missions/start':`/api/missions/${current.id}/${kind==='confirmation'?'confirm':'advance'}`;
      const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const value=await response.json();const restored=await fetch('/api/missions/'+current.id).then(r=>r.json());
      const unchanged=JSON.stringify(canonical(restored))===JSON.stringify(canonical(current));
      if ((duplicate?response.ok && value.id===current.id:response.status===409) && unchanged)
        setGuardResult(duplicate?'Duplicate request returned the same mission. No new effects.':'Stale '+kind+' rejected. Committed mission state is unchanged.');
      else throw new Error('Guard check did not match the expected preserved state.');
    } catch(failure) {setError(failure.message);} finally {lock.current=false;setBusy(false);waiters.current.shift()?.();}
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
  const voiceActive=active && voiceMissionId===mission.id;
  const voiceCalls=voiceMode==='live'?4:3;
  const budgetBlocked=capabilities?.request_budget?.remaining<voiceCalls;
  return <main className="v2">
    <header><strong>DriveOS<span>●</span></strong><small>MISSION ENGINE V2 · SYNTHETIC WORLD</small></header>
    <section className="intro"><p className="eyebrow">VOICE-FIRST MISSION EXECUTION</p><h1>You drive.<br/>It handles everything<br/>around the drive.</h1><p>One compound goal. Accountable actions. Recovery when the world changes.</p><div className="architecture-strip">Prisma hears <span>→</span> Interpreter proposes <span>→</span> Policy validates <span>→</span> DriveOS executes <span>→</span> Timbre speaks</div></section>
    <section className="mission" aria-label="Active mission">
      <div className="heading"><h2>YOUR MISSION</h2><span role="status">{mission?.status.replaceAll('_',' ') || 'READY'}</span></div>
      <h3>{active?mission.goal:'Get to the meeting with the details handled'}</h3>
      {active && <p className="note" aria-label="Mission identity">Mission ID: {mission.id} · revision {mission.revision}</p>}
      {!active && <><label htmlFor="v2goal">Mission goal</label><textarea id="v2goal" value={goal} onChange={event => {setGoal(event.target.value);startRequest.current=null;}} disabled={busy || recording}/></>}
      <div className="controls"><button className="primary" disabled={busy || recording} onClick={() => start(GOAL,'parking-change')}>Run changing-world demo</button><button className="primary" disabled={busy || !capabilities?.speech_configured || (!recording && budgetBlocked)} onClick={voice}>{recording?'Stop and run voice mission':'Start Gnani voice mission'}</button><button disabled={busy || recording} onClick={resetDemo}>Reset demo</button>{active && <button onClick={() => setPlaying(!playing)} disabled={busy || recording || mission.status!=='EXECUTING'}>{playing?'Pause demo':'Continue mission'}</button>}</div>
      <details><summary>Judge mode · bounded failure scenarios</summary><div className="controls"><label>Scenario <select value={scenario} disabled={busy || recording} onChange={event=>setScenario(event.target.value)}>{SCENARIOS.map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label><button disabled={busy || recording} onClick={()=>start(GOAL,scenario)}>Run scenario from clean world</button></div><p className="note">Each run creates an isolated synthetic world. Reset creates a fresh paused mission; Continue starts it. Existing mission records remain saved. Counter-offers pause for approval; failures escalate honestly.</p></details>
      <p className="note">Synthetic external actions · persistent mission state · {capabilities?.speech_configured?'Prisma / Timbre configured':'Configure Gnani for real voice'}{budgetBlocked?' · voice needs at least three remaining requests':''}.</p>
      <details open={!active}><summary>Voice settings · transcript fixtures · demo scope</summary>
      <p className="note">Starting authorizes the requested synthetic contact and calendar actions. The changing-world demo fills the garage after selection. No real calls, purchases or reservations. Closing this console pauses progression; mission state is saved.</p>
      <button disabled={busy || recording} onClick={() => start(goal)}>Run text mission</button>
      <div className="controls" aria-label="Gnani voice mission"><label>Planner <select disabled={recording || busy} value={voiceMode} onChange={event=>setVoiceMode(event.target.value)}><option value="speech_test">Prisma / DriveOS Interpreter / Timbre</option></select></label><label>Speech language <select disabled={recording || busy} value={language} onChange={event=>setLanguage(event.target.value)}><option value="en-IN">English</option><option value="kn-IN">Kannada</option><option value="hi-IN">Hindi / Hinglish</option></select></label>{voiceRequest.current && <button disabled={busy || recording} onClick={submitVoice}>Retry same recording</button>}</div>
      <p className="note" role="status">{recording?'Microphone recording · up to 15 seconds':capabilities?.speech_configured?'Real Prisma and Timbre; synthetic external actions. DriveOS Interpreter supports documented fixtures only (implemented by MockEvon; no model inference).':'Configure backend Gnani credentials to enable real speech.'}</p>
      <details><summary>What to say · {language==='kn-IN'?'Kannada':language==='hi-IN'?'Hinglish':'English'} fixture</summary><p className="fixture" lang={language.split('-')[0]}>{FIXTURES[language]}</p><p className="note">Finite fixture scope: Ananya, 4:30 and five shared detour minutes. Unsupported goals escalate. Spoken summaries are currently English.</p></details>
      {capabilities?.request_budget && <p className="note" role="status">Local request allowance: {capabilities.request_budget.remaining} calls left ({capabilities.request_budget.used} used of {capabilities.request_budget.maximum}). {budgetBlocked?`A new voice mission needs ${voiceCalls} calls. Voice start is paused until the free-credit balance is checked and the local allowance is updated.`:'This allowance counts requests, not provider credits.'}</p>}
      </details>
      {audioUrl && <audio ref={audioPlayer} src={audioUrl} controls aria-label="Timbre mission response" onPlaying={()=>setPlaybackStatus('Timbre playback started')} onEnded={()=>setPlaybackStatus('Timbre playback completed')} onError={()=>setPlaybackStatus('Playback failed · retry using the audio controls')}/>}
      {active && mission.mode!=='simulation' && ['COMPLETED','ESCALATED','AWAITING_CONFIRMATION'].includes(mission.status) && <button disabled={busy || recording} onClick={()=>speakResult()}>Speak current result with Timbre</button>}
      {captureStatus!=='Not recorded' && <section aria-label="Voice pipeline result" className="route-summary" aria-live="polite"><h2>VOICE MISSION RESULT</h2><p>Capture: {captureStatus}</p><p>Transcript: {heard?'Received from Prisma':'Waiting for transcription'}</p><p>Prisma transcript: {heard || 'Waiting for transcription'}</p><p>Mission: {voiceActive?'Created · '+mission.id:'Waiting for mission creation'} · {voiceActive?mission.status.replaceAll('_',' '):'Pending'}</p><p>Progress: {voiceActive?mission.current_action:'Waiting'} · Replans: {voiceActive?replans.length:0}</p><p>Final outcome: {voiceActive && ['COMPLETED','ESCALATED','CANCELLED'].includes(mission.status)?mission.spoken_response:'Not completed'}</p><p>{playbackStatus} · playback events do not prove that a person heard the audio.</p></section>}
      <HumanValidation request={GOAL} language={language}/>
      {error && <p className="error" role="alert">{error}</p>}{heard && <p className="note">Heard: {heard}</p>}
      {active && <>
        <div className="mission-metrics"><div><span>Current action</span><strong>{mission.current_action}</strong></div><div><span>Call with Ananya</span><strong>{call.replaceAll('_',' ')}</strong></div><div><span>Simulated ETA</span><strong>{time(mission.eta.arrival)}</strong><small>+{mission.eta.added_minutes} min route detour</small></div></div>
        <div className="constraint-chips"><span>Shared detour ≤ {mission.requirements.max_detour_minutes} min</span><span>Used {mission.eta.added_minutes} min</span><span>Fuel {mission.requirements.include_fuel?'optional within budget':'removed'}</span><span>World revision {mission.world.version}</span><span>{mission.mode==='simulation'?'Text rehearsal · browser speech fallback':'Real Prisma → Timbre'}</span></div>
        {replans.length>0 && <aside className="replan-banner" aria-live="polite"><p className="eyebrow">WORLD CHANGE → REPLANNING</p><strong>{replans[replans.length-1].message}</strong><p>Same mission · completed effects retained · {replans[replans.length-1].explanation?.selected_alternative || 'Checking the next valid action'}</p></aside>}
        {mission.confirmation && <aside className="confirmation" aria-label="Action confirmation"><h4>Decision needed</h4><p>{mission.confirmation.label}. {mission.confirmation.action==='plan.review'?'No action runs until the proposed plan is approved.':'This is outside the original meeting-time mandate.'}</p><button className="primary" disabled={busy || recording} onClick={() => confirm(true)}>Approve exact action</button> <button disabled={busy || recording} onClick={() => confirm(false)}>Decline</button></aside>}
        <section aria-label="Task timeline"><h2>TASK TIMELINE</h2><ol className="tasks">{mission.tasks.map((task,index) => <li key={task.id} data-state={task.status}><span className="task-number">{index+1}</span><div><strong>{task.description}</strong><p>{labels[task.status]}{task.output?.name?` · ${task.output.name}`:''}</p>{task.dependencies.length>0 && <small>After {task.dependencies.map(id => mission.tasks.find(item => item.id===id)?.description).join(', ')}</small>}<details><summary>Progress history</summary>{task.history.map((item,i) => <p key={i}>{item.message}</p>)}</details></div><span className="task-state">{labels[task.status]}</span></li>)}</ol></section>
        <div className="route-summary"><h2>WORLD / ROUTE & MEETING</h2><p>Meeting: {time(mission.world.calendar.time)} · Parking: {mission.route.parking?.name || 'Not selected'} · Fuel: {mission.route.fuel?.name || 'Not selected'}</p><p className="note">Office garage: {mission.world.parking[0].available?'available':'full'} · East lot: {mission.world.parking[1].available?'available':'full'} · Base travel: {mission.world.maps.base_minutes} min · Fuel service: {mission.world.fuel_service_failed?'failed':'available'}</p></div>
        <section aria-label="Mid-mission requirements"><h2>CHANGE A REQUIREMENT</h2><div className="controls"><label>Maximum added route time <select value={mission.requirements.max_detour_minutes} disabled={busy || recording} onChange={event => change('requirements',{max_detour_minutes:Number(event.target.value)})}><option value={5}>5 minutes</option><option value={3}>3 minutes</option><option value={2}>2 minutes</option><option value={0}>No detour</option></select></label><label><input type="checkbox" checked={mission.requirements.include_fuel} disabled={busy || recording} onChange={event => change('requirements',{include_fuel:event.target.checked})}/> Include fuel stop</label></div><p className="note">You can also say “skip fuel” or “limit detour to three minutes”. Completed calls and calendar actions are retained.</p></section>
        <section aria-label="Replanning events"><h2>WHY IT REPLANNED</h2>{replans.length?<ol>{replans.map(event => <li key={event.id}><span>REPLAN · {event.step}</span><div><strong>{event.explanation?.trigger || event.message}</strong>{event.explanation && <><p>Affected: {event.explanation.affected_tasks.map(id=>mission.tasks.find(t=>t.id===id)?.description || id).join(', ')}</p><p>Selected: {event.explanation.selected_alternative || 'Pending verification'}</p><p>{event.explanation.constraint_impact}</p></>}</div></li>)}</ol>:<p className="note">{mission.status==='ESCALATED'?'The mission needs attention. Inspect failed or blocked tasks; committed work is saved.':'The mission is following the current plan.'}</p>}</section>
        <details className="world-controls"><summary>Change the simulated external world</summary><div className="controls"><button disabled={busy || recording} onClick={() => change('world',{parking_full:true})}>Garage becomes full</button><button disabled={busy || recording} onClick={() => change('world',{contact_response:'rejected'})}>Ananya declines 4:30</button><button disabled={busy || recording} onClick={() => change('world',{contact_response:'no_answer'})}>Ananya does not answer</button><button disabled={busy || recording} onClick={() => change('world',{fuel_detour_minutes:8})}>Fuel adds 8 minutes</button><button disabled={busy || recording} onClick={() => change('world',{base_travel_minutes:28})}>Traffic slows route</button></div><p className="note">Use these during execution. The demo clock advances one persisted transition each second. Changing completed routing can reopen those tasks without repeating contact or calendar effects.</p></details>
        <details className="mission-record"><summary>Mission Record · {mission.events.length} persisted events</summary><p>Original request: {mission.transcript}</p><p>Mission {mission.id} · revision {mission.revision} · {mission.status}</p><p>Route: {mission.route.parking?.name || 'No parking'} / {mission.route.fuel?.name || 'No fuel'} · ETA {time(mission.eta.arrival)}</p><a className="record-download" href={`/api/missions/${mission.id}/record`} download>Download mission evidence</a><ol>{mission.events.map(event => <li key={event.id}><span>#{event.id} · {event.status}</span><div>{event.message}<small>{event.timestamp}</small></div></li>)}</ol></details>
        <details><summary>Replay protection · inspect preserved state</summary><div className="controls"><button disabled={busy || recording || playing || !replayRequest} onClick={()=>checkGuard('duplicate')}>Submit same request twice</button><button disabled={busy || recording || playing || mission.revision===0} onClick={()=>checkGuard('revision')}>Send stale revision</button><button disabled={busy || recording || playing || !staleConfirmation.current} onClick={()=>checkGuard('confirmation')}>Send stale confirmation</button><button disabled={busy || recording} onClick={listen}>Browser voice change · local fallback</button>{mission.world.fuel_service_failed && <button disabled={busy || recording} onClick={()=>change('world',{fuel_service_failed:false})}>Restore synthetic fuel service</button>}</div><p className="note">Pause progression before checking replay guards. For a stale approval, run the counter-offer preset, then change the detour requirement; this retires the displayed confirmation. The control sends that actual old ID. Rejected commands leave saved state unchanged.</p><p role="status">{guardResult}</p></details>
        {['COMPLETED','ESCALATED','CANCELLED'].includes(mission.status) && <p className="outcome" aria-label="Completion outcome">{mission.spoken_response}</p>}
      </>}
      <details><summary>Personal · Work · Delivery examples</summary><p className="note">These contexts require tools outside the frozen demo contract. Each safely escalates without external effects.</p><div className="controls">{[ ['Personal',"Pick up Mom's medicine. Find a pharmacy on my route, confirm stock, and tell her my ETA."],['Work',"Tell the customer I'm 20 minutes away, check whether the replacement part is available, and replan if it isn't."],['Delivery',"The receiver isn't answering. Find out whether they can still take the shipment and update me if the slot changes."] ].map(([label,text])=><button key={label} disabled={busy || recording} onClick={()=>start(text)}>{label} example</button>)}</div></details>
    </section><footer>{mission?.planner==='Evon'?'Evon':mission?.planner==='provided-plan'?'Provided plan':'DriveOS Mission Interpreter (MockEvon)'} · Frozen planning contract · Deterministic policy · Persistent mission state</footer>
  </main>;
}
