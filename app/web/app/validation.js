'use client';
import { useEffect, useState } from 'react';

const KEY='driveos-human-validation';
const FIELDS=[['microphone_permission_granted','Microphone permission granted'],['recording_completed','Recording completed'],['transcript_observed','Prisma transcript observed with correct name, time and limit'],['mission_created','Mission ID appeared'],['mission_completed','Mission completed'],['replanning_observed','Same-mission garage replan observed'],['timbre_audio_generated','Timbre audio generated'],['timbre_audio_heard_by_user','I heard and understood the final Timbre summary']];
const empty=()=>Object.fromEntries(FIELDS.map(([key])=>[key,false]));

export default function HumanValidation({request,language}) {
  const [checks,setChecks]=useState(empty),[outcome,setOutcome]=useState('INCOMPLETE'),[notes,setNotes]=useState(''),[records,setRecords]=useState([]),[message,setMessage]=useState('');
  useEffect(()=>{
    try {const saved=JSON.parse(localStorage.getItem(KEY) || '[]');if (Array.isArray(saved)) setRecords(saved.slice(-10));}
    catch {setMessage('Saved local validation could not be read.');}
  },[]);
  function save() {
    if (outcome==='PASS' && !FIELDS.every(([key])=>checks[key])) {setMessage('A pass requires every observation, including hearing the final summary.');return;}
    const next=[...records,{date_time:new Date().toISOString(),language,outcome,source:'human-reported',...checks,notes:notes.trim()}].slice(-10);
    try {localStorage.setItem(KEY,JSON.stringify(next));setRecords(next);setMessage('Human-reported result saved on this browser only. It has not updated submission claims.');}
    catch {setMessage('Local storage unavailable. Result was not saved.');}
  }
  function clear() {
    try {localStorage.removeItem(KEY);setRecords([]);setChecks(empty());setNotes('');setOutcome('INCOMPLETE');setMessage('Local validation records cleared.');}
    catch {setMessage('Could not clear local storage.');}
  }
  return <details className="human-validation"><summary>Human voice validation · instructions & local result</summary>
    <p className="fixture">English request: “{request}”</p>
    <p className="note">First check provider credits and allow at least three local requests. Use localhost/HTTPS while stationary. Human validation remains UNVERIFIED until you perform this test.</p>
    <ol className="validation-steps">{['Allow microphone access when prompted (the prompt normally appears after Start).','Click Start Gnani voice mission.','Say the English request above.','Click Stop and run voice mission within 15 seconds.','Verify the actual Prisma transcript: Ananya, 4:30 and five minutes.','Verify mission ID and task progress.','Verify the garage replan to East lot under the same mission ID.','Verify final Timbre playback; press play if autoplay is blocked.'].map((step,index)=><li key={step}>{index+1}. {step}</li>)}</ol>
    <p className="note"><strong>Success:</strong> correct transcript and constraints, completed same mission, replan, total detour ≤5 minutes, and an audible, understandable final Timbre result. <strong>Failure:</strong> permission/capture/provider error, incorrect transcript, escalation or stalled mission, missed replan, incorrect constraint, or missing/unheard final audio. Do not mark a text rehearsal as a microphone pass.</p>
    <p className="note">Recording and transcript are not copied into this result. Store observations only; do not put names, transcripts, recordings, credentials or personal details in notes. The normal voice path still sends audio to Prisma and keeps ignored backend caches.</p>
    <fieldset><legend>Human observations · {language}</legend>{FIELDS.map(([key,label])=><label key={key}><input type="checkbox" checked={checks[key]} onChange={event=>setChecks({...checks,[key]:event.target.checked})}/>{label}</label>)}</fieldset>
    <label>Result <select value={outcome} onChange={event=>setOutcome(event.target.value)}><option value="INCOMPLETE">Incomplete / not run</option><option value="PASS">Human-reported pass</option><option value="FAIL">Human-reported failure</option></select></label>
    <label>Notes (observations only)<textarea value={notes} maxLength={500} onChange={event=>setNotes(event.target.value)} placeholder="For example: autoplay needed a manual play click."/></label>
    <div className="controls"><button onClick={save}>Save local validation result</button><button onClick={clear}>Clear local results</button>{records.length>0 && <a className="record-download" download="driveos-human-validation.json" href={'data:application/json;charset=utf-8,'+encodeURIComponent(JSON.stringify(records,null,2))}>Export local results</a>}</div>
    <p role="status">{message}</p>{records.length>0 && <p className="note">Last saved: {records[records.length-1].date_time} · {records[records.length-1].language} · {records[records.length-1].outcome} · human-reported. At most ten results are kept locally.</p>}
  </details>;
}
